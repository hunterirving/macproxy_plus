macproxy
========

A simple HTTP proxy script for putting a Mac Plus (and other early computers) on the Web.

proxy.py runs a flask server that takes all requests and proxies them, using macify.py to strip tags that are incompatible with MacWeb.

start.sh will create and manage a venv Python environment before launching the proxy script.
