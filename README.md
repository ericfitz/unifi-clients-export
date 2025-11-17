# UniFi Clients Export

A Python script to export all client devices and UniFi infrastructure from a UniFi Network controller to CSV files.

## Features

- **Comprehensive Client Export**: Exports all clients (online and offline) with connection details
- **UniFi Device Inventory**: Includes all UniFi infrastructure devices (switches, access points, gateways)
- **Switch Port Mapping**: Generates detailed port information for each switch, including:
  - Connected clients and devices
  - PoE status and power consumption
  - Port speed and duplex settings
  - Traffic statistics (RX/TX bytes, packets, errors)
- **Network Topology**: Shows which switch and port each device is connected to
- **Environment-based Configuration**: Secure credential management via `.env` files

## Requirements

- Python 3.8 or higher
- UniFi Network Application v9.5.21 or higher
- Read-only API key from your UniFi controller

## Installation

### 1. Get the Code

Clone or download this repository:

```bash
git clone https://github.com/ericfitz/unifi-clients-export
cd unifi-clients-export
```

### 2. Configure Your Environment

Copy the example configuration and edit it with your settings:

```bash
cp example.env .env
```

Edit `.env` with your UniFi controller details:

```env
CONTROLLER_URL=https://your-controller-ip:443
API_KEY=your-api-key-here
SITE_ID=default
VERIFY_SSL=false
```

### Getting Your API Key

1. Log in to your UniFi Network Application
2. Navigate to **Settings > Control Plane > Applications**
3. Click **Create API Key**
4. Give it a descriptive name (e.g., "Client Export - Read Only")
5. Select **Read Only** permissions
6. Copy the generated API key to your `.env` file

### 3. Install Dependencies

Choose your preferred method:

#### Option A: If you are going to run the tool using uv run (Recommended)

[uv](https://docs.astral.sh/uv/) automatically manages dependencies - no manual installation or virtual environment management needed!

Install uv if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

The dependencies will be installed the first time you run the tool with uv run.

#### Option B: If you are going to run the tool directly with the python(3) executable (uses pip and venv to manage dependencies)

Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### With uv (Recommended)

Run the script using `uv`:

```bash
uv run uce.py
```

Dependencies are automatically installed and managed by uv using PEP 723 inline metadata.

### With python executable

Make sure your virtual environment is activated, then run:

```bash
source venv/bin/activate
python3 uce.py
```

# On Windows when not using wsl:

```windows
venv\Scripts\activate
python3 uce.py
```

The script will generate the following files:

### Output Files

1. **`unifi_clients.csv`** - Master inventory file containing:

   - All client devices (wireless and wired)
   - All UniFi infrastructure devices (switches, APs, gateways)
   - Columns: Type, Name, MAC Address, IP Address, Model, Connection Type, Switch, Port, Last Seen, Status

2. **`switch_<name>.csv`** - Per-switch port details, one file per switch:
   - Port status and configuration
   - Connected clients and devices
   - PoE information and power consumption
   - Traffic statistics

## Configuration Options

| Variable         | Required | Default   | Description                                      |
| ---------------- | -------- | --------- | ------------------------------------------------ |
| `CONTROLLER_URL` | Yes      | -         | UniFi controller URL (include protocol and port) |
| `API_KEY`        | Yes      | -         | Read-only API key from UniFi controller          |
| `SITE_ID`        | No       | `default` | Site ID (use 'default' for single-site setups)   |
| `VERIFY_SSL`     | No       | `true`    | SSL certificate verification (`true`/`false`)    |

### Boolean Values

For `VERIFY_SSL`, the following values are treated as `false`:

- `false`, `False`, `0`, `no`, `No`

All other values (or missing) default to `true` for security.

## Example Output

### unifi_clients.csv

```csv
Type,Name,MAC Address,IP Address,Model,Connection Type,Switch,Port,Last Seen,Status
Client,iPhone,C2:88:E5:F2:CC:D4,192.168.1.225,,Wireless,,,2025-11-17 10:40:50,Online
Client,homeassistant,2C:CF:67:10:44:CC,192.168.1.254,,Wired,Switch - Den,6,2025-11-17 10:41:23,Online
Device - Switch,Switch - Den,6C:63:F8:AC:65:96,192.168.1.137,USPM16P,Wired,Switch - 24 Port,22,2025-11-17 10:40:32,Online
Device - Access Point,AP - Media Room,94:2A:6F:2C:85:52,192.168.1.228,U7PROMAX,Wired,Switch - Media Room,1,2025-11-17 10:41:22,Online
```

### switch_Switch - Den.csv

```csv
Port,Port Index,Status,Speed,Full Duplex,PoE Enabled,PoE Power (W),PoE Class,Connected Type,Connected Name,Connected MAC,Connected Model,RX Bytes,TX Bytes,...
Port 1,1,Up,100 Mbps,Yes,No,0.00,Unknown,Client,Receiver,00:06:78:70:AD:80,,76680256,216506717,...
Port 4,4,Up,1000 Mbps,Yes,No,0.00,Unknown,Device - Switch,Switch - Front,70:A7:41:C8:BC:DE,USL8LP,30690781659,1322518689,...
Port 6,6,Up,1000 Mbps,Yes,Yes,4.95,Class 4,Client,homeassistant,2C:CF:67:10:44:CC,,195791846,11065229054,...
```

## Troubleshooting

### "ERROR: CONTROLLER_URL is not set"

- Make sure you've copied `example.env` to `.env`
- Verify your `.env` file contains the `CONTROLLER_URL` setting

### "ERROR: API_KEY is not set or using placeholder value"

- Get your API key from **Settings > Control Plane > Applications**
- Update the `API_KEY` value in your `.env` file

### SSL Certificate Errors

- If using a self-signed certificate, set `VERIFY_SSL=false` in your `.env` file
- For production environments, consider using a valid SSL certificate

### Connection Timeouts

- Verify your `CONTROLLER_URL` is correct and accessible
- Check that your UniFi controller is running and reachable
- Ensure firewall rules allow access to the controller

## Development

Dependencies are managed via PEP 723 inline script metadata:

- `requests` - HTTP client for UniFi API
- `pandas` - Data manipulation and CSV export
- `python-dotenv` - Environment variable management

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- UniFi Network Application API documentation
- [uv](https://docs.astral.sh/uv/) for fast Python package management
