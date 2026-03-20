# EdgeRIC
This repository contains the EdgeRIC-enabled RAN stack built on top of **srsRAN_Project (v25.10)**, with **Open5GS** as the core network. 

Refer to full paper: https://www.usenix.org/system/files/nsdi24-ko.pdf  

Refer to EdgeRIC website: https://edgeric.github.io/  


## Build the repository

```bash
####### 1. Clone the repository
git clone https://github.com/ushasigh/EdgeRIC-srsRAN-25.10.git
cd EdgeRIC-srsRAN-25.10

####### 2. Git submodules (srsUE stack)
#(If you cloned without submodules, the next step still fetches them.)
git submodule update --init --recursive
# This populates `srsRAN_4G/` (required for `scripts/make-ue.sh`).

####### 3. System dependencies (Ubuntu / Debian)
sudo apt-get update && sudo apt-get install -y \
  cmake make gcc g++ pkg-config \
  libfftw3-dev libmbedtls-dev libsctp-dev libyaml-cpp-dev \
  libzmq3-dev libprotobuf-dev protobuf-compiler

#######  4. Protobufs
## RAN (C++) protobufs
cd lib/protobufs
protoc --cpp_out=../edgeric *.proto

## EdgeRIC (python) protobufs
cd edgeric/protobufs
protoc --python_out=.. *.proto
cd ../..

####### 5. Build RAN (gNB with EdgeRIC + ZMQ) and srsUE
cd scripts
./make-ran.sh    # cmake + make; EdgeRIC-enabled RAN with ENABLE_ZEROMQ=ON
./make-ue.sh     # build srsUE inside srsRAN_4G submodule
# After a successful build, look under `build/apps/gnb/` for **gnb** and under `srsRAN_4G/build/` for the **srsue** binary (exact subpath depends on srsRAN_4G CMake output).
```

## Tutorials

Run the repository with srsue (virtual radios over ZMQ): [Emulation Mode](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/emulation-mode.md)

Run the repository in Split 8 mode: [OTA with SDR](https://edgeric.github.io/edgeric-workshop-tutorial.html)  

## EdgeRIC documentation
EdgeRIC Architecture: [Architecture](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/edgeric-architecture.md)   
EdgeRIC telemetry: [Metrics Collector](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/edgeric-collector.md)  
EdgeRIC muApps: [Scheduler muApp](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/muapp-scheduling/README.md) [MCS muApp](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/muapp-mcs/README.md)  


## Summary of config file locations found in this repository


### open5gs

``/open5gs`` --> All open5gs configs   
These files correspond to the core network functions (AMF, SMF, UPF, etc.) and should be copied to `/etc/open5gs/` before running the core network.  
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


## EdgeRIC with srsRAN — repository structure

High-level layout (after clone). `build/` is produced by CMake and is usually not committed.

```
.
├── apps/                    # gNB, CU, DU, DU-low, helpers, services, flexible O-DU units
├── cmake/                   # CMake modules
├── configs/                 # Upstream example gNB / CU / DU YAML (srsRAN Project)
├── configs-gnb/             # Project gNB configs (ZMQ emulation, OTA N320, …)
├── configs-srsue/           # srsUE `.conf` files for multi-UE ZMQ / emulation
├── docker/                  # Container and observability assets
├── docs/                    # Additional srsRAN documentation
├── edgeric/                 # EdgeRIC Python side: muApps, collector, shared protobufs
│   ├── collector.py         # Subscribe to per-TTI metrics (TtiMetrics)
│   ├── protobufs/           # metrics.proto, control_weights.proto, control_mcs.proto → Python
│   ├── muapp-scheduling/    # Scheduling-weights muApp (Redis / algorithms)
│   ├── muapp-mcs/           # MCS-override muApp
│   ├── metrics_pb2.py, …    # Generated `*_pb2.py` after `protoc` (see edgeric/protobufs/)
│   ├── edgeric-architecture.md
│   ├── requirements.txt
│   └── venv/                # Optional local Python env (often gitignored)
├── external/                # Bundled third-party sources (fmt, CLI11, …)
├── include/srsran/          # Public C++ headers
├── lib/                     # Core RAN libraries (L1/L2/L3, scheduler, …)
│   ├── edgeric/             # RAN EdgeRIC agent (ZMQ, protobuf, metrics export)
│   └── protobufs/           # .proto sources compiled for C++ EdgeRIC
├── open5gs/                 # Open5GS-related configs
├── scripts/                 # Build, run gNB/UE, Open5GS helper scripts
├── srsRAN_4G/               # Git submodule: srsUE / srsENB stack (emulation-mode UE)
├── traffic-generator/       # Example iperf / traffic scripts for multi-UE tests
├── tests/                   # Unit and integration tests
├── utils/                   # Utilities
├── emulation-mode.md        # How to run ZMQ / multi-UE emulation
├── srsRAN-readme.md         # Upstream srsRAN Project build notes (reference)
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