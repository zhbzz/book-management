#!/bin/bash

if [ -z "$1" ]; then
    echo "[ERROR PARAMS] usage:"
    echo "    clean_pyc.sh /path/to/folder"
else
    find "$1" -type d -name '__pycache__' -exec rm -rf {} +
fi
