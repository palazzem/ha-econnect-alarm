"""
Debug script for polling e-Connect/IESS alarm systems.

This script connects to an e-Connect/IESS alarm system via the E-Connect or Metronet
cloud platform, authenticates using provided credentials, and continuously polls
for updates on sectors, inputs, outputs, alerts, and panel status.

It prints the 'last_id' received for each category in every poll cycle.

Usage:
    python -m scripts.debug_polling <system> <domain> <username> <password>

Arguments:
    domain: The domain identifier for the alarm system (e.g., vendor).
    system: The cloud platform to connect to ('econnect' or 'iess').
    username: The username for authentication.
    password: The password for authentication.
"""

import argparse

from custom_components.econnect_metronet.api.v1 import query as q
from custom_components.econnect_metronet.api.v1 import systems
from custom_components.econnect_metronet.api.v1.client import ElmoClient

if __name__ == "__main__":
    # Argument Parsing
    parser = argparse.ArgumentParser(description="Poll e-Connect/IESS alarm systems.")
    parser.add_argument("system", choices=["econnect", "iess"], help="Cloud platform ('econnect' or 'iess').")
    parser.add_argument("domain", help="Domain identifier for the alarm system.")
    parser.add_argument("username", help="Username for authentication.")
    parser.add_argument("password", help="Password for authentication.")
    args = parser.parse_args()

    # Determine system URL
    system_url = systems.ELMO_E_CONNECT if args.system == "econnect" else systems.IESS_METRONET

    # Initialize Client
    client = ElmoClient(base_url=system_url, domain=args.domain)
    client.auth(args.username, args.password)
    print("Authenticated")
    last_ids = {}

    # Poll the system
    while True:
        sectors = client.query(q.SECTORS)
        inputs = client.query(q.INPUTS)
        outputs = client.query(q.OUTPUTS)
        alerts = client.query(q.ALERTS)
        panel = client.query(q.PANEL)

        last_ids[q.SECTORS] = sectors.get("last_id", 0)
        last_ids[q.INPUTS] = inputs.get("last_id", 0)
        last_ids[q.OUTPUTS] = outputs.get("last_id", 0)
        last_ids[q.ALERTS] = alerts.get("last_id", 0)
        last_ids[q.PANEL] = panel.get("last_id", 0)

        print("-" * 100)
        print(f"Sectors: {sectors['last_id']}")
        print(f"Inputs: {inputs['last_id']}")
        print(f"Outputs: {outputs['last_id']}")
        print(f"Alerts: {alerts['last_id']}")
        print(f"Panel: {panel['last_id']}")
        print("-" * 100)
        client.poll(last_ids)
