#!/bin/bash -e

cd `dirname $0`

source ./venv/bin/activate

python3 ./launch.py

deactivate
