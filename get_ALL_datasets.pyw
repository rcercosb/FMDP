#!.venv\Scripts\pythonw.exe

import tkinter as tk
from tkinter import ttk, messagebox

import json
import os
import subprocess


################
# PROGRESS BAR #
################

root = tk.Tk()
root.title("get_ALL_datasets")

progressbar = ttk.Progressbar(root)
progressbar.place(relx = 0.1, rely = 0.4, relwidth = 0.8, relheight = 0.2)

label = tk.Label(root)
label.place(relx = 0.1, rely = 0.25)

width = 300
height = 200

x = int(root.winfo_screenwidth() / 2 - width / 2)
y = int(root.winfo_screenheight() / 2 - height / 2)

root.geometry("{}x{}+{}+{}".format(width, height, str(x), str(y)))

#######
# GET #
#######

# Loads the configuration file
with open("config.json") as file:
    config = json.load(file)

# Creates the datasets' root folder
try:
    os.mkdir(config["root_folder_path"])
except FileExistsError:
    print("The folder " + config["root_folder_path"] + " already exists")
except PermissionError:
    print("Permission denied: " + config["root_folder_path"])
except Exception as e:
    print("Error: " + e)

progressbar_step = 100 / len(config["datasets_folders_names"])

# For each dataset
for folder_name in config["datasets_folders_names"]:
    label['text'] = "Getting: " + folder_name
    root.update()
    
    folder_path = config["root_folder_path"] + folder_name
    
    # Creates a folder where to save the dataset
    try:
        os.mkdir(folder_path)
    except FileExistsError:
        print("The folder " + folder_path + " already exists")
    except PermissionError:
        print("Permission denied: " + folder_path)
    except Exception as e:
        print("Error: " + e)

    # Runs the Python file that obtains the dataset with the dataset's folder path as an argument
    subprocess.run("python get_" + folder_name + ".py " + folder_path + "/", shell = True)

    progressbar['value'] += progressbar_step
    
messagebox.showinfo(message = "ALL datasets have been downloaded and extracted", title = "get_ALL_datasets")