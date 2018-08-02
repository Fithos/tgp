#!/bin/bash

source env-var.sh

# Construct classpath

CP_LIB=""

for lib in `ls $PREPROCESSER_LIB_PATH`
do
    CP_LIB=${CP_LIB}${PREPROCESSER_LIB_PATH}/${lib}:
done

CLASSPATH=$PREPROCESSER_JAR:$CP_LIB


# Set up variables for not-default execution

IN_PREFIX=$PREPROCESSER_INPUT_PATH/
OUT_PREFIX=$PREPROCESSER_OUTPUT_PATH/
SUFFIX=$PREPROCESSER_FILE_EXT

if [ $# -eq 1 ]; then
    IN_PREFIX=$IN_PREFIX$1"-"
    OUT_PREFIX=$OUT_PREFIX$1"-"
fi

BLACKLIST=$IN_PREFIX"blacklist"$SUFFIX
WHITELIST=$IN_PREFIX"whitelist"$SUFFIX
BLACKLISTED=$OUT_PREFIX"blackTypes"$SUFFIX
WHITELISTED=$OUT_PREFIX"whiteTypes"$SUFFIX
METHODS=$OUT_PREFIX"methods"$SUFFIX
CLASSGRAPH=$OUT_PREFIX"typegraph.ser"
CLASSGRAPH_TEXT=$OUT_PREFIX"typegraph.txt"

COMMAND="$JAVA_HOME/bin/java -cp $CLASSPATH ch.usi.dag.typeparser.Parser -blackTypeFile $BLACKLISTED -whiteTypeFile $WHITELISTED -blacklistFile $BLACKLIST -whitelistFile $WHITELIST -attributeFile $METHODS -outputTypeGraphFile $CLASSGRAPH -outputTypeGraphTextFile $CLASSGRAPH_TEXT"

if [ ! -z ${DEBUG+x} ]; then
    echo $COMMAND
fi

$COMMAND
