#!/bin/bash
# Server Connection
#   Creates a connection to labrad with all servers given shortcuts.

# get directory of this file
FILE_DIR="$( dirname "$0" )/server_cxn.py"

# set up environment
source ~/.bash_profile
conda activate labart

# run file
python -ix $FILE_DIR

# unset variables
unset FILE_DIR
