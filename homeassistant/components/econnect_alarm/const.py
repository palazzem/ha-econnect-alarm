"""Constants for the E-connect Alarm integration."""
BASE_URL = "https://connect.elmospa.com"
CONF_ALARM_CODE = "alarm_code"
CONF_DOMAIN = "domain"
DOMAIN = "econnect_alarm"
KEY_DEVICE = "device"
KEY_COORDINATOR = "coordinator"
# Fast scanning is fine because long-polling is used
# and lasts 15 seconds
SCAN_INTERVAL = 5
POLLING_TIMEOUT = 16
