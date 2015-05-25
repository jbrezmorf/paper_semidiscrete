#!/bin/bash

rsync -ravz --update --exclude='*/core' jan_brezina@tarkil.cesnet.cz:/auto/praha1/jan_brezina/clanek/conv_tests/_JB_exp_sin/$1 .