#!/bin/bash

if [$1 -eq ""]; then
  echo "specify client hostname"
  exit 1
fi

CLIENTHOSTNAME=$1

cd /etc/openvpn/easy-rsa/2.0/
. ./vars
./pkitool $CLIENTHOSTNAME
cd /etc/openvpn
mkdir $CLIENTHOSTNAME
cp easy-rsa/2.0/keys/$CLIENTHOSTNAME.crt $CLIENTHOSTNAME/client.crt
cp easy-rsa/2.0/keys/$CLIENTHOSTNAME.key $CLIENTHOSTNAME/client.key
cp for_all/* $CLIENTHOSTNAME/
cd $CLIENTHOSTNAME
tar cvzf $CLIENTHOSTNAME.tgz ca.crt client.conf client.crt client.key client.up
cp $CLIENTHOSTNAME.tgz /var/www/keystore/
