#!/usr/bin/python

from __future__ import division
import sys
import csv

'''
This program associates to each class containing only coarse-grained tasks the total granularity, the total number of context-switches, and the average CPU utilization (taking into account both user and kernel components).
A class is considered coarse-grained if all its tasks comply to the following rules:
-> their number is equal to the specified number of cores
-> all their granularities are greater or equal than the specified one

It is also checked whether there is a number of classes equal to the specified number of cores having exactly one coarse-grained task.

For each class, the program associates the total granularity, the total number of context-switches, and the average CPU utilization (taking into account both user and kernel components).

The result is both printed on the standard output and written to a csv file named 'coarse-grained.csv'.

Usage: ./path/to/coarse_grained.py path/to/tasks.csv path/to/cs.csv path/to/cpu.csv number_of_cores minimum_granularity cores_option

Parameters:
-> path/to/tasks.csv: the csv file containing the tasks on which one would like to check which ones are coarse-grained
-> path/to/cs.csv: the csv file containing data on context-switches. This file should be filtered (see gc-filtering.py)
-> path/to/cpu.csv: the csv file containing data on CPU. This file should be filtered (see gc-filtering.py)
Note: files 'path/to/tasks.csv', 'path/to/cs.csv', and 'path/to/cpu.csv' should be produced by the same tgp analysis
-> number_of_cores: the number of cores on which the tgp analysis was carried out
-> minimum_granularity: the minimum granularity a task must have to be considered coarse-grained
-> cores_option: this parameter must be either 'true' or 'false'. If it true, then the number of tasks inside a class must be equal to the number of cores to be considered coarse-grained. If the parameter is set to false, then the number of cores is not taken into account in the analysis
'''

#The csv file containing tasks data
tasksfile = sys.argv[1]
#The file containing context-switches data
csfile = sys.argv[2]
#The file containing CPU data
cpufile = sys.argv[3]
#The number of cores
cores = int(sys.argv[4])
#The minimum granularity a task must have to be considered coarse-grained
min_granularity = long(sys.argv[5])
#Whether the fact that the number of tasks per class must be equal to the number of cores to be considered coarse-grained
cores_option = sys.argv[6]

#A dictionary associating a class name to an array of Task instances, which are 'contained' in said class
classes = {}

#A dictionary associating a class name to an array of Task instances. In this dictionary there are only classes containing only coarse-grained tasks
coarseclasses = {}

#An array containing ContextSwitch instances
contextswitches = []

#An array containing CPU instances
cpus = []

'''
A class containing some of the data from the tasks csv file. It contains data relevant to this analysis.
'''
class Task:
    def __init__(self, this_id, this_class, this_entrytime, this_exittime, this_granularity):
        self.this_id = this_id
        self.this_class = this_class
        self.this_entrytime = this_entrytime
        self.this_exittime = this_exittime
        self.this_granularity = this_granularity

'''
A class containing the same data as the csv file for context-switches.
'''
class ContextSwitch:
    def __init__(self, this_time, this_cs):
        self.this_time = this_time
        self.this_cs = this_cs

'''
A class containing the same data as csv file for CPU utilization.
'''
class CPU:
    def __init__(self, this_time, this_usr, this_sys):
        self.this_time = this_time
        self.this_usr = this_usr
        self.this_sys = this_sys

'''
Checks whether the input string contains letters.
string: the string on which to check the presence of letters.
Returns true if the string contains letters, false otherwise.
'''
def contains_letters(string):
    for s in string:
        if s.isalpha():
            return True
    return False

'''
Counts the number of classes spawning exactly one coarse-grained task and compares said number with the specified number of cores.
Returns true if the number of classes spawning exactly one coarse-grained task is equal to the specified number of cores, false otherwise.
'''
def is_one_taskers():
    one_taskers = 0
    for key in coarseclasses:
        if coarsegrained[key] == 1:
            one_taskers += 1
    return one_taskers == cores

'''
Reads the specified tasks csv file and sets up the classes dictionary.
'''
def read_tasks():
    linecounter = 0
    with open (tasksfile) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if linecounter > 0:
                if contains_letters(row[0]):
                    continue
                task_id = row[0]
                task_class = row[1]
                if contains_letters(row[12]):
                    continue
                task_entry = long(row[12])
                if contains_letters(row[13]):
                    continue
                task_exit = long(row[13])
                if contains_letters(row[14]):
                    continue
                task_gran = long(row[14])
                if task_entry >= 0 and task_exit >= 0:
                    if task_class not in classes:
                        classes[task_class] = []
                    classes[task_class].append(Task(task_id, task_class, task_entry, task_exit, task_gran))
            linecounter += 1

'''
Reads the specified csv file for context-switches.
'''
def read_cs():
    with open (csfile) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if contains_letters(row[0]):
                continue
            this_time = float(row[0])
            if contains_letters(row[1]):
                continue
            this_cs = float(row[1])
            contextswitches.append(ContextSwitch(this_time, this_cs))
'''
Reads the specified csv file for CPU utilization.
'''
def read_cpu():
    with open (cpufile) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if contains_letters(row[0]):
                continue
            this_time = long(row[0])
            if contains_letters(row[1]):
                continue
            this_usr = float(row[1])
            if contains_letters(row[2]):
                continue
            this_sys = float(row[2])
            cpus.append(CPU(this_time, this_usr, this_sys))

'''
For each class in the classes dictionary this function counts the number of coarse-grained tasks, which are used to set up the dictionary for the coarse-grained classes.
'''
def coarsegrained():
    for key in classes:
        tasks = classes[key]
        if (cores_option == "true" and (len(tasks) == 1 or len(tasks) == cores)) or (cores_option == "false"):
            all_coarse = True
            for task in tasks:
                if task.this_granularity < min_granularity:
                    all_coarse = False
                    break
            if all_coarse:
                coarseclasses[key] = tasks

'''
Computes the analysis for a class. More specifically, for each class this function computes the total granularity, the number of context-switches, and the average CPU utilization.
Returns an array containing the total granularity, the number of context-switches, and the average CPU utlilization.
'''
def class_analysis(tasks):
    total_cs = 0
    total_cpu_util = 0
    total_cpu = 0
    total_gran = 0
    for task in tasks:
        total_gran += task.this_granularity
        for cs in contextswitches:
            if cs.this_time >= task.this_entrytime and cs.this_time <= task.this_exittime:
                total_cs += cs.this_cs
        for cpu in cpus:
            if cpu.this_time >= task.this_entrytime and cpu.this_time <= task.this_exittime:
                total_cpu_util += cpu.this_usr + cpu.this_sys
                total_cpu += 1
    avg_cpu = 0
    if total_cpu > 0:
        avg_cpu = total_cpu_util/total_cpu
    return [total_gran, total_cs, avg_cpu]

'''
Writes to a csv file and prints the results of the analisys on the standard output.
'''
def output_results():
    contents = []
    print("")
    print("CLASSES CONTAINING COARSE-GRAINED TASKS:")
    for key in coarseclasses:
        content = {}
        if (cores_option == "true" and len(coarseclasses[key]) == cores) or (cores_option == "false"):
            res = class_analysis(coarseclasses[key])
            print("-> Class: %s \n   Total granularity: %s \n   Number of context-switches: %s \n   Average CPU utilization: %s" % (key, str(res[0]), str(res[1]), str(res[2])))
            content["Class"] = key
            content["Total granularity"] = str(res[0])
            content["Number of context-switches"] = str(res[1])
            content["Average CPU utilization"] = str(res[2])
            contents.append(content)
    print("")
    if cores_option == "true" and is_one_taskers():
        print("CLASSES SPAWNING EXACTLY ONE COARSE-GRAINED TASK AND HAVIN THE SAME NUMBER OF THE NUMBER OF CORES:")
        for key in coarseclasses:
            res = class_analysis(coarseclasses[key])
            print("-> Class: %s \n   Total granularity: %s \n   Number of context-switches: %s \n   Average CPU utilization: %s" % (key, str(res[0]), str(res[1]), str(res[2])))
    with open('coarse-grained.csv', 'w') as csvfile:
        fieldnames = ["Class", "Total granularity", "Number of context-switches", "Average CPU utilization"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for cont in contents:
            writer.writerow(cont)


read_tasks()

coarsegrained()

read_cs()

read_cpu()

output_results()
