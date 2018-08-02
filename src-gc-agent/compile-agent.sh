#!/bin/bash

#Compiles GC agent
#Arguments: none
#Output: compiles agent

#Source of global variables not declared in this script
source env-var.sh

AGENT_EXT=$AGENT_EXT_UNIX
INCLUDE="linux" 

#Checks if OS is MacOS
if [ `uname -s` == "Darwin" ]; then
    AGENT_EXT=$AGENT_EXT_MACOS
    INCLUDE="darwin"
fi

#Executes command to compile src-gc-agent/gc-agent.c
gcc -shared -fpic -o $GC_AGENT$AGENT_EXT -I$JAVA_HOME/include/ -I$JAVA_HOME/include/$INCLUDE/ src-gc-agent/gc-agent.c
