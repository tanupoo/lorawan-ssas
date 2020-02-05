#!/bin/sh

HOST=127.0.0.1
DBNAME=sensors
DBUSER=demo
opt="-h $HOST -d $DBNAME -U $DBUSER"

psql $opt -c "\d"
exit 0

if [ -z "$1" ] ; then
	echo "Usage: db_wbgt.sh (date)"
	echo "e.g. db_wbgt.sh 2019-07-22"
	exit 1
else
	dt=$1
fi

P=`echo $dt | awk '{gsub(/-/,"");print $0}'`

psql $opt -c "select * from raw_gs_lw360hr where ts between '$dt 00:00:00' and '$dt 23:59:59' order by ts;" > vital-db-${P}.dat

psql $opt -c "select * from raw_gh_wbgt where ts between '$dt 00:00:00' and '$dt 23:59:59' order by ts;" > wbgt-db-${P}.dat
