#!/usr/bin/env sh

set -e

flake8 --exclude technique/sans/test general instrument technique
pylint --ignore test general instrument technique
coverage run --source=general,instrument,technique -m unittest discover
coverage html
cd doc
make html
make latexpdf
