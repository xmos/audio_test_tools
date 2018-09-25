#!/bin/bash
export PYTHONPATH=`pwd`:`dirname $BASH_SOURCE`:`dirname $BASH_SOURCE`/../../lib_vad/python:`dirname $BASH_SOURCE`/../../lib_aec/python:`dirname $BASH_SOURCE`/../../lib_beamsteering/python:`dirname $BASH_SOURCE`/../../lib_interference_canceller/python:`dirname $BASH_SOURCE`/../../lib_noise_suppression/python:`dirname $BASH_SOURCE`/../../lib_agc/python:$PYTHONPATH
