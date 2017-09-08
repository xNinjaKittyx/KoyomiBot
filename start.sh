#!/bin/sh
DIR=$(cd `dirname $0` && pwd)
cd $DIR
while true
do
    python3 main.py
done
