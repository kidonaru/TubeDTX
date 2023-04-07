#!/bin/bash -e

cd `dirname $0`

source ./venv/bin/activate

python3 -m unittest discover -s ./tests

deactivate
