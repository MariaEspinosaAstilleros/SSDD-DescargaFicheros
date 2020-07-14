#!/bin/sh
#

echo "Creating directories..."
mkdir -p db/Registry 
mkdir -p IceStorm/

echo "Exec registry"
icegridregistry --Ice.Config=./config_files/registry.config &
sleep 1

echo "Exec icestorm"
icebox --Ice.Config=./config_files/icebox.config &
sleep 1

echo "Exec server-side elements"
./sender_factory.py --Ice.Config=./config_files/senders.config files/ &
sleep 1
./transfer_manager.py --Ice.Config=./config_files/transfers.config  -s "senderFactory -t -e 1.1 @ SenderAdapter"

echo "Shoutting down..."
sleep 1
rm $OUT