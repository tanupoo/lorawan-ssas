#!/bin/sh

PROGNAME=lrwssas.py
SSASHOME=/home/lorawan/ssas
PID=${SSASHOME}/${PROGNAME}.pid

do_stop()
{
	if [ -f $PID ] ; then
		PID=`cat $PID`
	else
		PID=`ps auxw | grep lorawan-ssas/${PROGNAME} | awk '!/grep/{print $2}'`
	fi
	if [ -z "$PID" ] ; then
		echo "${PROGNAME} doesn't exist."
	else
		echo "kill $PID of ${PROGNAME}."
		kill $PID
	fi
}

do_start()
{
	if [ ! -z "`do_status`" ] ; then
		echo "${PROGNAME} already exists"
		exit 1
	fi
        export PYTHONPATH=${SSASHOME}/lorawan-ssas
        #nohup ${SSASHOME}/lorawan-ssas/lrwssas.py ${SSASHOME}/config.json $* &
        ${SSASHOME}/lorawan-ssas/lrwssas.py ${SSASHOME}/config.json $* &
}

do_status()
{
        ps auxw | grep python | grep lorawan-ssas/${PROGNAME} | grep -v grep
}

#
# main
#
case "$1" in
        restart|forcestart) shift; do_stop; do_start $* ;;
        start) shift; do_start $* ;;
        debugstart) shift; do_start -d $* ;;
        stop) do_stop ;;
        status) do_status ;;
        *) echo "Usage: ssasctl.sh (start|stop)" ;;
esac

exit 0
