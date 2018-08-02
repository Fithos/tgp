#!/bin/bash

#If the context-switches profiling was enabled, filters the generated file as follows:
# - deletes all blank columns
# - converts the local (to perf) timestamps in seconds associated to the context switches to global timestamps in nanoseconds (using the global timestamp in PERF_START_TIMESTAMP_TRACE)
# - deletes all rows where context switches were not counted
# - Adds a proper header to the file

#If perf.csv exists
if [ -f $PERF_TRACE ]; then

    #Creates CS_FILE if it does not exist 
    if [ ! -f $CS_FILE ]; then
        touch $CS_FILE
    fi

    NANO=1000000000.0
    #Gets base timestamp from PERF_START_TIMESTAMP_TRACE
    START=$(cat $PERF_START_TIMESTAMP_TRACE)

    #Performs filtering
    sed '/^#/ d' $PERF_TRACE | awk 'NF' | awk -v n="$NANO" 'BEGIN{FS=OFS=","}{$1=$1*n}1' | awk -F"," '{ printf("%d,%s,%s,%s,%s\n", $1,$2,$3,$4,$5)}' | awk -v s="$START" 'BEGIN{FS=OFS=","}{$1=$1+s}1' | grep -v "<not counted" | cut -d',' -f1,2 > $CS_FILE

    #Adds header
    sed -i '1s/^/Timestamp (ns),Context Switches\n/' $CS_FILE

    rm $PERF_TRACE
    rm $PERF_START_TIMESTAMP_TRACE

fi

#Moves profiles directory into traces directory
mv $PROFILES_PATH $TRACES_PATH/
