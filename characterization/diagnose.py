#!/usr/bin/python

'''
This program performs statistical analysis based on input files containing data on tasks, context-switches, and CPU utilization.
In particular, the analysis focuses on the average granularity of spawned tasks, their distribution, and their closedness to a specific granularity value. The analysis also computes the average of context-switches (during tasks execution) and CPU utilization (during tasks execution), providing for the latter an interval of confidence of 95%.

The results are both printed on the stardard output and written on a new trace (named 'diagnostics.csv' by default).

Usage: ./diagnose.py -t <path to tasks trace> --cs <path to context switches trace> --cpu <path to CPU trace> [--sc <class name> --cg <centre granularity> -o <path to results trace>]

Parameters:
-> -t: the task trace
-> --cs: the context switches trace
-> --cpu: the CPU measurements trace
Note: files 'path/to/task trace, 'path/to/context switches trace', and 'path/to/CPU trace' should be produced by the same profiling run.
Optional parameters:
-> --sc: a specific class on which to focus the analysis. For example, if 'specific_class' is 'ExampleClass', then all statistics will be referred to tasks belonging to 'ExampleClass', and ignoring the rest. If no specific class is to be focused on, then this value should be set to 'null'. By default, the tool does not focus on any specific class
-> --cg: is used to compute the percentage of tasks whose granularity has the same order as the specified one. By default, this granularity is 0
-> -o: the name of the output trace that will be produced. If none is provided, then the output trace will be named 'diagnostics.csv'
'''

from __future__ import division
from optparse import OptionParser
import sys
import csv
import math

#By default, the analysis does not focus on any class.
DEFAULT_SPECIFIC_CLASS = "null"
#Default centre granularity
DEFAULT_CENTRE_GRAN = 0
#The default name of the output file
DEFAULT_OUT_FILE = "diagnostics.csv"

#Number of fields of tasks file
FIELDS_TASKS = 22
#Number of fields of the context-switches file
FIELDS_CS = 2
#Number of fields of the CPU file
FIELDS_CPU = 3

#The z-score corresponding to confidence of 0.95. It is used to compute the confidence interval of the CPU average
Z_SCORE = 1.96

#An array containing instances of Task objects
tasks = []

#An array containing instances of ContextSwitch objects
contextswitches = []

#An array containing instances of CPU objects
cpus = []

#An array containing all granularity values
grans = []

#The total granularity of all spawned (valid) tasks
total_grans = 0

#The number of total executed tasks
exec_tasks = 0

class Task:
    '''
    A class containing some of the data from the csv file for tasks.
    '''
    def __init__(self, this_id, this_class, this_entry, this_exit, this_gran):
        self.this_id = this_id
        self.this_class = this_class
        self.this_entry = this_entry
        self.this_exit = this_exit
        self.this_gran = this_gran

class ContextSwitch:
    '''
    A class containing the data from the csv file for context-switches.
    '''
    def __init__(self, this_time, this_cs):
        self.this_time = this_time
        self.this_cs = this_cs

class CPU:
    '''
    A class containing the data from the csv file for CPU.
    '''
    def __init__(self, this_time, this_usr, this_sys):
        self.this_time = this_time
        self.this_usr = this_usr
        self.this_sys = this_sys

def contains_letters(string):
    '''
    Checks whether the specified string contains letters.
    string: the string on which to perform the check.
    Returns true if the specified string contains letters, false otherwise.
    '''
    for s in string:
        if s.isalpha():
            return True
    return False

def read_tasks():
    '''
    Reads the csv file for tasks. For each valid task, i.e., it is executed, it creates a new instance of Task and inserts it into the tasks array.
    Note that if the parameter 'specific_class' has a valid value, then only tasks which have been executed and have class equal to 'specific_class' are considered.
    '''
    linecounter = 0
    with open(tasks_file) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if len(row) != FIELDS_TASKS:
                print("Wrong task trace format")
                exit(0)
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
                    exec_tasks += 1
                    if specific_class != "null":
                        if this_class == specific_class:
                            tasks.append(Task(this_id, this_class, this_entry, this_exit, this_gran))
                            global total_grans
                            total_grans += this_gran
                            grans.append(this_gran)
                    else:
                        tasks.append(Task(this_id, this_class, this_entry, this_exit, this_gran))
                        global total_grans
                        total_grans += this_gran
                        grans.append(this_gran)
            linecounter += 1

def read_cs():
    '''
    Reads the csv file for context-switches and for each measurement which has taken place during the execution of a task, it creates a new ContextSwitch instance and inserts it into the contextswitches array.
    '''
    with open(cs_file) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if len(row) != FIELDS_CS:
                print("Wrong context switches trace format")
                exit(0)
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
    Reads the csv file for CPU and for each measurement which has taken place during the execution of a task, it creates a new CPU instance and inserts it into the cpus array.
    '''
    with open(cpu_file) as csvfile:
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
    Computes the number of tasks with granularity having the same order of magnitude as the specified granularity.
    Returns the number of tasks satifying said property.
    '''
    count = 0
    for task in tasks:
        if gran_centre > 0 and (abs(math.log(gran_centre, 10) - math.log(task.this_gran, 10)) <= 1):
            count += 1
    return count

def tasks_statistics():
   '''
   Computes basic statistics related to tasks.
   Returns a dictionary containing these tasks statistics.
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
   res = "-> Total number of tasks: " + str(exec_tasks) + " \n-> Average granularity: " + str(avg) + " \n-> One percentile granularity: " + str(one_percentile) + " \n-> Five percentile granularity: " + str(five_percentile) + " \n-> Fifty percentage (median) granularity: " + str(median) + " \n-> Ninety-five percentile granularity: " + str(ninetyfive_percentile) + " \n-> Ninety-nine percentile granularity: " + str(ninetynine_percentile) + " \n-> IQC: " + str(inter_quartile) + " \n-> Whiskers range: [" + str(low_w) + ", " + str(high_w) + "] \n-> Percentage of tasks having granularity within whiskers range: " + str(percentage_range) + "% \n-> Percentage of tasks with granularity around " + str(gran_centre) + ": " + str(percentage) + "%"
   print(res)
   res_dict = {}
   res_dict["Total number of tasks"] = str(exec_tasks)
   res_dict["Average granularity"] = str(avg)
   res_dict["One percentile granularity"] = str(one_percentile)
   res_dict["Five percentile granularity"] = str(five_percentile)
   res_dict["Fifty percentage (median) granularity"] = str(median)
   res_dict["Ninety-five percentile granularity"] = str(ninetyfive_percentile)
   res_dict["Ninety-nine percentile granularity"] = str(ninetynine_percentile)
   res_dict["IQC"] = str(inter_quartile)
   res_dict["Whiskers range"] = "[" + str(low_w) + ", " + str(high_w) + "]"
   res_dict["Percentage of tasks having granularity within whiskers range"] = str(percentage_range) + "%"
   res_dict["Percentage of tasks with granularity around " + str(gran_centre) + ": "] = str(percentage) + "%"
   return res_dict

def cs_statistics():
    '''
    Computes statistics related to context-switches.
    In particular it computes the average number of context-switches.
    Returns a dictionary containing these context-switches statistics.
    '''
    print("")
    print("CONTEXT SWITCHES STATISTICS")
    total_cs = 0
    for cs in contextswitches:
        total_cs += cs.this_cs
    avg = 0
    if len(contextswitches) > 0:
        avg = total_cs/len(contextswitches)
    res = "-> Average context switches: " + str(avg) + "cs/100ms"
    print(res)
    res_dict = {}
    res_dict["Average context switches"] = str(avg) + "cs/100ms"
    return res_dict

def cpu_mean():
    '''
    Computes the average CPU utilization, considering both user and kernel components.
    Returns the average CPU utilization.
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
    Computes the standard deviation for the average CPU utilization.
    Returns the standard deviation for the average CPU utilization.
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
    Computes the confidence interval for the average CPU utilization.
    Returns the confidence interval for the average CPU utilization.
    '''
    mean = cpu_mean()
    sd = cpu_standard_deviation()
    if mean == 0 and sd == 0:
        return 0
    return (Z_SCORE * sd)/math.sqrt(len(cpus))

def cpu_statistics():
    '''
    Computes statistics related to CPU utilization.
    In particular, it computes the average CPU utilization and the confidence interval for it.
    Returns a dictionary containing these CPU statistics.
    '''
    print("")
    mean = cpu_mean()
    interval = cpu_confidence_interval()
    print("CPU STATISTICS")
    res = "-> Average CPU utilization: " + str(mean) + "+-" + str(interval)
    print(res)
    print("")
    res_dict = {}
    res_dict["Average CPU utilization"] = str(mean) + "+-" + str(interval)
    return res_dict

def write_stats():
    '''
    Writes the results of statistics for tasks, context-switches, and CPU utilization on a csv file named 'diagnostics.csv'.
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
        if specific_class != "null":
            content["Selected class"] = specific_class
        else:
            content["Selected class"] = "no class selected"
        for key in tasks_stats:
            content[key] = tasks_stats[key]
        for key in cs_stats:
            content[key] = cs_stats[key]
        for key in cpu_stats:
            content[key] = cpu_stats[key]
        writer.writerow(content)

if __name__ == "__main__":
    #Flags parser
    parser = OptionParser('usage: -t <path to tasks trace> --cs <path to context switches trace> --cpu <path to CPU trace> [--sc <class name> --cg <centre granularity> -o <path to results trace>]')
    parser.add_option('-t', dest='tasks_file', type='string', help="the task trace")
    parser.add_option('--cs', dest='cs_file', type='string', help="the containing context switches trace")
    parser.add_option('--cpu', dest='cpu_file', type='string', help="the CPU trace")
    parser.add_option('--sc', dest='specific_class', type='string', help="a specific class on which to focus the analysis. For example, if 'specific_class' is 'ExampleClass', then all statistics will be referred to tasks belonging to 'ExampleClass', and ignoring th    e rest. If no specific class is to be focused on, then this value should be set to 'null'. By default, the tool does not focus on any specific class")
    parser.add_option('--cg', dest='gran_centre', type='long', help="is used to compute the percentage of tasks whose granularity has the same order as the specified one. By default, this granularity is 0")
    parser.add_option('-o', dest='output_file', type='string', help="the name of the trace that will be produced. If none is provided, then the trace will be named 'diagnostics.csv'")
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
    print("Beginning diagnose...")

    read_tasks()

    read_cs()

    read_cpu()

    write_stats()
