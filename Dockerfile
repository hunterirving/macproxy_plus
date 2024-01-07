FROM python:alpine3.18

# use PROXY_ARGS to pass flags to the proxy via command line
# see the README for supported flags.
ENV PROXY_ARGS ""

# install the proxy code in the container
WORKDIR /macproxy
COPY . .
RUN pip3 install -r requirements.txt

# command to execute when container runs
CMD python3 proxy.py ${PROXY_ARGS}