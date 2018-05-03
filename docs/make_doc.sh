#!/bin/sh
set -o errexit

( cd ..; test -e genie_python || ln -s ./Lib/site-packages/genie_python genie_python )
mkdir ../smslib
mkdir ../smslib/sms
touch ../smslib/__init__.py
touch ../smslib/sms/__init__.py

env PYTHONPATH=.. make html

( cd ..; test -h genie_python  && rm -f genie_python )
rm -fr ../smslib

rm -fr /isis/www/doxygen/genie_python/sphinx
cp -r _build/html /isis/www/doxygen/genie_python/sphinx
