#!/bin/bash

#Sets up and runs the profiling
#Arguments: $1 the profiling mode, which is also the name of .jar file containing the profiler (task-bc|task-rc|cc)
#Output: runs the bash scripts in the bin directory to perform the analysis
#        error if there is less than one argument

#Checks if APP_MAIN_CLASS in env-var.sh is already set. If not, source such file
if [ -z ${APP_MAIN_CLASS+x} ]; then
    source env-var.sh
fi

#Removes the traces from old analysis
if [ -d $TRACES_PATH ]; then
    mv $TRACES_PATH/ $PROFILES_PATH/
fi
 
rm $PROFILES_PATH/*

#Checks whether there is at least one argument otherwise exits the script
PROFILER_JAR=""
if [ $# -ge 1 ]; then
    PROFILER_JAR=$PROFILER_PREFIX$1$PROFILER_SUFFIX
else
    echo "Usage: $0 <profiler-jar>"
    exit -1
fi

#Creates the right extension for agents: .so for unix and .jnilib for MacOS
AGENT_EXT=$AGENT_EXT_UNIX
if [ `uname -s` == "Darwin" ]; then
    AGENT_EXT=$AGENT_EXT_MACOS
fi

#Initializes variables
APP_CP=""
AGENT_FLAGS=""
COMMAND_SUFFIX=""

CP_PAPI_SUFFIX=""
AGENT_PAPI_TOKEN=""
AGENT_GC_TOKEN=""

#When profiling reference cycles, checks if HPC support is available, otherwise exists
if [ "$1" == "task-rc" ]; then

    if [ `uname -s` == "Darwin" ]; then
        echo "ERROR: HPC not supported on MacOS!"
        exit -1
    fi
#Sets the GC agent, PAPI and activates context switches and CPU sampling
    CP_PAPI_SUFFIX=":$PAPI_BENCH_JAR"
    AGENT_PAPI_TOKEN="-agentpath:$PAPI_BENCH_AGENT$AGENT_EXT"
fi

#Sets the application class path 
APP_CP=$APP_CLASSPATH:$SHADOW_VM_DISPATCH_JAR$CP_PAPI_SUFFIX
#Sets the agent flags (GC is set if PROFILE_GC is "yes")
if [ $PROFILE_GC == "yes" ]; then
    AGENT_GC_TOKEN="-agentpath:$GC_AGENT$AGENT_EXT"
fi

AGENT_FLAGS="-agentpath:$DISL_SERVER_AGENT_PREFIX$AGENT_EXT -agentpath:$SHADOW_VM_AGENT_PREFIX$AGENT_EXT $AGENT_GC_TOKEN $AGENT_PAPI_TOKEN -Xbootclasspath/a:$DISL_BYPASS_JAR:$PROFILER_JAR:$SHADOW_VM_DISPATCH_JAR$CP_PAPI_SUFFIX"

if [ ! -z ${SHARE_DISL_SERVER+x} ] && [ $SHARE_DISL_SERVER == true ]; then
#Sf DiSL server can be shared
    RUNNING_SERVER=$(pgrep -u `id -u` -f ch.usi.dag.dislserver.DiSLServer)
    if [ "$RUNNING_SERVER" == "" ]; then
          #Starts the instrumentation server in background if there is no server running
	      $BIN_PATH/startInstrumentationServer.sh $PROFILER_JAR $CP_PAPI_SUFFIX &
    else 
	     echo "DiSL server already running. Skipping creation of a new server"
    fi
else
   #DiSL server is not shared, so it is killed
   pkill -9 -u `id -u` -f ch.usi.dag.dislserver.DiSLServer
   sleep 1
   #Starts instrumentation server
   $BIN_PATH/startInstrumentationServer.sh $PROFILER_JAR $CP_PAPI_SUFFIX &
fi

sleep 1

#Starts the ShadowVM in background
$BIN_PATH/startShadowVM.sh $PROFILER_JAR &

sleep 1

#Composes the command which will run the target application
COMMAND="$JAVA_HOME/bin/java -cp $APP_CP $AGENT_FLAGS $APP_FLAGS $APP_OPTIONS $APP_MAIN_CLASS $APP_ARGS $COMMAND_SUFFIX"

#Prints command if in debug mode
if [ ! -z ${DEBUG+x} ]; then
    echo $COMMAND
fi

#Executes command in background
$COMMAND &

#Sets the identifier of the current process
export PID=$!

#Starts context switches sampling by using perf: 
if [ $PROFILE_CS == "yes" ]; then
    $BIN_PATH/startPerf.sh $PID &
fi
  
#Starts CPU sampling by using top:
if [ $PROFILE_CPU == "yes" ]; then  
    $BIN_PATH/time-cpu.sh $PID & 
fi

#Waits until the process indicated by PID has finished executing
wait $PID

#Kills the perf process (if context-switches profiling option is set)
if [ `uname -s` == "Linux" ] && [ $PROFILE_CS == "yes" ]; then
        pgrep perf | xargs kill -9
fi

#Executes filtering script (just for perf)
$BIN_PATH/filter-cs.sh
