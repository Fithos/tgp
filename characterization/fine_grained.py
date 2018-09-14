#!/usr/bin/python

from __future__ import division
from optparse import OptionParser
import sys
import csv

'''
This program associates to each class containing only fine-grained tasks the average granularity and the average number of context-switches occurring during its tasks' execution.

Tasks within the same class are considered fine-grained if:
-> all their granularities are smaller or equal to the specified one
-> all their granularities lie within the specified relative range
-> their number is greater or equal then the average number of tasks per class
-> their number is greater or equal to the specified minimum number of tasks

The results are both printed via standard output and written to a new trace (named 'fine-grained.csv' by default).

Usage: ./fine_grained.py -t <path to tasks trace> --cs <path to context switches trace> [--Mr <maximum relative granularities range> --ga <greater or equal average> --mt <minimum number of tasks per class> --Mg <maximum task granularity> -o <path to results trace>]

Parameters:
-> -t: the csv file containing tasks on which to check whether they are fine grained
-> --cs: the csv file containing the number of context-switches associated to an analysis
Note: parameters 'path/to/tasks.csv' and 'path/to/cs.csv' should be produced by the same analysis.
Optional parameters:
-> --Mr: the maximum difference between granularities of the same class, i.e., if granularities are [1, 3, 4, 6] and the maximum range is 3, then these granularities are not valid, as 1 and 6 differ more than 3. By defualt this number is 100000000
-> --ga: a condition which states whether the number of tasks in a class should be greater or equal to the overall ratio tasks/class. If this option should be taken into account, then parameter 'greater_than_average' should be set to 'true', 'false' otherwise. By default this option is 'false'
-> --mt: the minimum number of tasks that should be in a class to be considered fine-grained. By default this value is 0
-> --Mg: the maximum granularity a task can have. By default this value is 100000000 (10^8)
-> -o: the name of the trace containing the results of the analysis. If none is provided, then the output file will be named 'fine-grained.csv'
'''

#Default name for the output csv file
DEFAULT_OUT_FILE = "fine-grained.csv"
#Default maximum relative range
DEFAULT_MAX_RANGE = 100000000
#Default average option
DEFAULT_AVERAGE = "false"
#Default minimum number of tasks
DEFAULT_MIN_TASKS = 0
#Default maximum granularity
DEFAULT_MAX_GRAN = 100000000

#Number of rows in the tasks file
ROWS_TASK = 22
#Number of rows in the context-switches file
ROWS_CS = 2

#Flags parser
parser = OptionParser('usage: -t <input tasks csv file> --cs <input context-switches csv file> [--Mr <maximum relative granularities range> --ga <greater than average> --mt <minimum number of tasks per class> --Mg <maximum task granularity> -o <output csv file name>]')
parser.add_option('-t', dest='tasksfile', type='string', help="the csv file containing tasks on which to check whether they are fine grained")
parser.add_option('--cs', dest='csfile', type='string', help="the csv file containing the number of context-switches associated to an analysis")
parser.add_option('--Mr', dest='margin', type='float', help="the maximum difference between granularities of the same class, i.e., if granularities are [1, 3, 4, 6] and the maximum range is 3, then these granularities are not valid, as 1 and 6 differ more than 3. By defualt this number is 100000000")
parser.add_option('--ga', dest='average_option', type='string', help="a condition which states whether the number of tasks in a class should be greater or equal to the overall ratio tasks/class. If this option should be taken into account, then parameter 'greater_than_average' should be set to 'true', 'false' otherwise. By default this option is 'false'")
parser.add_option('--mt', dest='min_tasks_number', type='float', help="the minimum number of tasks that should be in a class to be considered fine-grained. By default this value is 0")
parser.add_option('--Mg', dest='max_granularity', type='long', help="the maximum granularity a task can have. By default this value is 100000000 (10^8)")
parser.add_option('-o', dest='output_file', type='string', help="the name of the csv file containing the results of the analysis. If none is provided, then the output file will be named 'fine-grained.csv'")
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
if (options.margin == None):
    margin = DEFAULT_MAX_RANGE
else:
    margin = options.margin
if (options.average_option == None):
    average_option = DEFAULT_AVERAGE
else:
    average_option = options.average_option
if (options.min_tasks_number == None):
    min_tasks_number = DEFAULT_MIN_TASKS
else:
    min_tasks_number = options.min_tasks_number
if (options.max_granularity == None):
    max_granularity = DEFAULT_MAX_GRAN
else:
    max_granularity = options.max_granularity
if (options.output_file == None):
    output_file = DEFAULT_OUT_FILE
else:
    output_file = options.output_file

#The array containing context-switches data
contextswitches = []

#The dictionary associating each class to an array of Task instances
classes = {}

#The dictionary associating each class to the total number of context-switches occured while fine-grained tasks contained in said class were executing
fineclasses = {}

#The total number of tasks
total_tasks = 0

#The average number of tasks per class
average = 0

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
A class containing data from the context-switches csv file.
'''
class ContextSwitch:
    def __init__(self, this_timestamp, this_contextswitches):
        self.this_timestamp = this_timestamp
        self.this_contextswitches = this_contextswitches

'''
Checks whether the input string contains letters.
string: the string on which to check the presence of letters
Returns true if the string contains letters, false otherwise.
'''
def contains_letters(string):
    for s in string:
        if s.isalpha():
            return True
    return False

'''
Reads the input csv file and based on the input data type it initializes the right data structures.
inputfile: the csv file to read
datatype: the type of the data to read.
'''
def read_csv(inputfile, datatype):
    linecounter = 0
    with open (inputfile) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            #Reads tasks
            if datatype == "TASK" and linecounter > 0:
                if len(row) != ROWS_TASK:
                    print("Wrong tasks file format")
                    exit(0)
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
                #An instance of Task is created if the timestamp associated with its execution are non-negative
                if task_entry >= 0 and task_exit >= 0:
                    if task_class not in classes:
                        classes[task_class] = []
                    #Inserts the new Task instance into the corresponding class entry
                    classes[task_class].append(Task(task_id, task_class, task_entry, task_exit, task_gran))
                    global total_tasks
                    total_tasks += 1
            #Reads context-switches
            elif datatype == "CS" and linecounter > 0:
                if len(row) != ROWS_CS:
                    print("Wrong context-switches file format")
                    exit(0)
                cs_time = float(row[0])
                cs_css = float(row[1])
                contextswitches.append(ContextSwitch(cs_time, cs_css))
            linecounter += 1

'''
Computes the average of valid and executed tasks per class.
'''
def compute_average():
    if len(classes) > 0:
        global average
        average = total_tasks/len(classes)

'''
Sorts in place each entry of the classes dictionary based on the granularity.
This is done so that checking the granularities' range is faster.
'''
def sort_tasks():
    for key, value in classes.iteritems():
        value.sort(key=lambda x:x.this_granularity, reverse=True)

'''
Checks for the input array whether all granularities are within a specified relative range, greater then the number of cores, whether the ratio tasks/class is greater or equal than the overall average
and whether the number of tasks in the specific class is greater or equal than the specified minimum number of tasks.
array: the array to perform the check on
Returns true if the granularities fall within the same relative range, false otherwise.
'''
def are_finegrained(array):
    all_grans_min = True
    for arr in array:
        if arr.this_granularity > max_granularity:
            all_grans_min = False
            break
    if all_grans_min == False:
        return False
    condition = array[0].this_granularity - array[len(array) - 1].this_granularity <= margin and len(array) >= min_tasks_number
    if average_option == "true":
        condition = condition and len(array) >= average
    return condition

'''
For each class, this functions counts the total number of context-switches occurring during the execution of the class's fine-grained tasks.
'''
def finegrained_contextswitches():
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

'''
Computes the average of context switches occurring outside fine-grained tasks execution.
Return such an average.
'''
def context_switches_not_in_finegrained():
    cs_num = 0
    cs_total = 0
    avg_cs = 0
    for cs in contextswitches:
        is_outside = True
        for key in fineclasses:
            tasks = classes[key]
            for task in tasks:
                if cs.this_timestamp >= task.this_entrytime and cs.this_timestamp <= task.this_exittime:
                    is_outside = False
                    break
            if is_outside == False:
                break
        if is_outside == True:
            cs_num += 1
            cs_total += cs.this_contextswitches
    if cs_num > 0:
        avg_cs = cs_total/cs_num
    return avg_cs

'''
Writes the result on a csv file as well as printing it on the standard output.
'''
def output_results():
    contents = []
    avg_cs_out = context_switches_not_in_finegrained()
    print("")
    print("Average number of context switches outside non-fine-grained classes: %s" % str(avg_cs_out))
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
        content["Average number of context switches"] = str(avg_cs) + "cs/100ms"
        contents.append(content)
    print("")
    with open(output_file, 'w') as csvfile:
        fieldnames = ["Class", "Average granularity", "Average number of context switches"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for cont in contents:
            writer.writerow(cont)

print("")
print("Starting analysis...")

read_csv(tasksfile, "TASK")
read_csv(csfile, "CS")

sort_tasks()

finegrained_contextswitches()

output_results()
