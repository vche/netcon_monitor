import logging
import signal
import sys
from netcon_monitor.dashboard.app import NetconMonApp
from netcon_monitor.monitor.db import NetconMonDb
from netcon_monitor.monitor.input import NetconMonIpCommandInput, NetconMonAsusCommandResolver
from netcon_monitor.monitor.monitor import NetconMonMonitor

# Next steps:
# create ui
# create dev config
# create docker


ENVVAR_CONFIG="NETCONMON_CONFIG"
log = logging.getLogger(__name__)


def setup_logging(logfile=None, loglevel=logging.INFO) -> None:
    logging.basicConfig(
        filename=logfile or None,
        level=loglevel,
        format="[%(levelname)-7s %(asctime)s %(name)s,%(filename)s:%(lineno)d] %(message)s",
    )


def main() -> None:
    """Main entry point."""
    dashboard = NetconMonApp(None, "netcon_monitor.config.Config", ENVVAR_CONFIG)
    setup_logging(logfile=dashboard.config["LOG_FILE"], loglevel=dashboard.config.get("LOG_LEVEL"))
    database = NetconMonDb(dashboard.config)
    monitor = NetconMonMonitor(NetconMonIpCommandInput, NetconMonAsusCommandResolver, dashboard.config, database)
    log.info(f"Started netcon_monitor {dashboard.config['VERSION']}")

    def signal_handler(sig, frame):
        monitor.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGILL, signal_handler)

    monitor.start()
    dashboard.run(database)

if __name__ == "__main__":
    main()
