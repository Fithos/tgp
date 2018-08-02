#!/bin/bash

#Starts ShadowVM
#Arguments: $1 the path to the profiler to be used for the analysis
#Output: executes a command that runs the ShadowVM
#        error if there is less than one argument

PROFILER_JAR=""
if [ $# -ge 1 ]; then #checks whether there is at least one argument
    PROFILER_JAR=$1
else
    echo "Usage: $0 <profiler-jar>" 
    exit -1
fi

#Composes the ShadowVM class path
SHADOW_VM_CP=$SHADOW_VM_JAR:$PROFILER_JAR

#Composes the command to run the ShadowVM
COMMAND="$JAVA_HOME/bin/java -cp $SHADOW_VM_CP $SHADOW_VM_OPTIONS ch.usi.dag.dislreserver.DiSLREServer"

#Prints command if in debug mode
if [ ! -z ${DEBUG+x} ]; then
    echo $COMMAND
fi

#Executes command
$COMMAND
