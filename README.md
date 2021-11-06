macproxy
========

A simple HTTP proxy script for putting early computers on the Web.

proxy.py runs a flask server that takes all requests and proxies them, using macify.py to strip tags that are incompatible with, or pulls in contents that aren't parsable by old browsers such as Netscape 4 or MacWeb.

start.sh will create and manage a venv Python environment before launching the proxy script.
