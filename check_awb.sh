if [ $# -eq 0 ]; then
	term='balance=1'
else 
	term=$1
fi
tmp=$(mktemp)
for dir in /home/ftp/data/*/
do
    find $dir/*.meta -type f -printf '%T@ %p\n' 2> /dev/null | sort -n | tail -1 | cut -f2- -d" " >> $tmp
done
grep -i -m1 $term $(cat $tmp)
