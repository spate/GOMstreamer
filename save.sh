#!/bin/sh
EMAIL='youremail@example.com'
PASSWORD='PASSWORD'
QUALITY='SQTest'
OUTPUTFILE='dump.ogm'
python ./gomparser.py -e $EMAIL -p $PASSWORD -q $QUALITY -o $OUTPUTFILE
