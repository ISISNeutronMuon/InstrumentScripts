#!/bin/sh
set -o errexit
sphinx-apidoc -d 5 -l -T -a -o source/ ../
env PYTHONPATH=.. make html
ls -R _build/html
rm -fr /isis/www/doxygen/shared_instrument_scripts/sphinx
cp -r _build/html /isis/www/doxygen/shared_instrument_scripts/sphinx
