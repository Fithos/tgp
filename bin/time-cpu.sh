#!/bin/bash

#Activates CPU utilization sampling using top (CPU used by user and CPU used by the system, only available in Linux)
#Arguments: $1 PID of the process to track
#Output: writes the analysis on the file indicated by CPU_TRACE

if [ `uname -s` == "Linux" ]; then
    
    echo "Timestamp (ns),CPU utilization (user),CPU utilization (kernel)"  > $CPU_TRACE
    
    while kill -0 $1 >/dev/null 2>&1 # Until the process exists 
    do
	echo $(cat /proc/timer_list | grep now | awk '{print $3","}' | sed "s/$/ /g"; 
	    top -b -d 0 -n 2 | grep "%Cpu(s)" | tail -n 1 | awk '{print $2,",",$4}' | tr -d ' ';) >> $CPU_TRACE #Outputs cpu data in the CPU trace
    done
fi
