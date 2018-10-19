#!/usr/bin/python

from __future__ import division
from optparse import OptionParser
import sys
import csv

helper = '''This script extracts useful information related to the execution of fine-grained tasks. In particular, the script identifies classes spawning only fine-grained tasks and, for each of them, computes the average task granularity and the average amount of context switches experienced by the application during task execution. The script also computes the average amount of context switches occurred when no fine-grained task was in execution.
        
A class is considered as "spawning only fine-grained tasks" if ALL tasks of such class satisfy ALL the following conditions:
  (1) task granularity is smaller than or equal to MAX_GRAN (user-customizable)
  (2) the difference between the maximum and minimum task granularity is smaller than or equal MAX_DIFF (user-customizable)
  (3) the number of tasks spawned by the class is greater than or equal to MIN_TASKS_SPAWNED (user-customizable)
        
The results are both printed to stardard output and written in a new trace (named 'fine-grained.csv' by default).
        
Note: All input traces should have been produced by tgp with a SINGLE profiling run, either in the bytecode profiling or reference-cycles profiling mode.

Usage: ./fine_grained.py -t <path to task trace> -c <path to CS trace> [-G <MAX_GRAN> -D <MAX_DIFF> -m <MIN_TASKS_SPAWNED> -o <path to result trace (output)>]'''

#Default name for the output csv file
DEFAULT_OUT_FILE = "fine-grained.csv"
#Default maximum relative range
DEFAULT_MAX_RANGE = 100000000
#Default minimum number of tasks
DEFAULT_MIN_TASKS = 0
#Default maximum granularity
DEFAULT_MAX_GRAN = 100000000

#Number of columns in the task trace
FIELDS_TASK = 22
#Number of columns in the CS trace
FIELDS_CS = 2

#The alost containing context-switches data
contextswitches = []

#The dictionary associating each class to a list of Task instances
classes = {}

#The dictionary associating each class to the total number of context-switches occured while fine-grained tasks contained in such class were executing
fineclasses = {}

#The total number of tasks
total_tasks = 0

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
    def __init__(self, this_timestamp, this_contextswitches):
        self.this_timestamp = this_timestamp
        self.this_contextswitches = this_contextswitches

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

def read_csv(inputfile, datatype):
    '''
        Reads the input csv file. Based on the file format (specified via 'datatype'), initializes the appropriate data structures.
    inputfile: the csv file to read.
    datatype: the type of the file to read.
    '''
    linecounter = 0
    with open (inputfile) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            #Reads tasks
            if datatype == "TASK" and linecounter > 0:
                if len(row) != FIELDS_TASK:
                    print("Wrong task trace format")
                    exit(-1)
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
                #An instance of Task is created if the timestamp associated with its execution is non-negative
                if task_entry >= 0 and task_exit >= 0:
                    if task_class not in classes:
                        classes[task_class] = []
                    #Inserts the new Task instance into the corresponding class entry
                    classes[task_class].append(Task(task_id, task_class, task_entry, task_exit, task_gran))
                    global total_tasks
                    total_tasks += 1
            #Reads context-switches
            elif datatype == "CS" and linecounter > 0:
                if len(row) != FIELDS_CS:
                    print("Wrong CS trace format")
                    exit(-1)
                cs_time = float(row[0])
                cs_css = float(row[1])
                contextswitches.append(ContextSwitch(cs_time, cs_css))
            linecounter += 1

def sort_tasks():
    '''
    Sorts in place each entry of the class dictionary based on task granularity.
    This is done so that checking the granularities' range is faster.
    '''
    for key, value in classes.iteritems():
        value.sort(key=lambda x:x.this_granularity, reverse=True)

def are_finegrained(array):
    '''
    Checks whether all granularities in the input array satisfy the conditions to consider the class as fine-grained.
    array: the array to perform the check on.
    Returns true if all conditions are satisfied, false otherwise.
    '''
    all_grans_min = True
    for arr in array:
        if arr.this_granularity > max_granularity:
            all_grans_min = False
            break
    if all_grans_min == False:
        return False
    condition = array[0].this_granularity - array[len(array) - 1].this_granularity <= margin and len(array) >= min_tasks_number
    return condition

def finegrained_contextswitches():
    '''
    For each class, this functions counts the total number of context switches occurred during task execution.
    '''
    for key in classes:
        tasks = classes[key]
        #Checks if the conditions for tasks to be considered fine-grained hold
        if are_finegrained(tasks):
            total_num_gran = 0
            total_gran = 0
            total_num_cs = 0
            total_cs = 0
            for task in tasks:
                total_num_gran += 1
                total_gran += task.this_granularity
                for cs in contextswitches:
                    #Checks whether the context-switch timestamp falls within the task execution
                    if cs.this_timestamp >= task.this_entrytime and cs.this_timestamp <= task.this_exittime:
                        total_cs += cs.this_contextswitches
                        total_num_cs += 1
            fineclasses[key] = [total_gran, total_cs, total_num_gran, total_num_cs]

def context_switches_not_in_finegrained():
    '''
    Returns the average number of context switches occurred when fine-grained tasks are not in execution.
    '''
    cs_num = 0
    cs_total = 0
    avg_cs = 0
    for cs in contextswitches:
        is_outside = True
        for key in fineclasses:
            tasks = classes[key]
            if is_outside == False:
                break
            for task in tasks:
                if cs.this_timestamp >= task.this_entrytime and cs.this_timestamp <= task.this_exittime:
                    is_outside = False
                    break
        if is_outside == True:
            cs_num += 1
            cs_total += cs.this_contextswitches
    if cs_num > 0:
        avg_cs = cs_total/cs_num
    return avg_cs

def output_results():
    '''
    Writes the result on a csv file and prints them on standard output.
    '''
    contents = []
    avg_cs_out = context_switches_not_in_finegrained()
    print("")
    print("Average number of context switches experienced when fine-grained tasks are not in execution: %scs/100ms" % str(avg_cs_out))
    print("")
    for key in fineclasses:
        content = {}
        avg_gran = 0
        avg_cs = 0
        if fineclasses[key][2] > 0:
            avg_gran = fineclasses[key][0]/fineclasses[key][2]
        if fineclasses[key][3] > 0:
            avg_cs = fineclasses[key][1]/fineclasses[key][3]
        print("Class: %s -> Average granularity: %s -> Average number of context switches: %s" % (key, str(avg_gran), str(avg_cs) + "cs/100ms"))
        content["Class"] = key
        content["Average granularity"] = str(avg_gran)
        content["Average number of context switches"] = str(avg_cs)
        contents.append(content)
    print("")
    with open(output_file, 'w') as csvfile:
        fieldnames = ["Class", "Average granularity", "Average number of context switches"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for cont in contents:
            writer.writerow(cont)

if __name__ == "__main__":
    #Flags parser
    parser = OptionParser(helper)
    parser.add_option('-t', '--task', dest='tasksfile', type='string', help="path to the task trace containing data to be analyzed", metavar="TASK_TRACE")
    parser.add_option('-c', '--context-switches', dest='csfile', type='string', help="path to the CS trace containing data to be analyzed", metavar="CS_TRACE")
    parser.add_option('-D', '--max-gran-diff', dest='margin', type='float', help="sets MAX_DIFF (10^8 by default)", metavar="MAX_DIFF")
    parser.add_option('-m', '--min-task-spawned', dest='min_tasks_number', type='float', help="sets MIN_TASK_SPAWNED (0 by default)", metavar="MIN_TASK_SPAWNED")
    parser.add_option('-G','--max-granularity', dest='max_granularity', type='long', help="sets MAX_GRAN (10^8 by default)", metavar="MAX_GRAN")
    parser.add_option('-o', '--output', dest='output_file', type='string', help="the path to the output trace containing the results. If none is provided, then the output trace will be produced in './fine-grained.csv'", metavar="RESULT_TRACE")
    (options, arguments) = parser.parse_args()
    if (options.tasksfile is None):
        print(parser.usage)
        exit(0)
    else:
        tasksfile = options.tasksfile
    if (options.csfile is None):
        print(parser.usage)
        exit(0)
    else:
        csfile = options.csfile
    if (options.margin is None):
        margin = DEFAULT_MAX_RANGE
    else:
        margin = options.margin
    if (options.min_tasks_number is None):
        min_tasks_number = DEFAULT_MIN_TASKS
    else:
        min_tasks_number = options.min_tasks_number
    if (options.max_granularity is None):
        max_granularity = DEFAULT_MAX_GRAN
    else:
        max_granularity = options.max_granularity
    if (options.output_file is None):
        output_file = DEFAULT_OUT_FILE
    else:
        output_file = options.output_file

    print("")
    print("Starting analysis...")

    read_csv(tasksfile, "TASK")
    read_csv(csfile, "CS")

    sort_tasks()

    finegrained_contextswitches()

    output_results()
