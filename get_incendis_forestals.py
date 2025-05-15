#!.venv\Scripts\python.exe

import sys
import urllib.request
import os
from zipfile import ZipFile
from datetime import datetime


URL = "http://www.gencat.cat/agricultura/sig/bases/incendis"


def download(dataset_folder_path, year):
    urllib.request.urlretrieve(URL + year + ".zip", dataset_folder_path + "incendis" + year + ".zip")

def check_filenames(year_folder_path):
    current_yy = str(datetime.now().year)[-2:] # e.g.: 2025 -> 25
    folder_yy = year_folder_path[-2:] # e.g.: .../incendis00 -> 00

    if folder_yy > current_yy:
        filename_yyyy = "19" + folder_yy # e.g.: 90 > 25 -> 1990
    else:
        filename_yyyy = "20" + folder_yy # e.g.: 18 <= 25 -> 2018

    year_folder_entry_names = os.listdir(year_folder_path)

    # For each entry inside the folder
    for entry_name in year_folder_entry_names:
        if filename_yyyy not in entry_name:
            file_extension = entry_name[entry_name.index('.'):] # e.g.: incendis.shp -> .shp

            os.rename(year_folder_path + "/" + entry_name, year_folder_path + "/incendis" + filename_yyyy + file_extension) # e.g.: .../incendis10/incendis.shp -> .../incendis10/incendis2010.shp

def extract(dataset_folder_path, year):  
    input_path = dataset_folder_path + "incendis" + year + ".zip"
    output_path = dataset_folder_path + "incendis" + year

    # Creates a folder for the contents of a given year's ZIP file
    try:
        os.mkdir(output_path)
    except FileExistsError:
        print("The folder " + output_path + " already exists")
    except PermissionError:
        print("Permission denied: " + output_path)
    except Exception as e:
        print("Error: " + e)

    # Extracts a given year's ZIP file contents into the previous folder
    with ZipFile(input_path, "r") as zipfile:
        zipfile.extractall(path = output_path)

    # Checks the naming of the files extracted (2010's and 2022's is different from the rest)
    check_filenames(output_path)

def main():
    # Reads the first and only argument
    dataset_folder_path = sys.argv[1]

    years_20 = list(map(str, range(86, 100))) # ['86', '87', ... , '98', '99']

    years_21 = list(map(str, range(100, 124))) # ['100', '101', ... , '122', '123']
    years_21 = [y[1:] for y in years_21] # ['00', '01', ... , '22', '23']

    years = years_20 + years_21

    for year in years:
        download(dataset_folder_path, year)
        extract(dataset_folder_path, year)


if __name__ == "__main__":
    main()