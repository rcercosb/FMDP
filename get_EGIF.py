#!.\venv\Scripts\python.exe

import sys
import urllib.request
from zipfile import ZipFile


URL = "https://www.miteco.gob.es/content/dam/miteco/es/biodiversidad/temas/incendios-forestales/estad%C3%ADstica-iiff/Historico_Actualizado.zip"


def download(file_path):
    urllib.request.urlretrieve(URL, file_path)

def extract(input_path, output_path):
    with ZipFile(input_path, "r") as zipfile:
        zipfile.extractall(path = output_path)

def main():
    # Reads the first and only argument
    dataset_folder_path = sys.argv[1]
    
    file_path = dataset_folder_path + "Historico_Actualizado.zip"

    download(file_path)
    extract(file_path, dataset_folder_path)


if __name__ == "__main__":
    main()