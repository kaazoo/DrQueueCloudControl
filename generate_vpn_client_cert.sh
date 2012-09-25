#!/bin/bash

if [ "$1" == "" ]; then
  echo "specify client hostname"
  exit 1
fi

if [ "$2" == "" ]; then
  echo "specify server ip address"
  exit 1
fi

CLIENTHOSTNAME=$1
SERVER_IP=$2

cd /etc/openvpn/easy-rsa/2.0/
. ./vars
./pkitool $CLIENTHOSTNAME
cd /etc/openvpn
mkdir $CLIENTHOSTNAME
cp easy-rsa/2.0/keys/$CLIENTHOSTNAME.crt $CLIENTHOSTNAME/client.crt
cp easy-rsa/2.0/keys/$CLIENTHOSTNAME.key $CLIENTHOSTNAME/client.key
cp for_all/* $CLIENTHOSTNAME/
cd $CLIENTHOSTNAME
sed "s/REPL_SERVER_IP/$SERVER_IP/" client_repl.conf >client.conf
tar cvzf $CLIENTHOSTNAME.tgz ca.crt client.conf client.crt client.key client.up
cp $CLIENTHOSTNAME.tgz /var/www/keystore/
