# FROM python:3
FROM ubuntu:focal

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libssl-dev libffi-dev python3-dev cargo \
        python3-pip \
        && rm -rf /var/cache/apt /var/lib/apt/lists

ADD src/ /src
ADD setup.py /
ADD setup.cfg /
ADD etc/config/config.py /config/
ENV NETCONMON_CONFIG /config/config.py

RUN pip3 install virtualenv
RUN virtualenv /pyvenv

# ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN /pyvenv/bin/pip install -U pip

# Install dependencies:
WORKDIR /
RUN /pyvenv/bin/pip -v install -e .

# Run the application:
CMD ["/pyvenv/bin/netcon_monitor", "2>&1"]

VOLUME /config
EXPOSE 9334
