#!/bin/bash
export HOST=$1
export PORT=$2
export USER=$3

clear
echo "Connecting to $USER@$HOST ..."
echo "(No password found in config file)"

ssh $USER@$HOST -p $PORT