import base64
import os
import re
import time
import urllib.parse
from copy import deepcopy
from importlib import metadata
from flask import Blueprint, Flask, current_app, render_template
from netcon_monitor.monitor.db import NetconMonDb, NetconMonDbItem

# from pyweblogalyzer.dataset.weblogdata import WebLogData

appblueprint = Blueprint("dashboard", __name__)


class NetconMonApp(Flask):

    def __init__(self, dataset, config_class, config_env: None):
        super().__init__(__name__)
        # self._dataset = dataset
        self._load_config(config_class, config_env)
        self.register_blueprint(appblueprint)

    def _load_config(self, config_class, config_env):
        self.config.from_object(config_class)
        if config_env and os.environ.get(config_env):
            self.config.from_envvar(config_env)        
        self.config['VERSION'] = metadata.version('netcon_monitor')

    def run(self, database: NetconMonDb):
        """Start the web app."""
        # Don't use the reloader as it restarts the app dynamically, creating a new collector
        self._db = database
        super().run(host=self.config["HOST"], port=self.config["PORT"], debug=self.config["DEBUG"], use_reloader=False)
        self.logger.info("Dashboard started, listening on port {self.config['PORT']}")

    def render_index(self):
        return render_template('index.html', config=self.config, db=self._db)

    def allow_device(self, mac_str: str, allow: bool) -> bool:
        """Set a device as allowed, reset alarm , and return the device status."""
        device = self._db.get(mac_str)
        device.allowed = allow
        if allow:
            device.set_alarm(False)
        self._db.add_item(device)
        return self._db.get(mac_str).allowed


@appblueprint.route("/", methods=["GET"])
def get_index():
    return current_app.render_index()


@appblueprint.route("/allow/<dev_key>", methods=["GET"])
def enable_device(dev_key):
    mac_str = ":".join([dev_key[i:i+2] for i in range(0, len(dev_key), 2)])
    status = current_app.allow_device(mac_str, True)
    return {'status': status}


@appblueprint.route("/disallow/<dev_key>", methods=["GET"])
def disable_device(dev_key):
    mac_str = ":".join([dev_key[i:i+2] for i in range(0, len(dev_key), 2)])
    status = current_app.allow_device(mac_str, False)
    return {'status': status}
