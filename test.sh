#!/usr/bin/env sh

set -e

flake8 --exclude technique/sans/test general instrument technique
pylint --ignore test general instrument technique
coverage run --source=general,instrument,technique -m unittest discover
coverage html
python doc/call.py > call.dot
python doc/functions.py general instrument
python doc/functions.py technique instrument
dot -Tpng -O *.dot
mv general_instrument.dot.png doc/source/
mv technique_instrument.dot.png doc/source/
mv call.dot.png doc/source/
cd doc
make html
make latexpdf
