macproxy
========

A simple HTTP proxy script for putting early computers on the Web. Despite its name, there is nothing Mac specific about this proxy. It was originally designed with compatibility with the MacWeb web browser in mind, but has been tested on a variety of vintage web browsers since.

The proxy.py script runs a Flask server that takes all requests and proxies them, using html_utils.py to strip tags that are incompatible with, or pulls in contents that aren't parsable by old browsers such as Netscape 4 or MacWeb.

The proxy server listens to port 5000 by default, but the port number can be changed using a command line parameter.

Requirements
============
Python3 for running the script, venv if you want to use the virtual environment, or pip if you want to install libraries manually.

```
$ sudo apt install python3 python3-venv python3-pip
```

Usage
=====
The start.sh shell script will create and manage a venv Python environment, and if successful launch the proxy script.

```
$ ./start.sh
```

Launch with a specific port number (defaults to port 5000):

```
$ ./start.sh --port=5001
```

You may also start the Python script by itself, using system Python.

```
$ pip3 install -r requirements.txt
$ python3 proxy.py
```

Launch with a specific port number:

```
$ python3 proxy.py 5001
```

systemd service
===============
This repo comes with a systemd service configuration, the preferred way to manage daemons on Debian based Linux flavors.
Edit the macproxy.service file and point the ExecStart= parameter to the location of the start.sh file, e.g. on a Raspberry Pi:

```
ExecStart=/home/pi/macproxy/start.sh
```

Then copy the service file to /etc/systemd/system and enable the service:

```
$ sudo cp macproxy.service /etc/systemd/system/
$ sudo systemctl enable macproxy
$ sudo systemctl daemon-reload
$ sudo systemctl start macproxy
```
