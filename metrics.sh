#!/bin/bash

#Contains customizable user variables to enable/disable metric profiling

#Automatically exports the variables set in this file
set -a

#Sets whether to profile context switches: "yes" or "no"
PROFILE_CS="no"

#Sets whether to profile CPU utilization: "yes" or "no"
PROFILE_CPU="no"

#Sets whether to profile stop-the-world GC cycles: "yes" or "no"
PROFILE_GC="no"

#Prevents any further variable to be exported
set +a
