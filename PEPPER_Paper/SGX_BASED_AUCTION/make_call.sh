#!/bin/bash

for i in {1..100}
do     > stdout.txt 2> stderr.txt
    curl -k  https://0.0.0.0:8045/initEnclave -w %{time_total} >> enclave_time_1K.txt 
    echo ' ' >> enclave_time_1K.txt
    res=$?
    if test "$res" != "0"; then
        curl -k  https://0.0.0.0:8045/closeApp
    fi
done
