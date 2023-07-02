#!/bin/bash

log_file="disk_usage.log"

timestamp=$(date "+%Y-%m-%d %H:%M:%S")
disk_usage=$(iostat -d -x -y | grep Device)
echo "$timestamp $disk_usage" | tee $log_file

while true
do
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    disk_usage=$(iostat -d -x -y | grep sda)
    echo "$timestamp $disk_usage" | tee -a $log_file
    sleep 1
done
