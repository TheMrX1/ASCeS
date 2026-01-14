import time
import random
import sys
from scapy.all import wrpcap, IP, TCP, UDP, Ether, Raw

# ----- Configuration & Profiles -----

class UserProfile:
    def __init__(self, name, base_ip, cookies, behavior_type="normal"):
        self.name = name
        self.base_ip = base_ip
        self.current_ip = base_ip
        self.cookies = cookies
        self.behavior_type = behavior_type # normal, attacker
        self.requests_made = 0

    def rotate_ip(self):
        # Simulate moving to a coffee shop or VPN
        octets = self.base_ip.split('.')
        new_octet = int(octets[3]) + random.randint(1, 20)
        self.current_ip = f"{octets[0]}.{octets[1]}.{octets[2]}.{new_octet}"
        print(f"[{self.name}] Rotated IP to {self.current_ip}")

    def get_headers(self):
        return f"GET /api/resource HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0 ({self.name})\r\nCookie: session={self.cookies}\r\n\r\n"

# Define Users
users = [
    UserProfile("Alice", "192.168.1.100", "alice_session_id_12345"),
    UserProfile("Bob", "192.168.1.101", "bob_session_id_67890"),
    UserProfile("Charlie", "192.168.1.102", "charlie_session_id_abcde"),
]

# Define Attackers
attackers = [
    UserProfile("Attacker1", "192.168.1.166", "hacker_session_x"),
    UserProfile("Attacker2", "192.168.1.167", "hacker_session_y"),
    UserProfile("Attacker3 (Bot)", "192.168.1.168", "bottoken_z", "bot"),
]


def generate_packet(profile, timestamp, dst_ip="192.168.1.20", payload_mult=1):
    payload = profile.get_headers() + ("X" * (50 * payload_mult))
    pkt = Ether(src=f"00:11:22:33:44:{random.randint(10,99)}", dst="ff:ff:ff:ff:ff:ff") / \
          IP(src=profile.current_ip, dst=dst_ip) / \
          TCP(sport=random.randint(10000, 60000), dport=80, flags="PA") / \
          Raw(load=payload)
    pkt.time = timestamp
    return pkt

def generate_normal_traffic(filename="normal.pcap", duration=300):
    print(f"Generating realistic NORMAL traffic to {filename} ({duration}s)...")
    packets = []
    start_time = time.time()
    current_time = start_time
    
    while current_time - start_time < duration:
        # Simulate normal user browsing
        # Choose a random user
        user = random.choice(users)
        
        # IP Rotation Chance (very low in normal)
        if random.random() < 0.001: 
            user.rotate_ip()
            
        # Requests come in small bursts (page load)
        burst = random.randint(2, 8)
        for _ in range(burst):
            current_time += random.expovariate(2.0) # Avg 0.5s between resources
            pkt = generate_packet(user, current_time)
            packets.append(pkt)
            
        # Think time between pages (Simulating a busier network with multiple active users)
        current_time += random.uniform(0.1, 0.5) # Avg 0.3s gap between user actions
        
    wrpcap(filename, packets)
    print(f"Done. {len(packets)} packets.")

def generate_anomalous_traffic(filename="anomaly.pcap", duration=300):
    if duration < 60: duration = 60
    print(f"Generating realistic ANOMALY mixed traffic to {filename} ({duration}s)...")
    packets = []
    start_time = time.time()
    current_time = start_time
    
    # State tracking
    anomaly_active = False
    
    while current_time - start_time < duration:
        # 1. Background Normal Traffic (Always happening)
        # ---------------------------------------------
        if random.random() < 0.7:
            user = random.choice(users)
            current_time += random.uniform(0.01, 0.1) # Background hum
            pkt = generate_packet(user, current_time)
            packets.append(pkt)
        
        # 2. STRANGE Traffic (WARN) - Occasional
        # ---------------------------------------------
        # One of the "Normal" users acting weirdly (e.g., high rate for a moment)
        # Bob decides to download rapidly?
        if random.random() < 0.05: # 5% chance of strange event
            target = users[1] # Bob
            # print(f"STRANGE event by {target.name}")
            for _ in range(random.randint(20, 40)):
                current_time += 0.05
                pkt = generate_packet(target, current_time, payload_mult=10) # Larger payload
                packets.append(pkt)
                
        # 3. CRIT Traffic - Attackers
        # ---------------------------------------------
        if random.random() < 0.02: # 2% chance of attack burst
            attacker = random.choice(attackers)
            # print(f"CRIT Attack by {attacker.name}")
            burst_len = random.randint(50, 150)
            
            # Attacker might rotate IP mid-attack
            if random.random() < 0.3: attacker.rotate_ip()
                
            for _ in range(burst_len):
                current_time += 0.005 # Fast spam
                pkt = generate_packet(attacker, current_time, payload_mult=5)
                packets.append(pkt)

        # Advance time slightly if nothing happened to avoid stuck loop
        current_time += 0.001

    wrpcap(filename, packets)
    print(f"Done. {len(packets)} packets over {current_time - start_time:.2f}s.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python traffic_gen.py [normal|anomaly] [duration_seconds]")
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
