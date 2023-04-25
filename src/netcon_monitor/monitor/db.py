import shelve
import json
from datetime import datetime, timedelta
from ipaddress import IPv4Address
import logging

import attr

from netcon_monitor.monitor.input import MacAddress


@attr.s
class NetconMonDbItem():
    # Default values
    DEFAULT_MAC="0:0:0:0:0:0"
    DEFAULT_IP="127.0.0.1"

    # Properties
    mac = attr.ib(default=MacAddress(DEFAULT_MAC), type=MacAddress)
    ip = attr.ib(default=DEFAULT_IP, type=IPv4Address)
    hostname = attr.ib(default=None, type=str)
    manufacturer = attr.ib(default=None, type=str)
    last_seen = attr.ib(default=datetime.now(), type=datetime)
    alarm_timestamp = attr.ib(default=None, type=datetime)
    allowed = attr.ib(default=False, type=bool)

    # Dict representation keys
    DICT_KEY_MAC = "mac"
    DICT_KEY_IP = "ip"
    DICT_KEY_HOSTNAME = "hostname"
    DICT_KEY_MANUFACTURER = "manufacturer"
    DICT_KEY_LASTSEEN = "last_seen"
    DICT_KEY_ALARMTS = "alarm_timestamp"
    DICT_KEY_ALLOWED = "allowed"

    @classmethod
    def from_dict(cls, raw_dict):
        return cls(
            mac=MacAddress(raw_dict.get(cls.DICT_KEY_MAC, cls.DEFAULT_MAC)),
            ip=raw_dict.get(cls.DICT_KEY_IP, cls.DEFAULT_IP),
            hostname=raw_dict.get(cls.DICT_KEY_HOSTNAME),
            manufacturer=raw_dict.get(cls.DICT_KEY_MANUFACTURER),
            last_seen=datetime.fromisoformat(raw_dict.get(cls.DICT_KEY_LASTSEEN)),
            alarm_timestamp=datetime.fromisoformat(raw_dict.get(cls.DICT_KEY_ALARMTS)),
            allowed=raw_dict.get(cls.DICT_KEY_ALLOWED),
        )

    def to_dict(self) -> str:
        return {
            self.DICT_KEY_MAC: str(self.mac),
            self.DICT_KEY_IP: str(self.ip),
            self.DICT_KEY_HOSTNAME: self.hostname,
            self.DICT_KEY_MANUFACTURER: self.manufacturer,
            self.DICT_KEY_LASTSEEN: str(self.last_seen),
            self.DICT_KEY_ALARMTS: str(self.alarm_timestamp),
            self.DICT_KEY_ALLOWED: self.allowed,
        }

    def __attrs_post_init__(self):
        if not self.manufacturer:
            self.manufacturer = self.mac.get_manufacturer()

    def refresh(self) -> None:
        """Refresh the last seen time, and the alarm if in alarm."""
        self.last_seen = datetime.now()
        if not self.manufacturer:
            # To avoid throttling from the mac vendors api, check at refresh if we need to try to re update
            self.manufacturer = self.mac.get_manufacturer()

    def set_alarm(self, in_alarm: bool = True) -> None:
        """Set or clear the alarm."""
        if in_alarm:
            if not self.alarm_timestamp:
                self.alarm_timestamp = datetime.now()
        else:
            self.alarm_timestamp = None

    def in_alarm(self) -> bool:
        return True if self.alarm_timestamp else False

    def is_online(self, ttl: timedelta) -> bool:
        return (datetime.now() - self.last_seen) < ttl


class NetconMonDbItemSerializer(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, NetconMonDbItem):
            return o.to_dict()
        return json.JSONEncoder.default(self, o)


class NetconMonDb:
    DATABASE_FILE = "connections.db"
    ONLINE_JITTER_SECS = 60

    def __init__(self, config) -> None:
        self.store = None
        self._config = config
        self._db_path=self._config["DATABASE_PATH"] + "/" + self.DATABASE_FILE
        self.online_ttl = timedelta(seconds=self._config["MONITOR_DELAY_SECS"] + self.ONLINE_JITTER_SECS)
        self.logger = logging.getLogger(__name__)
        self.load()
        self.logger.info(f"Loaded datastore {self._db_path}, {len(self.store)} elements")

    def load(self):
        self.store = {}
        # self.store = shelve.open(self._db_path, writeback=True)
        try:
            with open(self._db_path, "r") as f:
                raw_store = json.load(f)
                self.store = { key: NetconMonDbItem.from_dict(raw_store[key]) for key in raw_store }
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self.logger.info("Creating a new database file")

    def save(self):
        # self.store.sync()
        with open(self._db_path, "w") as f:
            json.dump(self.store, f, cls=NetconMonDbItemSerializer)

    def close(self) -> None:
        self.save()

    def add(self, **kwargs) -> NetconMonDbItem:
        return self.add_item(NetconMonDbItem(**kwargs))

    def add_item(self, item: NetconMonDbItem) -> NetconMonDbItem:
        self.store[str(item.mac)] = item
        self.save()
        return item

    def has(self, item_key: str) -> bool:
        return item_key in self.store

    def get(self, item_key: str) -> NetconMonDbItem:
        return self.store[item_key] if item_key in self.store else None

    def update(self, item: NetconMonDbItem) -> None:
        item.refresh()
        self.add_item(item)

    def dump(self):
        date_format = "%d/%m/%Y %H:%M:%S"
        print(f"{len(self.store)} elements in datastore")
        print(
            "#   Enabled MAC address       IP Address      Last seen           Hostname                       Manufacturer                        Alarm date"
        )
        for i, elt in enumerate(self.store):
            print(
                "{:<3} {:<7} {:<17} {:<15} {:<19} {:<30} {:<35} {:<19}".format(
                    i,
                    "YES" if self.store[elt].allowed else "NO",
                    str(self.store[elt].mac),
                    str(self.store[elt].ip),
                    self.store[elt].last_seen.strftime("%d/%m/%Y %H:%M:%S"),
                    str(self.store[elt].hostname),
                    str(self.store[elt].manufacturer),
                    self.store[elt].alarm_timestamp.strftime(date_format) if self.store[elt].alarm_timestamp else "-",
                )
            )
