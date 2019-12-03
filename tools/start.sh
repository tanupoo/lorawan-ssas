#!/bin/sh
SSASHOME=/home/lorawan/ssas
export PYTHONPATH=${SSASHOME}/lorawan-ssas
${SSASHOME}/lorawan-ssas/lrwssas.py ${SSASHOME}/config.json -d

