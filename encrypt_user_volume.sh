#!/bin/bash

if [ "$1" == "" ]; then
  echo "specify device name"
  exit 1
fi

if [ "$2" == "" ]; then
  echo "specify user hash"
  exit 1
fi

if [ "$3" == "" ]; then
  echo "specify encryption input"
  exit 1
fi

DEVICENAME=$1
USERHASH=$2
ENCINPUT=$3

CRYPTKEY=`echo $USERHASH$ENCINPUT | sha512sum | awk '{print $1}'`

echo $CRYPTKEY | cryptsetup -c aes-xts-plain -s 256 -v --batch-mode luksFormat $DEVICENAME
echo $CRYPTKEY | cryptsetup luksOpen $DEVICENAME $USERHASH --batch-mode

mkfs.ext3 /dev/mapper/$USERHASH
mkdir /usr/local/drqueue/tmp/$USERHASH
mount -o noatime /dev/mapper/$USERHASH /usr/local/drqueue/tmp/$USERHASH
