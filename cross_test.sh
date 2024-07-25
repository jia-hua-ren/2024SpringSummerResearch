#!/bin/bash

mainPath="/genTests/"

methodsPath="/genTests/methods"

testsPath="/genTests/methods/tests"

# get the length of the methods path + 1 to get filename substring later
length=$((${#methodsPath} + 1))
# echo $length

testLength=$((${#testsPath} + 1))

for method in "$methodsPath"/*; do
    if [ -f "$method" ]; then
	fileName=${method:length}
	for tst in "$testsPath"/*.cpp; do
	    if [ -f "$tst" ]; then
		# check if we are running the method's own test; skip if we are
		base="${fileName%.*}"
		ext="${fileName##*.}"
		newname="${base}_dot_${ext}"
		if [[ "${tst}" =~ "${newname}" ]]; then
		     continue
		fi
		testing="${tst:testLength}"
		echo "####################################"
		echo "Cross testing ${fileName} to ${testing}"
	    	# the script takes the current file name and the current test file		
		python3 transform_test.py "$fileName" "$method" "$tst"
		cmake /genTests/CMakeLists.txt > /dev/null
		if ! make -C "/genTests/" > /dev/null; then
		     echo -e "\e[0;31mmake compilation error! skipped\e[0m"
		     # perhaps something to mark that there is an error
		     continue
		fi
		output=$(/genTests/runTests)
		regex=".*\[[[:space:]][[:space:]]PASSED[[:space:]][[:space:]]\][[:space:]][1-9]+[[:space:]]test(s?)\.$"
		if [[ "$output" =~ $regex ]]; then
		  echo -e "\e[0;32m${fileName} is functionally equivalent to ${testing}\e[0m"
		fi
	    fi
	done
    fi

done
