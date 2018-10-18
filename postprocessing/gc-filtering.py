#!/usr/bin/python

from optparse import OptionParser
import sys
import csv

helper = '''Usage: ./gc-filtering.py -c <path to CS trace> -p <path to CPU trace> -g <path to GC trace> [--outcs <path to filtered CS trace (output)> --outcpu <path to filtered CPU trace (output)>]
    
This script filters the CS and the CPU traces, eliminating measurements obtained during GC cycles.

The script produces two new traces (named 'filtered-cs.csv' and 'filtered-cpu.csv' by default), containing the filtered CS and CPU measurements, respectively.

Note: All input traces should have been produced by tgp with a SINGLE profiling run, either in the bytecode profiling or reference-cycles profiling mode.
'''

#Default name of the output filtered CS trace
DEFAULT_CS_OUT_FILE = "filtered-cs.csv"
#Default name of the output filtered CPU trace
DEFAULT_CPU_OUT_FILE = "filtered-cpu.csv"

#Number of columns in the CS trace
FIELDS_CS = 2
#Number of columns in the CPU trace
FIELDS_CPU = 3
#Number of columns in the GC trace
FIELDS_GC = 2

#A list containing context-switches data before filtering
cs_data_array_bf = []
#A list containing context-switches data after filtering
cs_data_array = []

#A list containing CPU data before filtering
cpu_data_array_bf = []
#A list containing CPU data after filtering
cpu_data_array = []

#A list containing garbage-collection data
gc_data_array = []

class CSData:
    '''
    A class containing context-switches data taken from the CS trace.
    '''
    def __init__(self, timestamp, context_switches):
        self.timestamp = timestamp
        self.context_switches = context_switches

class CPUData:
    '''
    A class containing CPU data taken from the CPU trace.
    '''
    def __init__(self, timestamp, user, system):
        self.timestamp = timestamp
        self.user = user
        self.system = system

class GCData:
    '''
    A class containing GC data taken from the GC trace.
    '''
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time

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

def read_csv(input_csv_file, target_array, data_type, file_delimiter):
    '''
    Reads the input csv file, and sets up the input data structure.
    Depending on the data type, a new instance of CSData, CPUData, or GCData will be created and added to the target list.
    input_csv_file: the csv file to read.
    target_array: the list where to write the content of the csv file.
    data_type: the data which will be read.
    file_delimiter: the delimiter used by the file.
    '''
    csv_line_counter = 0
    with open(input_csv_file) as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=file_delimiter)
        old_gc = 0
        gc_counter = 0
        for row in csv_reader:
            #Reads and writes context-switches data
            if data_type == "CS" and csv_line_counter > 1:
                if len(row) != FIELDS_CS:
                    print("Wrong CS trace format")
                    exit(-1)
                if row[0][0] != "-" and row[1][0] != "-" and contains_letters(row[0]) == False and contains_letters(row[1]) == False:
                    new_cs = CSData(float(row[0]), float(row[1]))
                    cs_data_array_bf.append(new_cs)
            #Reads and writes CPU data
            elif data_type == "CPU" and csv_line_counter != 0:
                if len(row) != FIELDS_CPU:
                    print("Wrong CPU trace format")
                    exit(-1)
                if len(row[0]) > 0 and len(row[1]) > 0 and len(row[2]) > 0 and row[0][0] != "-" and row[1][0] != "-" and row[2][0] != "-" and contains_letters(row[0]) == False and contains_letters(row[1]) == False and contains_letters(row[2]) == False:
                    new_cpu = CPUData(long(row[0]), float(row[1]), float(row[2]))
                    cpu_data_array_bf.append(new_cpu)
            #Reads and writes GC data
            elif data_type == "GC":
                if len(row) != FIELDS_GC:
                    print("Wrong GC trace format")
                    exit(-1)
                if gc_counter == 1:
                    if old_gc[0] != "-" and row[1][0] != "-" and contains_letters(old_gc) == False and contains_letters(row[1]) == False:
                        new_gc = GCData(long(old_gc), long(row[1]))
                        gc_data_array.append(new_gc)
                else:
                    old_gc = row[1]
                gc_counter = (gc_counter + 1) % 2
            csv_line_counter = csv_line_counter + 1

def filter_cs():
    '''
    Filters the context-switches list and writes the valid CS data into the filtered array.
    To determine whether a CS measurement is valid, the timestamp of such measurement is checked against all GC start and end timestamps: if the timestamp does not fall in any time interval where GC was active, then the context-switch is valid.
    '''
    for cs_data in cs_data_array_bf:
        found = False
        for gc_data in gc_data_array:
            if cs_data.timestamp >= gc_data.start_time and cs_data.timestamp <= gc_data.end_time:
                found = True
                break
        if found == False:
            cs_data_array.append(cs_data)

def filter_cpu():
    '''
    Filters the CPU array and writes the valid CPU data into the filtered array.
    To determine whether a CPU measurement is valid, the timestamp of such measurement is checked against all GC start and end timestamps: if the timestamp does not fall in any time interval where GC was active, then the CPU measurement is valid.
    '''
    for cpu_data in cpu_data_array_bf:
        found = False
        for gc_data in gc_data_array:
            if cpu_data.timestamp >= gc_data.start_time and cpu_data.timestamp <= gc_data.end_time:
                found = True
                break
        if found == False:
            cpu_data_array.append(cpu_data)

def write_cs_csv():
    '''
    Writes the filtered context-switches list into a new csv file.
    '''
    with open (out_cs_file, 'w') as csvfile:
        fieldnames = ['Timestamp (ns)', 'Context Switches']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for cs_data in cs_data_array:
            writer.writerow({'Timestamp (ns)': cs_data.timestamp, 'Context Switches': cs_data.context_switches})

def write_cpu_csv():
    '''
    Writes the filtered CPU list into a new csv file.
    '''
    with open (out_cpu_file, 'w') as csvfile:
        fieldnames = ['Timestamp (ns)', 'CPU utilization (user)', 'CPU utilization (system)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for cpu_data in cpu_data_array:
            writer.writerow({'Timestamp (ns)': cpu_data.timestamp, 'CPU utilization (user)': cpu_data.user, 'CPU utilization (system)': cpu_data.system})

if __name__ == "__main__":
    #Flags parser
    parser = OptionParser(helper)
    parser.add_option('-c','--context-switches', dest='cs_file', type='string', help="path to the CS trace to be filtered", metavar="CS_TRACE")
    parser.add_option('-p', '--cpu', dest='cpu_file', type='string', help="path to the CPU trace to be filtered", metavar="CPU_TRACE")
    parser.add_option('-g','--garbage-collector', dest='gc_file', type='string', help="path to the GC trace. Filtering of CS and CPU measurements are be based on data contained in this trace", metavar="GC_TRACE")
    parser.add_option('--outcs', dest='out_cs_file', type='string', help="path to the output trace containing the filtered context switches. If none is provided, then the output trace will be produced in './filtered-cs.csv'", metavar="FILTERED_CS_TRACE")
    parser.add_option('--outcpu', dest='out_cpu_file', type='string', help="path to the output trace containing the filtered CPU utilization measurements. If none is provided, then the output trace will be produced in './filtered-cpu.csv'", metavar="FILTERED_CPU_TRACE")
    (options, arguments) = parser.parse_args()
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
    if (options.gc_file is None):
        print(parser.usage)
        exit(0)
    else:
        gc_file = options.gc_file
    if (options.out_cs_file is None):
        out_cs_file = DEFAULT_CS_OUT_FILE
    else:
        out_cs_file = options.out_cs_file
    if (options.out_cpu_file is None):
        out_cpu_file = DEFAULT_CPU_OUT_FILE
    else:
        out_cpu_file = options.out_cpu_file

    read_csv(cs_file, cs_data_array, "CS", ',')
    read_csv(cpu_file, cpu_data_array, "CPU", ',')
    read_csv(gc_file, gc_data_array, "GC", ',')

    print("")
    print("Starting filtering...")
    print("")
    print("Number of context switches measurements: %s" % str(len(cs_data_array_bf)))
    print("Number of CPU samplings: %s" % str(len(cpu_data_array_bf)))

    filter_cs()

    filter_cpu()

    print("")
    print("Number of context switches measurements after filtering: %s" % str(len(cs_data_array)))
    print("Number of CPU samplings after filtering: %s" % str(len(cpu_data_array)))
    print("")
    print("Filtering complete.")
    print("")

    write_cs_csv()

    write_cpu_csv()


