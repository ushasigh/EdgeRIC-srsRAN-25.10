

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


### Running in zmq mode (virtual radios)

**GNU flowgraph - (Terminal 1)**  
Run the GNU radio flowgraph - for two UEs run:
```bash
cd scripts
sudo python3 top_block_2ue-no_gui.py 
```

**Run the srsRAN - (Terminal 2)**
```bash
cd scripts
sudo ./run_gnb_multi_ue.sh
```
Press ``t`` to see the network metrics  
**Run User Equipments (srsue) in zmq mode - - (Terminal 3)**  
For two UEs, you can run the script:
```bash
sudo ./run2ue-zmq-mode.sh
```

You can also run the UEs in separate terminals

## Traffic Generation (Downlink)
**(Terminal 4)**
```bash
cd traffic-generator
sudo ./iperf_server_2ues.sh # starts iperf servers on the UEs
```
**(Terminal 5)**
```bash
cd traffic-generator
sudo ./iperf_client_2ues_tcp.sh 13M 13M 1000 # starts TCP traffic from the CN to the UEs (downlink) -- run this where you have the core network
```

## How to run EdgeRIC?

**Scheduling muApp** Run various schedulers with EdgeRIC - refer to ``edgeric/muapp-scheduling``  
**MCS muApp** Run various schedulers with EdgeRIC - refer to ``edgeric/muapp-mcs``   

