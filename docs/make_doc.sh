#!/bin/sh
set -o errexit
env PYTHONPATH=.. make html
rm -fr /isis/www/doxygen/shared_scripting/sphinx
cp -r _build/html /isis/www/doxygen/shared_scripting/sphinx
