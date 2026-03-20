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

MCS values are sent as an ordered array matching the gNB's UE order (sorted by RNTI):
- Values 0-28: Override MCS to specified value
- Value 255: No override (use link adaptation)

```bash
cd edgeric/muapp-mcs

# Interactive mode
python3 mcs_controller.py -i

# Command-line
python3 mcs_controller.py --rnti 17921 --mcs 20
python3 mcs_controller.py --rnti 17921 --clear
```



### UE Scheduling Weight Control

[Scheduling-muApp](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/muapp-scheduling/README.md)  