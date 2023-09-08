"""Constants for the E-connect Alarm integration."""
from elmo import systems as s

SUPPORTED_SYSTEMS = {
    s.ELMO_E_CONNECT: "Elmo e-Connect",
    s.IESS_METRONET: "IESS Metronet",
}
CONF_DOMAIN = "domain"
CONF_SYSTEM_URL = "system_base_url"
CONF_AREAS_ARM_HOME = "areas_arm_home"
CONF_AREAS_ARM_NIGHT = "areas_arm_night"
CONF_AREAS_ARM_VACATION = "areas_arm_vacation"
DOMAIN = "econnect_alarm"
KEY_DEVICE = "device"
KEY_COORDINATOR = "coordinator"
KEY_UNSUBSCRIBER = "options_unsubscriber"
# Fast scanning is fine because long-polling is used
# and lasts 15 seconds
SCAN_INTERVAL = 5
POLLING_TIMEOUT = 20
