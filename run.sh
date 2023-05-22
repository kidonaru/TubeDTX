#!/bin/bash -e

cd `dirname $0`

./setup.sh true

source ./venv/bin/activate

python3 ./launch.py

deactivate
