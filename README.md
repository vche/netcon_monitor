## Netcon Monitor

netcon_mon monitors new connections to the specify networks, and send notifications for unkonwn devices.
Start with `./netcon_monitor` or start the docker image and connect to http://<host>:9334/

Specify the configuration file to use with environment variable `NETCONMON_CONFIG`.
e.g. NETCONMON_CONFIG=/config/config.py

For docker, the config file path is `/config/config.py` so map the `/config` volume or file directly

The config.py file (example in etc/config.py with default values in src/config.py) allows configuring the tool:
- Dashboard (web UI)
- Notification (currently only support telegram alerts)
- Networks to monitor
- Target to connect to (to get the connected hosts, typically your router)
- Connected devices detection. Defaults to NetconMonIpCommandInput to use `ip neigh` but NetconMonArpCommandInput is also available to use `arp` detection, and other methods can be implemented by extending NetconMonInput
- Devices hostnames detection. Defaults to NetconMonAsusCommandResolver to use asus router specific methods but other methods can be implemented by extending NetconMonResolver

### Development

#### Installing sources projects

Get the project and create the virtual env:
```sh
git clone https://github.com/vche/netcon_monitor.git
virtualenv pyvenv
. pyvenv/bin/activate
pip install -e .
```

Note: Entry points will be installed in pyvenv/bin, libs with pyvenv libs

#### Run tests

```sh
pip install tox
tox
```

#### Generate documentation:

```sh
pip install sphinx sphinx_rtd_theme m2r
./setup.py doc
```

In case new classes/modules are added, update the autodoc list:
```sh
rm  docs/sphinx_conf/source/*
sphinx-apidoc -f -o docs/sphinx_conf/source/ src/netcon_monitor --separate
```
