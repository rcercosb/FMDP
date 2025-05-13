#!.\venv\Scripts\python.exe

import sys
import json
import subprocess


def convert_file(dataset_folder_path, ogr2ogr_path):
    input_path = dataset_folder_path + "doc.kml"
    output_path = dataset_folder_path + "shapefile"

    ogr2ogr_command = ogr2ogr_path + " -f \"ESRI Shapefile\" " + output_path + " " + input_path

    subprocess.run(ogr2ogr_command, shell = True)

def import_file(dataset_folder_path, shp2pgsql_path, psql_path):
    input_path = dataset_folder_path + "/shapefile/CUADRICULAS.shp"
    output_path = dataset_folder_path + "cuadriculas.sql"

    # Creates a SQL file that, in turn, creates a PostgreSQL / PostGIS table with the Shapefile's data
    shp2pgsql_command = shp2pgsql_path + " -s 4326 -I " + input_path + " > " + output_path # -s: specifies the Spatial Reference System Identifier (CUADRICULAS.prj -> https://epsg.io/4326), -I: creates a spatial index
    
    subprocess.run(shp2pgsql_command, shell = True)

    # Removes the table, if exists, before creating it again
    sql_command = "DROP TABLE IF EXISTS cuadriculas;"

    psql_command = psql_path + " -h localhost -p 5432 -U postgres -d Wildfires -c \"" + sql_command + "\""

    subprocess.run(psql_command, shell = True)

    # Runs the previous SQL file
    psql_command = psql_path + " -h localhost -p 5432 -U postgres -d Wildfires -f \"" + output_path + "\""

    subprocess.run(psql_command, shell = True)

def main():
    # Reads the first and only argument
    dataset_folder_path = sys.argv[1]

    # Loads the configuration file
    with open("config.json") as file:
        config = json.load(file)

    ogr2ogr_path = "\"" + config["bin_folder_path"] + "ogr2ogr.exe\""

    convert_file(dataset_folder_path, ogr2ogr_path)    
    
    shp2pgsql_path = "\"" + config["bin_folder_path"] + "shp2pgsql.exe\""
    psql_path = "\"" + config["bin_folder_path"] + "psql.exe\""

    import_file(dataset_folder_path, shp2pgsql_path, psql_path)


if __name__ == "__main__":
    main()