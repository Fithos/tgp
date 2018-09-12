#!/usr/bin/python

import sys
import csv

'''
This program associates to each class containing only fine-grained tasks the total granularity and the total number of context-switches occurring during its tasks' execution.

Tasks within the same class are considered fine-grained if:
-> their number is greater than the provided number of cores
-> all their granularities are smaller or equal to the specified one
-> all their granularities lie within the specified relative range
-> their number is greater or equal then the average number of tasks per class
-> their number is greater or equal to the specified minimum number of tasks

The results are both printed via standard output and written to a csv file named 'fine-grained.csv'.

Usage: ./path/to/fine_grained.py path/to/tasks.csv path/to/cs.csv number_of_cores maximum_range_between_tasks_granularity_in_same_class greater_than_average minimum_number_tasks_in_same_class maximum_task_granularity

Parameters:
-> path/to/tasks.csv: the csv file containing tasks on which to check whether they are fine grained
-> path/to/cs.csv: the csv file containing the number of context-switches associated to an analysis. This file should be first filtered (gc-filtering.py).
Note: parameters 'path/to/tasks.csv' and 'path/to/cs.csv' should be produced by the same analysis.
-> number_of_cores: the number of cores used for the analysis (can set to 0 if they should not be accounted).
-> maximum_range_between_tasks_granularity_in_same_class: the maximum difference between granularities of the same class, i.e., if granularities are [1, 3, 4, 6] and the maximum range is 3, then these granularities are not valid, as 1 and 6 differ more than 3
-> greater_than_average: a condition which states whether the number of tasks in a class should be greater or equal to the overall ratio tasks/class. If this option should be taken into account, then parameter 'greater_than_average' should be set to 'true', 'false' otherwise
-> minimum_number_tasks_in_same_class: the minimum number of tasks that should be in a class to be considered fine-grained.
-> maximum_task_granularity: the maximum granularity a task can have
'''

#The tasks.csv file
tasksfile = sys.argv[1]
#The cs.csv file (context-switches)
csfile = sys.argv[2]
#The number of cores
cores_number = int(sys.argv[3])
#The margin between granularities, i.e., the minimum difference between tasks' granularities belonging to the same class for them to be considered fine-grained
margin = float(sys.argv[4])
#An option indicating that the number of tasks in a class must be greater or equal than the average of tasks per class
average_option = sys.argv[5]
#The absolute number of tasks per class
min_tasks_number = float(sys.argv[6])
#The maximum granularity a task can have
max_granularity = long(sys.argv[7])

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
    condition = array[0].this_granularity - array[len(array) - 1].this_granularity <= margin and len(array) > cores_number and len(array) >= min_tasks_number
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
            total_gran = 0
            total_cs = 0
            for task in tasks:
                total_gran += task.this_granularity
                for cs in contextswitches:
                    #Checks whether the context-switch timestamp falls within the task execution
                    if cs.this_timestamp >= task.this_entrytime and cs.this_timestamp <= task.this_exittime:
                        total_cs += cs.this_contextswitches
            fineclasses[key] = [total_gran, total_cs]

'''
Writes the result on a csv file as well as printing it on the standard output.
'''
def output_results():
    contents = []
    print("")
    for key in fineclasses:
        content = {}
        print("Class: %s -> Total granularity: %s -> Number of context-switches: %s" % (key, str(fineclasses[key][0]), str(fineclasses[key][1])))
        content["Class"] = key
        content["Total granularity"] = str(fineclasses[key][0])
        content["Number of context-switches"] = str(fineclasses[key][1])
        contents.append(content)
    print("")
    with open('fine-grained.csv', 'w') as csvfile:
        fieldnames = ["Class", "Total granularity", "Number of context-switches"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for cont in contents:
            writer.writerow(cont)

read_csv(tasksfile, "TASK")
read_csv(csfile, "CS")

sort_tasks()

finegrained_contextswitches()

output_results()
