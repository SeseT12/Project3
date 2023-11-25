#!/bin/bash

for port in {33000..34000}; do
    pid=$(lsof -t -i :$port)

    if [ -n "$pid" ]; then
        echo "Terminating process using port $port (PID: $pid)"
        kill -9 $pid
    else
        echo "No process found using port $port"
    fi
done