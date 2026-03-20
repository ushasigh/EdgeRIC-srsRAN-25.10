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


### Summary of all config file locations found in this repository
**open5gs**
``/open5gs`` --> All open5gs configs  
```bash
## Some useful command for database queries for registered users with open5gs core network
mongosh # use mongodb
use open5gs # switch to the open5gs webui database
db.subscribers.find({}, { _id: 0, imsi: 1 }).forEach(s => print(s.imsi)) ## view all registered imsis
db.subscribers.findOne({ imsi: "001010999912305" }) ## view all entries for a specific imsi
```
**Configs below are for a 10MHz BW system, 20MHz settings are also available as comments**        
``configs-srsue/ue1-4g-zmq.conf`` --> config file for UE1 in multi UE zmq mode, check section ``[usim]`` and appropriately add those credentials in the open5gs webui database        
``configs-srsue/ue2-4g-zmq.conf`` --> config file for UE2 in multi UE zmq mode, check section ``[usim]`` and appropriately add those credentials in the open5gs webui database     
``configs-srsue/ue3-4g-zmq.conf`` --> config file for UE3 in multi UE zmq mode, check section ``[usim]`` and appropriately add those credentials in the open5gs webui database     
``configs-srsue/ue4-4g-zmq.conf`` --> config file for UE4 in multi UE zmq mode, check section ``[usim]`` and appropriately add those credentials in the open5gs webui database     
``configs-gnb/n320-ota-amarisoft.yml`` --> run srsgnb in Over the air mode with usrp N320, in section ``cell_cfg`` you can change the band and bandwidth of operation      
``configs-gnb/zmq-mode-10Mhz-UG.yml`` --> run srsgnb in zmq mode with srsue, BW - 10MHz    
   

For a full set of allowed configs from srsRAN, refer [here](https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html)



