import json
import logging
import subprocess
from ipaddress import IPv4Address, ip_address, ip_network
from typing import Any, Dict, List, Tuple

import requests
from paramiko import AutoAddPolicy, SSHClient


class MacAddress:
    def __init__(self, mac_str: str) -> None:
        self._bytes = mac_str.split(":")
        self._bytes = [int(byte, 16) for byte in self._bytes]
        if len(self._bytes) != 6:
            raise ValueError(f"Invalid MAC address {mac_str}")

    def __str__(self) -> str:
        return ":".join([f"{byte:0>2X}" for byte in self._bytes])

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    def get_manufacturer(self):
        url = "https://api.macvendors.com/"
        response = requests.get(url + self.__str__())
        if response.status_code != 200:
            return None
        return response.content.decode()


class NetconMonError(Exception):
    pass


class NetconMonInput:
    def __init__(self, config: Dict[str, Any]) -> None:
        super(NetconMonInput, self).__init__(config)
        self._config = config
        self.logger = logging.getLogger(__name__)
        self._monitored_networks = [ip_network(local_net) for local_net in self._config["MONITORED_NETWORKS"]]

    def is_monitored(self, device: Tuple[IPv4Address, MacAddress]) -> bool:
        dev_ip, _ = device
        if not self._monitored_networks:
            return True
        for monitored_net in self._monitored_networks:
            if dev_ip in monitored_net:
                return True
        return False

    def get_monitored_devices(self) -> List[Tuple[IPv4Address, MacAddress]]:
        return [device for device in self.get_connected_devices() if self.is_monitored(device)]

    def get_connected_devices(self) -> List[Tuple[IPv4Address, MacAddress]]:
        raise NotImplementedError


class NetconMonResolver:
    def __init__(self, config: Dict[str, Any]) -> None:
        super(NetconMonResolver, self).__init__(config)
        self._config = config
        self.logger = logging.getLogger(__name__)

    def get_hostname_mapping(self) -> Dict[MacAddress, str]:
        raise NotImplementedError


class NetconMonCommand:
    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self.logger = logging.getLogger(__name__)
        self._ssh_client = self._init_remote_client()

    def _init_remote_client(self) -> SSHClient:
        ssh_client = None
        if self._config["REMOTE_HOSTNAME"]:
            ssh_client = SSHClient()
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            ssh_client.load_system_host_keys()
        return ssh_client

    def connect(self) -> None:
        try:
            self._ssh_client.connect(
                hostname=self._config["REMOTE_HOSTNAME"],
                port=self._config["REMOTE_PORT"],
                username=self._config["REMOTE_USER"],
                password=self._config["REMOTE_PASS"],
                pkey=self._config["REMOTE_PRIVATE_KEY"],
                key_filename=self._config["REMOTE_PRIVATE_KEY_FILE"],
            )
        except TimeoutError as e:
            raise NetconMonError


    def disconnect(self) -> None:
        self._ssh_client.close()

    def run_command(self, command: str, autconnect=True) -> Tuple[str, str]:
        if self._ssh_client:
            if autconnect:
                self.connect()
            _, stdout, stderr = self._ssh_client.exec_command(" ".join(command))
            command_output_stdout = stdout.read().decode()
            command_output_stderr = stderr.read().decode()
            if autconnect:
                self.disconnect()
            return command_output_stdout, command_output_stderr
        else:
            command_output = subprocess.run(command, capture_output=True)
            return command_output.stdout.decode(), command_output.stderr.decode()


class NetconMonArpCommandInput(NetconMonInput, NetconMonCommand):
    SHELL_COMMAND = ["arp", "-a"]

    def __init__(self, config: Dict[str, Any]):
        NetconMonCommand.__init__(self, config)
        NetconMonInput.__init__(self, config)

    def get_connected_devices(self) -> List[Tuple[IPv4Address, MacAddress]]:
        devices = []
        try:
            command_stdout, _ = self.run_command(self.SHELL_COMMAND)

            # Parse results
            for line in command_stdout.splitlines():
                try:
                    tokens = line.split(" ")
                    ip = ip_address(tokens[1].replace("(", "").replace(")", ""))
                    mac = MacAddress(tokens[3])
                    devices.append((ip, mac))
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Invalid output or ip, skipping line {line}: {e}")
        except NetconMonError as e:
            self.logger.error(f"Error executing commant: {e}")

        return devices


class NetconMonIpCommandInput(NetconMonInput, NetconMonCommand):
    SHELL_COMMAND = ["ip", "neigh"]
    EXCLUDE_STATES = ["FAIL", "INCOMPLETE"]

    def __init__(self, config: Dict[str, Any]):
        NetconMonCommand.__init__(self, config)
        NetconMonInput.__init__(self, config)

    def get_connected_devices(self) -> List[Tuple[IPv4Address, MacAddress]]:
        devices = []
        try:
            command_stdout, _ = self.run_command(self.SHELL_COMMAND)

            # Parse results
            for line in command_stdout.splitlines():
                try:
                    tokens = line.split(" ")
                    ip = ip_address(tokens[0])
                    mac = MacAddress(tokens[4])
                    if tokens[5].upper() not in self.EXCLUDE_STATES:
                        devices.append((ip, mac))
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Invalid output or ip, skipping line {line}: {e}")
        except NetconMonError as e:
            self.logger.error(f"Error executing commant: {e}")

        return devices


class NetconMonAsusCommandResolver(NetconMonResolver, NetconMonCommand):
    SHELL_COMMAND_DNS_CFG = ["grep", '"dhcp-host"', "/etc/dnsmasq.conf"]
    SHELL_COMMAND_CLI_CFG = ["cat", "/jffs/nvram/custom_clientlist"]
    SHELL_COMMAND_NMP = ["cat", "/jffs/nmp_cl_json.js"]

    def __init__(self, config: Dict[str, Any]):
        NetconMonCommand.__init__(self, config)
        NetconMonResolver.__init__(self, config)

    def get_hostname_mapping(self) -> Dict[MacAddress, str]:
        try:
            self.connect()
            mapping = {}

            # Get asus resolved config
            command_stdout, _ = self.run_command(self.SHELL_COMMAND_NMP, autconnect=False)
            payload = json.loads(command_stdout)
            for mac in payload:
                if payload[mac]["name"]:
                    mapping[mac] = payload[mac]["name"]

            # Get dns static host config
            command_stdout, _ = self.run_command(self.SHELL_COMMAND_DNS_CFG, autconnect=False)
            for line in command_stdout.splitlines():
                tokens = line.split(",")
                mapping[tokens[0].replace("dhcp-host=", "")] = tokens[2]

            # Get UI static host config
            command_stdout, _ = self.run_command(self.SHELL_COMMAND_CLI_CFG, autconnect=False)
            for dev in command_stdout.split(">>"):
                tokens = dev.replace("<", "").split(">")
                entry = list(filter(None, tokens))
                if entry:
                    mapping[entry[1]] = entry[0]

            if self.logger.isEnabledFor(logging.DEBUG):
                for dev in mapping:
                    print(f"{dev}: {mapping[dev]}")
        except NetconMonError as e:
            self.logger.error(f"Error retrieving hostnames: {e}")

        self.disconnect()
        return mapping
