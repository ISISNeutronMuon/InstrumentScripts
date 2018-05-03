#!/bin/sh
set -o errexit
env PYTHONPATH=.. make html
if [ ! -d /isis/www/doxygen/shared_instrument_scripts/ ]; then
  mkdir -p /isis/www/doxygen/shared_instrument_scripts/
fi
rm -fr /isis/www/doxygen/shared_instrument_scripts/sphinx
cp -r _build/html /isis/www/doxygen/shared_instrument_scripts/sphinx
