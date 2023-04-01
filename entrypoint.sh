#!/bin/bash

if [ -f "/pumpkin-py/pumpkin.py" ];
then
    echo "/pumpkin-py directory exists."
else
    echo "pumpkin.py does not exist."
    echo "Pulling from https://github.com/pumpkin-py/pumpkin-py.git"
    git clone https://github.com/pumpkin-py/pumpkin-py.git /pumpkin-py || (echo "Couldn't clone pumpkin-py repository. Volume /pumpkin-py isn't empty and it doesn't contain pumpkin-py repository." && exit 1)
fi

if [ -z "${TZ}" ]; then
    echo "TZ is not set, using UTC instead"
    ln -snf /usr/share/zoneinfo/Etc/UTC /etc/localtime && echo $TZ > /etc/timezone
else
    echo "TZ is set to $TZ"
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
fi

if [ -n "${EXTRA_PKGS}" ]; then
    echo "Installing extra packages: $EXTRA_PKGS"
    apt-get -y --no-install-recommends install $EXTRA_PKGS
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
echo ""
python3 /pumpkin-py/pumpkin.py
