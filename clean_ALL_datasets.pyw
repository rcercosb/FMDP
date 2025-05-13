#!.\venv\Scripts\python.exe

import tkinter as tk
from tkinter import ttk, messagebox

import json
import subprocess
import threading


def clean():
    # Loads the configuration file
    with open("config.json") as file:
        config = json.load(file)

    # Starts the database
    subprocess.run("\"" + config["bin_folder_path"] + "pg_ctl.exe\" -D \"" + config["data_folder_path"] + "\" start", shell = True)

    # Runs the clean_ALL_datasets SQL file
    psql_path = "\"" + config["bin_folder_path"] + "psql.exe\""
    input_path = "./clean_ALL_datasets.sql"

    psql_command = psql_path + " -h localhost -p 5432 -U postgres -d Wildfires -f \"" + input_path + "\""

    subprocess.run(psql_command, shell = True)

    # Stops the database
    subprocess.run("\"" + config["bin_folder_path"] + "pg_ctl.exe\" -D \""  + config["data_folder_path"] +"\" stop", shell = True)

    # Informs the user that the program is done running
    selection = messagebox.showinfo(message = "ALL datasets have been cleaned", title = "clean_ALL_datasets")

    if selection == "ok":
        progressbar.stop()
        progressbar.destroy()
        
        root.quit()
        

if __name__ == "__main__":
    root = tk.Tk()
    root.title("clean_ALL_datasets")

    progressbar = ttk.Progressbar(root, mode = "indeterminate")
    progressbar.place(relx = 0.1, rely = 0.4, relwidth = 0.8, relheight = 0.2)

    label = tk.Label(root)
    label.place(relx = 0.1, rely = 0.25)

    width = 300
    height = 200

    x = int(root.winfo_screenwidth() / 2 - width / 2)
    y = int(root.winfo_screenheight() / 2 - height / 2)

    root.geometry("{}x{}+{}+{}".format(width, height, str(x), str(y)))

    progressbar.start()

    thread = threading.Thread(target = clean)
    thread.start()

    root.mainloop()