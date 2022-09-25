import logging


class Config(object):
    """This is the basic configuration class for Netcon Monitor."""

    #This will be populated after load from the setup.cfg value, any value specified here will be overwritten.
    VERSION=""

    ###################################################################################################
    # General settings
    ###################################################################################################
    LOG_FILE = None  # Leave to None to log in stderr and see in docker logs
    LOG_LEVEL = logging.DEBUG

    ###################################################################################################
    # Network monitor settings
    ###################################################################################################

    # Period in second to read new connection data
    MONITOR_DELAY_SECS = 600

    # Hostname refresh period, as multiple of MONITOR_DELAY_SECS.
    # e.g. MONITOR_HOSTS_PERIODS=6 means hostnames are refreshed every 6*MONITOR_DELAY_SECS secodes
    MONITOR_HOSTS_PERIODS = 6

    # List networks to monitor (leave empty to monitor all connections on all networks)
    MONITORED_NETWORKS=["192.168.0.0/24", "192.168.13.0/24"]

    # To get connection from a remote host (e.g. router), REMOTE_HOSTNAME must be specified, as well as
    # credentials (either, REMOTE_PASS, REMOTE_PRIVATE_KEY, or REMOTE_PRIVATE_KEY_FILE, or have them
    # in the user's .ssh folder
    REMOTE_HOSTNAME = "192.168.0.1" # Remote host to connect, IP or hostname. Default to empty (local monitoring)
    REMOTE_PORT = 22                # Port to use. Defaults to 22
    REMOTE_USER = "viv"             # User to use for connection. Defaults to root
    REMOTE_PASS = None              # Use password to connect
    REMOTE_PRIVATE_KEY = None       # Use private key to connect
    REMOTE_PRIVATE_KEY_FILE = None  # Use the private key in the specified file to connect

    # Path where to store the database
    DATABASE_PATH = "/Users/viv/dev/netcon_monitor/etc/dev/config"

    ###################################################################################################
    # Network alarm settings
    ###################################################################################################
    ALARM_TTL_SECS = 1800

    # To enable telegram notifications, both keys must be filled
    ENABLE_TELEGRAM = True
    TELEGRAM_BOT_KEY="1110478838:AAGZVZaDmjUPffFTIxpgLVIKI5r7yg5h_8g"
    TELEGRAM_CHAT_ID="-489291168"
    TELEGRAM_MESSAGE="<b>{} new connections to Dwarfnet</b>:\n\n{}"
    TELEGRAM_MESSAGE_DEVICE="- {}, {}, {}, {}\n"

    ###################################################################################################
    # Dashboard server settings
    ###################################################################################################

    # Server config
    HOST = "0.0.0.0"  # use 0.0.0.0 to bind to all interfaces
    PORT = 9333  # ports < 1024 need root
    DEBUG = True  # if True, enable reloader and debugger

    # Preset refresh times in seconds
    REFRESH_TIMES = [30, 60, 300, 600]
