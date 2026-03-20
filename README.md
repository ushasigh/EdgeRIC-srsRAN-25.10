# EdgeRIC
This repository contains the EdgeRIC-enabled RAN stack built on top of **srsRAN_Project (v25.10)**, with **Open5GS** as the core network. 

Refer to full paper: https://www.usenix.org/system/files/nsdi24-ko.pdf

Refer to EdgeRIC website: https://edgeric.github.io/

Refer to how to run the repository in emulation mode (virtual radios over ZMQ with srsue): https://edgeric.github.io/edgeric-workshop-tutorial.html

Refer to how to run the repository in over the air (Split 8): https://edgeric.github.io/edgeric-workshop-tutorial.html


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



