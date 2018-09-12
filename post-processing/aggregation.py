#!/usr/bin/python

import sys
import csv

'''
This program performs task aggregation, i.e., aggregates the execution of a nested task to its outer task. As a result of this operation, the granularities of the inner tasks are summed
up with the one from the outer task.
Task aggregation is performed on nested tasks if one of the following conditions is satisfied:
   1) the outer task is not a thread
   2) the outer task is a thread, and both the following conditions are true:
       2.1) the nested task has not been submitted
       2.2) the nested task is created and executed by the same thread

To perform aggregation, the tasks are modelled as a directed graph, where edges go from nested tasks to their outer one. Topological sorting is then used solve the dependencies.

The result is a csv file containing the aggregated tasks named 'aggregated-tasks.csv'.

Usage: ./path/to/aggregation/program/aggregation.py path/to/csv/tasks.csv

Parameters:
-> path/to/csv/tasks.csv: the csv file containing the tasks data on which to perform aggregation. This file should comply to the format produced by the tgp analysis
'''

#The input csv file containing the tasks, specified as the first parameter of the program
tasks_file = sys.argv[1]

#An array containing all tasks
tasks = []

#An array containing topologically sorted tasks
sorted_tasks = []

#A dictionary associating an ID with the correspoding task object
tasks_ids = {}

'''
Class Task contains all data relative to a task, as in the file tasks.csv.
The purpose of this class is both to hold data and to provide algorithms used to aggregate tasks.
'''
class Task:
    '''
    Initializes the Task class/structure.
    The first 22 parameters just store the same information as in the tasks.csv file.
    '''
    def __init__(self, this_id, class_name, outer_id, exec_n, create_t_id, create_t_class, create_t_name, exec_t_id, exec_t_class, exec_t_name, exec_id, exec_class, entry_time, exit_time, gran, is_t, is_r, is_c, is_fjt, is_r_exec, is_c_exec, is_e_exec):
        self.this_id = this_id 
        self.class_name = class_name
        self.outer_id = outer_id
        self.exec_n = exec_n
        self.create_t_id = create_t_id
        self.create_t_class = create_t_class
        self.create_t_name = create_t_name
        self.exec_t_id = exec_t_id
        self.exec_t_class = exec_t_class
        self.exec_t_name = exec_t_name
        self.exec_id = exec_id
        self.exec_class = exec_class
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.gran = gran
        self.is_t = is_t
        self.is_r = is_r
        self.is_c = is_c
        self.is_fjt = is_fjt
        self.is_r_exec = is_r_exec
        self.is_c_exec = is_c_exec
        self.is_e_exec = is_e_exec
        #The children of the task, i.e., the IDs of the tasks spawned by this task
        self.children = []
        #Whether the task has been marked in the DFS algorithm
        self.marked = False
        #Whether the task has been temporaneously marked in the DFS algorithm
        self.temp_marked = False
        #Whether the the task has been aggregated, i.e., its granularity has been added to its outer task. If this is false, then the task has no valid outer task and will be written in the aggregated tasks file
        self.aggregated = False
    '''
    Implements the recursive visit routine of the DFS algorithm.
    In the context, it is used to topologically sort the tasks, i.e, every task comes before its outer task.
    During the visit, the task is appended to the children list of its outer task (if it exists).
    '''
    def visit(self):
        if self.marked == True:
            return
        if self.temp_marked == True:
            sys.exit("Not a DAG")
        self.temp_marked = True
        if self.outer_id in tasks_ids:
            neighbour = tasks_ids[self.outer_id]
            neighbour.visit()
            neighbour.children.append(self)
        self.marked = True
        sorted_tasks.insert(0, self)
    '''
    Applies the aggregation rules, returns true if they hold, false otherwise.
    child: the nested task on which to apply the second part of the rules.
    '''
    def aggregation_rules(self, child):
        return self.is_t == "F" or (child.is_e_exec == "F" and child.create_t_id == child.exec_t_id)
    '''
    Performs aggregation for a task by adding the granularities of its children.
    If the task has no child, then its granularity is returned.
    If the task has children, then for each one of them aggregation rules are checked. If the rules hold, then the function is recursively called on the child, and the total
    granularity is added to the outer task. Last, the child is marked as aggregated.
    On the other hand, if the rules do not apply to the child, then said child is skipped for the iteration.
    '''
    def aggregate(self):
        if len(self.children) == 0:
            return self.gran
        else:
            for child in self.children:
                if self.aggregation_rules(child) == True:
                    self.gran = self.gran + child.aggregate()
                    child.aggregated = True
        return self.gran

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
Reads the tasks.csv file. For each task in the file, as Task object is instantiated and added to the tasks list. The ID of said task is also inserted to the IDs dictionary, pointing to the
newly created Task instance.
'''
def read_csv():
    csv_line_counter = 0
    with open(tasks_file, 'rb') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        for row in csv_reader:
            if csv_line_counter != 0:
                this_id = row[0]
                if contains_letters(this_id):
                    continue
                class_name = row[1]
                outer_id = row[2]
                if contains_letters(outer_id):
                    continue
                if contains_letters(row[3]):
                    continue
                exec_n = long(row[3])
                create_t_id = row[4]
                if contains_letters(create_t_id):
                    continue
                create_t_class = row[5]
                create_t_name = row[6]
                exec_t_id = row[7]
                if contains_letters(exec_t_id):
                    continue
                exec_t_class = row[8]
                exec_t_name = row[9]
                exec_id = row[10]
                if contains_letters(exec_id):
                    continue
                exec_class = row[11]
                if contains_letters(row[12]):
                    continue
                entry_time = long(row[12])
                if contains_letters(row[13]):
                    continue
                exit_time = long(row[13])
                if contains_letters(row[14]):
                    continue
                gran = long(row[14])
                is_t = row[15]
                is_r = row[16]
                is_c = row[17]
                is_fjt = row[18]
                is_r_exec = row[19]
                is_c_exec = row[20]
                is_e_exec = row[21]
                if outer_id != "-1":
                    new_task = Task(this_id, class_name, outer_id, exec_n, create_t_id, create_t_class, create_t_name, exec_t_id, exec_t_class, exec_t_name, exec_id, exec_class, entry_time, exit_time, gran, is_t, is_r, is_c, is_fjt, is_r_exec, is_c_exec, is_e_exec)
                    tasks.append(new_task)
                    tasks_ids[this_id] = new_task
            csv_line_counter = csv_line_counter + 1
    
'''
Creates and writes the csv file containing the aggregated tasks.
'''
def write_csv():
    with open('aggregated-tasks.csv', 'w') as csvfile:
        fieldnames = ['ID',
                      'Class',
                      'Outer Task ID',
                      'Execution N.',
                      'Creation thread ID',
                      'Creation thread class',
                      'Creation thread name',
                      'Execution thread ID',
                      'Execution thread class',
                      'Execution thread name',
                      'Executor ID',
                      'Executor class',
                      'Entry execution time',
                      'Exit execution time',
                      'Granularity',
                      'Is Thread',
                      'Is Runnable',
                      'Is Callable',
                      'Is ForkJoinTask',
                      'Is run() executed',
                      'Is call() executed',
                      'Is exec() executed']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for s_task in sorted_tasks:
            if s_task.aggregated == False:
                writer.writerow({
                        'ID': s_task.this_id,
                        'Class': s_task.class_name,
                        'Outer Task ID': s_task.outer_id,
                        'Execution N.': s_task.exec_n,
                        'Creation thread ID': s_task.create_t_id,
                        'Creation thread class': s_task.create_t_class,
                        'Creation thread name': s_task.create_t_name,
                        'Execution thread ID': s_task.exec_t_id,
                        'Execution thread class': s_task.exec_t_class,
                        'Execution thread name': s_task.exec_t_name,
                        'Executor ID': s_task.exec_id,
                        'Executor class': s_task.exec_class,
                        'Entry execution time': s_task.entry_time,
                        'Exit execution time': s_task.exit_time,
                        'Granularity': s_task.gran,
                        'Is Thread': s_task.is_t,
                        'Is Runnable': s_task.is_r,
                        'Is Callable': s_task.is_c,
                        'Is ForkJoinTask': s_task.is_fjt,
                        'Is run() executed': s_task.is_r_exec,
                        'Is call() executed': s_task.is_c_exec,
                        'Is exec() executed': s_task.is_e_exec
                    })

'''
Sorts the tasks using DFS.
'''
def topological_sort():
    for task in tasks:
        if task.marked == False:
            task.visit()

'''
Aggregates the tasks.
The functions starts by the last element of the sorted array, as at the end there are the most 'outer' tasks.
'''
def aggregate():
    index = len(sorted_tasks) - 1
    while index >= 0:
        if sorted_tasks[index].aggregated == False:
            sorted_tasks[index].aggregate()
        index = index - 1

read_csv()

topological_sort()

aggregate()

write_csv()
