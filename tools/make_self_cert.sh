#!/bin/sh

if [ -z "$1" ] ; then
    echo "Usage: make_self_cert.sh (your server's name)"
    echo "    e.g. make_self_cert.sh /C=JP/ST=Tokyo/L=Akasaka/CN=test"
    exit 1
else
    name=$1
fi

openssl req -x509 -sha256 -nodes -newkey rsa:4096 \
    -days 7300 \
    -keyout server.crt \
    -out server.crt \
    -subj ${name}
