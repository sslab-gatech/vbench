#!/bin/bash

PERF=/home/sanidhya/research/linux/tools/perf/perf

sudo $PERF record -g exim-mod/bin/exim -bdf -oX 2526 -C config
