#!/bin/bash -ex

cd `dirname $0`

skip_key_wait=$1

git submodule update --init --recursive

python3.10 -m venv venv
source ./venv/bin/activate

pip3 install --upgrade -r requirements.txt

cd modules/pytube
pip3 install -e .
cd ../..

pip3 list

if [ "$skip_key_wait" != "true" ]; then
  read -p "All complate!!! plass any key..."
fi

deactivate
