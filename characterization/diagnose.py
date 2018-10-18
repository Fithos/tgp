#!/usr/bin/python

'''
This scripts performs basic statistical analysis on task granularity, based on the input task, CS, and CPU traces.
The analysis focuses on the average granularity of executed tasks, its distribution, and its closedness to a specific granularity value. The analysis also computes the average number of context switches and CPU utilization experienced during task execution.

The results are both printed to stardard output and written in a new trace (named 'diagnostics.csv' by default).

Usage: ./diagnose.py -t <path to task trace> --cs <path to CS trace> --cpu <path to CPU trace> [--sc <class name> --cg <centre granularity> -o <path to result trace (output)>]

Parameters:
-> -t: path to the task trace containing data to be analyzed
-> --cs: path to the CS trace containing data to be analyzed
-> --cpu: path to the CPU trace containing data to be analyzed
Note: All input traces should have been produced by tgp with a SINGLE profiling run, either in the bytecode profiling or reference-cycles profiling mode.

Optional parameters:
-> --sc: a specific class on which to focus the analysis. For example, if '--sc ExampleClass' is passed, then all statistics will refer only to tasks of class 'ExampleClass', ignoring all other tasks. If the script should analyze all tasks, then this parameter should not be set (or should be set to 'null', which is the default value).
-> --cg: specifies the 'centre granularity'. The script computes the percentage of tasks whose granularity has the same order as the centre granularity. Setting this parameter allows users to change the centre granularity (which is 10^5 by default).
-> -o: the path to the output trace containing the results. If none is provided, then the output trace will be produced in './diagnostics.csv'
'''

from __future__ import division
from optparse import OptionParser
import sys
import csv
import math

#By default, the analysis does not focus on any class.
DEFAULT_SPECIFIC_CLASS = "null"
#Default centre granularity
DEFAULT_CENTRE_GRAN = 100000
#The default name of the output result file
DEFAULT_OUT_FILE = "diagnostics.csv"

#Number of columns in the task trace
FIELDS_TASKS = 22
#Number of columns in the CS trace
FIELDS_CS = 2
#Number of columns in the CPU trace
FIELDS_CPU = 3

#The z-score corresponding to a confidence of 0.95. It is used to compute the confidence interval of the average CPU utilization
Z_SCORE = 1.96

#A list containing Task objects
tasks = []

#A list containing ContextSwitch objects
contextswitches = []

#A list containing CPU objects
cpus = []

#A list containing all granularity values
grans = []

#The total granularity of all executed (valid) tasks
total_grans = 0

#The number of total executed tasks
exec_tasks = 0

class Task:
    '''
    A class containing relevant data taken from the task trace.
    '''
    def __init__(self, this_id, this_class, this_entry, this_exit, this_gran):
        self.this_id = this_id
        self.this_class = this_class
        self.this_entry = this_entry
        self.this_exit = this_exit
        self.this_gran = this_gran

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
    Reads the task trace. For each executed task, create a new instance of Task and inserts it into the task list.
    Note that if the parameter 'specific_class' has a non-null value, then only tasks which have been executed and have class equal to 'specific_class' are considered.
    '''
    linecounter = 0
    with open(tasks_file) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if len(row) != FIELDS_TASKS:
                print("Wrong task trace format")
                exit(-1)
            if linecounter > 0:
                if contains_letters(row[0]):
                    continue
                this_id = row[0]
                this_class = row[1]
                if contains_letters(row[12]):
                    continue
                this_entry = long(row[12])
                if contains_letters(row[13]):
                    continue
                this_exit = long(row[13])
                if contains_letters(row[14]):
                   continue
                this_gran = long(row[14])
                #Checks that task has been executed
                if this_entry >= 0 and this_exit >= 0:
                    global exec_tasks
                    if specific_class != "null":
                        if this_class == specific_class:
                            tasks.append(Task(this_id, this_class, this_entry, this_exit, this_gran))
                            global total_grans
                            total_grans += this_gran
                            grans.append(this_gran)
                            exec_tasks += 1
                    else:
                        tasks.append(Task(this_id, this_class, this_entry, this_exit, this_gran))
                        global total_grans
                        total_grans += this_gran
                        grans.append(this_gran)
                        exec_tasks += 1
            linecounter += 1

def read_cs():
    '''
    Reads the CS trace. For each measurement which occurred during the execution of a task, create a new ContextSwitch instance and inserts it into the contextswitches list.
    '''
    with open(cs_file) as csvfile:
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
            for task in tasks:
                #Checks if the measurement has occurred during the execution of a task
                if this_time >= task.this_entry and this_time <= task.this_exit:
                    contextswitches.append(ContextSwitch(this_time, this_cs))
                    break
def read_cpu():
    '''
    Reads the CPU trace. For each measurement which occurred during the execution of a task, create a new CPU instance and inserts it into the cpus list.
    '''
    with open(cpu_file) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if len(row) != FIELDS_CPU:
                print("Wrong CPU trace format")
                exit(-1)
            if contains_letters(row[0]):
                continue
            this_time = long(row[0])
            if contains_letters(row[1]):
                continue
            this_usr = float(row[1])
            if contains_letters(row[2]):
                continue
            this_sys = float(row[2])
            for task in tasks:
                #Checks if the measurement has occurred during the execution of a task
                if this_time >= task.this_entry and this_time <= task.this_exit:
                    cpus.append(CPU(this_time, this_usr, this_sys))
                    break

def gran_percentage_in_range(low_w, high_w):
    '''
    Computes the percentage of tasks having granularity within the specified range ([low_w, high_w]).
    low_w: the lower bound of the range.
    high_w: the upper bound of the range.
    Returns the percentage.
    '''
    count = 0
    for gran in grans:
        if gran >= low_w and gran <= high_w:
            count += 1
    return ((count/len(grans))*100)

def in_specified_range():
    '''
    Computes the number of tasks with granularity having the same order of magnitude as gran_centre.
    '''
    count = 0
    for task in tasks:
        if gran_centre > 0 and (abs(math.log(gran_centre, 10) - math.log(task.this_gran, 10)) <= 1):
            count += 1
    return count

def tasks_statistics():
   '''
   Computes basic statistics related to tasks.
   Returns a dictionary containing such statistics.
   '''
   print("")
   print("TASKS STATISTICS")
   grans.sort()
   m_index = 0
   third_q = 0
   first_q = 0
   median = 0
   inter_quartile = 0
   low_w = 0
   high_w = 0
   percentage_range = 0
   avg = 0
   percentage = 0
   if len(grans) != 0 and len(tasks) != 0:
       m_index = int(len(grans)/2)
       third_q = int((len(grans) - m_index)/2) + m_index
       first_q = int(m_index/2)
       median = grans[m_index]
       one_percentile = grans[int(len(grans)*0.01)]
       five_percentile = grans[int(len(grans)*0.05)]
       ninetyfive_percentile = grans[int(len(grans)*0.9)]
       ninetynine_percentile = grans[int(len(grans)*0.95)]
       inter_quartile = grans[third_q] - grans[first_q]
       low_w = grans[first_q] - 1.5 * inter_quartile
       if low_w < 0:
           low_w = 0
       high_w = grans[third_q] + 1.5 * inter_quartile
       if high_w > grans[len(grans) - 1]:
           high_w = grans[len(grans) - 1]
       percentage_range = gran_percentage_in_range(low_w, high_w)
       avg = total_grans/len(tasks)
       percentage = (in_specified_range()/len(tasks))*100
   res = "-> Total number of tasks: " + str(exec_tasks) + " \n-> Average granularity: " + str(avg) + " \n-> 1st percentile - granularity: " + str(one_percentile) + " \n-> 5th percentile - granularity: " + str(five_percentile) + " \n-> 50th percentile (median) - granularity: " + str(median) + " \n-> 95th percentile - granularity: " + str(ninetyfive_percentile) + " \n-> 99th percentile - granularity: " + str(ninetynine_percentile) + " \n-> IQC - granularity: " + str(inter_quartile) + " \n-> Whiskers range - granularity: [" + str(low_w) + ", " + str(high_w) + "] \n-> Percentage of tasks having granularity within whiskers range: " + str(percentage_range) + "% \n-> Percentage of tasks with granularity around " + str(gran_centre) + ": " + str(percentage) + "%"
   print(res)
   res_dict = {}
   res_dict["Total number of tasks"] = str(exec_tasks)
   res_dict["Average granularity"] = str(avg)
   res_dict["1st percentile - granularity"] = str(one_percentile)
   res_dict["5th percentile - granularity"] = str(five_percentile)
   res_dict["50th percentile (median) - granularity"] = str(median)
   res_dict["95th percentile - granularity"] = str(ninetyfive_percentile)
   res_dict["99th percentile - granularity"] = str(ninetynine_percentile)
   res_dict["IQC - granularity"] = str(inter_quartile)
   res_dict["Lower whiskers range - granularity"] = str(low_w)
   res_dict["Upper whiskers range - granularity"] = str(high_w)
   res_dict["Percentage of tasks having granularity within whiskers range"] = str(percentage_range)
   res_dict["Centre granularity"] = str(gran_centre)
   res_dict["Percentage of tasks with granularity around centre granularity"] = str(percentage)
   return res_dict

def cs_statistics():
    '''
    Computes statistics related to context-switches.
    Returns a dictionary containing such statistics.
    '''
    print("")
    print("CONTEXT-SWITCHES STATISTICS")
    total_cs = 0
    for cs in contextswitches:
        total_cs += cs.this_cs
    avg = 0
    if len(contextswitches) > 0:
        avg = total_cs/len(contextswitches)
    res = "-> Average number of context switches: " + str(avg) + "cs/100ms"
    print(res)
    res_dict = {}
    res_dict["Average number of context switches"] = str(avg)
    return res_dict

def cpu_mean():
    '''
    Computes the average CPU utilization.
    '''
    mean = 0
    if len(cpus) == 0:
        return mean
    for cpu in cpus:
        mean += cpu.this_usr + cpu.this_sys
    mean /= len(cpus)
    return mean

def cpu_standard_deviation():
    '''
    Computes the standard deviation of the average CPU utilization.
    '''
    sd = 0
    if len(cpus) == 0:
        return sd
    mean = cpu_mean()
    for cpu in cpus:
        sd += pow((cpu.this_usr + cpu.this_sys - mean), 2)
    sd /= (len(cpus) - 1)
    sd = math.sqrt(sd)
    return sd

def cpu_confidence_interval():
    '''
    Computes the confidence intervals of the average CPU utilization.
    '''
    mean = cpu_mean()
    sd = cpu_standard_deviation()
    if mean == 0 and sd == 0:
        return 0
    return (Z_SCORE * sd)/math.sqrt(len(cpus))

def cpu_statistics():
    '''
    Computes statistics related to CPU utilization.
    Returns a dictionary containing such statistics.
    '''
    print("")
    mean = cpu_mean()
    interval = cpu_confidence_interval()
    print("CPU STATISTICS")
    res = "-> Average CPU utilization: " + str(mean) + "+-" + str(interval)
    print(res)
    print("")
    res_dict = {}
    res_dict["Average CPU utilization"] = str(mean)
    res_dict["STD CPU utilization"] = str(interval)
    
    return res_dict

def write_stats():
    '''
    Writes statistics for tasks, context switches, and CPU utilization on a csv file.
    '''
    tasks_stats = tasks_statistics()
    cs_stats = cs_statistics()
    cpu_stats = cpu_statistics()
    with open(output_file, 'w') as csvfile:
        fieldnames = []
        fieldnames.append("Selected class")
        for key in tasks_stats:
            fieldnames.append(key)
        for key in cs_stats:
            fieldnames.append(key)
        for key in cpu_stats:
            fieldnames.append(key)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        content = {}
        content["Selected class"] = specific_class
        for key in tasks_stats:
            content[key] = tasks_stats[key]
        for key in cs_stats:
            content[key] = cs_stats[key]
        for key in cpu_stats:
            content[key] = cpu_stats[key]
        writer.writerow(content)

if __name__ == "__main__":
    #Flags parser
    parser = OptionParser("./diagnose.py -t <path to task trace> --cs <path to CS trace> --cpu <path to CPU trace> [--sc <class name> --cg <centre granularity> -o <path to result trace (output)>]")
    parser.add_option('-t', dest='tasks_file', type='string', help="path to the task trace containing data to be analyzed", metavar="TASK_TRACE")
    parser.add_option('--cs', dest='cs_file', type='string', help="path to the CS trace containing data to be analyzed", metavar="CS_TRACE")
    parser.add_option('--cpu', dest='cpu_file', type='string', help="path to the CPU trace containing data to be analyzed", metavar="CPU_TRACE")
    parser.add_option('--sc', dest='specific_class', type='string', help="a specific class on which to focus the analysis. For example, if '--sc ExampleClass' is passed, then all statistics will refer only to tasks of class 'ExampleClass', ignoring all other tasks. If the script should analyze all tasks, then this parameter should not be set (or should be set to 'null', which is the default value)", metavar="CLASS")
    parser.add_option('--cg', dest='gran_centre', type='long', help="specifies the 'centre granularity'. The script computes the percentage of tasks whose granularity has the same order as the centre granularity. Setting this parameter allows users to change the centre granularity (which is 10^5 by default).", metavar="CENTRE_GRAN")
    parser.add_option('-o', dest='output_file', type='string', help="the path to the output trace containing the results. If none is provided, then the output trace will be produced in './diagnostics.csv'", metavar="RESULT_TRACE")
    (options, arguments) = parser.parse_args()
    if (options.tasks_file is None):
        print(parser.usage)
        exit(0)
    else:
        tasks_file = options.tasks_file
    if (options.cs_file is None):
        print(parser.usage)
        exit(0)
    else:
        cs_file = options.cs_file
    if (options.cpu_file is None):
        print(parser.usage)
        exit(0)
    else:
        cpu_file = options.cpu_file
    if (options.specific_class is None):
        specific_class = DEFAULT_SPECIFIC_CLASS
    else:
        specific_class = options.specific_class
    if (options.gran_centre is None):
        gran_centre = DEFAULT_CENTRE_GRAN
    else:
        gran_centre = options.gran_centre
    if (options.output_file is None):
        output_file = DEFAULT_OUT_FILE
    else:
        output_file = options.output_file

    print("")
    print("Beginning diagnosis...")
    print("")

    if (specific_class != "null") :
        print("Restricting analysis to tasks of class: " + specific_class)
        print ("")

    read_tasks()

    read_cs()

    read_cpu()

    write_stats()


