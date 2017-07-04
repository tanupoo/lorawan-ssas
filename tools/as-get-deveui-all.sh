#!/bin/sh

cmd='db.app.distinct("DevEUI_uplink.DevEUI")'

echo $cmd | mongo --quiet lorawan
