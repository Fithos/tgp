#!/usr/bin/python

from __future__ import division
from optparse import OptionParser
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

Usage: ./coarse_grained.py -t <input tasks csv file> --cs <input context-switches csv file> --cpu <input CPU csv file>[-c <number of cores> --ming <minimum task granularity> --maxg <maximum task granularity> --co <cores enabling option> -o <output csv file name>]

Parameters:
-> -t: the csv file containing the tasks on which one would like to check which ones are coarse-grained
-> --cs: the csv file containing data on context-switches. This file should be filtered (see gc-filtering.py)
-> --cpu: the csv file containing data on CPU. This file should be filtered (see gc-filtering.py)
Note: files 'path/to/tasks.csv', 'path/to/cs.csv', and 'path/to/cpu.csv' should be produced by the same tgp analysis
Optional parameters:
-> -c: the number of cores on which the tgp analysis was carried out. By default this value is 0
-> --ming: the minimum granularity a task must have to be considered coarse-grained. By default this value is 1000000000 (10^9)
-> --maxg: the maximum granularity a task must have to be considered coarse-grained. By default this value is 100000000000 (10^11)
-> --co: this parameter must be either 'true' or 'false'. If it true, then the number of tasks inside a class must be equal to the number of cores to be considered coarse-grained. If the parameter is set to false, then the number of cores is not taken into account in the analysis. By default this option is 'false'
'''

#Default name for the output csv file
DEFAULT_OUT_FILE = "coarse-grained.csv"
#Default number of cores
DEFAULT_CORES = 0
#Default minimum granularity
DEFAULT_MIN_GRAN = 1000000000
#Default maximum granularity
DEFAULT_MAX_GRAN = 100000000000
#Default cores option
DEFAULT_CORES_OPTION = "false"

#Number of rows in the tasks file
ROWS_TASK = 22
#Number of rows in the context-switches file
ROWS_CS = 2
#Number of rows in the CPU file
ROWS_CPU = 3

#Flags parser
parser = OptionParser('usage: -t <input tasks csv file> --cs <input context-switches csv file> --cpu <input CPU csv file>[-c <number of cores> --ming <minimum task granularity> --maxg <maximum task granularity> --co <cores enabling option> -o <output csv file name>]')
parser.add_option('-t', dest='tasksfile', type='string')
parser.add_option('--cs', dest='csfile', type='string')
parser.add_option('--cpu', dest='cpufile', type='string')
parser.add_option('-c', dest='cores', type='int')
parser.add_option('--ming', dest='min_granularity', type='long')
parser.add_option('--maxg', dest='max_granularity', type='long')
parser.add_option('--co', dest='cores_option', type='string')
parser.add_option('-o', dest='output_file', type='string')
(options, arguments) = parser.parse_args()
if (options.tasksfile == None):
    print parser.usage
    exit(0)
else:
    tasksfile = options.tasksfile
if (options.csfile == None):
    print parser.usage
    exit(0)
else:
    csfile = options.csfile
if (options.cpufile == None):
    print parser.usage
    exit(0)
else:
    cpufile = options.cpufile
if (options.cores == None):
    cores = DEFAULT_CORES
else:
    cores = options.cores
if (options.min_granularity == None):
    min_granularity = DEFAULT_MIN_GRAN
else:
    min_granularity = options.min_granularity
if (options.max_granularity == None):
    max_granularity = DEFAULT_MAX_GRAN
else:
    max_granularity = options.max_granularity
if (options.cores_option == None):
    cores_option = DEFAULT_CORES_OPTION
else:
    cores_option = options.cores_option
if (options.output_file == None):
    output_file = DEFAULT_OUT_FILE
else:
    output_file = options.output_file

#A dictionary associating a class name to an array of Task instances, which are 'contained' in said class
classes = {}

#A dictionary associating a class name to an array of Task instances. In this dictionary there are only classes containing only coarse-grained tasks
coarseclasses = {}

#A dictionary associating a class name to an array of Task instance. This dictionary is used to compute the average number of context-switches occurring during non-coarse-grained classes' tasks execution.
notcoarseclasses = {}

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
            if len(row) != ROWS_TASK:
                print("Wrong tasks file format")
                exit(0)
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
            if len(row) != ROWS_CS:
                print("Wrong context-switches file format")
                exit(0)
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
            if len(row) != ROWS_CPU:
                print("Wrong CPU file format")
                exit(0)
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
                if task.this_granularity < min_granularity or task.this_granularity > max_granularity:
                    all_coarse = False
                    break
            if all_coarse:
                coarseclasses[key] = tasks
            else:
                notcoarseclasses[key] = tasks
        else:
            notcoarseclasses[key] = tasks

'''
Computes the average number of context-switches occurring during the execution of non-coarse-grained classes' tasks.
Returns such an average.
'''
def non_coarsegrained_avg_cs():
    total_css = 0
    total_cs = 0
    avg_cs = 0
    for key in notcoarseclasses:
        tasks = notcoarseclasses[key]
        for task in tasks:
            for cs in contextswitches:
                if cs.this_time >= task.this_entrytime and cs.this_time <= task.this_exittime:
                    total_cs += cs.this_cs
                    total_css += 1
    if total_css > 0:
        avg_cs = total_cs/total_css
    return avg_cs

'''
Computes the analysis for a class. More specifically, for each class this function computes the total granularity, the number of context-switches, and the average CPU utilization.
Returns an array containing the total granularity, the number of context-switches, and the average CPU utlilization.
'''
def class_analysis(tasks):
    total_cs = 0
    total_css = 0
    total_cpu_util = 0
    total_cpu = 0
    total_gran = 0
    total_tasks = 0
    for task in tasks:
        total_gran += task.this_granularity
        total_tasks += 1
        for cs in contextswitches:
            if cs.this_time >= task.this_entrytime and cs.this_time <= task.this_exittime:
                total_cs += cs.this_cs
                total_css += 1
        for cpu in cpus:
            if cpu.this_time >= task.this_entrytime and cpu.this_time <= task.this_exittime:
                total_cpu_util += cpu.this_usr + cpu.this_sys
                total_cpu += 1
    avg_cpu = 0
    avg_cs = 0
    avg_gran = 0
    if total_cpu > 0:
        avg_cpu = total_cpu_util/total_cpu
    if total_css > 0:
        avg_cs = total_cs/total_css
    if total_tasks > 0:
        avg_gran = total_gran/total_tasks
    return [avg_gran, avg_cs, avg_cpu]

'''
Writes to a csv file and prints the results of the analisys on the standard output.
'''
def output_results():
    contents = []
    avg_cs_not_coarse = non_coarsegrained_avg_cs()
    print("")
    print("Average number of context-switches of non-coarse-grained classes: %s" % str(avg_cs_not_coarse))
    print("")
    print("CLASSES CONTAINING COARSE-GRAINED TASKS:")
    for key in coarseclasses:
        content = {}
        if (cores_option == "true" and len(coarseclasses[key]) == cores) or (cores_option == "false"):
            res = class_analysis(coarseclasses[key])
            avg_cs_not_coarse = non_coarsegrained_avg_cs()
            increase = 0
            if avg_cs_not_coarse > 0:
                increase = ((res[1] - avg_cs_not_coarse)/avg_cs_not_coarse)*100
            print("-> Class: %s \n   Average granularity: %s \n   Average number of context-switches: %s \n   Average CPU utilization: %s \n   Increase/Decreasing in context-switches compared to non-coarse-grained classes: %s" % (key, str(res[0]), str(res[1]), str(res[2]), str(increase) + "%"))
            content["Class"] = key
            content["Average granularity"] = str(res[0])
            content["Average number of context-switches"] = str(res[1])
            content["Average CPU utilization"] = str(res[2])
            content["Increase/Decreasing in context-switches compared to non-coarse-grained classes"] = str(increase)
            contents.append(content)
    print("")
    if cores_option == "true" and is_one_taskers():
        print("CLASSES SPAWNING EXACTLY ONE COARSE-GRAINED TASK AND HAVIN THE SAME NUMBER OF THE NUMBER OF CORES:")
        for key in coarseclasses:
            res = class_analysis(coarseclasses[key])
            increase = 0
            if avg_cs_not_coarse > 0:
                increase = ((res[1] - avg_cs_not_coarse)/avg_cs_not_coarse)*100
            print("-> Class: %s \n   Average granularity: %s \n   Average number of context-switches: %s \n   Average CPU utilization: %s \n   Increase/Decreasing in context-switches compared to non-coarse-grained classes: %s" % (key, str(res[0]), str(res[1]), str(res[2]), str(increase)))
    with open(output_file, 'w') as csvfile:
        fieldnames = ["Class", "Average granularity", "Average number of context-switches", "Average CPU utilization", "Increase/Decreasing in context-switches compared to non-coarse-grained classes"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for cont in contents:
            writer.writerow(cont)

print("")
print("Starting analysis...")

read_tasks()

coarsegrained()

read_cs()

read_cpu()

output_results()
