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
    
    # -------------------------------------------------------------
    # 1. Target Calculations (Strict Limits)
    # Total events: 150 - 200
    # Crit: 1/4 (25%) to 1/3 (33.3%) of Total
    # Warn: The rest
    # -------------------------------------------------------------
    total_events = random.randint(150, 200)
    crit_ratio = random.uniform(0.25, 0.33)
    target_crits = int(total_events * crit_ratio)
    target_warns = total_events - target_crits
    
    print(f"Generating ANOMALY traffic (Bob + Hacker) to {filename} ({duration}s)...")
    print(f"Targets: Total={total_events}, CRIT={target_crits}, WARN={target_warns}")

    packets = []
    # Virtual Time
    start_time = time.time()
    current_time = start_time
    end_time = start_time + duration
    
    # -------------------------------------------------------------
    # 2. Schedule "Attack Windows" (For CRIT events)
    # -------------------------------------------------------------
    num_attacks = 3 # Fixed 3 distinct attacks windows to hold the CRITs
    valid_window_start = start_time + 300
    valid_window_end = end_time - 300
    
    attack_starts = sorted([random.uniform(valid_window_start, valid_window_end) for _ in range(num_attacks)])
    attack_windows = []
    types = ["DDoS", "SessionHijacking", "DDoS"] 
    
    # We need to squeeze 'target_crits' events into these 3 windows
    crits_per_window = target_crits // num_attacks
    
    for i, start in enumerate(attack_starts):
        a_type = types[i % len(types)]
        a_duration = 180 # 3 minutes fixed
        
        # Cookie logic: Hijacker gets Bob's cookie, DDoS gets generic hacker cookie
        hacker_cookie = "hacker_token_666"
        if a_type == "SessionHijacking":
            hacker_cookie = bob.cookies # STEAL!
            
        attack_windows.append({
            "start": start,
            "end": start + a_duration,
            "type": a_type,
            "ip": f"10.66.6.{random.randint(10, 200)}",
            "cookie": hacker_cookie,
            "events_allocated": crits_per_window if i < num_attacks-1 else (target_crits - (crits_per_window * (num_attacks-1)))
        })
        print(f"  -> Scheduled {a_type} at T+{int(start-start_time)}s ({attack_windows[-1]['events_allocated']} events allocated)")

    # -------------------------------------------------------------
    # 3. Schedule "Background WARNs" (Strange Bob behavior)
    # -------------------------------------------------------------
    # WARNs happen randomly throughout the session, but NOT during attacks to keep signals clear
    warn_timestamps = []
    while len(warn_timestamps) < target_warns:
        ts = start_time + random.uniform(0, duration)
        # Check collision with attacks
        in_attack = False
        for aw in attack_windows:
            if aw["start"] <= ts <= aw["end"]:
                in_attack = True
                break
        if not in_attack:
            warn_timestamps.append(ts)
    warn_timestamps.sort()

    # Sort packets by time (since we injected attacks slightly out of order/parallel)
    
    # NEW LOGIC: Event Queue Processing
    # We pre-calculate ALL timestamps where an event MUST happen.
    # 1. Background Bob: every 0.5s approx
    # 2. WARN Events: Fixed timestamps
    # 3. CRIT Events: Distributed inside Attack Windows
    
    event_queue = [] # (timestamp, type, data)
    
    # A. Bob's Normal Background (Entire Duration)
    t = start_time
    while t < end_time:
       t += random.uniform(0.3, 0.7)
       if t < end_time:
           event_queue.append((t, "NORMAL_BOB", None))
           
    # B. WARN Events
    for w_ts in warn_timestamps:
        event_queue.append((w_ts, "WARN", None))
        
    # C. CRIT Events (Strict Allocation)
    for aw in attack_windows:
        allocated = aw["events_allocated"]
        # Distribute these N events randomly within the window
        for _ in range(allocated):
            # Pick a time inside the window
            # Ensure we don't pick exact same float to avoid sort stability issues, though unlikely
            c_ts = random.uniform(aw["start"], aw["end"])
            event_queue.append((c_ts, "CRIT", aw))
            
    # D. Bob IP Rotation
    # Schedule moves
    move_t = start_time + random.randint(600, 900)
    while move_t < end_time:
        event_queue.append((move_t, "MOVE", None))
        move_t += random.randint(600, 900)
        
    # Sort Queue by Time
    event_queue.sort(key=lambda x: x[0])
    
    # Process Queue
    print(f"Processing {len(event_queue)} scheduled events...")
    
    # Ensure Bob starts with a random IP to avoid "Static IP" look if user runs script multiple times
    bob.rotate_ip("Initial Randomization")
    
    for ts, etype, data in event_queue:
        current_time = ts
        
        if etype == "MOVE":
            bob.rotate_ip(random.choice(locations))
            
        elif etype == "NORMAL_BOB":
            burst = random.randint(2, 5)
            for _ in range(burst):
                # Micro-burst around this timestamp
                pkt_t = ts + random.uniform(0, 0.1)
                pkt = generate_packet(bob, pkt_t)
                packets.append(pkt)
                
        elif etype == "WARN":
            generated_warns += 1
            # Bob behaving badly
            burst = random.randint(40, 60)
            for _ in range(burst):
                pkt_t = ts + random.uniform(0, 0.5) # Spread over 0.5s
                pkt = generate_packet(bob, pkt_t, payload_mult=3)
                packets.append(pkt)
                
        elif etype == "CRIT":
            generated_crits += 1
            # Hacker Attack Burst
            aw = data
            burst = random.randint(80, 150)
            hacker_prof = UserProfile("Hacker", aw["ip"], aw["cookie"])
            
            for _ in range(burst):
                # Super fast burst (DDoS style)
                pkt_t = ts + random.uniform(0, 0.05) 
                pkt = generate_packet(hacker_prof, pkt_t)
                packets.append(pkt)

    packets.sort(key=lambda x: x.time)
    
    wrpcap(filename, packets)
    print(f"Done. {len(packets)} packets. Generated: WARN={generated_warns}, CRIT={generated_crits}")

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
