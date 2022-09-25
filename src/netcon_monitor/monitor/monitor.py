import logging
import time
from threading import Thread
from netcon_monitor.monitor.db import NetconMonDb, NetconMonDbItem
from netcon_monitor.monitor.alarm import NetconMonAlarm


class NetconMonMonitor(Thread):
    def __init__(self, input_class: str, resolver_class: str, config, database: NetconMonDb = None):
        super().__init__(name=__name__, daemon=True)
        self._config = config
        self._fetcher = input_class(config)
        self._resolver = resolver_class(config)
        self._alarm = NetconMonAlarm(config)
        self._period = self._config["MONITOR_DELAY_SECS"]
        self.logger = logging.getLogger(__name__)
        self.db = database or NetconMonDb(self._config)

    def run(self):
        """Run the thread periodically polling log files."""
        loops = 0
        self._running = True

        if self.logger.isEnabledFor(logging.DEBUG):
            self.db.dump()

        while self._running:
            devs = self._fetcher.get_monitored_devices()
            hosts = self._resolver.get_hostname_mapping() if loops % self._config["MONITOR_HOSTS_PERIODS"] == 0 else {}
            self.logger.info(f"{len(devs)} devices connected")
            for dev_ip, dev_mac in devs:
                mac_str = str(dev_mac)
                device = self.db.get(mac_str)
                if device:
                    device.ip = dev_ip
                    if mac_str in hosts:
                        device.hostname = hosts[mac_str]
                else:
                    self.logger.info(f"New device detected {dev_mac}")
                    device = NetconMonDbItem(ip=dev_ip, mac=dev_mac, hostname=hosts.get(mac_str))
                self._alarm.process_device(device)
                self.db.update(device)

            self._alarm.send_pending_alarms()
            time.sleep(self._period)
            loops +=1

    def stop(self):
        self._running = False
        self.db.close()
