#!.\venv\Scripts\python.exe

import tkinter as tk
from tkinter import ttk, messagebox

import json
import subprocess


################
# PROGRESS BAR #
################

root = tk.Tk()
root.title("import_ALL_datasets")

progressbar = ttk.Progressbar(root)
progressbar.place(relx = 0.1, rely = 0.4, relwidth = 0.8, relheight = 0.2)

label = tk.Label(root)
label.place(relx = 0.1, rely = 0.25)

width = 300
height = 200

x = int(root.winfo_screenwidth() / 2 - width / 2)
y = int(root.winfo_screenheight() / 2 - height / 2)

root.geometry("{}x{}+{}+{}".format(width, height, str(x), str(y)))

##########
# IMPORT #
##########

# Loads the configuration file
with open("config.json") as file:
    config = json.load(file)

# Starts the database
subprocess.run("\"" + config["bin_folder_path"] + "pg_ctl.exe\" -D \"" + config["data_folder_path"] + "\" start", shell = True)

pg_step = 100 / len(config["datasets_folders_names"])

# For each dataset
for folder_name in config["datasets_folders_names"]:
    label['text'] = "Importing: " + folder_name
    root.update()

    folder_path = config["root_folder_path"] + folder_name
   
    # Runs the Python file that imports the dataset with the dataset's folder path as an argument
    subprocess.run("python import_" + folder_name + ".py " + folder_path + "/", shell = True)

    progressbar['value'] += pg_step

# Stops the database
subprocess.run("\"" + config["bin_folder_path"] + "pg_ctl.exe\" -D \""  + config["data_folder_path"] +"\" stop", shell = True)

messagebox.showinfo(message = "ALL datasets have been imported", title = "import_ALL_datasets")