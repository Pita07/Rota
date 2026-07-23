import numpy as np
import random as rd

# Function to randomize dictionary keys
def randomize_dict_keys(d):
    keys = list(d.keys())
    rd.shuffle(keys)
    new_dict = {k: d[k] for k in keys}
    return new_dict

# Function to find full days where a worker is available
def full_days(dispo):
    full_days = []
    for i in range(0, len(dispo), 2):
        if dispo[i] == "IN" and dispo[i + 1] == "IN":
            full_days.append(i)
    return np.array(full_days)

# Function to reorder all tasks based on a new task order
def reorder_all(tasks, Doctors, Physiologists, Assistants, new_task_order):
    old_idx = {t: i for i, t in enumerate(tasks)}
    idx_order = [old_idx[t] for t in new_task_order]

    def r(d):
        nd = {}
        for k, v in d.items():
            nd[k] = [v[i] for i in idx_order]
        return nd

    return np.array(new_task_order), r(Doctors), r(Physiologists), r(Assistants)
    
# Function to order tasks based on number of available workers
def order_tasks(present_workers, tasks, Doctors, Physiologists, Assistants, day):
     # Ensure tasks is an ndarray for consistent indexing
    if not isinstance(tasks, np.ndarray):
        tasks = np.array(tasks)

    # map task -> original index
    task_to_idx = {t: i for i, t in enumerate(tasks)}

    # compute how many present workers can do each task
    task_availability = {}
    for task in tasks:
        idx = task_to_idx[task]
        count = 0
        for worker in present_workers:
            if (worker in Doctors and Doctors[worker][idx] == 'YES') \
               or (worker in Physiologists and Physiologists[worker][idx] == 'YES') \
               or (worker in Assistants and Assistants[worker][idx] == 'YES'):
                count += 1
        task_availability[task] = count

    # sort by availability (ascending = fewer people first)
    sorted_tasks = sorted(task_availability.keys(), key=lambda t: task_availability[t])

    return reorder_all(tasks, Doctors, Physiologists, Assistants, sorted_tasks)

# Function to prioritize a specific task, moving it to the front of the list
def prioritize_task(sorted_tasks, Doctors, Physiologists, Assistants, task):
    if task not in sorted_tasks:
        return sorted_tasks, Doctors, Physiologists, Assistants

    sorted_tasks = np.array(sorted_tasks)
    new_tasks = np.array([task] + [t for t in sorted_tasks if t != task])
    
    return reorder_all(sorted_tasks, Doctors, Physiologists, Assistants, new_tasks)

# Function to assign a worker to a task
def assign_worker(task_schedules, used_workers, i, day, part, task, dispositions, role_dict, tasks):
    for worker, dispo in dispositions.items():
        if dispo[day][part] == "IN" and worker not in used_workers[i]:
            if worker in role_dict and role_dict[worker][np.where(tasks == task)[0][0]] == 'YES':
                task_schedules[task][i].append(worker)
                used_workers[i].append(worker)
                # print assignment for debugging
                '''print(f"Assigned {worker} to {task} on day {day+1}, {'AM' if part == 0 else 'PM'}")
                print(task_schedules[task][i])'''
                return
    # If no suitable worker found print debug message
    '''print(f"No available worker for {task} on day {day+1}, {'AM' if part == 0 else 'PM'}")
    print(task_schedules[task][i])'''

def check_student_leave_days(dispositions, Trainees, physios_in):
    student_leave_days = {trainee: [] for trainee in Trainees}
    # randomize the order of trainees to avoid bias
    rd.shuffle(Trainees)

    # determine best days for each trainee to take leave
    for trainee in Trainees:
        dispo = dispositions[trainee].flatten()
        days_available = full_days(dispo)
        # Try and assign both student leaves in the same day for Priya
        if trainee == "Priya" and days_available.size > 0:
            # Check which day has the most physiologists available
            best_day = -1
            for day in days_available:
                if physios_in[day] + physios_in[day + 1] > best_day:
                    best_day = int(day)
            student_leave_days[trainee].append(best_day)
            student_leave_days[trainee].append(best_day + 1)
            # Decrease availability for that day
            physios_in[day] -= 1
            physios_in[day + 1] -= 1  
        else:
            for i in range(2): # 2 student leaves per week
                temp_physios_in = physios_in.copy()  # Copy to avoid modifying the original list
                while True:
                    # Check if they're in on the day part where physiologists are most available
                    max_physios = temp_physios_in.index(max(temp_physios_in))
                    temp_physios_in[max_physios] = -1  # Temporarily mark this day part as unavailable
                    if dispo[max_physios] == "IN":
                        student_leave_days[trainee].append(max_physios)
                        physios_in[max_physios] -= 1  # Decrease availability for that day part
                        break

    return student_leave_days