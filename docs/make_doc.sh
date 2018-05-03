#!/bin/sh
set -o errexit
env PYTHONPATH=.. make html
if [ ! -d /isis/www/doxygen/shared_scripting/ ]; then
  mkdir -p /isis/www/doxygen/shared_scripting/
fi
rm -fr /isis/www/doxygen/shared_scripting/sphinx
cp -r _build/html /isis/www/doxygen/shared_scripting/sphinx
