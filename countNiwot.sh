#!/bin/bash
year="$1"
d1="$2"
d2="$3"

printf "Year "
printf $year
printf ":  "
printf $d1
printf " to "
printf $d2
printf "\n"
echo  "----------------------------"
#echo $d1
#echo $d2

for doy in $(seq -f "%03g" $d1 -1 $d2)
do 
	printf "DOY "
	printf $doy
	printf ":\t"
	cmd="find /data/archive/niwotflir/$year/*/niwotflir-*-"
	cmd+=$doy
	cmd+="_* -type f -size 617180c -ls"
	$cmd 2> /dev/null |wc -l
done



