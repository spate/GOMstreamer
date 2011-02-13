#!/bin/bash

# Set the versioner environment variable for Mac OS X
# (Necessary for Snow Leopard)
export VERSIONER_PYTHON_PREFER_32_BIT=yes

SCRIPTNAME=`readlink $0`
if [ -z "$SCRIPTNAME" ]
then
  SCRIPTNAME="$0"
fi
SCRIPTPATH=`dirname $SCRIPTNAME`
GUI=$SCRIPTPATH/gui.py

python $GUI $@

