echo "iperf3 -c 10.45.0.2 -i 1 -b $1 -t $3"
iperf3 -c 10.45.0.2 -i 1 -b $1 -t $3  &


sleep 3

echo "iperf3 -c 10.45.0.3 -i 1 -b $2 -t $3"
iperf3 -c 10.45.0.3 -i 1 -b $2 -t $3 