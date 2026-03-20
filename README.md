# EdgeRIC
This repository contains the EdgeRIC-enabled RAN stack built on top of **srsRAN_Project (v25.10)**, with **Open5GS** as the core network. 

Refer to full paper: https://www.usenix.org/system/files/nsdi24-ko.pdf  

Refer to EdgeRIC website: https://edgeric.github.io/  


EdgeRIC with srsRAN Repository structure
--------------------

High-level layout of this tree (after clone; `build/` is created by CMake and is not versioned):

```
.
├── apps/                    # gNB, CU, DU, DU-low, helpers, services, flexible O-DU units
├── cmake/                   # CMake modules
├── configs/                 # Example gNB / CU / DU YAML configurations
├── docker/                  # Container and observability assets
├── docs/                    # Additional documentation
├── edgeric/                 # EdgeRIC: ZMQ muApps, metrics collector, Python protobufs
│   ├── collector.py         # Subscribe to per-TTI metrics (TtiMetrics)
│   ├── protobufs/           # metrics.proto, control_weights.proto, control_mcs.proto
│   ├── muapp-scheduling/    # Scheduling weights muApp (Redis / algorithms)
│   ├── muapp-mcs/           # MCS override muApp
│   └── venv/                # Optional local Python env (often gitignored)
├── external/                # Bundled third-party sources (fmt, CLI11, etc.)
├── include/srsran/          # Public C++ headers
├── lib/                     # Core libraries (RAN stack, schedulers, …)
│   ├── edgeric/             # EdgeRIC agent in RAN (ZMQ, protobuf, metrics export)
│   └── protobufs/           # .proto sources used by C++ EdgeRIC
├── scripts/                 # Convenience build / run scripts
├── srsRAN_4G                # submodule: upstream srsRAN_4G (srsue stack) -- Run the software UE for emulation mode
├── tests/                   # Unit and integration tests
├── utils/                   # Utilities
├── CMakeLists.txt
├── LICENSE
└── README.md
```

**EdgeRIC-related paths**

| Path | Role |
|------|------|
| `lib/edgeric/` | RAN-side EdgeRIC: metrics publishing, weight/MCS subscribers |
| `lib/protobufs/` | Protobuf definitions compiled into the DU/gNB |
| `edgeric/protobufs/` | Same schemas for Python (`protoc --python_out=..`) |
| `edgeric/muapp-scheduling/` | External scheduling controller (weights → RAN) |
| `edgeric/muapp-mcs/` | External MCS controller |
| `edgeric/collector.py` | Standalone metrics viewer / JSON export |

### Tutorials

Run the repository with srsue (virtual radios over ZMQ): [Emulation Mode](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/emulation-mode.md)

Run the repository in Split 8 mode: [OTA with SDR](https://edgeric.github.io/edgeric-workshop-tutorial.html)  

### EdgeRIC documentation
EdgeRIC Architecture: [Architecture](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/edgeric-architecture.md)   
EdgeRIC telemetry: [Metrics Collector](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/edgeric-collector.md)  
EdgeRIC muApps: [Scheduler muApp](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/muapp-scheduling/README.md) [MCS muApp](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/muapp-mcs/README.md)  


## Summary of config file locations found in this repository

These files correspond to the core network functions (AMF, SMF, UPF, etc.) and should be copied to `/etc/open5gs/` before running the core network.
### open5gs

``/open5gs`` --> All open5gs configs 
Open5GS stores subscriber information in MongoDB (`open5gs` database). The following commands are useful for inspecting registered UEs:
**Useful MongoDB Commands**  
```bash
mongosh
use open5gs

# List all registered IMSIs
db.subscribers.find({}, { _id: 0, imsi: 1 }).forEach(s => print(s.imsi))

# View full entry for a specific IMSI
db.subscribers.findOne({ imsi: "001010999912305" })
``` 

### RAN and UE


**Example configs:** defaults assume **10 MHz** bandwidth; **20 MHz** options are often available as comments in the same files.

| Config file | Description |
|-------------|-------------|
| `configs-srsue/ue1-4g-zmq.conf` | UE1 in multi-UE ZMQ mode; see `[usim]` and match credentials in the Open5GS WebUI subscriber DB. |
| `configs-srsue/ue2-4g-zmq.conf` | UE2 in multi-UE ZMQ mode; see `[usim]` and match credentials in the Open5GS WebUI subscriber DB. |
| `configs-srsue/ue3-4g-zmq.conf` | UE3 in multi-UE ZMQ mode; see `[usim]` and match credentials in the Open5GS WebUI subscriber DB. |
| `configs-srsue/ue4-4g-zmq.conf` | UE4 in multi-UE ZMQ mode; see `[usim]` and match credentials in the Open5GS WebUI subscriber DB. |
| `configs-gnb/n320-ota-amarisoft.yml` | OTA gNB with USRP N320; in `cell_cfg` set band and channel bandwidth. |
| `configs-gnb/zmq-mode-10Mhz-UG.yml` | ZMQ mode with srsUE; 10 MHz bandwidth. |
   

For a full set of allowed configs from srsRAN, refer [here](https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html)



