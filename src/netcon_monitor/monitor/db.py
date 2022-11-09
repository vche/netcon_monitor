import shelve
from datetime import datetime, timedelta
from ipaddress import IPv4Address

import attr

from netcon_monitor.monitor.input import MacAddress


@attr.s
class NetconMonDbItem:
    mac = attr.ib(default="0:0:0:0:0:0", type=MacAddress)
    ip = attr.ib(default="127.0.0.1", type=IPv4Address)
    hostname = attr.ib(default=None, type=str)
    manufacturer = attr.ib(default=None, type=str)
    last_seen = attr.ib(default=datetime.now(), type=datetime)
    alarm_timestamp = attr.ib(default=None, type=datetime)
    allowed = attr.ib(default=False, type=bool)

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


class NetconMonDb:
    DATABASE_FILE = "connections.db"
    ONLINE_JITTER_SECS = 60

    def __init__(self, config) -> None:
        self._config = config
        self._db_path=self._config["DATABASE_PATH"] + "/" + self.DATABASE_FILE
        self.store = shelve.open(self._db_path)
        self.online_ttl = timedelta(seconds=self._config["MONITOR_DELAY_SECS"] + self.ONLINE_JITTER_SECS)

    def close(self) -> None:
        self.store.close()

    def add(self, **kwargs) -> NetconMonDbItem:
        return self.add_item(NetconMonDbItem(**kwargs))

    def add_item(self, item: NetconMonDbItem) -> NetconMonDbItem:
        self.store[str(item.mac)] = item
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
