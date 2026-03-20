echo "sudo ip netns exec ue1 iperf3 -s"
sudo ip netns exec ue1 iperf3 -s &



echo "sudo ip netns exec ue2 iperf3 -s"
sudo ip netns exec ue2 iperf3 -s 