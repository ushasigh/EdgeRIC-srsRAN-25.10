

# Run the Network
## Core Network (CN)

Open5gs Official documentation: [open5gs-quickstart](https://open5gs.org/open5gs/docs/guide/01-quickstart/)

Run the following commands to restart/ stop CN:  
```bash
cd scripts
sudo ./restart-open5gs.sh # to restart the open5gs services
sudo ./stop-open5gs.sh # to stop the opnen5gs services
```
**how to know open5gs is installed?**  
Run ``ps aux | grep open5gs`` --> this will show 16 active processes  
**Where are open5gs configs located?**  
``~/etc/open5gs`` --> folder contains all config files as .yaml --> to write, you need to change permission --> ``sudo chmod a+w ~/etc/open5gs/``  
This repository contains all the open5gs configs used in folder ``open5gs``  
**How to update UE data base on open5gs core network?**  
``http://localhost:9999`` --> username: admin, password: 1423, add all UE sim credentials, press ``Add a subscriber``
 
## Radio Access Network


### Running in over the air mode (Split 8 w/ SDR as RF Frontend)


**Run the srsRAN - (Terminal 1)**
```bash
cd scripts
sudo ./run_gnb_n310.sh
```
Press ``t`` to see the network metrics  

**Connect Your Phones** 

## Traffic Generation (Downlink)
**(Terminal 4)**
```bash
cd traffic-generator
sudo ./iperf_server_2ues.sh # starts iperf servers on the UEs, run these commands separately on the phones/ UEs connected
```
**(Terminal 5)**
```bash
cd traffic-generator
sudo ./iperf_client_2ues_tcp.sh 13M 13M 1000 # starts TCP traffic from the CN to the UEs (downlink) -- run this where you have the core network
```

## How to run EdgeRIC?

### Collect Telemetry (EdgeRIC Terminal 1)

[Collector-Agent-documentation](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/edgeric-collector.md)

```bash
cd edgeric
# Pretty-printed output (default)
sudo python3 collector.py

# JSON output (one line per TTI)
sudo python3 collector.py --json

# JSON to file
sudo python3 collector.py --json --output metrics.json

# Quiet mode (MAC-level only, no per-DRB details)
sudo python3 collector.py --quiet
```

### Control the MCS (EdgeRIC Terminal 2)

[MCS-muApp Documentation](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/muapp-mcs/README.md)  

```bash
cd edgeric/muapp-mcs

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


### Control the Scheduling Priority (EdgeRIC Terminal 3)

[Scheduling-muApp Documentation](https://github.com/ushasigh/EdgeRIC-srsRAN-25.10/blob/main/edgeric/muapp-scheduling/README.md) 

#### With Redis Algorithm Selection

```bash
cd edgeric/muapp-scheduling
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


