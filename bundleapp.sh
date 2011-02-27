#!/bin/bash

rm -rf GOMstreamer.app
mkdir GOMstreamer.app
mkdir GOMstreamer.app/Contents
mkdir GOMstreamer.app/Contents/MacOS
mkdir GOMstreamer.app/Contents/Resources
cp Info.plist GOMstreamer.app/Contents
cp *.py GOMstreamer.app/Contents/Resources
cp gui.xrc GOMstreamer.app/Contents/Resources
cp gui.icns GOMstreamer.app/Contents/Resources
cp gui.sh GOMstreamer.app/Contents/MacOS
ln -s ../Resources/gui.py GOMstreamer.app/Contents/MacOS/gui.py

