import sys
import json
import os
from datetime import datetime
import subprocess


def create_1986_2023_table(psql_path):
    sql_commands = ["DROP SEQUENCE IF EXISTS wildfires_seq;",
                    "DROP TABLE IF EXISTS wildfires_1986_2023;",
                    "CREATE SEQUENCE wildfires_seq INCREMENT 1 START 1;",
                    "CREATE TABLE wildfires_1986_2023 (gid integer NOT NULL, final_code character varying(11), municipality character varying(80), wildfire_date date, geom geometry);"]
    
    for sql_command in sql_commands:
        psql_command = psql_path + " -h localhost -p 5432 -U postgres -d Wildfires -c \"" + sql_command + "\""

        subprocess.run(psql_command, shell = True)

def drop_table(filename_yyyy, psql_path):
    sql_command = "DROP TABLE IF EXISTS incendis" + filename_yyyy + ";"

    psql_command = psql_path + " -h localhost -p 5432 -U postgres -d Wildfires -c \"" + sql_command + "\""

    subprocess.run(psql_command, shell = True)

def repair_insert_into_lines(filename):
    # Reads and stores each line of a given file
    with open(filename, "r", encoding = "UTF-8") as file:
        lines = file.readlines()

    start_line_num_list = []
    end_line_num_list = []

    # Reads each line
    for line_num in range(len(lines)):
        # If the line starts with "INSERT" but doesn't end with "');"
        if lines[line_num].startswith("INSERT") and "');" not in lines[line_num]:
            start_line_num_list.append(line_num) # The line number where the INSERT INTO command starts

        # If the line doesn't start with "INSERT" but ends with "');"
        if not lines[line_num].startswith("INSERT") and "');" in lines[line_num]:
            end_line_num_list.append(line_num) # The line number where the INSERT INTO command ends
            
    remove_line_list = []
    
    # For each start line number (start_line_num_list and end_line_num_list have the same length)
    for i in range(len(start_line_num_list)):
        start_line_num = start_line_num_list[i]
        end_line_num = end_line_num_list[i]

        full_line = ""

        # From start line number to end line number [ , )
        for j in range(start_line_num, end_line_num + 1):
            # Remove all lines, except the first
            if len(full_line) > 0:
                remove_line_list.append(lines[j])

            full_line += lines[j].rstrip() # .rstrip(): removes trailing whitespaces

        lines[start_line_num] = full_line + "\n"

    # Removes each line in remove_line_list
    for line in remove_line_list:
        lines.remove(line)

    # Rewrites the file
    with open(filename, "w", encoding = "UTF-8") as file:
        file.writelines(lines)

def remove_unburned_lines(filename):
    # Reads and stores each line of a given file
    with open(filename, "r", encoding = "UTF-8") as file:
        lines = file.readlines()

    remove_line_list = []

    # Reads each line
    for line in lines:
        # If the line starts with "INSERT" and includes a '0'
        if line.startswith("INSERT") and "'0'" in line:
            remove_line_list.append(line) # It has to be removed

    # Removes each line in remove_line_list
    for line in remove_line_list:
        lines.remove(line)

    # Rewrites the file
    with open(filename, "w", encoding = "UTF-8") as file:
        file.writelines(lines)

def import_each_folder(dataset_folder_path, folder_name, filename_yyyy, shp2pgsql_path, psql_path):
    input_path = dataset_folder_path + folder_name + "/incendis" + filename_yyyy + ".shp"
    output_path = dataset_folder_path + folder_name + "/incendis" + filename_yyyy + ".sql"

    # Creates a SQL file that, in turn, creates a PostgreSQL / PostGIS table with the Shapefile's data
    shp2pgsql_command = shp2pgsql_path + " -s 25831 -I " + input_path + " > " + output_path # -s: specifies the Spatial Reference System Identifier, -I: creates a spatial index
    
    subprocess.run(shp2pgsql_command, shell = True)

    # The vast majority of INSERT INTO commands are a line long.
    # The problem is that the ones that are not, have a string split in two, making the string longer than it really is.
    # Due to this, the database raises an error because the string is longer than the specified maximum length.
    # So, this function finds and concatenates them into a line.
    repair_insert_into_lines(output_path)

    # Deletes the INSERT INTO commands of unburned perimeters (grid_code = '0')
    remove_unburned_lines(output_path)

    # Runs the previous SQL file
    psql_command = psql_path + " -h localhost -p 5432 -U postgres -d Wildfires -f \"" + output_path + "\""

    subprocess.run(psql_command, shell = True)

def populate_1986_2023_table(filename_yyyy, psql_path):
    sql_command = "INSERT INTO wildfires_1986_2023 SELECT nextval('wildfires_seq'), codi_final AS final_code, municipi AS municipality, TO_DATE(data_incen, 'DD/MM/YY') AS wildfire_date, geom FROM incendis" + filename_yyyy + ";"

    psql_command = psql_path + " -h localhost -p 5432 -U postgres -d Wildfires -c \"" + sql_command + "\""

    subprocess.run(psql_command, shell = True)

def main():
    # Reads the first and only argument
    dataset_folder_path = sys.argv[1]

    # Loads the configuration file
    with open("config.json") as file:
        config = json.load(file)

    shp2pgsql_path = "\"" + config["bin_folder_path"] + "shp2pgsql.exe\""
    psql_path = "\"" + config["bin_folder_path"] + "psql.exe\""

    create_1986_2023_table(psql_path) # Creates the table that will store all the wildfires

    dataset_folder_entry_names = os.listdir(dataset_folder_path)
    folders_names = [entry_name for entry_name in dataset_folder_entry_names if ".zip" not in entry_name] # If it's not a ZIP file, it's a folder

    current_yy = str(datetime.now().year)[-2:] # e.g.: 2025 -> 25

    # For each wildfire folder
    for folder_name in folders_names:
        folder_yy = folder_name[-2:] # e.g.: incendis00 -> 00

        if folder_yy > current_yy:
            filename_yyyy = "19" + folder_yy # e.g.: 90 > 25 -> 1990
        else:
            filename_yyyy = "20" + folder_yy # e.g.: 18 <= 25 -> 2018

        drop_table(filename_yyyy, psql_path)
        import_each_folder(dataset_folder_path, folder_name, filename_yyyy, shp2pgsql_path, psql_path)
        
        populate_1986_2023_table(filename_yyyy, psql_path)
        drop_table(filename_yyyy, psql_path)


if __name__ == "__main__":
    main()