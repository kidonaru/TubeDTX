#!/bin/bash -ex

cd `dirname $0`

git pull origin main

python3.10 -m venv venv
source ./venv/bin/activate

pip3 install --upgrade -r requirements-osx.txt

read -p "All complate!!! plass any key..."
