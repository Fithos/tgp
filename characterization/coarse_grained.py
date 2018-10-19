#!/usr/bin/python

from __future__ import division
from optparse import OptionParser
import sys
import csv

helper = '''This script extracts useful information related to the execution of coarse-grained tasks. In particular, the script identifies classes spawning only coarse-grained tasks and, for each of them, computes the average task granularity, as well as the average amount of context switches and average CPU utilization experienced by the application during task execution. The script also computes the average amount of context switches occurred when no coarse-grained task was in execution.

A class is considered as "spawning only coarse-grained tasks" if ALL tasks of such class satisfy ALL the following conditions:

  (1) task granularity is within range [MIN_GRAN, MAX_GRAN]. Both limits are user-customizable, default range is [10^9, 10^11]
  (2) the number of tasks spawned by the class is within range [MIN_TASK_SPAWNED, MAX_TASK_SPAWNED]. Both limits are user-customizable, default range is [1, 100]

The results are both printed to stardard output and written in a new trace (named 'coarse-grained.csv' by default).

Note: All input traces should have been produced by tgp with a SINGLE profiling run, either in the bytecode profiling or reference-cycles profiling mode.

Usage: ./coarse_grained.py -t <path to task trace> -c <path to CS trace> -p <path to CPU trace> [-g <MIN_GRAN> -G <MAX_GRAN> -s <MIN_TASK_SPAWNED> -S <MAX_TASK_SPAWNED> -o <path to result trace (output)>]'''

#Default name for the output csv file
DEFAULT_OUT_FILE = "coarse-grained.csv"
#Default minimum granularity
DEFAULT_MIN_GRAN = 1000000000
#Default maximum granularity
DEFAULT_MAX_GRAN = 100000000000
#Default minimum number of tasks
DEFAULT_MIN_TASKS = 1
#Default maximum number of tasks
DEFAULT_MAX_TASKS = 100

#Number of columns in the task trace
FIELDS_TASK = 22
#Number of columns in the CS trace
FIELDS_CS = 2
#Number of columns in the CPU trace
FIELDS_CPU = 3

#A dictionary associating a class name to a list of Task instances, which belong to such class
classes = {}

#A dictionary associating a class name to an array of Task instances. In this dictionary are stored only classes containing only coarse-grained tasks
coarseclasses = {}

#A dictionary associating a class name to an array of Task instance. This dictionary is used to compute the average number of context switches occurring when no coarse-grained task was in execution.
notcoarseclasses = {}

#A list containing ContextSwitch instances
contextswitches = []

#A list containing CPU instances
cpus = []

class Task:
    '''
    A class containing relevant data taken from the task trace.
    '''
    def __init__(self, this_id, this_class, this_entrytime, this_exittime, this_granularity):
        self.this_id = this_id
        self.this_class = this_class
        self.this_entrytime = this_entrytime
        self.this_exittime = this_exittime
        self.this_granularity = this_granularity

class ContextSwitch:
    '''
    A class containing data taken from the CS trace.
    '''
    def __init__(self, this_time, this_cs):
        self.this_time = this_time
        self.this_cs = this_cs

class CPU:
    '''
    A class containing data taken from the CPU trace.
    '''
    def __init__(self, this_time, this_usr, this_sys):
        self.this_time = this_time
        self.this_usr = this_usr
        self.this_sys = this_sys

def contains_letters(string):
    '''
    Checks whether the input string contains letters.
    string: the string on which to check the presence of letters.
    Returns true if the string contains letters, false otherwise.
    '''
    for s in string:
        if s.isalpha():
            return True
    return False

def read_tasks():
    '''
    Reads the task trace and sets up the dictionary.
    '''
    linecounter = 0
    with open (tasksfile) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if len(row) != FIELDS_TASK:
                print("Wrong task trace format")
                exit(-1)
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

def read_cs():
    '''
    Reads the CS trace and sets up the dictionary.
    '''
    with open (csfile) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if len(row) != FIELDS_CS:
                print("Wrong CS trace format")
                exit(-1)
            if contains_letters(row[0]):
                continue
            this_time = float(row[0])
            if contains_letters(row[1]):
                continue
            this_cs = float(row[1])
            contextswitches.append(ContextSwitch(this_time, this_cs))

def read_cpu():
    '''
    Reads the CPU trace and sets up the dictionary.
    '''
    with open (cpufile) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if len(row) != FIELDS_CPU:
                print("Wrong CPU trace format")
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

def coarsegrained():
    '''
    For each class in the classes dictionary, this function counts the number of coarse-grained tasks, which are used to set up the dictionary for the coarse-grained classes.
    '''
    for key in classes:
        tasks = classes[key]
        all_coarse = True
        for task in tasks:
            if task.this_granularity < min_granularity or task.this_granularity > max_granularity:
                all_coarse = False
                break
        if all_coarse and len(tasks) >= min_tasks and len(tasks) <= max_tasks:
            coarseclasses[key] = tasks

def context_switches_not_in_coarsegrained():
    '''
    Returns the average number of context switches occurring when coarse-grained tasks are not in execution.
    '''
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

def class_analysis(tasks):
    '''
    Performs the analysis on coarse-grained tasks. More specifically, for each class, this function computes the total granularity, the number of context switches, and the average CPU utilization, returning them in a list.
    '''
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

def output_results():
    '''
    Writes results to a csv file and prints them to standard output.
    '''
    contents = []
    print("")
    avg_cs_out = context_switches_not_in_coarsegrained()
    print("Average number of context switches experienced when coarse-grained tasks are not in execution: %scs/100ms" % str(avg_cs_out))
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
        content["Average number of context switches"] = str(res[1])
        content["Average CPU utilization"] = str(res[2])
        contents.append(content)
    print("")
    with open(output_file, 'w') as csvfile:
        fieldnames = ["Class", "Average granularity", "Average number of context switches", "Average CPU utilization"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for cont in contents:
            writer.writerow(cont)

if __name__ == "__main__":
    #Flags parser
    parser = OptionParser(helper)
    parser.add_option('-t', '--task', dest='tasksfile', type='string', help="path to the task trace containing data to be analyzed", metavar="TASK_TRACE")
    parser.add_option('-c', '--context-switches', dest='csfile', type='string', help="path to the CS trace containing data to be analyzed", metavar="CS_TRACE")
    parser.add_option('-p', '--cpu', dest='cpufile', type='string', help="path to the CPU trace containing data to be analyzed", metavar="CPU_TRACE")
    parser.add_option('-g', '--min-granularity', dest='min_granularity', type='long', help="sets MIN_GRAN (10^9 by default)", metavar="MIN_GRAN")
    parser.add_option('-G', '--max-granularity', dest='max_granularity', type='long', help="sets MAX_GRAN (10^11 by default)", metavar="MAX_GRAN")
    parser.add_option('-s', '--min-task-spawned', dest='min_tasks', type='long', help="sets MIN_TASK_SPAWNED (1 by default)", metavar="MIN_TASK_SPAWNED")
    parser.add_option('-S', '--max-task-spawned', dest='max_tasks', type='long', help="sets MAX_TASK_SPAWNED (100 by default)", metavar="MAX_TASK_SPAWNED")
    parser.add_option('-o', '--output', dest='output_file', type='string', help="the path to the output trace containing the results. If none is provided, then the output trace will be produced in './coarse-grained.csv'", metavar="RESULT_TRACE")
    (options, arguments) = parser.parse_args()
    if (options.tasksfile is None):
        print parser.usage
        exit(0)
    else:
        tasksfile = options.tasksfile
    if (options.csfile is None):
        print(parser.usage)
        exit(0)
    else:
        csfile = options.csfile
    if (options.cpufile is None):
        print(parser.usage)
        exit(0)
    else:
        cpufile = options.cpufile
    if (options.min_granularity is None):
        min_granularity = DEFAULT_MIN_GRAN
    else:
        min_granularity = options.min_granularity
    if (options.max_granularity is None):
        max_granularity = DEFAULT_MAX_GRAN
    else:
        max_granularity = options.max_granularity
    if (options.min_tasks is None):
        min_tasks= DEFAULT_MIN_TASKS
    else:
        min_tasks = options.min_tasks
    if (options.max_tasks is None):
        max_tasks = DEFAULT_MAX_TASKS
    else:
        max_tasks = options.max_tasks
    if (options.output_file is None):
        output_file = DEFAULT_OUT_FILE
    else:
        output_file = options.output_file

    print("")
    print("Starting analysis...")

    read_tasks()

    coarsegrained()

    read_cs()

    read_cpu()

    output_results()

