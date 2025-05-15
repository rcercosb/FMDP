#!.venv\Scripts\pythonw.exe

import json
import subprocess

import tkinter as tk
from tkinter import Button


# Loads the configuration file
with open("config.json") as file:
    config = json.load(file)

############
# START DB #
############

def start_db():
    start_button.config(fg = "black")
    stop_button.config(fg = "red")

    subprocess.run("\"" + config["bin_folder_path"] + "pg_ctl.exe\" -D \"" + config["data_folder_path"] + "\" start", shell = True)

###########
# STOP DB #
###########

def stop_db():
    start_button.config(fg = "green")
    stop_button.config(fg = "black")

    subprocess.run("\"" + config["bin_folder_path"] + "pg_ctl.exe\" -D \"" + config["data_folder_path"] + "\" stop", shell = True)

###########
# BUTTONS #
###########

root = tk.Tk()
root.title("start_stop_DB")

width = 300
height = 200

x = int(root.winfo_screenwidth() / 2 - width / 2)
y = int(root.winfo_screenheight() / 2 - height / 2)

root.geometry("{}x{}+{}+{}".format(width, height, str(x), str(y)))

start_button = Button(root, text = "START", command = start_db, width = 10, height = 3, fg = "green")
stop_button = Button(root, text = "STOP", command = stop_db, width = 10, height = 3)

start_button.pack(side = "left", padx = 35)
stop_button.pack(side = "right", padx = 35)

root.mainloop()