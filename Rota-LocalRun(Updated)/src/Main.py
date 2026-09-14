# --- Imports ---
import os
import time
import numpy as np
import pandas as pd
import tkinter as tk
import random as rd
import json
import webbrowser
from pathlib import Path
from tkinter import messagebox

import Helper as hp

root = tk.Tk()
root.withdraw()  # hides the main window

# Verify that files exist
if not os.path.exists("Files\\Data Base.xlsx"):
    messagebox.showerror("Error", "Data Base.xlsx file not found.")
    root.quit()
    exit()

if not os.path.exists("Files\\Weekly Rota.xlsx"):
    messagebox.showerror("Error", "Weekly Rota.xlsx file not found.")
    root.quit()
    exit()

if not os.path.exists("Files\\Women.txt"):
    messagebox.showinfo("Warning", "NO Women.txt file found. This will impossibilitate women assignment to CC5 task on Fridays.")

# --- Get file directories ---
script_dir = Path(__file__).parent
root_dir = script_dir.parent        # parent folder of src/

worker_data_path = root_dir / "Files" / "Data Base.xlsx"
weekly_data_path = root_dir / "Files" / "Weekly Rota.xlsx"
women_path = root_dir / "Files" / "Women.txt"

print("Last modified:", time.ctime(os.path.getmtime(worker_data_path)), time.ctime(os.path.getmtime(weekly_data_path)))

# --- Get Worker Data and Worker Dispositions + verifications ---
worker_data = pd.read_excel(worker_data_path)
weekly_data = pd.read_excel(weekly_data_path)
names = np.array(weekly_data.iloc[:, 0].tolist())[1:]

# Verify if names match
for name in names:
    if name not in worker_data['Name'].values:
        messagebox.showerror("Error", f"Worker not in database: {name}")
        root.quit()
        exit()
for name in worker_data['Name'].values:
    if name not in names:
        messagebox.showerror("Error", f"Worker not in Weekly Rota: {name}")
        root.quit()
        exit()

# Switch the names order to the one in the worker data
names = np.array(worker_data['Name'].values.tolist())

# Ensure 'Cathlab' and 'Pacing' columns are last, they won't be used for task assignment 
if 'Cathlab' in worker_data.columns and 'Pacing' in worker_data.columns:
    cols = list(worker_data.columns)
    if cols[-2] != 'Cathlab' or cols[-1] != 'Pacing':
        cols.remove('Cathlab')
        cols.remove('Pacing')
        cols.append('Cathlab')
        cols.append('Pacing')
        worker_data = worker_data[cols]
        worker_data.to_excel(worker_data_path, index=False)
        time.sleep(0.5) # wait for file to be saved

# --- Organize Worker Data ---
tasks = np.array(worker_data.columns.values.tolist())[2:-2] # Array with all tasks

Assistants = {} # Dic with all Assistants: Name -> abilities for tasks (in same order as tasks)
Doctors = {} # Dic with all Doctors: Name -> abilities for tasks (in same order as tasks)
Physiologists = {} # Dic with all Physiologists: Name -> abilities for tasks (in same order as tasks)

worker_dataMx = worker_data.values.tolist()
for i in range(len(worker_dataMx)):
    row = worker_dataMx[i]
    name = row[0]
    role = row[1]
    abilities = ['NO' if pd.isna(x) or x == '' or x == 'nan' else x for x in row[2:-2]]  # Exclude 'Cathlab' and 'Pacing' columns
    if role == 'Assistant':
        Assistants[name] = abilities
    elif role == 'Doctor':
        Doctors[name] = abilities
    elif role == 'Physiologist':
        Physiologists[name] = abilities

# Store data for frontend use
# Original worker order
original_worker_order = names.tolist()
# Last physiologist and last Assistant in original order
last_physiologist = max([original_worker_order.index(name) for name in Physiologists.keys()])
last_assistant = max([original_worker_order.index(name) for name in Assistants.keys()])

# Admin workers will only work as admins if they are not needed elsewhere so store them seperately
Admins = [] # List of admin workers
n = tasks.tolist().index('Admin')  # Get where Admin appears in tasks
for i in range(len(worker_dataMx)):
    row = worker_dataMx[i]
    name = row[0]
    if row[2 + n] == 'YES':
        Admins.append(name)

# Trainees will have to leave for Student Leave (SL) so store them seperately
Trainees = [] # List of trainee workers
n = tasks.tolist().index('SL')  # Get where SL appears in tasks
for i in range(len(worker_dataMx)):
    row = worker_dataMx[i]
    name = row[0]
    if row[2 + n] == 'YES':
        Trainees.append(name)

# Get women
with open(women_path, "r") as f:
    women = [line.strip() for line in f.readlines()]

if len(women) == 0:
    messagebox.showinfo("Warning", "No women found in Women.txt. This will impossibilitate women assignment to CC5 task on Fridays.")

# Print worker abilities for debugging
'''print("Physiologists:\n")
print(f"Tasks: {tasks}\n")
for physio, abilities in Physiologists.items():
    print(f"{physio}: {abilities}\n")
print("Doctors:\n")
print(f"Tasks: {tasks}\n")
for doctor, abilities in Doctors.items():
    print(f"{doctor}: {abilities}\n")
print("Assistants:\n")
print(f"Tasks: {tasks}\n")
for assistant, abilities in Assistants.items():
    print(f"{assistant}: {abilities}\n")'''


# --- Organize Weekly Worker Dispositions ---
# Disposition is divided into Morning, Afternoon for the seven days of the week
dispositions = {} # Dic: worker name -> numpy array with 7 lists (morning, afternoon)
weekly_dataMx = weekly_data.values.tolist()
for i in range(1, len(weekly_dataMx)):
    row = weekly_dataMx[i]
    name = row[0]
    week_dispositions = []
    for j in range(1, 15, 2):
        morning = row[j] if row[j] not in [np.nan, '', 'nan'] else 'OFF'
        afternoon = row[j+1] if row[j+1] not in [np.nan, '', 'nan'] else 'OFF'
        joint = (morning, afternoon)
        week_dispositions.append(joint)
    dispositions[name] = np.array(week_dispositions)

# Change Dr Elkady and Dr Khalil dispositions to only work on Monday am and Tuesday am respectively
if "Dr Elkady" in dispositions:
    # if present monday am, set rest of week to OFF
    if dispositions["Dr Elkady"][0][0] == "IN":
        dispositions["Dr Elkady"] = np.array([("IN", "OFF")] + [("OFF", "OFF")] * 6)
    else: 
        dispositions["Dr Elkady"] = np.array([("OFF", "OFF")] * 7)
if "Dr Khalil" in dispositions:
    # if present tuesday am, set rest of week to OFF
    if dispositions["Dr Khalil"][1][0] == "IN":
        dispositions["Dr Khalil"] = np.array([("OFF", "OFF")] + [("IN", "OFF")] + [("OFF", "OFF")] * 5)
    else: 
        dispositions["Dr Khalil"] = np.array([("OFF", "OFF")] * 7)

# Print dispositions for debugging
'''for name, dispo in dispositions.items():
    print(f"{name}:\n {dispo}\n")'''

# --- Variables needed to start organizing rota ---
task_schedules = {task: [[] for _ in range(14)] for task in tasks} # Dic: task_name -> list of lists with assigned workers for each day part

present_workers = [] #workers in for the day part
used_workers = [[] for _ in range(14)] #workers already assigned to tasks for each day part

# Check the best days for student leaves

# count how many physios are in each day part
physios_in = [0 for i in range(14)] # List of physiologists available in each day part
for worker in dispositions.keys():
    if worker in Physiologists:
        flat = dispositions[worker].flatten()
        for i in range(len(flat)):
            if flat[i] == "IN":
                physios_in[i] += 1

student_leave_days = hp.check_student_leave_days(dispositions, Trainees, physios_in)

# --- Start organizing rota with conditions in mind ---
for i in range(14):
    # Get day and part
    day = i // 2
    part = i % 2

    # Shuffle workers to avoid repeating patterns
    dispositions = hp.randomize_dict_keys(dispositions)
    # Change admins to last in order to prioritize other workers
    for admin in Admins:
        if admin in dispositions:
            dispo = dispositions.pop(admin)
            dispositions[admin] = dispo
    # Put Dr Elkday and Dr Khalil at the front to prioritize their limited availability
    for special_doc in ["Dr Elkady", "Dr Khalil"]:
        if special_doc in dispositions:
            dispo = dispositions.pop(special_doc)
            dispositions = {special_doc: dispo, **dispositions}

    present_workers = [worker for worker, dispo in dispositions.items() if dispo[day][part] == "IN"]
    # prioritize tasks with less available workers
    sorted_tasks, Doctors_ord, Phys_ord, Assist_ord = hp.order_tasks(present_workers, tasks, Doctors, Physiologists, Assistants, day)
    # prioritize IP Echo and Analysis tasks as they need a minimum number of physiologists
    if "IP Echo" in sorted_tasks:
        sorted_tasks, Doctors_ord, Phys_ord, Assist_ord = hp.prioritize_task(sorted_tasks, Doctors_ord, Phys_ord, Assist_ord, "IP Echo")
    if "Analysis" in sorted_tasks:
        sorted_tasks, Doctors_ord, Phys_ord, Assist_ord = hp.prioritize_task(sorted_tasks, Doctors_ord, Phys_ord, Assist_ord, "Analysis")
    # prioritize CB6 as it needs the 3 workers
    if "CB6" in sorted_tasks:
        sorted_tasks, Doctors_ord, Phys_ord, Assist_ord = hp.prioritize_task(sorted_tasks, Doctors_ord, Phys_ord, Assist_ord, "CB6")
    # on Friday prioritize CC5 to choose a woman as soon as possible, on Wendsday CC5 is prioritized as should be done by Liliana, Charlotte or Raiyan
    if day == 4 or day == 2:
        if "CC5" in sorted_tasks:
            sorted_tasks, Doctors_ord, Phys_ord, Assist_ord = hp.prioritize_task(sorted_tasks, Doctors_ord, Phys_ord, Assist_ord, "CC5")

    # pre-assigned workers can't be chosen for other tasks
    # Iqbal and Sharon if present will do CC1 on Monday pm, Friday all day and Sunday pm, cc1 won't happen if Iqbal is not present
    if day == 0 and part == 1:  # Monday pm
        if "Iqbal" in present_workers:
            used_workers[i].append("Iqbal")
        if "Sharon" in present_workers:
            used_workers[i].append("Sharon")
    if day == 4:  # Friday all day
        if "Iqbal" in present_workers:
            used_workers[i].append("Iqbal")
        if "Sharon" in present_workers:
            used_workers[i].append("Sharon")
    if day == 6 and part == 1:  # Sunday pm
        if "Iqbal" in present_workers:
            used_workers[i].append("Iqbal")
        if "Sharon" in present_workers:
            used_workers[i].append("Sharon")
    # if present Iqbal will do analyisis Saturday all day and Sunday am
    if day == 5:  # Saturday all day
        if "Iqbal" in present_workers:
            used_workers[i].append("Iqbal")
    if day == 6 and part == 0:  # Sunday am
        if "Iqbal" in present_workers:
            used_workers[i].append("Iqbal")
    # if present Sam does Ip Echo Sunday am
    if day == 6 and part == 0:  # Sunday am
        if "Sam" in present_workers:
            used_workers[i].append("Sam")
    # if present Raiyan will do CC5 on Monday
    if day == 0:  # Monday
        if "Raiyan" in present_workers:
            used_workers[i].append("Raiyan")
    # if present Gabriel will do CC2
    if "Gabriel" in present_workers:
        used_workers[i].append("Gabriel")
    # Dr Alzetani does CC9 when Dr Henein is in on Thursday	
    if day == 3 and "Dr Henein" in present_workers:  # Thursday
        used_workers[i].append("Dr Alzetani")
    # Dr Marcus when in on Thursday am does CC6 and on Friday am does CB6
    if day == 3 and part == 0 and "Dr Marcus" in present_workers:
        used_workers[i].append("Dr Marcus")
    if day == 4 and part == 0 and "Dr Marcus" in present_workers:
        used_workers[i].append("Dr Marcus")
    # Dr Khalil when in on Wednesday pm does CC10
    if day == 2 and part == 1 and "Dr Khalil" in present_workers:
        used_workers[i].append("Dr Khalil")
    # If there's more than 7 physiologists present, Nick will always do MGMT
    physio_count = sum(1 for worker in present_workers if worker in Physiologists)
    if physio_count > 7 and "Nick" in present_workers:
        used_workers[i].append("Nick")
    # Trainees on student leave won't be assigned
    for trainee, leave_days in student_leave_days.items():
        if i in leave_days:
            if trainee in present_workers:
                used_workers[i].append(trainee)
                task_schedules['SL'][i].append(trainee)

    # Start assigning tasks based on conditions
    for task in sorted_tasks:
        # Start with specific conditions:
        if task == "CC1": # only on Monday pm, Wednesday all day, Friday all day and Sunday pm, assign Iqbal and Sharon if present every day except Wednesday	
            if (day == 0 and part == 1) or (day == 4) or (day == 6 and part == 1):
                # Assign Iqbal if present
                if "Iqbal" in present_workers:
                    task_schedules[task][i].append("Iqbal")
                else:
                    # NO CC1
                    task_schedules[task][i] = []
                if len(task_schedules[task][i]) > 0:
                    # Assign Sharon if present
                    if "Sharon" in present_workers:
                        task_schedules[task][i].append("Sharon")
                    else:
                        # Assign an assistant instead
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
            elif day == 2:  # Wednesday all day needs one physiologist and one assistant/or Dawn
                # Assign physiologist
                hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)

                # Assign assistant
                if len(task_schedules[task][i]) > 0:
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
            else:
                task_schedules[task][i] = []
        elif task == "CC2": # not on weekends, assisntants will also assist on CC6 and if Gabriel is present he will do CC2
            if day in [5, 6]:
                task_schedules[task][i] = []
            else:
                # Verify if Gabriel is present
                if "Gabriel" in present_workers:
                    task_schedules[task][i].append("Gabriel")
                else:
                    # Assign other physiologist
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                # Verify if there is a saved assistant from CC6 otherwise assign new one
                if len(task_schedules[task][i]) > 0:
                    if task_schedules["CC6"][i] and len(task_schedules["CC6"][i]) > 1:
                        task_schedules[task][i].append(task_schedules["CC6"][i][1])  # second assigned worker in CC6 is the assistant
                    else:
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
        elif task == "CC4": # not on weekends, only needs an assistant
            if day in [5, 6]:
                task_schedules[task][i] = []
            else:
                # Assign assistant
                hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
        elif task == "CC5": # only on Monday, Wednesday and Friday, on Monday if Raiyan is present he will do CC5, on Wendsday CC5 should be done by Liliana, Charlotte or Raiyan, Friday needs a woman as physiologist when possible  
            if day == 0:
                if "Raiyan" in present_workers:
                    task_schedules[task][i].append("Raiyan")
                else:
                    # Assign other physiologist
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                # Assign assistant
                if len(task_schedules[task][i]) > 0:
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
            elif day == 2:
                possible_workers = [worker for worker in present_workers if worker in ["Liliana", "Charlotte", "Raiyan"] and worker not in used_workers[i]]
                # Assign random worker from possible workers
                if possible_workers:
                    choice = rd.choice(possible_workers)
                    task_schedules[task][i].append(choice)
                    used_workers[i].append(choice)
                else:
                    # Assign other physiologist
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                # Assign assistant
                if len(task_schedules[task][i]) > 0:
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)       
            elif day == 4:
                # assign a woman physiologist if possible
                if len(women) > 0:
                    for worker, dispo in dispositions.items():
                        if dispo[day][part] == "IN" and worker not in used_workers[i] and worker in women:
                            if worker in Phys_ord and Phys_ord[worker][np.where(sorted_tasks == task)[0][0]] == 'YES':
                                task_schedules[task][i].append(worker)
                                used_workers[i].append(worker)
                                break
                if len(task_schedules[task][i]) == 0:
                    # Assign any physiologist
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                # Assign assistant
                if len(task_schedules[task][i]) > 0:
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
            else:
                task_schedules[task][i] = []
        elif task == "CC6": # not on weekends, assign same assistant as CC2, on Thursday am assign Dr Marcus if present, on Monday am and Tuesday am may have a doctor
            if day in [5, 6]:
                task_schedules[task][i] = []
            else:
                # Assign Dr Marcus if Thursday am
                if day == 3 and part == 0:
                    if "Dr Marcus" in present_workers:
                        task_schedules[task][i].append("Dr Marcus")
                    if len(task_schedules[task][i]) == 0:
                        # Assign physiologist instead
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                elif (day == 0 and part == 0) or (day == 1 and part == 0):
                    # try to assign a doctor first
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Doctors_ord, sorted_tasks)
                    if len(task_schedules[task][i]) == 0:
                        # Assign physiologist instead
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                else:
                    # Assign a physiologist instead
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                    # Verify if there is a saved assistant from CC2 otherwise assign new one
                if len(task_schedules[task][i]) > 0:
                    if task_schedules["CC2"][i] and len(task_schedules["CC2"][i]) > 1:
                        task_schedules[task][i].append(task_schedules["CC2"][i][1])  # second assigned worker in CC2 is the assistant
                    else:
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
        elif task == "CC9": # only on Monday, Tuesday and Thursday, on Thursday assign Dr Alzetani if Dr Henein is present
            if day == 3:
                # Assign Dr Alzetani if Dr Henein is present
                if "Dr Henein" in present_workers and "Dr Alzetani" in present_workers:
                    task_schedules[task][i].append("Dr Alzetani")
                else:
                    # Assign a physiologist instead
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                # Assign assistant
                if len(task_schedules[task][i]) > 0:
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
                            
            elif day == 0 or day == 1:   
                # Assign physiologist
                hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                
                # Assign assistant
                if len(task_schedules[task][i]) > 0:
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)

            else:
                task_schedules[task][i] = []
        elif task == "CC10": # not on weekends, Dr Khalil on Wednesday pm if present
            if day == 2 and part == 1:
                # Assign Dr Khalil if present
                if "Dr Khalil" in present_workers:
                    task_schedules[task][i].append("Dr Khalil")
                else:
                    # Assign physiologist instead
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                # Assign assistant
                if len(task_schedules[task][i]) > 0:
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
            elif day in [5, 6]:
                task_schedules[task][i] = []
            else:
                # Assign physiologist
                hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                # Assign assistant
                if len(task_schedules[task][i]) > 0:
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
        elif task == "CB2": # only Thursday pm, only needs an assistant
            if day == 3 and part == 1:
                hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
            else:
                task_schedules[task][i] = []
        elif task == "CB4": # only Tuesday am and Thursday am, only needs an assistant
            if (day == 1 and part == 0) or (day == 3 and part == 0):
                hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
            else:
                task_schedules[task][i] = []
        elif task == "CB6": # Tuesday all day, Wednesday all day, Thursday all day and Friday am, needs one doctor, one physiologist and one assistant, Friday am dr Marcus if present
            if (day == 4 and part == 0):
                if "Dr Marcus" in present_workers:
                    task_schedules[task][i].append("Dr Marcus")
                    # Volodymyr can't work with Dr Marcus
                    used_workers[i].append("Volodymyr")
                    # Assign physiologist
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                    # Assign assistant
                    if len(task_schedules[task][i]) > 0:
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
                    used_workers[i].remove("Volodymyr")
                else:
                    # Assign doctor
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Doctors_ord, sorted_tasks)
                    doctor = task_schedules[task][i][0] if len(task_schedules[task][i]) > 0 else None
                    if doctor == "Dr Henein": # Mark does not work with Dr Henein
                        used_workers[i].append("Mark")
                        # Assign physiologist
                        if len(task_schedules[task][i]) > 0:
                            hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                        # Assign assistant
                        if len(task_schedules[task][i]) > 0:
                            hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
                        used_workers[i].remove("Mark")
                    elif doctor == "Dr Alzetani": # Volodymyr does not work with Dr Marcus or Dr Alzetani
                        used_workers[i].append("Volodymyr")
                        # Assign physiologist
                        if len(task_schedules[task][i]) > 0:
                            hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                        # Assign assistant
                        if len(task_schedules[task][i]) > 0:
                            hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
                        used_workers[i].remove("Volodymyr")
                    else:
                        # Assign physiologist
                        if len(task_schedules[task][i]) > 0:
                            hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                        # Assign assistant
                        if len(task_schedules[task][i]) > 0:
                            hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
            elif day in [1, 2, 3] :
                # Assign doctor
                hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Doctors_ord, sorted_tasks)
                doctor = task_schedules[task][i][0] if len(task_schedules[task][i]) > 0 else None
                if doctor == "Dr Henein": # Mark does not work with Dr Henein
                    used_workers[i].append("Mark")
                    # Assign physiologist
                    if len(task_schedules[task][i]) > 0:
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                    # Assign assistant
                    if len(task_schedules[task][i]) > 0:
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
                    used_workers[i].remove("Mark")
                elif doctor == "Dr Marcus" or doctor == "Dr Alzetani": # Volodymyr does not work with Dr Marcus or Dr Alzetani
                    used_workers[i].append("Volodymyr")
                    # Assign physiologist
                    if len(task_schedules[task][i]) > 0:
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                    # Assign assistant
                    if len(task_schedules[task][i]) > 0:
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
                    used_workers[i].remove("Volodymyr")
                else:
                    # Assign physiologist
                    if len(task_schedules[task][i]) > 0:
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                    # Assign assistant
                    if len(task_schedules[task][i]) > 0:
                        hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
            else:
                task_schedules[task][i] = []
        elif task == "IP Echo": # needs at least 2 physiologists, not on weekends except Sunday am when Sam will do it if present
            if day == 6 and part == 0:
                if "Sam" in present_workers:
                    task_schedules[task][i].append("Sam")
            elif day == 5 or (day == 6 and part == 1):
                task_schedules[task][i] = []
            else:
                # Assign first physiologist
                hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
                # Assign second physiologist
                hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
        elif task == "Analysis": # needs at least 1 physiologist, Iqbal on weekends except Sunday pm, not on Sunday pm
            if day == 6 and part == 1:
                task_schedules[task][i] = []
            elif day == 5 or (day == 6 and part == 0):
                if "Iqbal" in present_workers:
                    task_schedules[task][i].append("Iqbal")
            else:
                # Assign physiologist
                hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
        elif task == "MGMT":
            if "Nick" in present_workers and physio_count > 7:
                task_schedules[task][i].append("Nick")
        elif task == "ECG": # 1 assistant only every day
            hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Assist_ord, sorted_tasks)
        else:
            continue  # Admin and Reviewing will be assigned at the end, SL already assigned
    # End of task assignment for the day part
    
    # if there's a physio unassigned that can do Reviewing, assign them
    hp.assign_worker(task_schedules, used_workers, i, day, part, "R", dispositions, Phys_ord, sorted_tasks)

    # if there are physios unassigned, assign to IP Echo and Analysis if possible
    for j in range(2): # assign one physio to each task twice
        for task in ["Analysis", "IP Echo"]:
            if task in task_schedules:
                if len(task_schedules[task][i]) > 0:
                    hp.assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, Phys_ord, sorted_tasks)
    # if there are admins unassigned assign to admin
    for worker in Admins:
        if worker in present_workers and worker not in used_workers[i]:
            task_schedules["Admin"][i].append(worker)
            used_workers[i].append(worker)

# print rota for debugging
'''for day_part in range(14):
    day = day_part // 2
    part = day_part % 2
    print(f"\nDay {day+1} {'AM' if part == 0 else 'PM'} Rota:\n")
    for task in tasks:
        assigned_workers = task_schedules[task][day_part]
        if assigned_workers:
            print(task + ": ", end="")
            print(assigned_workers)
    
    print()'''

# --- Write and open Html rota ---
html_template = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Schedule</title>
<font size="40pt">
<style>
    table {{
        border-collapse: collapse;

    }}
    th, td {{
        border: 1px solid black;
        padding: 6px;
        text-align: center;
    }}
    /* Thicker vertical separator after each day's PM column */
    th.day-sep, td.day-sep {{
        border-right: 10px solid black;
    }}
    /* Thicker vertical separator after the names column */
    th.name-sep, td.name-sep {{
        border-right: 10px solid black;
    }}
    /* Thicker horizontal separator after rows (applied to the whole row) */
    tr.row-sep th, tr.row-sep td {{
        border-bottom: 10px solid black;
    }}
    th {{
        background-color: #eee;
    }}
    thead tr {{
        height: 40px;
    }}
    thead th[rowspan="2"] {{
        height: 80px;
        vertical-align: middle;
        text-align: center;
        /* Ensure header cells that span two rows have the thick bottom border so the separator
           spans from the very first to the very last column */
        border-bottom: 10px solid black;
    }}
    td[contenteditable="true"] {{
        vertical-align: top;
        white-space: pre-wrap;
    }}
    /* Alternating row colors for body only; leave header and first (name) column unchanged */
    tbody tr:nth-child(even) td {{ background: #CCC; }}
    tbody tr:nth-child(odd) td {{ background: #FFF; }}
</style>
</head>
<body>

<div id="title-wrapper" style="margin-bottom:8px; text-align:left;">
    <img id="title-image" src="../Assets/title(fs10).png" alt="Task Schedule" style="max-height:120px; display:inline-block; margin:0; vertical-align:middle;">
    <h2 id="title-text" style="display:none; text-align:left; margin:0;">Task Schedule</h2>
</div>

<table id="schedule-table"></table>

<script>
const taskSchedules = {json.dumps(task_schedules)};
const originalWorkerOrder = {json.dumps(original_worker_order)};
const lastPhysioIndex = {last_physiologist};
const lastAssistIndex = {last_assistant};
const allPeople = (typeof originalWorkerOrder !== 'undefined' && Array.isArray(originalWorkerOrder) && originalWorkerOrder.length > 0) ? originalWorkerOrder.slice() : {json.dumps(list(names))};
</script>

<script>
    document.getElementById('title-image').addEventListener('error', function() {{
        this.style.display = 'none';
        document.getElementById('title-text').style.display = 'block';
    }});
</script>

<div id ="caption" style="margin-top:12px; font-size:30pt; color:#070707;">
    <p>AL - Annual Leave <br> LT - Lieu Time <br> SL - Study Leave <br> ADO - Allocated Day Off <br> MGMT - Management <br> R-Reviewing <br> ᴮ-Bleep <br> ᴰ-Check 3 Crash Trolleys (Defib) + Blood Glucose</p>
</div>

<div id ="footer" style="margin-top:12px; font-size:35pt; color:#070707; text-align:center;">
    <p>This Rota is subject to change at short notice. Please check throughout the week.</p>
</div>

<script src="script.js"></script>
</body>
</html>
"""

# Write HTML file inside the src directory
out = script_dir / "schedule.html"
out.write_text(html_template, encoding="utf-8")

# Open in browser
webbrowser.open(out.resolve().as_uri())