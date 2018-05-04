#!/bin/sh
set -o errexit
cd ..
sphinx-autogen -o source/ docs/shared_instrument_scripts.rst
cd ./docs
ls -R .
env PYTHONPATH=.. make html
ls -R _build/html
rm -fr /isis/www/doxygen/shared_instrument_scripts/sphinx
cp -r _build/html /isis/www/doxygen/shared_instrument_scripts/sphinx
