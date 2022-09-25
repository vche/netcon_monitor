FROM python:3
ADD src/ /src
ADD setup.py /
ADD setup.cfg /
ADD src/pyweblogalyzer/config.py /config/
ENV PYWEBLOGALYZER_CONFIG /config/config.py

RUN pip3 install virtualenv
RUN virtualenv /pyvenv

# Install dependencies:
WORKDIR /
RUN /pyvenv/bin/pip -v install -e .

# Run the application:
CMD ["/pyvenv/bin/pyweblogalyzer", "2>&1"]

VOLUME /config
VOLUME /logs
VOLUME /geoipdb
EXPOSE 9333
