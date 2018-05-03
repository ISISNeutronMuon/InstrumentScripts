#!/bin/sh
set -o errexit
env PYTHONPATH=.. make html
rm -fr /isis/www/doxygen/shared_instrument_scripts/sphinx
cp -r _build/html /isis/www/doxygen/shared_instrument_scripts/sphinx
