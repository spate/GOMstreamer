#!/bin/bash

# Set the versioner environment variable for Mac OS X
# (Necessary for Snow Leopard)
export VERSIONER_PYTHON_PREFER_32_BIT=yes

PKGBIN=`basename $0`
PKGPATH=`echo $0 | sed "s/$PKGBIN//"`
PKGPATH=`cd $PKGPATH && pwd`

python "${PKGPATH}/gui.py"

