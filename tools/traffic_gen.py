import time
import random
import sys
from scapy.all import wrpcap, IP, TCP, UDP, Ether, Raw

# ----- Configuration & Profiles -----

class UserProfile:
    def __init__(self, name, base_ip, cookies):
        self.name = name
        self.base_ip = base_ip
        self.current_ip = base_ip
        self.cookies = cookies
        self.last_rotation = 0

    def rotate_ip(self, context_name):
        # Simulate moving to a new location (Home -> Cafe -> Theater)
        octets = self.base_ip.split('.')
        # Completely new IP logic
        new_third = int(octets[2]) + random.randint(0, 5) 
        new_fourth = random.randint(10, 200)
        self.current_ip = f"{octets[0]}.{octets[1]}.{new_third}.{new_fourth}"
        print(f"[{self.name}] Moved to {context_name}. New IP: {self.current_ip}")

    def get_headers(self):
        base = f"GET /api/resource HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0 ({self.name})\r\n"
        if self.cookies and self.cookies != "none":
            base += f"Cookie: session={self.cookies}\r\n"
        base += "\r\n"
        return base

# Only Bob exists in normal world
bob = UserProfile("Bob", "192.168.1.100", "bob_session_secret_123")

def generate_packet(profile, timestamp, dst_ip="192.168.1.20", payload_mult=1, custom_cookie=None):
    headers = profile.get_headers()
    if custom_cookie:
        headers = headers.replace(f"session={profile.cookies}", f"session={custom_cookie}")
        
    payload = headers + ("X" * (50 * payload_mult))
    pkt = Ether(src=f"00:11:22:33:44:{random.randint(10,99)}", dst="ff:ff:ff:ff:ff:ff") / \
          IP(src=profile.current_ip, dst=dst_ip) / \
          TCP(sport=random.randint(10000, 60000), dport=80, flags="PA") / \
          Raw(load=payload)
    pkt.time = timestamp
    return pkt

def generate_normal_traffic(filename="normal.pcap", duration=1200):
    print(f"Generating NORMAL traffic (Bob Only) to {filename} ({duration}s)...")
    packets = []
    # Virtual Time Simulation
    start_time = time.time() # This is just the base offset
    current_time = start_time
    end_time = start_time + duration
    
    # Bob moves every ~10-15 minutes
    next_move_time = current_time + random.randint(600, 900)
    locations = ["Cafe", "Theater", "Park", "Friend's House"]
    
    # Loop until virtual time exceeds duration
    while current_time < end_time:
        # Check rotation
        if current_time > next_move_time:
            bob.rotate_ip(random.choice(locations))
            next_move_time = current_time + random.randint(600, 900)
            
        # Bob browsing behavior
        # Bursts of activity followed by reading/watching
        burst = random.randint(3, 12)
        for _ in range(burst):
            current_time += random.uniform(0.1, 0.8) 
            pkt = generate_packet(bob, current_time)
            packets.append(pkt)
            
        # Reading time (3-15 seconds)
        current_time += random.uniform(3, 15)
        
    wrpcap(filename, packets)
    print(f"Done. {len(packets)} packets. (Bob traffic only)")

def generate_anomalous_traffic(filename="anomaly.pcap", duration=3600):
    # Ensure min duration for scenario logic
    if duration < 2400: duration = 2400 # Min 40 mins
    
    print(f"Generating ANOMALY traffic (Bob + Hacker) to {filename} ({duration}s)...")
    print(f"Generating ANOMALY traffic (Bob + Hacker) to {filename} ({duration}s)...")
    packets = []
    # Virtual Time
    start_time = time.time()
    current_time = start_time
    end_time = start_time + duration
    
    # 1. Schedule Attacks
    # 3-4 attacks total
    num_attacks = random.randint(3, 4)
    # Distribute them within the duration (avoiding first/last 5 mins)
    valid_window_start = start_time + 300
    valid_window_end = end_time - 300
    
    attack_starts = sorted([random.uniform(valid_window_start, valid_window_end) for _ in range(num_attacks)])
    attacks = []
    types = ["DDoS", "SessionHijacking", "DDoS"] # Weighted mix
    
    for start in attack_starts:
        a_type = random.choice(types)
        # Attack lasts 2-3 minutes
        a_duration = random.randint(120, 180) 
        attacks.append({
            "start": start,
            "end": start + a_duration,
            "type": a_type,
            "ip": f"10.66.6.{random.randint(10, 200)}" # Hacker IP
        })
        print(f"  -> Scheduled {a_type} at T+{int(start-start_time)}s (Duration {a_duration}s) from {attacks[-1]['ip']}")

    # Bob's Schedule
    next_move_time = current_time + random.randint(600, 900)
    locations = ["Cafe", "Theater", "Park", "Friend's House"]

    # Hacker State
    active_attacks = []

    while current_time < end_time:
        # A. Bob's Normal Life (Background)
        if current_time > next_move_time:
            bob.rotate_ip(random.choice(locations))
            next_move_time = current_time + random.randint(600, 900)
        
        # Bob browsing
        burst = random.randint(3, 12)
        for _ in range(burst):
            current_time += random.uniform(0.1, 0.8)
            pkt = generate_packet(bob, current_time)
            packets.append(pkt)
        
        # B. Hacker Intervention
        # Check if we are in any attack window
        for attack in attacks:
            if attack["start"] <= current_time <= attack["end"]:
                # Execute Attack Logic
                
                if attack["type"] == "DDoS":
                    # High Rate Check
                    # Generate many packets in this small time slice
                    # DDoS: ~50-100 packets per second logic, but integrated into this loop
                    # We inject a burst right now
                    ddos_burst = random.randint(10, 20)
                    for _ in range(ddos_burst):
                        # Slight time increment for ddos packets
                        pkttime = current_time + random.uniform(0.001, 0.05)
                        # Hacker Profile (Dynamic)
                        hacker_prof = UserProfile("Hacker", attack["ip"], "none") 
                        pkt = generate_packet(hacker_prof, pkttime, payload_mult=5)
                        packets.append(pkt)
                        
                elif attack["type"] == "SessionHijacking":
                    # Hijacking: Hacker IP uses BOB'S Cookie
                    # Moderate rate, looking like normal usage but from wrong IP
                    hijack_burst = random.randint(2, 5)
                    for _ in range(hijack_burst):
                        pkttime = current_time + random.uniform(0.1, 0.5)
                        hacker_prof = UserProfile("Hacker", attack["ip"], bob.cookies) # Stolen Cookie!
                        pkt = generate_packet(hacker_prof, pkttime)
                        packets.append(pkt)

        # C. Time Passage
        # Normal reading time
        current_time += random.uniform(3, 15)

    # Sort packets by time (since we injected attacks slightly out of order/parallel)
    packets.sort(key=lambda x: x.time)
    
    wrpcap(filename, packets)
    print(f"Done. {len(packets)} packets. Generated {num_attacks} attacks.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python traffic_gen.py [normal|anomaly] [duration_seconds]")
        sys.exit(1)
        
    mode = sys.argv[1]
    duration = 1200
    if len(sys.argv) > 2:
        duration = int(sys.argv[2])

    if mode == "normal":
        generate_normal_traffic(duration=duration)
    elif mode == "anomaly":
        generate_anomalous_traffic(duration=duration)
    else:
        print("Unknown mode")
