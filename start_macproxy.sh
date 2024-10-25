#!/usr/bin/env bash
set -e
#set -x # Uncomment to Debug

# verify packages installed
ERROR=0
if ! command -v python3 &> /dev/null ; then
	echo "python3 could not be found."
	echo "Run 'sudo apt install python3' to fix."
	ERROR=1
fi
if ! python3 -m venv --help &> /dev/null ; then
	echo "venv could not be found."
	echo "Run 'sudo apt install python3-venv' to fix."
	ERROR=1
fi
if [ $ERROR = 1 ] ; then
	echo
	echo "Fix errors and re-run ./start_macproxy.sh."
	exit 1
fi

# Test for two known broken venv states
if test -e venv; then
	GOOD_VENV=true
	if ! test -e venv/bin/activate; then
		GOOD_VENV=false
	else
		source venv/bin/activate
		pip3 list &> /dev/null
		test $? -eq 1 && GOOD_VENV=false
	fi
	if ! "$GOOD_VENV"; then
		echo "Deleting bad python venv"
		sudo rm -rf venv
	fi
fi

# Create the venv if it doesn't exist
cd "$(dirname "$0")"
if ! test -e venv; then
	echo "Creating python venv for Macproxy Plus..."
	python3 -m venv venv
	echo "Activating venv..."
	source venv/bin/activate
	echo "Installing base requirements.txt..."
	pip3 install wheel &> /dev/null
	pip3 install -r requirements.txt &> /dev/null
	git rev-parse HEAD > current
fi

source venv/bin/activate

# Gather all requirements from enabled extensions
ALL_REQUIREMENTS=""
for ext in $(python3 -c "import config; print(' '.join(config.ENABLED_EXTENSIONS))"); do
	if test -e "extensions/$ext/requirements.txt"; then
		ALL_REQUIREMENTS+=" -r extensions/$ext/requirements.txt"
	fi
done

# Install all requirements at once if there are any
if [ ! -z "$ALL_REQUIREMENTS" ]; then
	echo "Installing requirements for enabled extensions..."
	pip3 install $ALL_REQUIREMENTS -q --upgrade
else
	echo "No additional requirements for enabled extensions."
fi

# parse arguments
while [ "$1" != "" ]; do
	PARAM=$(echo "$1" | awk -F= '{print $1}')
	VALUE=$(echo "$1" | awk -F= '{print $2}')
	case $PARAM in
		-p | --port)
			PORT="--port $VALUE"
			;;
		*)
			echo "ERROR: unknown parameter \"$PARAM\""
			exit 1
			;;
	esac
	shift
done

echo "Starting Macproxy Plus..."
python3 proxy.py ${PORT}