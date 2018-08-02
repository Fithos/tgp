#!/bin/bash

#Starts the DiSL instrumentation server
#Arguments: 
#    $1 the path to the profiler to be used for the analysis
#    $2 the path to the PAPI agent jar
#Output: executes a command starting the instrumentation server
#        error if there is less than one argument

#Checks whether there is at least one argument
PROFILER_JAR=""
if [ $# -ge 1 ]; then
    PROFILER_JAR=$1
else
    echo "Usage: $0 <profiler-jar> <PAPI-agent-jar>"
    exit -1
fi

#Composes the server class path
SERVER_CP=$DISL_SERVER_JAR:$PROFILER_JAR:$PARSER_JAR$2

#Composes the command executing the DiSL instrumentation server
COMMAND="$JAVA_HOME/bin/java -cp $SERVER_CP $DISL_SERVER_OPTIONS ch.usi.dag.dislserver.DiSLServer"

#Prints the command if in debug mode
if [ ! -z ${DEBUG+x} ]; then
    echo $COMMAND
fi

#Executes the command
$COMMAND
