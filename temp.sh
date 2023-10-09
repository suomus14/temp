#!/bin/sh

ip_addr="192.168.11.108"
file_name="SiM01.txt"
if [ -e $file_name ]; then
    rm -f $file_name
fi
touch $file_name
sshpass -p '1018' ssh suomus@192.168.11.108 -o StrictHostKeyChecking=no ls -l --time-style="+%Y%m%d-%H%M%S" /mnt/usb0/02_book/41_wallpaper >> $file_name


