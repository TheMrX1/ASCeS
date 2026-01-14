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
        
        # Interval ~0.05s but with more variance (Poisson-like)
        # Use exponential distribution for intervals to mimic real traffic
        interval = random.expovariate(20.0) # Avg rate 20
        start_time += interval
        pkt_time = start_time
        
        # Randomize IPs/Ports to ensure Unique* features have variance
        # Pick from a small pool to keep "normal" pattern stable but not constant
        src_ip = f"192.168.1.{random.randint(10, 15)}"
        src_port = random.choice([12345, 12346, 12347, 443, 8080])
        
        # Explicit MACs to avoid ARP lookups/warnings
        pkt = Ether(src="00:11:22:33:44:55", dst="ff:ff:ff:ff:ff:ff") / IP(src=src_ip, dst="192.168.1.20") / TCP(sport=src_port, dport=80) / ("X" * payload_size)
        pkt.time = pkt_time
        packets.append(pkt)
        
    wrpcap(filename, packets)
    print("Done.")

def generate_anomalous_traffic(filename="anomaly.pcap", duration=300):
    """
    Generates 'anomalous' traffic mixed with STRANGE (WARN) and CRIT patterns.
    """
    print(f"Generating anomalous traffic to {filename}...")
    packets = []
    start_time = time.time()
    current_time = start_time
    
    # 1. STRANGE Traffic (WARN)
    # Behavior: Unusual IP, consistent but slightly higher rate, maybe unusual port
    # Requirement: At least 20 packets
    print("Generating STRANGE (WARN) traffic...")
    strange_count = 25
    for i in range(strange_count):
        # Interval ~0.2s (5 packets/sec) - consistent
        current_time += 0.2
        
        # Source: 192.168.1.77 (Unusual host)
        # Port: 8888 (Uncommon)
        pkt = Ether(src="00:11:22:33:44:77", dst="ff:ff:ff:ff:ff:ff") / \
              IP(src="192.168.1.77", dst="192.168.1.20") / \
              TCP(sport=8888, dport=80) / \
              ("S" * 200) # 'S' for Strange
        pkt.time = current_time
        packets.append(pkt)

    # Gap between events
    current_time += 2.0

    # 2. CRIT Traffic
    # Behavior: Attack-like burst from another IP
    # Requirement: At least 20 packets
    print("Generating CRIT traffic...")
    crit_count = 30
    for i in range(crit_count):
        # High rate burst: 0.005s interval
        current_time += 0.005
        
        # Source: 192.168.1.66 (Attacker)
        # Port: 6666
        pkt = Ether(src="00:aa:bb:cc:dd:ee", dst="ff:ff:ff:ff:ff:ff") / \
              IP(src="192.168.1.66", dst="192.168.1.20") / \
              TCP(sport=6666, dport=80) / \
              ("A" * 500) # 'A' for Attack
        pkt.time = current_time
        packets.append(pkt)
        
    # Fill remaining time with some background noise if needed
    # (Optional, but keeps the file timeline realistic)
    
    wrpcap(filename, packets)
    print(f"Done. Generated {len(packets)} packets.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python traffic_gen.py [normal|anomaly] [duration_seconds]")
        print("Default duration: 300s")
        sys.exit(1)
        
    mode = sys.argv[1]
    duration = 300
    if len(sys.argv) > 2:
        duration = int(sys.argv[2])

    if mode == "normal":
        generate_normal_traffic(duration=duration)
    elif mode == "anomaly":
        generate_anomalous_traffic(duration=duration)
    else:
        print("Unknown mode")
