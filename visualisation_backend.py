#!.venv\Scripts\python.exe

import sqlalchemy
import geopandas


engine = sqlalchemy.create_engine("postgresql://postgres@localhost:5432/Wildfires")

adm_divs_table_column = {
    "cat": {
        "adm_div_table": "catalunya_50000",
        "adm_div_column": "nomcat"
    },
    "p": {
        "adm_div_table": "provincies_50000",
        "adm_div_column": "nomprov"
    },
    "v": {
        "adm_div_table": "vegueries_50000",
        "adm_div_column": "nomvegue"
    },
    "c": {
        "adm_div_table": "comarques_50000",
        "adm_div_column": "nomcomar"
    },
    "m": {
        "adm_div_table": "municipis_50000",
        "adm_div_column": "nommuni"
    }
}


def get_date_range():
    with engine.connect() as con:
        statement = sqlalchemy.sql.text("SELECT MIN(detection_timestamp::date), MAX(detection_timestamp::date) FROM public.wildfires_egif;")
        exe = con.execute(statement)
        
        min_max = exe.fetchone()

        return min_max[0], min_max[1]


def get_adm_div_names(adm_div_level, date_range):
    detection_start = date_range[0].strftime("%Y-%m-%d")
    detection_end = date_range[1].strftime("%Y-%m-%d")

    if adm_div_level == "m":
        sql = """
                SELECT DISTINCT municipality
                FROM public.wildfires_egif
                WHERE detection_timestamp::date BETWEEN '{0}' AND '{1}'
                ORDER BY municipality ASC;
              """.format(detection_start, detection_end)
    else:
        adm_div_column = adm_divs_table_column[adm_div_level]["adm_div_column"]

        sql = """
                SELECT DISTINCT {0}
                FROM public.municipis_50000
                WHERE nommuni IN (
                    SELECT DISTINCT municipality
                    FROM public.wildfires_egif
                    WHERE detection_timestamp::date BETWEEN '{1}' AND '{2}'
                )
                ORDER BY {0} ASC;
              """.format(adm_div_column, detection_start, detection_end)

    statement = sqlalchemy.sql.text(sql)
    
    with engine.connect() as con:
        exe = con.execute(statement)
        
        adm_div_names = exe.fetchall()

        return [adm_div_name[0] for adm_div_name in adm_div_names] # e.g.: [('A',), ('B',)] -> ['A', 'B']


def get_adm_div_geoms(adm_div_level, adm_div_values = None):
    adm_div_table = adm_divs_table_column[adm_div_level]["adm_div_table"]
    adm_div_column = adm_divs_table_column[adm_div_level]["adm_div_column"]
    
    if adm_div_values != None:
        adm_div_values = [value.replace("'", "''") for value in adm_div_values] # e.g.: 'Terres de l'Ebre' -> 'Terres de l''Ebre'
        adm_div_values = ['\'{}\''.format(value) for value in adm_div_values] # e.g.: ["'A'", "'B'"]
        adm_div_values = "(" + ", ".join(adm_div_values) + ")" # e.g.: "('A', 'B')"

    if adm_div_level == "cat":
        sql = """
                SELECT geom
                FROM public.{};
              """.format(adm_div_table)
    else:
        sql = """
                SELECT geom
                FROM public.{0}
                WHERE {1} IN {2};
              """.format(adm_div_table, adm_div_column, adm_div_values)

    with engine.connect() as con:
        adm_divs = geopandas.read_postgis(sql = sql, con = con, crs = 25831)

        return adm_divs.to_crs(epsg = 4326) # Transforms the geometry to the Geographic coordinate system used by ipyleaflet (https://epsg.io/4326)


def get_wildfires(date_range, adm_div_level, adm_div_values = None):
    detection_start = date_range[0].strftime("%Y-%m-%d")
    detection_end = date_range[1].strftime("%Y-%m-%d")

    if adm_div_values != None:
        adm_div_values = [value.replace("'", "''") for value in adm_div_values]
        adm_div_values = ['\'{}\''.format(value) for value in adm_div_values]
        adm_div_values = "(" + ", ".join(adm_div_values) + ")"

    if adm_div_level == "cat":
        sql = """
                SELECT municipality, wildfire_date, geom
                FROM public.wildfires_1986_2023
                WHERE gid IN (
                    SELECT DISTINCT wildfires_1986_2023_gid
                    FROM public.wildfires_egif
                    WHERE detection_timestamp::date BETWEEN '{0}' AND '{1}'
                );
              """.format(detection_start, detection_end)
    elif adm_div_level == "m":
        sql = """
                SELECT municipality, wildfire_date, geom
                FROM public.wildfires_1986_2023
                WHERE gid IN (
                    SELECT DISTINCT wildfires_1986_2023_gid
                    FROM public.wildfires_egif
                    WHERE detection_timestamp::date BETWEEN '{0}' AND '{1}' AND municipality IN {2}
                );
              """.format(detection_start, detection_end, adm_div_values)
    else:
        adm_div_column = adm_divs_table_column[adm_div_level]["adm_div_column"]

        sql = """
                SELECT municipality, wildfire_date, geom
                FROM public.wildfires_1986_2023
                WHERE gid IN (
                    SELECT DISTINCT wildfires_1986_2023_gid
                    FROM public.wildfires_egif
                    WHERE detection_timestamp::date BETWEEN '{0}' AND '{1}' AND municipality IN (
                        SELECT nommuni
                        FROM public.municipis_50000
                        WHERE {2} IN {3}
                    )
                );
              """.format(detection_start, detection_end, adm_div_column, adm_div_values)

    with engine.connect() as con:
        wildfires = geopandas.read_postgis(sql = sql, con = con, parse_dates = ["wildfire_date"])

        wildfires["wildfire_date"] = wildfires["wildfire_date"].dt.strftime('%d/%m/%Y')

        return wildfires.to_crs(epsg = 4326)
    

def get_center(adm_div_GDF):
    adm_div_GDF = adm_div_GDF.dissolve()

    adm_div_GDF["geom"] = adm_div_GDF["geom"].to_crs(epsg = 3857) # Transforms the geometry to the Projected coordinate system used by ipyleaflet (https://epsg.io/3857)

    centroid = adm_div_GDF["geom"].centroid

    centroid = centroid.to_crs(epsg = 4326)  

    return [centroid.loc[0].y, centroid.loc[0].x]