cd ../../srsRAN_4G/build
sudo ./srsue/src/srsue ../../configs-srsue/ue1-4g-zmq.conf & 

sleep 2
sudo ./srsue/src/srsue ../../configs-srsue/ue2-4g-zmq.conf 