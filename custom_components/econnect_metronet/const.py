"""Constants for the E-connect Alarm integration."""
from elmo import systems as s

SUPPORTED_SYSTEMS = {
    s.ELMO_E_CONNECT: "Elmo e-Connect",
    s.IESS_METRONET: "IESS Metronet",
}
CONF_DOMAIN = "domain"
CONF_SYSTEM_URL = "system_base_url"
CONF_SYSTEM_NAME = "system_name"
CONF_AREAS_ARM_HOME = "areas_arm_home"
CONF_AREAS_ARM_NIGHT = "areas_arm_night"
CONF_AREAS_ARM_VACATION = "areas_arm_vacation"
CONF_SCAN_INTERVAL = "scan_interval"
DOMAIN = "econnect_metronet"
KEY_DEVICE = "device"
KEY_COORDINATOR = "coordinator"
KEY_UNSUBSCRIBER = "options_unsubscriber"
# Defines the default scan interval in seconds.
# Fast scanning is required for real-time updates of the alarm state.
SCAN_INTERVAL_DEFAULT = 5
POLLING_TIMEOUT = 20

# Experimental Settings
CONF_EXPERIMENTAL = "experimental"
CONF_FORCE_UPDATE = "force_update"
