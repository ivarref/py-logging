#!/usr/bin/env bash

echo '' > results.txt

./race_threads_original.py 2> ./output.txt | tee -a results.txt
./race_threads_mp_rlock.py 2> ./output.txt | tee -a results.txt

./race_threads_original.py 2> ./output.txt | tee -a results.txt
./race_threads_mp_rlock.py 2> ./output.txt | tee -a results.txt

./race_threads_original.py 2> ./output.txt | tee -a results.txt
./race_threads_mp_rlock.py 2> ./output.txt | tee -a results.txt

./race_threads_original.py 2> ./output.txt | tee -a results.txt
./race_threads_mp_rlock.py 2> ./output.txt | tee -a results.txt

./race_threads_original.py 2> ./output.txt | tee -a results.txt
./race_threads_mp_rlock.py 2> ./output.txt | tee -a results.txt
