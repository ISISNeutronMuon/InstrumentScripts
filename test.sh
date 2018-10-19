#!/usr/bin/env sh

set -e

flake8 general instrument technique
pylint general instrument technique
# # coverage run --source scans -m doctest doc/source/tutorial.rst doc/source/instrument.rst
coverage run --source=general,instrument,technique -m unittest discover
coverage html
cd doc
make html
