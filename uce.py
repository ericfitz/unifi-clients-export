# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "requests",
#   "pandas",
#   "python-dotenv",
# ]
# ///

#!/usr/bin/env python3
"""
UniFi Network Client Export Script (API Key Authentication)

Exports all client devices (online and offline) from a UniFi Network controller
to a CSV file using a read-only API key.

Compatible with UniFi Network Application v9.5.21+.

Configuration:
  Copy example.env to .env and configure your UniFi controller settings.

Run with: `uv run uce.py`

Automatically installs dependencies via PEP 723 metadata when using `uv`.

Author: Assistant
Date: November 15, 2025
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_config():
    """Load and validate configuration from environment variables."""
    # Required configuration
    controller_url = os.getenv("CONTROLLER_URL")
    api_key = os.getenv("API_KEY")

    # Check required values
    if not controller_url:
        print("ERROR: CONTROLLER_URL is not set.")
        print("   → Copy example.env to .env and configure your settings")
        sys.exit(1)

    if not api_key or api_key == "your-api-key-here":
        print("ERROR: API_KEY is not set or using placeholder value.")
        print("   → Get your API key from: Settings > Control Plane > Applications")
        print("   → Update the API_KEY value in your .env file")
        sys.exit(1)

    # Optional configuration with defaults
    site_id = os.getenv("SITE_ID", "default")

    # Parse VERIFY_SSL boolean
    verify_ssl_str = os.getenv("VERIFY_SSL", "true").lower()
    verify_ssl = verify_ssl_str not in ("false", "0", "no")

    return controller_url, api_key, site_id, verify_ssl


def main() -> None:
    # Load configuration
    CONTROLLER_URL, API_KEY, SITE_ID, VERIFY_SSL = get_config()
    session = requests.Session()
    session.headers.update(
        {
            "X-API-KEY": API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )

    # Test sites endpoint
    sites_url = f"{CONTROLLER_URL}/proxy/network/api/self/sites"
    print(f"Testing: {sites_url}")
    try:
        resp = session.get(sites_url, verify=VERIFY_SSL, timeout=15)
        print(f"HTTP {resp.status_code}")
        if resp.status_code == 401:
            print("   → 401 Unauthorized: Invalid API key.")
            return
        if resp.status_code == 404:
            print("   → 404: Trying fallback endpoint...")
            sites_url = f"{CONTROLLER_URL}/api/self/sites"
            resp = session.get(sites_url, verify=VERIFY_SSL, timeout=15)
            print(f"Fallback HTTP {resp.status_code}")
        if resp.status_code != 200:
            print(f"   → Failed: {resp.status_code}. Raw: {resp.text[:500]}")
            return
        sites = resp.json().get("data", [])
        print(f"Found {len(sites)} site(s): {[s.get('desc') for s in sites]}")
    except Exception as e:
        print(f"Connection error: {e}")
        return

    # Fetch devices (switches, APs, etc.) for name mapping
    devices_url = f"{CONTROLLER_URL}/proxy/network/api/s/{SITE_ID}/stat/device"
    print(f"\nFetching devices: {devices_url}")
    devices_map = {}
    try:
        resp = session.get(devices_url, verify=VERIFY_SSL, timeout=15)
        if resp.status_code == 404:
            print("   → 404: Trying fallback...")
            devices_url = f"{CONTROLLER_URL}/api/s/{SITE_ID}/stat/device"
            resp = session.get(devices_url, verify=VERIFY_SSL, timeout=15)
        resp.raise_for_status()
        devices_data = resp.json().get("data", [])
        # Build a map of MAC address to device name
        for device in devices_data:
            mac = device.get("mac", "").upper()
            name = device.get("name") or device.get("hostname") or mac
            devices_map[mac] = name
        print(f"Found {len(devices_map)} device(s)")
    except Exception as e:
        print(f"Warning: Could not fetch devices: {e}")
        print("   → Switch names will show as MAC addresses")

    # Fetch clients
    clients_url = f"{CONTROLLER_URL}/proxy/network/api/s/{SITE_ID}/stat/sta"
    print(f"\nFetching clients: {clients_url}")
    try:
        resp = session.get(clients_url, verify=VERIFY_SSL, timeout=15)
        if resp.status_code == 404:
            print("   → 404: Trying fallback...")
            clients_url = f"{CONTROLLER_URL}/api/s/{SITE_ID}/stat/sta"
            resp = session.get(clients_url, verify=VERIFY_SSL, timeout=15)
        resp.raise_for_status()
        clients_data = resp.json().get("data", [])
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        print(f"Response: {e.response.text[:500]}")
        return
    except Exception as e:
        print(f"Failed: {e}")
        return

    # Process client data
    records = []
    for c in clients_data:
        conn = "Wireless" if c.get("ap_mac") else "Wired"
        last = (
            datetime.fromtimestamp(c.get("last_seen", 0))
            if c.get("last_seen")
            else None
        )

        # Extract switch and port info for wired clients
        switch_name = ""
        switch_port = ""
        if conn == "Wired":
            sw_mac = c.get("sw_mac", "").upper()
            if sw_mac:
                switch_name = devices_map.get(sw_mac, sw_mac)
            sw_port = c.get("sw_port")
            if sw_port is not None:
                switch_port = str(sw_port)

        records.append(
            {
                "Type": "Client",
                "Name": c.get("name") or c.get("hostname") or "Unknown",
                "MAC Address": c.get("mac", "").upper(),
                "IP Address": c.get("ip", ""),
                "Model": "",
                "Connection Type": conn,
                "Switch": switch_name,
                "Port": switch_port,
                "Last Seen": last.strftime("%Y-%m-%d %H:%M:%S") if last else "",
                "Status": "Online"
                if c.get("is_wired") is False or c.get("ap_mac")
                else "Offline",
            }
        )

    # Process UniFi device data
    device_type_map = {
        "usw": "Switch",
        "uap": "Access Point",
        "ugw": "Gateway",
        "udm": "Dream Machine",
        "uxg": "Gateway",
        "ubb": "Building Bridge",
        "ulte": "LTE",
        "pdu": "PDU",
    }

    for device in devices_data:
        device_type = device.get("type", "")
        friendly_type = device_type_map.get(device_type, device_type.upper())

        # Determine connection type and switch info
        conn = "Wired"
        switch_name = ""
        switch_port = ""

        # Check if device is connected via uplink
        if device.get("uplink"):
            uplink = device["uplink"]
            uplink_mac = uplink.get("uplink_mac", "").upper()
            if uplink_mac:
                switch_name = devices_map.get(uplink_mac, uplink_mac)
            uplink_port = uplink.get("uplink_remote_port")
            if uplink_port is not None:
                switch_port = str(uplink_port)

        # Get last seen time
        last_seen_time = device.get("last_seen")
        last = datetime.fromtimestamp(last_seen_time) if last_seen_time else None

        # Determine status
        state = device.get("state", 0)
        status = "Online" if state == 1 else "Offline"

        records.append(
            {
                "Type": f"Device - {friendly_type}",
                "Name": device.get("name") or device.get("hostname") or "Unknown",
                "MAC Address": device.get("mac", "").upper(),
                "IP Address": device.get("ip", ""),
                "Model": device.get("model", ""),
                "Connection Type": conn,
                "Switch": switch_name,
                "Port": switch_port,
                "Last Seen": last.strftime("%Y-%m-%d %H:%M:%S") if last else "",
                "Status": status,
            }
        )

    if not records:
        print("No clients or devices found.")
        return

    df = pd.DataFrame(records)
    df.to_csv("unifi_clients.csv", index=False)

    # Count clients and devices
    client_count = sum(1 for r in records if r["Type"] == "Client")
    device_count = len(records) - client_count
    print(f"\nSuccess: {len(records)} total entries → unifi_clients.csv")
    print(f"   → {client_count} clients")
    print(f"   → {device_count} UniFi devices")

    # Generate per-switch port information CSV files
    print("\nGenerating switch port CSV files...")
    switches_processed = 0
    for device in devices_data:
        # Only process switches (usw = UniFi Switch)
        if device.get("type") != "usw":
            continue

        device_name = device.get("name") or device.get("hostname") or device.get("mac")
        port_table = device.get("port_table", [])

        if not port_table:
            continue

        # Build port records
        port_records = []
        for port in port_table:
            # Find connected device/client info
            connected_name = ""
            connected_mac = ""
            connected_type = ""
            connected_model = ""

            if port.get("up") and "mac_table_count" in port and port["mac_table_count"] > 0:
                # First check for clients connected to this port
                for client in clients_data:
                    if (client.get("sw_mac", "").upper() == device.get("mac", "").upper() and
                        client.get("sw_port") == port.get("port_idx")):
                        connected_name = client.get("name") or client.get("hostname") or ""
                        connected_mac = client.get("mac", "").upper()
                        connected_type = "Client"
                        break

                # If no client found, check for UniFi devices connected via uplink
                if not connected_name:
                    for dev in devices_data:
                        if dev.get("uplink"):
                            uplink = dev["uplink"]
                            uplink_mac = uplink.get("uplink_mac", "").upper()
                            uplink_port = uplink.get("uplink_remote_port")
                            if (uplink_mac == device.get("mac", "").upper() and
                                uplink_port == port.get("port_idx")):
                                connected_name = dev.get("name") or dev.get("hostname") or ""
                                connected_mac = dev.get("mac", "").upper()
                                connected_model = dev.get("model", "")
                                dev_type = dev.get("type", "")
                                friendly_type = device_type_map.get(dev_type, dev_type.upper())
                                connected_type = f"Device - {friendly_type}"
                                break

            port_records.append({
                "Port": port.get("name") or f"Port {port.get('port_idx', '')}",
                "Port Index": port.get("port_idx", ""),
                "Status": "Up" if port.get("up") else "Down",
                "Speed": f"{port.get('speed', '')} Mbps" if port.get("speed") else "",
                "Full Duplex": "Yes" if port.get("full_duplex") else "No",
                "PoE Enabled": "Yes" if port.get("poe_enable") else "No",
                "PoE Power (W)": port.get("poe_power", ""),
                "PoE Class": port.get("poe_class", ""),
                "Connected Type": connected_type,
                "Connected Name": connected_name,
                "Connected MAC": connected_mac,
                "Connected Model": connected_model,
                "RX Bytes": port.get("rx_bytes", ""),
                "TX Bytes": port.get("tx_bytes", ""),
                "RX Packets": port.get("rx_packets", ""),
                "TX Packets": port.get("tx_packets", ""),
                "RX Errors": port.get("rx_errors", ""),
                "TX Errors": port.get("tx_errors", ""),
            })

        if port_records:
            # Sanitize filename
            safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in device_name)
            filename = f"switch_{safe_name}.csv"
            port_df = pd.DataFrame(port_records)
            port_df.to_csv(filename, index=False)
            switches_processed += 1
            print(f"   → {filename} ({len(port_records)} ports)")

    print(f"\nGenerated {switches_processed} switch port CSV files")


if __name__ == "__main__":
    main()
