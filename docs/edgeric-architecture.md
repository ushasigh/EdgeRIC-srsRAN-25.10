# EdgeRIC Architecture

## Overview

EdgeRIC is a real-time telemetry and control system for srsRAN gNB that collects metrics from multiple protocol layers and enables external control via ZeroMQ.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              srsRAN gNB Process                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│  │   GTP-U      │   │    PDCP      │   │     RLC      │   │     MAC      │          │
│  │  (CU-UP)     │   │   (CU-UP)    │   │    (DU)      │   │    (DU)      │          │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘          │
│         │                  │                  │                  │                  │
│         │ report_gtp_*     │ report_pdcp_*    │ report_rlc_*     │ set_mac_*        │
│         │ (ue_index)       │ (ue_index)       │ (du_ue_index)    │ (RNTI)           │
│         │                  │                  │                  │                  │
│         ▼                  ▼                  ▼                  ▼                  │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           edgeric (Static Class)                             │   │
│  ├──────────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                              │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐     │   │
│  │  │                    ID Correlation Maps                               │     │   │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │     │   │
│  │  │  │ du_ue_to_rnti   │  │ e1ap_to_rnti    │  │ cu_up_ue_to_e1ap    │  │     │   │
│  │  │  │ du_ue_index→RNTI│  │ e1ap_id→RNTI    │  │ cu_up_idx→e1ap_id   │  │     │   │
│  │  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │     │   │
│  │  └─────────────────────────────────────────────────────────────────────┘     │   │
│  │                                                                              │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐     │   │
│  │  │                    Per-TTI Metrics Storage                          │     │   │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │     │   │
│  │  │  │ mac_ue       │  │ mac_drb      │  │ rlc_drb      │  │ pdcp_drb │ │     │   │
│  │  │  │ map<RNTI,..> │  │ map<key,..>  │  │ map<key,..>  │  │ map<..>  │ │     │   │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘ │     │   │
│  │  │  ┌──────────────┐                                                   │     │   │
│  │  │  │ gtp_ue       │   Protected by std::mutex for thread safety       │     │   │
│  │  │  │ map<ue_idx,> │                                                   │     │   │
│  │  │  └──────────────┘                                                   │     │   │
│  │  └─────────────────────────────────────────────────────────────────────┘     │   │
│  │                                                                              │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐     │   │
│  │  │                    Control Reception                                │     │   │
│  │  │  ┌─────────────────┐  ┌─────────────────┐                           │     │   │
│  │  │  │ mcs_recved      │  │ weights_recved  │                           │     │   │
│  │  │  │ map<RNTI,MCS>   │  │ map<RNTI,float> │                           │     │   │
│  │  │  └─────────────────┘  └─────────────────┘                           │     │   │
│  │  └─────────────────────────────────────────────────────────────────────┘     │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                            │
│                            ┌───────────┼───────────┐                                │
│                            │           │           │                                │
│                            ▼           ▼           │                                │
│                   get_mcs_from_er()   get_weights_from_er()                        │
│                                        │                                            │
│                                        │ send_tti_metrics() @ every TTI             │
│                                        ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                         Protobuf Serialization                               │   │
│  │                                                                              │   │
│  │   TtiMetrics {                                                               │   │
│  │     tti_index: uint32 (rolls over @ 10000)                                   │   │
│  │     timestamp_us: uint64 (Unix time in microseconds)                         │   │
│  │     ues: [                                                                   │   │
│  │       UeMetrics {                                                            │   │
│  │         rnti, mac (MacUeMetrics), mac_drb[], rlc_drb[], pdcp_drb[], gtp      │   │
│  │       }, ...                                                                 │   │
│  │     ]                                                                        │   │
│  │   }                                                                          │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                            │
└────────────────────────────────────────┼────────────────────────────────────────────┘
                                         │
          ┌──────────────────────────────┴──────────────────────────────┐
          │                                                             │
          ▼                                                             ▼
┌─────────────────────────┐                              ┌─────────────────────────┐
│   ZMQ PUB Socket        │                              │   ZMQ SUB Sockets       │
│ ipc:///tmp/metrics_data │                              │ (Control Channels)      │
│                         │                              │                         │
│  Publishes TtiMetrics   │                              │ • control_mcs           │
│  every TTI (1ms)        │                              │ • control_weights       │
│  (Conflate mode)        │                              │                         │
└───────────┬─────────────┘                              └───────────┬─────────────┘
            │                                                        │
            ▼                                                        ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           EdgeRIC Python Agents (edgeric/)                        │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                         │
│  │    collector.py         │  │    muapp-mcs/           │                         │
│  │    (Metrics Display)    │  │    mcs_controller.py    │                         │
│  │                         │  │                         │                         │
│  │  • Subscribes to        │  │  • Set MCS per UE       │                         │
│  │    metrics_data         │  │  • Values 0-28          │                         │
│  │  • Pretty print / JSON  │  │  • 255 = auto (LA)      │                         │
│  │  • Rolling BLER calc    │  │                         │                         │
│  └─────────────────────────┘  └─────────────────────────┘                         │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```
## Interfaces - ZMQ Addresses

| Channel | Direction | Address |
|---------|-----------|---------|
| Metrics/ Telemetry | gNB → Agent | `ipc:///tmp/metrics_data` |
| Scheduling Weight Control | Agent → gNB | `ipc:///tmp/control_weights` |
| MCS Control | Agent → gNB | `ipc:///tmp/control_mcs` |


## Data Flow (Telemetry)

[Collector-Agent-documentation](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/edgeric-collector.md)

**Metrics Collection (Per Layer)**  

| Layer | Reporter Function | Key Type | Metrics |
|-------|------------------|----------|---------|
| **MAC** | `set_mac_ue()`, `set_dl_tbs()`, `inc_dl_harq_ack()` | RNTI | CQI, SNR, buffer sizes, TBS, MCS, PRBs, HARQ stats, goodput |
| **MAC Delays** | `report_mac_delays()` | RNTI | CE/CRC/HARQ/SR delays (from scheduler metrics, per-report-period) |
| **RLC** | `report_rlc_metrics()` | du_ue_index → RNTI | TX/RX SDUs, PDUs, latency, retransmissions (per LCID) |
| **PDCP** | `report_pdcp_metrics()` | cu_up_ue_index → RNTI | TX/RX PDUs, SDUs, dropped packets, latency (per DRB) |
| **GTP** | `report_gtp_dl/ul_pkt()` | cu_up_ue_index | DL/UL packet counts and bytes (N3 interface) |

```bash
# Pretty-printed output (default)
sudo python3 collector.py

# JSON output (one line per TTI)
sudo python3 collector.py --json

# JSON to file
sudo python3 collector.py --json --output metrics.json

# Quiet mode (MAC-level only, no per-DRB details)
sudo python3 collector.py --quiet
```

## Data Flow (Control)

External controllers can send commands via ZMQ PUB sockets:

| Channel | Protobuf Message | Effect |
|---------|-----------------|--------|
| `ipc:///tmp/control_mcs` | `mcs_control` | Override MCS selection (255 = no override) |
| `ipc:///tmp/control_weights` | `SchedulingWeights` | Override PF scheduler weights |



### MCS control

[MCS-muApp](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/muapp-mcs/README.md)  


```bash
cd muapp-mcs

# Fixed MCS: Set MCS=20 for all UEs
python3 mcs_muapp.py --algorithm fixed --mcs 20

# Random MCS: Random MCS between 10-20 for each UE
python3 mcs_muapp.py --algorithm random

# Random MCS with custom range
python3 mcs_muapp.py --algorithm random --min-mcs 15 --max-mcs 25

# CQI-based MCS: Map CQI to MCS
python3 mcs_muapp.py --algorithm cqi

# Test staleness (MCS should be rejected)
python3 mcs_muapp.py --algorithm fixed --mcs 20 --tti-offset -3
```


### UE Scheduling Weight Control

[Scheduling-muApp](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/muapp-scheduling/README.md)  


#### With Redis Algorithm Selection

```bash
# Start muApp (reads algorithm from Redis)
python3 scheduling_muapp.py

# Set algorithm via Redis
redis-cli SET scheduling_algorithm "Fixed Weight"
redis-cli SET scheduling_algorithm "Max CQI"
redis-cli SET scheduling_algorithm "Max Weight"
redis-cli SET scheduling_algorithm "Proportional Fair"
redis-cli SET scheduling_algorithm "Round Robin"
```

#### With Fixed Algorithm (No Redis)

```bash
python3 scheduling_muapp.py --algorithm "Max CQI"
python3 scheduling_muapp.py --algorithm "Proportional Fair"
python3 scheduling_muapp.py --algorithm "Fixed Weight"
```

#### Available Algorithms

| Algorithm | Description |
|-----------|-------------|
| `Fixed Weight` | Static weights (edit `fixed_weights()` function) |
| `Max CQI` | Prioritize UE with best channel quality |
| `Max Weight` | CQI × Backlog weighted scheduling |
| `Proportional Fair` | Rate-proportional fairness |
| `Round Robin` | Time-based round robin |

#### Customizing Fixed Weights (Custom UE priority)

Edit `scheduling_muapp.py`, function `fixed_weights()`:

```python
def fixed_weights():
    # ...
    for i in range(numues):
        weights[i*2+0] = RNTIs[i]
        # Customize weights here:
        if i == 0:
            weights[i*2+1] = 0.3  # First UE: 30%
        elif i == 1:
            weights[i*2+1] = 0.7  # Second UE: 70%
        else:
            weights[i*2+1] = 1.0 / numues
    return weights
```