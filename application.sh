#!/bin/bash

#Contains user-customizable variables to profile a custom application with tgp

#Automatically exports the variables set in this file
set -a

#Sets the root path of tgp (optional)
#To profile a target application from a location external to the default tgp directory: 
#<ant -buildfile <path/to/tgp/build.xml> <profile-task-bc|profile-task-rc|profile-cc>
#Uncomment to change root path of tgp
#ROOT_PATH="path/to/tgp"

#Sets the classpath of the target application
#Uncomment to change the classpath of the target application
#APP_CLASSPATH="classpath-of-application"

#Sets the flags to be sent to the JVM executing the target application, if any 
#Uncomment to change the flags to be sent to the JVM executing the target application
#Flags are assigned with a String value, and are separated by a single space
#APP_FLAGS="flags-of-application"

#Sets target application main class in the target jar file
#Uncomment to change main class
#APP_MAIN_CLASS="MainClass"

#Sets the arguments to be sent to the target application, if the application requires them
#Uncomment to change the arguments to be sent to the target application
#Arguments should be separated by a single space
#APP_ARGS="arguments-of-application"

#Prevents any further variable to be exported
set +a
