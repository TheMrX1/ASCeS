import time
import random
import sys
from scapy.all import wrpcap, IP, TCP, UDP, Ether

def generate_normal_traffic(filename="normal.pcap", count=2000):
    """
    Generates 'normal' traffic: random packet sizes, random intervals (white noise-like).
    Hurst exponent should be close to 0.5.
    """
    print(f"Generating {count} normal packets to {filename}...")
    packets = []
    start_time = time.time()
    
    for i in range(count):
        # Random sizes (White Noise)
        payload_size = random.randint(64, 1500)
        
        # Random intervals
        pkt_time = start_time + (i * 0.05) + random.uniform(-0.01, 0.01)
        
        pkt = Ether() / IP(src="192.168.1.10", dst="192.168.1.20") / TCP(sport=12345, dport=80) / ("X" * payload_size)
        pkt.time = pkt_time
        packets.append(pkt)
        
    wrpcap(filename, packets)
    print("Done.")

def generate_anomalous_traffic(filename="anomaly.pcap", count=2000):
    """
    Generates 'anomalous' traffic: highly persistent packet sizes or bursts.
    Hurst exponent should be > 0.5 (long-range dependence).
    """
    print(f"Generating {count} anomalous packets to {filename}...")
    packets = []
    start_time = time.time()
    
    # Simulate a bursty/persistent process
    # We'll use a regime switching model: small packets for a while, then huge packets
    current_size = 100
    
    for i in range(count):
        # Persistence: size tends to stay similar to previous
        if random.random() < 0.9:
            # Stay close to current
            current_size += random.randint(-10, 10)
        else:
            # Jump
            current_size = random.randint(64, 1500)
            
        current_size = max(64, min(1500, current_size))
        
        # Bursty timing
        if random.random() < 0.1:
            # Burst
            interval = 0.001
        else:
            interval = 0.1
            
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
