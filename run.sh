#!/bin/bash -e

cd `dirname $0`

# 現在のバージョンがローカルバージョンと違う場合、setupする
touch .locel_version
local_version=`cat .locel_version`
current_version=`cat VERSION`
if [ "$local_version" != "$current_version" ]; then
  ./setup.sh true
fi

source ./venv/bin/activate

python3 ./launch.py

deactivate
