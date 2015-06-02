#!/bin/bash

subdir=`pwd`
subdir_base=${subdir##*/}
time rsync -ravz --update --exclude='*/core' jan_brezina@tarkil.cesnet.cz:/auto/praha1/jan_brezina/clanek/conv_tests/${subdir_base}/$1 .
