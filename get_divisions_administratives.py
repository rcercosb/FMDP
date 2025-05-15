#!.venv\Scripts\python.exe

import sys
import urllib.request
from zipfile import ZipFile
import os


URL = "https://datacloud.icgc.cat/datacloud/divisions-administratives/shp/divisions-administratives-v2r1-20250101.zip"


def download(file_path):
    urllib.request.urlretrieve(URL, file_path)

def filter_filenames(filenames):
    divisions_scales = ["municipis-50000-", "comarques-50000-", "vegueries-50000-", "provincies-50000-", "catalunya-50000-", "municipis-250000-"]
    
    filtered_filenames = []

    for filename in filenames:
        for division_scale in divisions_scales:
            if division_scale in filename:
                filtered_filenames.append(filename)

    return filtered_filenames

def get_new_filename(filename):
    start_index = len("divisions-administratives-v2r1-")
    end_index = filename.index("-20250101")

    extension = filename[filename.index("."):] # e.g.: .shp

    return filename[start_index:end_index].replace("-", "_") + extension # e.g.: comarques_50000.shp

def extract(dataset_folder_path, file_path):
    with ZipFile(file_path, "r") as zipfile:
        filtered_filenames = filter_filenames(zipfile.namelist()) # Gets the filenames of the divisions and scales of interest

        # For each file of interest
        for filename in filtered_filenames:
            zipfile.extract(path = dataset_folder_path, member = filename) # Extracts the given file
            
            os.rename(dataset_folder_path + filename, dataset_folder_path + get_new_filename(filename)) # Renames the file

def main():
    # Reads the first and only argument
    dataset_folder_path = str(sys.argv[1])
    file_path = dataset_folder_path + "div_adm.zip"

    download(file_path)
    extract(dataset_folder_path, file_path)


if __name__ == "__main__":
    main()