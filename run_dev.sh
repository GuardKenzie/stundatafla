#! /bin/sh
#
# run_dev.sh
# Copyright (C) 2021 kenzie <kenzie@willowroot>
#
# Distributed under terms of the MIT license.
#


export FLASK_APP="index" FLASK_ENV="development"
flask run
