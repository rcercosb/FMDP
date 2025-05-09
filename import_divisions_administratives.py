import sys
import json
import os
import subprocess


def import_each_file(dataset_folder_path, filename, shp2pgsql_path, psql_path):
    input_path = dataset_folder_path + filename + ".shp"
    output_path = dataset_folder_path + filename + ".sql"

    # Creates a SQL file that, in turn, creates a PostgreSQL / PostGIS table with the Shapefile's data
    shp2pgsql_command = shp2pgsql_path + " -s 25831 -I " + input_path + " > " + output_path # -s: specifies the Spatial Reference System Identifier, -I: creates a spatial index
    
    subprocess.run(shp2pgsql_command, shell = True)

    # Removes the table, if exists, before creating it again
    sql_command = "DROP TABLE IF EXISTS " + filename + ";"

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

    shp2pgsql_path = "\"" + config["bin_folder_path"] + "shp2pgsql.exe\""
    psql_path = "\"" + config["bin_folder_path"] + "psql.exe\""

    dataset_folder_entry_names = os.listdir(dataset_folder_path)
    filenames = [entry_name[0:entry_name.index(".")] for entry_name in dataset_folder_entry_names if ".shp" in entry_name] # e.g.: catalunya_50000

    for filename in filenames:
        import_each_file(dataset_folder_path, filename, shp2pgsql_path, psql_path)


if __name__ == "__main__":
    main()