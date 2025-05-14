
eapol_test -s foo -a 192.168.68.1  -c config

sudo tcpdump -i bridge100 port 1812 -w eap.pcap
