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
    """
    Generates anomaly traffic where:
    - Bob's behavior is MATHEMATICALLY IDENTICAL to training (normal) mode.
    - All anomalies come ONLY from the Hacker.
    - WARN = Hacker Probe (Smaller burst, not full attack)
    - CRIT = Hacker Full Attack (DDoS or Session Hijacking)
    """
    if duration < 2400: duration = 2400
    
    locations = ["Cafe", "Theater", "Park", "Friend's House"]
    
    # Event Counts
    total_events = random.randint(150, 200)
    crit_ratio = random.uniform(0.25, 0.33)
    target_crits = int(total_events * crit_ratio)
    target_warns = total_events - target_crits
    
    print(f"Generating ANOMALY traffic (Bob + Hacker) to {filename} ({duration}s)...")
    print(f"Targets: Total={total_events}, CRIT={target_crits}, WARN={target_warns}")

    packets = []
    start_time = time.time()
    end_time = start_time + duration
    
    # ------------------------------------------------------------------
    # 1. BOB'S TRAFFIC (IDENTICAL TO NORMAL MODE)
    # ------------------------------------------------------------------
    # Exact same parameters as generate_normal_traffic():
    # - burst = 3-12 packets
    # - inter-packet delay = 0.1-0.8s
    # - reading time = 3-15s
    # - IP rotation every 600-900s
    # ------------------------------------------------------------------
    current_time = start_time
    next_move_time = current_time + random.randint(600, 900)
    
    # Pre-randomize Bob's IP like in normal mode
    bob.rotate_ip("Session Start")
    
    while current_time < end_time:
        if current_time > next_move_time:
            bob.rotate_ip(random.choice(locations))
            next_move_time = current_time + random.randint(600, 900)
        
        # EXACT SAME burst logic as normal traffic
        burst = random.randint(3, 12)
        for _ in range(burst):
            current_time += random.uniform(0.1, 0.8)
            pkt = generate_packet(bob, current_time)
            packets.append(pkt)
        
        # EXACT SAME reading time as normal traffic
        current_time += random.uniform(3, 15)
        
    # ------------------------------------------------------------------
    # 2. HACKER'S TRAFFIC (ALL ANOMALIES)
    # ------------------------------------------------------------------
    # Hacker generates all WARN and CRIT events.
    # WARN = "Probe" (Smaller burst, testing defenses)
    # CRIT = "Full Attack" (DDoS or Session Hijacking)
    # ------------------------------------------------------------------
    
    # Hacker has multiple IPs across different attack windows
    hacker_ips = [f"10.66.6.{random.randint(10, 200)}" for _ in range(5)]
    
    # Schedule CRIT attack windows (3 distinct windows)
    num_crit_windows = 3
    valid_start = start_time + 300
    valid_end = end_time - 300
    
    crit_window_starts = sorted([random.uniform(valid_start, valid_end) for _ in range(num_crit_windows)])
    crit_windows = []
    attack_types = ["DDoS", "SessionHijacking", "DDoS"]
    crits_per_window = target_crits // num_crit_windows
    
    for i, ws in enumerate(crit_window_starts):
        atype = attack_types[i % len(attack_types)]
        cookie = "hacker_token_666" if atype != "SessionHijacking" else bob.cookies
        crit_windows.append({
            "start": ws,
            "end": ws + 180, # 3 minutes
            "type": atype,
            "ip": random.choice(hacker_ips),
            "cookie": cookie,
            "events": crits_per_window if i < num_crit_windows - 1 else (target_crits - crits_per_window * (num_crit_windows - 1))
        })
        print(f"  -> CRIT Window: {atype} at T+{int(ws-start_time)}s ({crit_windows[-1]['events']} events)")
    
    # Generate CRIT events (DDoS/Hijacking Bursts)
    for cw in crit_windows:
        for _ in range(cw["events"]):
            event_time = random.uniform(cw["start"], cw["end"])
            hacker = UserProfile("Hacker", cw["ip"], cw["cookie"])
            
            # Heavy Burst (80-150 packets in 0.05s - DDoS style)
            burst = random.randint(80, 150)
            for _ in range(burst):
                pkt_time = event_time + random.uniform(0, 0.05)
                pkt = generate_packet(hacker, pkt_time)
                packets.append(pkt)
    
    # Schedule WARN events (Hacker Probes - distributed across the timeline, avoiding CRIT windows)
    warn_times = []
    while len(warn_times) < target_warns:
        t = random.uniform(start_time, end_time)
        # Avoid CRIT windows
        in_crit = any(cw["start"] <= t <= cw["end"] for cw in crit_windows)
        if not in_crit:
            warn_times.append(t)
    
    for wt in warn_times:
        hacker = UserProfile("Hacker", random.choice(hacker_ips), "hacker_probe_token")
        # Smaller Probe Burst (15-30 packets in 0.2s)
        burst = random.randint(15, 30)
        for _ in range(burst):
            pkt_time = wt + random.uniform(0, 0.2)
            pkt = generate_packet(hacker, pkt_time)
            packets.append(pkt)
    
    # Sort all packets chronologically
    packets.sort(key=lambda x: x.time)
    
    wrpcap(filename, packets)
    print(f"Done. {len(packets)} packets. WARN={target_warns} (Hacker Probes), CRIT={target_crits} (Full Attacks)")

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
