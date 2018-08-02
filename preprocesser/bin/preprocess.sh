#!/bin/bash

source env-var.sh

if [ ! -d "$PREP_FILE_PATH" ]; then
    mkdir $PREP_FILE_PATH
fi

if  [ "$(ls -A $PREP_FILE_PATH)" ]; then
    if [ ! -z ${DEBUG+x} ]; then
	echo "Preprocessed types have already be computed. If you wish to run the preprocesser, delete all files from $PREP_FILE_PATH"
    fi
    exit 0
fi

rm -rf $PREPROCESSER_OUTPUT_PATH/*
echo "Preprocessing tasks (init)...."
$PREPROCESSER_SCRIPT_PATH/do_preprocess.sh task-init
sleep 2
echo "=================="
echo "Preprocessing runnable (init)...."
$PREPROCESSER_SCRIPT_PATH/do_preprocess.sh runnable-init
sleep 2
echo "=================="
echo "Preprocessing callable (init)...."
$PREPROCESSER_SCRIPT_PATH/do_preprocess.sh callable-init
sleep 2
echo "=================="
echo "Preprocessing forkjointask (init)...."
$PREPROCESSER_SCRIPT_PATH/do_preprocess.sh forkjointask-init
sleep 2
echo "=================="
echo "Preprocessing tasks (exec)...."
$PREPROCESSER_SCRIPT_PATH/do_preprocess.sh task-exec
sleep 2
echo "=================="
echo "Preprocessing executors (submit)...."
$PREPROCESSER_SCRIPT_PATH/do_preprocess.sh executor-submit
sleep 2
echo "=================="


if [ "$(ls -A $PREPROCESSER_OUTPUT_PATH)" ]; then
    cp -r $PREPROCESSER_OUTPUT_PATH/* $PREP_FILE_PATH
    echo "Preprocessed type hierarchy added to $PREP_FILE_PATH"
fi
