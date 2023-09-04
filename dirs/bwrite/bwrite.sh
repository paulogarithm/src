#!/bin/bash

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 [-f <input_file>] <bytes ...>"
    exit 1
fi

input_file=""
bytes=()

while [ $# -gt 0 ]; do
    case "$1" in
        -f)
            if [ -z "$2" ]; then
                echo "Error: Missing input file after -f"
                exit 1
            fi
            input_file="$2"
            shift 2
            ;;
        *)
            bytes+=("$1")
            shift
            ;;
    esac
done

if [ -n "$input_file" ]; then
    if [ ! -f "$input_file" ]; then
        echo "Error: Input file $input_file does not exist."
        exit 1
    fi
    while read -r line; do
        bytes+=($line)
    done < "$input_file"
fi

concatenated_bytes=""
for byte in "${bytes[@]}"; do
    concatenated_bytes="${concatenated_bytes}\\x$byte"
done

echo -ne "$concatenated_bytes"
