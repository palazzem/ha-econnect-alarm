"""
Centralizes predefined responses intended for integration testing, especially when used with the `server` fixture.
For standard tests, responses should be encapsulated within the test itself. This module should be referenced
primarily when updating the responses for the integration test client, ensuring a consistent test environment.

Key Benefits:
    - Central repository of standardized test responses.
    - Promotes consistent and maintainable testing practices.

Usage:
    1. Import the required response constant from this module:
       from tests.fixtures.responses import SECTORS

    2. Incorporate the imported response in your test logic:
       def test_client_get_sectors_status(server):
           server.add(responses.POST, "https://example.com/api/areas", body=SECTORS, status=200)
           # Continue with the test...
"""

LOGIN = """
    {
        "SessionId": "00000000-0000-0000-0000-000000000000",
        "Username": "test",
        "Domain": "domain",
        "Language": "en",
        "IsActivated": true,
        "IsConnected": true,
        "IsLoggedIn": false,
        "IsLoginInProgress": false,
        "CanElevate": true,
        "AccountId": 100,
        "IsManaged": false,
        "Redirect": false,
        "IsElevation": false
    }
"""
UPDATES = """
    {
        "ConnectionStatus": false,
        "CanElevate": false,
        "LoggedIn": false,
        "LoginInProgress": false,
        "Areas": true,
        "Events": false,
        "Inputs": true,
        "Outputs": false,
        "Anomalies": false,
        "ReadStringsInProgress": false,
        "ReadStringPercentage": 0,
        "Strings": 0,
        "ManagedAccounts": false,
        "Temperature": false,
        "StatusAdv": false,
        "Images": false,
        "AdditionalInfoSupported": true,
        "HasChanges": true
    }
"""
SYNC_LOGIN = """[
    {
        "Poller": {"Poller": 1, "Panel": 1},
        "CommandId": 5,
        "Successful": true
    }
]"""
SYNC_LOGOUT = """[
    {
        "Poller": {"Poller": 1, "Panel": 1},
        "CommandId": 5,
        "Successful": true
    }
]"""
SYNC_SEND_COMMAND = """[
    {
        "Poller": {"Poller": 1, "Panel": 1},
        "CommandId": 5,
        "Successful": true
    }
]"""
STRINGS = """[
    {
        "AccountId": 1,
        "Class": 9,
        "Index": 0,
        "Description": "S1 Living Room",
        "Created": "/Date(1546004120767+0100)/",
        "Version": "AAAAAAAAgPc="
    },
    {
        "AccountId": 1,
        "Class": 9,
        "Index": 1,
        "Description": "S2 Bedroom",
        "Created": "/Date(1546004120770+0100)/",
        "Version": "AAAAAAAAgPg="
    },
    {
        "AccountId": 1,
        "Class": 9,
        "Index": 2,
        "Description": "S3 Outdoor",
        "Created": "/Date(1546004147490+0100)/",
        "Version": "AAAAAAAAgRs="
    },
    {
        "AccountId": 1,
        "Class": 9,
        "Index": 3,
        "Description": "S4 Garage",
        "Created": "/Date(1546004147491+0100)/",
        "Version": "AAAAAAAAgRt="
    },
    {
        "AccountId": 1,
        "Class": 10,
        "Index": 0,
        "Description": "Entryway Sensor",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    },
    {
        "AccountId": 1,
        "Class": 10,
        "Index": 1,
        "Description": "Outdoor Sensor 1",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    },
    {
        "AccountId": 1,
        "Class": 10,
        "Index": 2,
        "Description": "Outdoor Sensor 2",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    },
    {
        "AccountId": 1,
        "Class": 10,
        "Index": 3,
        "Description": "Outdoor Sensor 3",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    },
    {
        "AccountId": 1,
        "Class": 12,
        "Index": 0,
        "Description": "Output 1",
        "Created": "/Date(1699548985673+0100)/",
        "Version": "AAAAAAAceCo="
    },
    {
        "AccountId": 1,
        "Class": 12,
        "Index": 1,
        "Description": "Output 2",
        "Created": "/Date(1699548985673+0100)/",
        "Version": "AAAAAAAceCs="
    },
    {
        "AccountId": 1,
        "Class": 12,
        "Index": 2,
        "Description": "Output 3",
        "Created": "/Date(1699548985673+0100)/",
        "Version": "AAAAAAAceCw="
    },
    {
        "AccountId": 1,
        "Class": 12,
        "Index": 3,
        "Description": "Output 4",
        "Created": "/Date(1699548985673+0100)/",
        "Version": "AAAAAAAceC0="
    }
]"""
AREAS = """[
   {
       "Active": true,
       "ActivePartial": false,
       "Max": false,
       "Activable": true,
       "ActivablePartial": false,
       "InUse": true,
       "Id": 1,
       "Index": 0,
       "Element": 1,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": true,
       "ActivePartial": false,
       "Max": false,
       "Activable": true,
       "ActivablePartial": false,
       "InUse": true,
       "Id": 2,
       "Index": 1,
       "Element": 2,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": false,
       "ActivePartial": false,
       "Max": false,
       "Activable": false,
       "ActivablePartial": false,
       "InUse": true,
       "Id": 3,
       "Index": 2,
       "Element": 3,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": false,
       "ActivePartial": false,
       "Max": false,
       "Activable": true,
       "ActivablePartial": false,
       "InUse": false,
       "Id": 4,
       "Index": 3,
       "Element": 5,
       "CommandId": 0,
       "InProgress": false
   }
]"""
INPUTS = """[
   {
       "Alarm": true,
       "MemoryAlarm": false,
       "Excluded": false,
       "InUse": true,
       "IsVideo": false,
       "Id": 1,
       "Index": 0,
       "Element": 1,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Alarm": true,
       "MemoryAlarm": false,
       "Excluded": false,
       "InUse": true,
       "IsVideo": false,
       "Id": 2,
       "Index": 1,
       "Element": 2,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Alarm": false,
       "MemoryAlarm": false,
       "Excluded": true,
       "InUse": true,
       "IsVideo": false,
       "Id": 3,
       "Index": 2,
       "Element": 3,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Alarm": false,
       "MemoryAlarm": false,
       "Excluded": false,
       "InUse": false,
       "IsVideo": false,
       "Id": 42,
       "Index": 3,
       "Element": 4,
       "CommandId": 0,
       "InProgress": false
   }
]"""
OUTPUTS = """[
   {
       "Active": true,
       "InUse": true,
       "DoNotRequireAuthentication": true,
       "ControlDeniedToUsers": false,
       "Id": 1,
       "Index": 0,
       "Element": 1,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": true,
       "InUse": true,
       "DoNotRequireAuthentication": false,
       "ControlDeniedToUsers": false,
       "Id": 2,
       "Index": 1,
       "Element": 2,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": false,
       "InUse": true,
       "DoNotRequireAuthentication": false,
       "ControlDeniedToUsers": true,
       "Id": 3,
       "Index": 2,
       "Element": 3,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": false,
       "InUse": false,
       "DoNotRequireAuthentication": false,
       "ControlDeniedToUsers": false,
       "Id": 4,
       "Index": 3,
       "Element": 4,
       "CommandId": 0,
       "InProgress": false
   }
]"""
STATUS = """
    {
        "StatusUid": 1,
        "PanelLeds": {
            "InputsLed": 2,
            "AnomaliesLed": 1,
            "AlarmLed": 0,
            "TamperLed": 0
        },
        "PanelAnomalies": {
            "HasAnomaly": false,
            "PanelTamper": 0,
            "PanelNoPower": 0,
            "PanelLowBattery": 0,
            "GsmAnomaly": 0,
            "GsmLowBalance": 0,
            "PstnAnomaly": 0,
            "SystemTest": 0,
            "ModuleRegistration": 0,
            "RfInterference": 0,
            "InputFailure": 0,
            "InputAlarm": 0,
            "InputBypass": 0,
            "InputLowBattery": 0,
            "InputNoSupervision": 0,
            "DeviceTamper": 1,
            "DeviceFailure": 0,
            "DeviceNoPower": 0,
            "DeviceLowBattery": 0,
            "DeviceNoSupervision": 0,
            "DeviceSystemBlock": 0
        },
        "PanelAlignmentAdv": {
            "ManualFwUpAvailable": false,
            "Id": 1,
            "Index": -1,
            "Element": 0
        }
    }
"""
