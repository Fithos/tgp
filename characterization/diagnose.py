#!/usr/bin/python

'''
This program performs statistical analysis based on input files containing data on tasks, context-switches, and CPU utilization.
In particular, the analysis focuses on the average granularity of spawned tasks, their distribution, and their closedness to a specific granularity value. The analysis also computes the average of context-switches (during tasks execution) and CPU utilization (during tasks execution), providing for the latter an interval of confidence of 95%.

The results are both printed on the stardard output and written on a csv file called 'diagnostics.csv'.

Usage: ./path/to/diagnose.py path/to/tasks.csv path/to/cs.csv path/to/cpu.csv specific_class specific_granularity

Parameters:
-> path/to/tasks.csv: the csv file containing tasks data.
-> path/to/tasks.csv: the csv file containing context-switches data. This file should be a filtered one (see gc-filtering.py)
-> path/to/cpu.csv: the csv file containing CPU utilization data. This file should be a filtered one (see gc-filtering.py)
Note: files 'path/to/tasks.csv', 'path/to/tasks.csv', and 'path/to/cpu.csv' should be produced by the same analysis
-> specific_class: a specific class on which to focus the analysis. For example, if 'specific_class' is 'ExampleClass', then all statistics will be referred to tasks belonging to 'ExampleClass', and ignoring the rest. If no specific class is to be focused on, then this value should be set to 'null'
-> specific_granularity: is used to compute the percentage of tasks whose granularity has the same order of magnitude of 'specific_granularity'
'''

from __future__ import division
import sys
import csv
import math

#The csv file containing tasks data
tasks_file = sys.argv[1]
#The csv file containing context-switches data
cs_file = sys.argv[2]
#The csv file containing CPU data
cpu_file = sys.argv[3]
#The class on which to focus the analysis
specific_class = sys.argv[4]
#The granularity on which to compute the percentage of tasks having their granularity of the same order of magnitude of said granularity
gran_centre = long(sys.argv[5])

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

'''
A class containing some of the data from the csv file for tasks.
'''
class Task:
    def __init__(self, this_id, this_class, this_entry, this_exit, this_gran):
        self.this_id = this_id
        self.this_class = this_class
        self.this_entry = this_entry
        self.this_exit = this_exit
        self.this_gran = this_gran

'''
A class containing the data from the csv file for context-switches.
'''
class ContextSwitch:
    def __init__(self, this_time, this_cs):
        self.this_time = this_time
        self.this_cs = this_cs

'''
A class containing the data from the csv file for CPU.
'''
class CPU:
    def __init__(self, this_time, this_usr, this_sys):
        self.this_time = this_time
        self.this_usr = this_usr
        self.this_sys = this_sys

'''
Checks whether the specified string contains letters.
string: the string on which to perform the check.
Returns true if the specified string contains letters, false otherwise.
'''
def contains_letters(string):
    for s in string:
        if s.isalpha():
            return True
    return False

'''
Reads the csv file for tasks. For each valid task, i.e., it is executed, it creates a new instance of Task and inserts it into the tasks array.
Note that if the parameter 'specific_class' has a valid value, then only tasks which have been executed and have class equal to 'specific_class' are considered.
'''
def read_tasks():
    linecounter = 0
    with open(tasks_file) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
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

'''
Reads the csv file for context-switches and for each measurement which has taken place during the execution of a task, it creates a new ContextSwitch instance and inserts it into the contextswitches array.
'''
def read_cs():
    with open(cs_file) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
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
'''
Reads the csv file for CPU and for each measurement which has taken place during the execution of a task, it creates a new CPU instance and inserts it into the cpus array.
'''
def read_cpu():
    with open(cpu_file) as csvfile:
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
            for task in tasks:
                #Checks if the measurement has occurred during the execution of a task
                if this_time >= task.this_entry and this_time <= task.this_exit:
                    cpus.append(CPU(this_time, this_usr, this_sys))
                    break

'''
Computes the percentage of tasks having granularity within the specified range ([low_w, high_w]).
low_w: the lower bound of the range.
high_w: the upper bound of the range.
Returns the percentage.
'''
def gran_percentage_in_range(low_w, high_w):
    count = 0
    for gran in grans:
        if gran >= low_w and gran <= high_w:
            count += 1
    return ((count/len(grans))*100)

'''
Computes the number of tasks with granularity having the same order of magnitude as the specified granularity.
Returns the number of tasks satifying said property.
'''
def in_specified_range():
    count = 0
    for task in tasks:
        if abs(math.log(gran_centre, 10) - math.log(task.this_gran, 10)) <= 1:
            count += 1
    return count

'''
Computes statistics related to tasks. In particular, this statistics include:
-> the average granularity
-> the median granualrity
-> the inter-quartile range
-> the whiskers range
-> the percentage of tasks having granularity within the whiskers range
-> the percentage of task falling within the range of the specified granularity
Returns a dictionary containing these tasks statistics.
'''
def tasks_statistics():
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
   res = "-> Average granularity: " + str(avg) + " \n-> Median granularity: " + str(median) + " \n-> IQC: " + str(inter_quartile) + " \n-> Whiskers range: [" + str(low_w) + ", " + str(high_w) + "] \n-> Percentage of tasks having granularity within whiskers range: " + str(percentage_range) + "% \n-> Percentage of tasks with granularity around " + str(gran_centre) + ": " + str(percentage) + "%"
   print(res)
   res_dict = {}
   res_dict["Average granularity"] = str(avg)
   res_dict["Median granularity"] = str(median)
   res_dict["IQC"] = str(inter_quartile)
   res_dict["Whiskers range"] = "[" + str(low_w) + ", " + str(high_w) + "]"
   res_dict["Percentage of tasks having granularity within whiskers range"] = str(percentage_range) + "%"
   res_dict["Percentage of tasks with granularity around " + str(gran_centre) + ": "] = str(percentage) + "%"
   return res_dict

'''
Computes statistics related to context-switches.
In particular it computes the average number of context-switches.
Returns a dictionary containing these context-switches statistics.
'''
def cs_statistics():
    print("")
    print("CONTEXT-SWITCHES STATISTICS")
    total_cs = 0
    for cs in contextswitches:
        total_cs += cs.this_cs
    avg = 0
    if len(contextswitches) > 0:
        avg = total_cs/len(contextswitches)
    res = "-> Average context-switches: " + str(avg) + "cs/100ms"
    print(res)
    res_dict = {}
    res_dict["Average context-switches"] = str(avg) + "cs/100ms"
    return res_dict

'''
Computes the average CPU utilization, considering both user and kernel components.
Returns the average CPU utilization.
'''
def cpu_mean():
    mean = 0
    if len(cpus) == 0:
        return mean
    for cpu in cpus:
        mean += cpu.this_usr + cpu.this_sys
    mean /= len(cpus)
    return mean

'''
Computes the standard deviation for the average CPU utilization.
Returns the standard deviation for the average CPU utilization.
'''
def cpu_standard_deviation():
    sd = 0
    if len(cpus) == 0:
        return sd
    mean = cpu_mean()
    for cpu in cpus:
        sd += pow((cpu.this_usr + cpu.this_sys - mean), 2)
    sd /= (len(cpus) - 1)
    sd = math.sqrt(sd)
    return sd

'''
Computes the confidence interval for the average CPU utilization.
Returns the confidence interval for the average CPU utilization.
'''
def cpu_confidence_interval():
    mean = cpu_mean()
    sd = cpu_standard_deviation()
    if mean == 0 and sd == 0:
        return 0
    return (Z_SCORE * sd)/math.sqrt(len(cpus))

'''
Computes statistics related to CPU utilization.
In particular, it computes the average CPU utilization and the confidence interval for it.
Returns a dictionary containing these CPU statistics.
'''
def cpu_statistics():
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

'''
Writes the results of statistics for tasks, context-switches, and CPU utilization on a csv file named 'diagnostics.csv'.
'''
def write_stats():
    tasks_stats = tasks_statistics()
    cs_stats = cs_statistics()
    cpu_stats = cpu_statistics()
    with open('diagnositcs.csv', 'w') as csvfile:
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

read_tasks()

read_cs()

read_cpu()

write_stats()
