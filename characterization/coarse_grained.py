#!/usr/bin/python

from __future__ import division
from optparse import OptionParser
import sys
import csv

'''
This program associates to each class containing only coarse-grained tasks the average granularity, the average number of context-switches, and the average CPU utilization (taking into account both user and kernel components).
A class is considered coarse-grained if all its tasks comply to the following rules:
-> all their granularities are within a specified range
-> their number is within a specified range

For each class, the program associates the total granularity, the total number of context-switches, and the average CPU utilization (taking into account both user and kernel components).

The result is both printed on the standard output and written to a new trace (named 'coarse-grained.csv' by default).

Usage: ./coarse_grained.py -t <path to tasks trace> --cs <path to context switches trace> --cpu <path to CPU trace> [--mg <minimum task granularity> --Mg <maximum task granularity> -o <path to results trace>]

Parameters:
-> -t: the csv file containing the tasks on which one would like to check which ones are coarse-grained
-> --cs: the csv file containing data on context-switches
-> --cpu: the csv file containing data on CPU
Note: files 'path/to/tasks.csv', 'path/to/cs.csv', and 'path/to/cpu.csv' should be produced by the same tgp analysis.
Optional parameters:
-> --mg: the minimum granularity a task must have to be considered coarse-grained. By default this value is 1000000000 (10^9)
-> --Mg: the maximum granularity a task must have to be considered coarse-grained. By default this value is 100000000000 (10^11)
-> --mt: the minimum number of tasks a class must have to be considered coarse-grained. By default this value is 10
-> --Mt: the maximum number of tasks a class must have to be considered coarse-grained. By default this value is 10000
-> -o: the name of the trace containing the results of the analysis. If none is provided, then the output file will be named 'coarse-grained.csv'
'''

#Default name for the output csv file
DEFAULT_OUT_FILE = "coarse-grained.csv"
#Default number of cores
DEFAULT_CORES = 0
#Default minimum granularity
DEFAULT_MIN_GRAN = 1000000000
#Default maximum granularity
DEFAULT_MAX_GRAN = 100000000000
#Default minimum number of tasks
DEFAULT_MIN_TASKS = 10
#Default maximum number of tasks
DEFAULT_MAX_TASKS = 10000
#Default cores option
DEFAULT_CORES_OPTION = "false"

#Number of rows in the tasks file
ROWS_TASK = 22
#Number of rows in the context-switches file
ROWS_CS = 2
#Number of rows in the CPU file
ROWS_CPU = 3

#Flags parser
parser = OptionParser('usage: -t <input tasks csv file> --cs <input context-switches csv file> --cpu <input CPU csv file> [--mg <minimum task granularity> --Mg <maximum task granularity> -o <output csv file name>]')
parser.add_option('-t', dest='tasksfile', type='string', help="the csv file containing the tasks on which one would like to check which ones are coarse-grained")
parser.add_option('--cs', dest='csfile', type='string', help="the csv file containing data on context-switches")
parser.add_option('--cpu', dest='cpufile', type='string', help="the csv file containing data on CPU")
parser.add_option('--mg', dest='min_granularity', type='long', help="the minimum granularity a task must have to be considered coarse-grained. By default this value is 1000000000 (10^9)")
parser.add_option('--Mg', dest='max_granularity', type='long', help="the maximum granularity a task must have to be considered coarse-grained. By default this value is 100000000000 (10^11)")
parser.add_option('--mt', dest='min_tasks', type='long', help="the minimum number of tasks a class must have to be considered coarse-grained. By default this value is 10")
parser.add_option('--Mt', dest='max_tasks', type='long', help="the maximum number of tasks a class must have to be considered coarse-grained. By default this value is 10000")
parser.add_option('-o', dest='output_file', type='string', help="the name of the csv file containing the results of the analysis. If none is provided, then the output file will be named 'coarse-grained.csv'")
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
if (options.min_granularity == None):
    min_granularity = DEFAULT_MIN_GRAN
else:
    min_granularity = options.min_granularity
if (options.max_granularity == None):
    max_granularity = DEFAULT_MAX_GRAN
else:
    max_granularity = options.max_granularity
if (options.min_tasks == None):
    min_tasks= DEFAULT_MIN_TASKS
else:
    min_tasks = options.min_tasks
if (options.max_tasks == None):
    max_tasks = DEFAULT_MAX_TASKS
else:
    max_tasks = options.max_tasks
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
        all_coarse = True
        for task in tasks:
            if task.this_granularity < min_granularity or task.this_granularity > max_granularity:
                all_coarse = False
                break
        if all_coarse and len(tasks) >= min_tasks and len(tasks) <= max_tasks:
            coarseclasses[key] = tasks

'''
Computes the average of context switches occurring outside coarse-grained tasks execution.
Return such an average.
'''
def context_switches_not_in_coarsegrained():
    cs_num = 0
    cs_total = 0
    avg_cs = 0
    for cs in contextswitches:
        is_outside = True
        for key in coarseclasses:
            tasks = coarseclasses[key]
            for task in tasks:
                if cs.this_time >= task.this_entrytime and cs.this_time <= task.this_exittime:
                    is_outside = False
                    break
            if is_outside == False:
                break
        if is_outside == True:
            cs_num += 1
            cs_total += cs.this_cs
    if cs_num > 0:
        avg_cs = cs_total/cs_num
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
    print("")
    avg_cs_out = context_switches_not_in_coarsegrained()
    print("Average number of context switches outside non-coarse-grained classes: %s" % str(avg_cs_out))
    print("")
    print("CLASSES CONTAINING COARSE-GRAINED TASKS:")
    print("")
    for key in coarseclasses:
        content = {}
        res = class_analysis(coarseclasses[key])
        increase = 0
        print("-> Class: %s \n   Average granularity: %s \n   Average number of context switches: %s \n   Average CPU utilization: %s" % (key, str(res[0]), str(res[1]) + "cs/100ms", str(res[2])))
        content["Class"] = key
        content["Average granularity"] = str(res[0])
        content["Average number of context switches"] = str(res[1]) + "cs/100ms"
        content["Average CPU utilization"] = str(res[2])
        contents.append(content)
    print("")
    with open(output_file, 'w') as csvfile:
        fieldnames = ["Class", "Average granularity", "Average number of context switches", "Average CPU utilization"]
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
