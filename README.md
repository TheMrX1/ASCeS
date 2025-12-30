# ASCeS — Adaptive Session Control System

ASCeS is a specialized network monitoring and anomaly detection system designed for Linux environments. It leverages statistical analysis (Hurst exponent) to detect anomalies in network traffic patterns (session contexts) without relying on signature-based detection.

## Features

- **Live & Offline Analysis**: Capture from network interfaces or read PCAP files.
- **Statistical Anomaly Detection**: Uses Rescaled Range (R/S) and DFA methods to calculate the Hurst exponent.
- **Adaptive Baselines**: Learns "normal" traffic patterns to establish dynamic baselines.
- **Web Interface**: Real-time dashboard for monitoring alerts and system status.
- **REST API**: Full programmatic access to alerts and metrics.

## Installation

### Prerequisites
- Python 3.11+
- `libpcap` (usually installed by default on Linux/macOS)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/asces.git
   cd asces
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install typer pydantic pyyaml scapy numpy pandas fastapi uvicorn jinja2 sqlalchemy aiofiles python-multipart
   ```
   Or using Poetry (recommended):
   ```bash
   poetry install
   ```

## Usage

### Configuration
Copy the example config and edit it:
```bash
cp configs/config.example.yaml config.yaml
```

### Training (Baseline)
Before monitoring, train the system on normal traffic:
```bash
poetry run python -m asces.cli train --iface eth0 --duration 240
# OR from PCAP
poetry run python -m asces.cli train --pcap normal_traffic.pcap
```

### Monitoring
Start the detection engine:
```bash
poetry run python -m asces.cli monitor --iface eth0
```

### Web Interface & API
Start the web server (default: http://localhost:8000):
```bash
poetry run python -m asces.cli serve
```

## Security & Permissions
Capturing packets requires `cap_net_raw` capabilities.
**Recommended**:
```bash
sudo setcap cap_net_raw,cap_net_admin+eip $(readlink -f $(which python3))
```
**Alternative**: Run as root (use with caution).

## Disclaimer
ASCeS is a defensive tool for monitoring and analysis. It does not include offensive capabilities.

## Test Verification

To verify the system functionality using synthetic traffic, follow these steps:

1. **Generate Synthetic Traffic**:
   ```bash
   # Generate "normal" traffic (1200 seconds)
   python3 tools/traffic_gen.py normal 1200
   
   # Generate "anomalous" traffic (600 seconds)
   python3 tools/traffic_gen.py anomaly 600
   ```

2. **Train Baseline**:
   Clear old data and train on the normal traffic.
   ```bash
   rm data/baselines/*.json data/asces.db
   python3 -m asces.cli train --pcap normal.pcap
   ```

3. **Monitor for Anomalies**:
   Run the monitor on the anomalous traffic. You should see `WARNING` or `CRITICAL` alerts in the console.
   ```bash
   python3 -m asces.cli monitor --pcap anomaly.pcap
   ```
