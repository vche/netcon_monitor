import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import telegram

from netcon_monitor.monitor.db import NetconMonDbItem


class NetconMonAlarmNotifier:
    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self.logger = logging.getLogger(__name__)

    def raise_alarm(self, item):
        pass


class NetconMonTelegramAlarmNotifier(NetconMonAlarmNotifier):
    def __init__(self, config: Dict[str, Any], loop=None) -> None:
        super().__init__(config)
        self.loop = loop or asyncio.new_event_loop()
        self._bot_key = self._config.get("TELEGRAM_BOT_KEY")
        self._chat_id = self._config.get("TELEGRAM_CHAT_ID")
        self._message_device = self._config.get("TELEGRAM_MESSAGE_DEVICE")
        self._message = self._config.get("TELEGRAM_MESSAGE")
        self._bot = telegram.Bot(token=self._bot_key)
        self.logger = logging.getLogger(__name__)
        self.loop.run_until_complete(self._bot.initialize())

    def raise_alarm(self, device_list):
        if not device_list:
            return

        content = ""
        for dev in device_list:
            content += self._message_device.format(dev.mac, dev.manufacturer, dev.ip, dev.hostname)

        self.logger.debug(f"Sending alert to {self._chat_id}: {self._message.format(len(device_list), content)}")
        self.loop.run_until_complete(
            self._bot.send_message(
                chat_id=self._chat_id,
                text=self._message.format(len(device_list), content),
                parse_mode="HTML",
            )
        )

    def close(self):
        self.loop.run_until_complete(self.bot.shutdown())
        self.loop.close()


class NetconMonIfttAlarmNotifier(NetconMonAlarmNotifier):
    pass


class NetconMonAlarm:
    def __init__(self, config):
        self._config = config
        self.logger = logging.getLogger(__name__)
        self._alarm_ttl = timedelta(seconds=self._config["ALARM_TTL_SECS"])
        self._notifiers = []
        if self._config.get("ENABLE_TELEGRAM"):
            self._notifiers.append(NetconMonTelegramAlarmNotifier(self._config))
        if self._config.get("ENABLE_IFTT"):
            self._notifiers.append(NetconMonIfttAlarmNotifier(self._config))
        self._pending_alarms = []

    def process_device(self, device: NetconMonDbItem):
        # If the device is in alarm but was not online for longer than the alarm ttl, clear it
        # print(f"{device.mac}: {datetime.now()}, {device.last_seen}, {datetime.now() - device.last_seen} > {self._alarm_ttl}")
        if device.in_alarm() and datetime.now() - device.last_seen > self._alarm_ttl:
            self.logger.info(f"Clearing alarm for device {device.mac}")
            device.set_alarm(in_alarm=False)

        # If the device is not allowed and not in alarm, raise alarm
        if not device.in_alarm() and not device.allowed:
            self._pending_alarms.append(device)
            device.set_alarm()

    def send_pending_alarms(self):
        for notifier in self._notifiers:
            notifier.raise_alarm(self._pending_alarms)
        self._pending_alarms = []
