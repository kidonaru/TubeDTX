#!/bin/bash -ex

cd `dirname $0`

skip_key_wait=$1

python3.10 -m venv venv
source ./venv/bin/activate

pip3 install --upgrade -r requirements.txt

if [ ! -d "pytube" ]; then
  git clone https://github.com/kidonaru/pytube.git
fi

cd pytube
git checkout v15.0.0-fix
pip3 install -e .
cd ..

pip3 list

if [ "$skip_key_wait" != "true" ]; then
  read -p "All complate!!! plass any key..."
fi

deactivate
