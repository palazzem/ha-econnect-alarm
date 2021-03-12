"""Constants for the E-connect Alarm integration."""
BASE_URL = "https://connect.elmospa.com"
CONF_DOMAIN = "domain"
CONF_AREAS_ARM_HOME = "areas_arm_home"
CONF_AREAS_ARM_NIGHT = "areas_arm_night"
DOMAIN = "econnect_alarm"
KEY_DEVICE = "device"
KEY_COORDINATOR = "coordinator"
# Fast scanning is fine because long-polling is used
# and lasts 15 seconds
SCAN_INTERVAL = 5
POLLING_TIMEOUT = 20
