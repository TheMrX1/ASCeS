import time
import random
import sys
from scapy.all import wrpcap, IP, TCP, UDP, Ether

def generate_normal_traffic(filename="normal.pcap", duration=300):
    """
    Generates 'normal' traffic for a specific duration to ensure sufficient window data.
    Rate: ~20 packets/sec
    """
    count = duration * 20
    print(f"Generating ~{count} normal packets to {filename} ({duration}s)...")
    packets = []
    start_time = time.time()
    
    for i in range(count):
        # Random sizes (White Noise)
        payload_size = random.randint(64, 1500)
        
        # Interval ~0.05s
        pkt_time = start_time + (i * 0.05) + random.uniform(-0.01, 0.01)
        
        pkt = Ether() / IP(src="192.168.1.10", dst="192.168.1.20") / TCP(sport=12345, dport=80) / ("X" * payload_size)
        pkt.time = pkt_time
        packets.append(pkt)
        
    wrpcap(filename, packets)
    print("Done.")

def generate_anomalous_traffic(filename="anomaly.pcap", duration=300):
    """
    Generates 'anomalous' traffic.
    """
    count = duration * 20
    print(f"Generating ~{count} anomalous packets to {filename} ({duration}s)...")
    packets = []
    start_time = time.time()
    
    current_size = 100
    
    for i in range(count):
        if random.random() < 0.9:
            current_size += random.randint(-10, 10)
        else:
            current_size = random.randint(64, 1500)
            
        current_size = max(64, min(1500, current_size))
        
        if random.random() < 0.1:
            interval = 0.001
        else:
            interval = 0.05
            
        pkt_time = start_time + (i * interval)
        
        pkt = Ether() / IP(src="192.168.1.66", dst="192.168.1.20") / TCP(sport=6666, dport=80) / ("A" * current_size)
        pkt.time = pkt_time
        packets.append(pkt)
        
    wrpcap(filename, packets)
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python traffic_gen.py [normal|anomaly]")
        sys.exit(1)
        
    mode = sys.argv[1]
    if mode == "normal":
        generate_normal_traffic()
    elif mode == "anomaly":
        generate_anomalous_traffic()
    else:
        print("Unknown mode")
