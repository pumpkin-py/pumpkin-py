#!/bin/bash

if [ -f "/pumpkin-py/pumpkin.py" ];
then
    echo "/pumpkin-py already contains the entry script."
else
    echo "Pulling https://github.com/pumpkin-py/pumpkin-py.git"
    git clone https://github.com/pumpkin-py/pumpkin-py.git /pumpkin-py || (echo "Couldn't clone pumpkin-py repository. Volume /pumpkin-py doesn't contain the core pumpkin-py repository." && exit 1)
fi

if [ -z "${BOT_TIMEZONE}" ]; then
    echo "BOT_TIMEZONE is not set, using UTC instead"
    ln -snf /usr/share/zoneinfo/Etc/UTC /etc/localtime && echo $BOT_TIMEZONE > /etc/timezone
else
    echo "BOT_TIMEZONE is set to $BOT_TIMEZONE"
    ln -snf /usr/share/zoneinfo/$BOT_TIMEZONE /etc/localtime && echo $BOT_TIMEZONE > /etc/timezone
fi

if [ -n "${BOT_EXTRA_PACKAGES}" ]; then
    echo "Installing extra packages via apt: $BOT_EXTRA_PACKAGES"
    apt-get -y --no-install-recommends install $BOT_EXTRA_PACKAGES
fi

mkdir -p /tempdir
find /pumpkin-py/modules/*/ -type f -name requirements.txt -exec grep -h "" {} \; | sort | uniq > /tempdir/requirements.txt

echo "Upgrading pip"
pip install -q --upgrade pip --root-user-action=ignore
echo "Installing default requirements"
python3 -m pip install -q -r /pumpkin-py/requirements.txt --user --no-warn-script-location --no-cache-dir --root-user-action=ignore
echo "Installing module requirements"
python3 -m pip install -q -r /tempdir/requirements.txt --user --no-warn-script-location --no-cache-dir --root-user-action=ignore

echo "Starting pumpkin-py"
cd /pumpkin-py && python3 pumpkin.py
