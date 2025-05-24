# Anàlisi i visualització interactiva d'incendis forestals

This is the code repository of the Final Master's Degree Project of UOC's Data Science Master's Degree.

It consists of the following files:

- `requirements.txt`: the list of libraries installed in the development environment (Python 3.12.7, venv).
- `start_stop_DB.pyw`: creates a window with two buttons (START and STOP), which the user interacts with to start and stop the PostgreSQL database. It's meant to be run by double-clicking on it.
- `config.json`:
  - `root_folder_path`: the datasets' root folder path.
  - `datasets_folders_names`: the datasets' folders names.
  - `bin_folder_path`: PostgreSQL's bin folder path.
  - `data_folder_path`: PostgreSQL's data folder path.
- `get_ALL_datasets.pyw`: for each dataset, creates a folder where to store it and runs the **get** code file to obtain it. It shows the progress through a progress bar and a message box. It's meant to be run by double-clicking on it.
  - `get_divisions_administratives.py`: downloads and extracts the "Divisions Administratives" dataset (&copy; ICGC).
  - `get_incendis_forestals.py`: downloads and extracts the "Superfícies afectades per incendis forestals v1.1 - Incendis ocorreguts durant l’any YYYY" dataset (&copy; ICGC).
  - `get_EGIF.py`: downlods and extracts the "Estadística General de Incendios Forestales (EGIF)" dataset (&copy; Ministerio para la transición ecológica y el reto demográfico).
  - `get_mapa_militar.py`: downlods and extracts the "Cuadriculas" dataset (&copy; Patricia Luengo Carretero).
- `import_ALL_datasets.pyw`: for each dataset, runs the corresponding **import** code file. It shows the progress through a progress bar and a message box. It's meant to be run by double-clicking on it.
  - `import_divisions_administratives.py`: imports the "Divisions Administratives" dataset into the PostgreSQL database.
  - `import_incendis_forestals.py`: imports the "Superfícies afectades per incendis forestals v1.1 - Incendis ocorreguts durant l’any YYYY" dataset into the PostgreSQL database.
  - `export_all.bas`: runs all the Microsoft Access database saved exports (the "Estadística General de Incendios Forestales (EGIF)" dataset). They export a subset of the tables into the PostgreSQL database.
  - `import_mapa_militar.py`: imports the "Cuadriculas" dataset into the PostgreSQL database.
- `clean_ALL_datasets.pyw`: runs the **clean** SQL file. It shows the progress through a progress bar and a message box. It's meant to be run by double-clicking on it.
  - `clean_ALL_datasets.sql`: cleans the PostgreSQL database tables.
- `app_visualisation.py`: visualises the administrative divisions and the wildfires on a map.
  - `visualisation_backend.py`: the functions inside this file act as middleware between the visualisation and the PostgreSQL database.
