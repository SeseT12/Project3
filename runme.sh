#!/bin/bash

# Activate the virtual environment
source env/bin/activate

# Start the keyserver in the background
python keyserver_start.py &

# Wait for the keyserver to initialize
sleep 2

# Start the main network node
python global_node_start.py
