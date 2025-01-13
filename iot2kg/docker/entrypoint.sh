#!/bin/sh

if [ "$1" = "preprocessor" ]; then
    shift
    python preprocessor.py "$@"
elif [ "$1" = "generator" ]; then
    shift
    python generator.py "$@"
else
    echo "Unknown command: $1"
    echo "Available commands: preprocessor, generator"
    exit 1
fi