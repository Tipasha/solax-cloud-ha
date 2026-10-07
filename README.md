# SolaX Cloud Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration for monitoring your SolaX inverter via the SolaX Cloud API.

## Features

✅ Cloud-based monitoring (no local Modbus needed)  
✅ Energy Dashboard-compatible cumulative energy counters  
✅ Live solar, grid, battery, and household consumption power  
✅ Grid-connected status detection  
✅ Five-minute SolaX Cloud polling  
✅ Masked Client Secret entry  
✅ Multiple inverter support  

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner, select **Custom repositories**
3. Add `https://github.com/Tipasha/solax-cloud-ha` with category **Integration**
4. Click **Download** on the integration card
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration**
7. Search for **SolaX Cloud** and follow the setup wizard

### Manual

1. Copy the `solax_cloud` folder to `/config/custom_components/` on your Home Assistant instance
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration**
4. Search for **SolaX Cloud** and follow the setup wizard

## Configuration

### Common Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Client ID** | Generated when you create a SolaX Developer Platform application | `7282a670...` |
| **Client Secret** | Generated with the Client ID; displayed as a password field | ••••••• |
| **API Region** | The API region listed under My Account in the SolaX Developer Portal | Global |
| **Inverter Serial Number** | Found on your inverter or SolaXCloud app | SL123456789 |
## Security
- The Client Secret is masked while entered in the Home Assistant UI
- API tokens are **never logged**
- Credentials are only sent over **HTTPS** to SolaX Cloud

## Supported Sensors

All live power sensors use watts (`W`). Cumulative energy sensors use
kilowatt-hours (`kWh`) and have a `total_increasing` state class for the Home
Assistant Energy Dashboard.

### Live Power

- **Solar Production Power** — Current PV input power
- **Grid Import Power** — Current power purchased from the grid
- **Grid Export Power** — Current power supplied to the grid
- **Battery Charging Power** — Current battery charging power
- **Battery Discharging Power** — Current battery discharging power
- **Battery State of Charge** — Current battery charge level (%)
- **Battery Remaining Energy** — Energy currently stored in the battery (kWh)
- **Home Consumption Power** — Calculated from solar, grid, and battery flows

Home consumption is an estimate and can differ slightly from a dedicated
whole-home meter due to inverter conversion losses.

### Cumulative Energy

- **Solar Production** — Total solar generation
- **Grid Import** — Total energy purchased from the grid
- **Grid Export** — Total energy supplied to the grid
- **Battery Charged** — Total energy charged into the battery
- **Battery Discharged** — Total energy discharged from the battery

### Grid Status

- **Grid Connected** — Off only while the inverter reports a documented
	EPS/islanded mode.

## Energy Dashboard

In **Settings → Dashboards → Energy**, select these SolaX Cloud entities:

| Energy Dashboard field | SolaX Cloud entity |
|-------|-------------|
| Solar panels | **Solar Production** |
| Grid consumption | **Grid Import** |
| Return to grid | **Grid Export** |
| Battery energy in | **Battery Charged** |
| Battery energy out | **Battery Discharged** |

Home Assistant calculates household consumption from the configured solar,
grid, and battery energy flows.

## Troubleshooting

### "SolaX Cloud rejected the Client ID or Client Secret"
- Verify the credentials from Application Management in the SolaX Developer Platform
- Confirm that the application has the required API service package

### "No data received"
- Verify the inverter serial number matches a device accessible to the application
- Check internet connectivity
- Increase the update interval if rate-limited

### "Connection error"
- Check your Home Assistant internet connectivity
- Verify SolaX Cloud API is accessible (may have regional issues)

## Development

To test locally:
```bash
cd custom_components/solax_cloud
python -m pytest
```
