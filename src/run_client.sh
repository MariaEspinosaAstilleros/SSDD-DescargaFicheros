#!/bin/sh
#

mkdir -p ../downloads/
./file_downloader.py --Ice.Config=./config_files/client.config -t "transferFactory -t -e 1.1 @ TransferAdapter" "$@"