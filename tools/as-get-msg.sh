#!/bin/sh

usage() {
	cat << EOF
Usage: $0 [-h] -n [deveui]
       $0 [-h] [-l num] [-a] deveui

    -n: retrieve new records.
    -l: retrieve the last num records. default is 10.
    -a: show the application data. default is to show all data.
        the message content can be displayed if decoded.

EOF
	exit 0
}

if [ $# -eq 0 ] ; then
	usage
fi

lastone=0
msgnum=10
appdata=0
debug=0
deveui=""

while [ $# -gt 0 ] ; do
	case "$1" in
	--help|-h)
		usage
		;;
	-n)
		lastone=1
		;;
	-l)
		msgnum=$2
		shift
		;;
	-a)
		appdata=1
		;;
	-d)
		debug=1
		;;
	-*)
		usage
		;;
	*)
		deveui=$1
	esac
	shift
done

if [ $lastone -eq 1 ] ; then
	if [ -z "$deveui" ] ; then
		cmd='db.app.aggregate([ { "$group": { "_id":"$DevEUI_uplink.DevEUI", "latest": { "$last":"$DevEUI_uplink" }, }}, { "$project": { "_id":0, "DevEUI":"$_id", "latest":"$latest" }} ])'
	else
		cmd='db.app.find({"DevEUI_uplink.DevEUI":"'$deveui'"}).sort({$natural:-1}).limit(1)'
	fi
else
	if [ $appdata -eq 1 ] ; then
		cmd='db.app.find({"DevEUI_uplink.DevEUI":"'$deveui'"},{"_id":0,"DevEUI_uplink.__app_data":"app_data"}).limit('$msgnum')'
	else
		cmd='db.app.find({"DevEUI_uplink.DevEUI":"'$deveui'"}).limit('$msgnum')'
	fi
fi

if [ $debug -eq 1 ] ; then
	echo $cmd
fi
echo $cmd | mongo --quiet lorawan
