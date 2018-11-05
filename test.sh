#!/usr/bin/env sh

set -e

flake8 --exclude technique/sans/test general instrument technique
# pylint --ignore test general instrument technique
# # coverage run --source scans -m doctest doc/source/tutorial.rst doc/source/instrument.rst
# coverage run --source=general,instrument,technique -m unittest discover
coverage run --source=general -m unittest discover
coverage html
cd doc
make html
