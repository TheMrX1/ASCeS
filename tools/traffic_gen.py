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
        
        # Explicit MACs to avoid ARP lookups/warnings
        pkt = Ether(src="00:11:22:33:44:55", dst="ff:ff:ff:ff:ff:ff") / IP(src="192.168.1.10", dst="192.168.1.20") / TCP(sport=12345, dport=80) / ("X" * payload_size)
        pkt.time = pkt_time
        packets.append(pkt)
        
    wrpcap(filename, packets)
    print("Done.")

def generate_anomalous_traffic(filename="anomaly.pcap", duration=300):
    """
    Generates 'anomalous' traffic with high self-similarity (Pareto ON/OFF).
    """
    # Rate: 20 pkts/sec avg
    count = duration * 20
    print(f"Generating ~{count} anomalous packets to {filename} ({duration}s)...")
    packets = []
    start_time = time.time()
    
    # Pareto ON/OFF model logic simplified for packet stream
    # Bursts of packets followed by silence
    
    current_time = start_time
    packets_generated = 0
    
    while packets_generated < count:
        # ON period: burst of packets
        # Pareto shape 1.2 -> Heavy tailed
        burst_size = int(random.paretovariate(1.2) * 10)
        burst_size = max(5, min(burst_size, 500))
        
        for _ in range(burst_size):
            payload_size = 500 # Constant size often seen in attacks or large transfers
            
            # Very short interval in burst
            current_time += 0.002 
            
            pkt = Ether(src="00:aa:bb:cc:dd:ee", dst="ff:ff:ff:ff:ff:ff") / IP(src="192.168.1.66", dst="192.168.1.20") / TCP(sport=6666, dport=80) / ("A" * payload_size)
            pkt.time = current_time
            packets.append(pkt)
            packets_generated += 1
            
            if packets_generated >= count:
                break
        
        # OFF period
        # Pareto again for silence
        silence = random.paretovariate(1.2) * 0.1
        current_time += silence

    wrpcap(filename, packets)
    print("Done.")

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
