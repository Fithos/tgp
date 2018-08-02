#!/bin/bash

#Activates context-switches profiling using perf (only available in Linux)
#Arguments: $1 the PID (process identifier) indicating the process to profile
#Output: writes the collected metric on the file indicated by PERF_TRACE

if [ `uname -s` == "Linux" ]; then
    #Dump starting timestamp of perf 
    cat /proc/timer_list | grep now | awk '{print $3 }' > $PERF_START_TIMESTAMP_TRACE
    
    echo "perf stat --output $PERF_TRACE --append -I 100 -e $PERF_METRICS -x, -a -p $1"
    
    #Profiles every 100ms the context switches experienced by the target application since the last measure
	perf stat --output $PERF_TRACE --append -I 100 -e $PERF_METRICS -x, -a -p $1 #PERF_METRICS is by default context-switches
fi