#!/usr/bin/env sh

set -e

coverage run --source scans -m doctest doc/source/tutorial.rst doc/source/instrument.rst
PERCENT=`coverage report | awk '/TOTAL/ {print $4}'`
# coverage report | sed '/TOTAL/'
sed -r "s/-[0-9]+%25-/-${PERCENT}25-/" readme.md > readme.md.tmp
mv readme.md.tmp readme.md
coverage html
pylint scans
flake8 scans
