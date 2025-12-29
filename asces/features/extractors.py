from typing import Dict, Any, List
from scapy.all import Packet, IP, TCP, UDP, ICMP

class FeatureExtractor:
    """Extracts features from a list of packets."""
    
    @staticmethod
    def extract(packets: List[Packet]) -> Dict[str, float]:
        if not packets:
            return {
                "packets_per_window": 0,
                "bytes_per_window": 0,
                "unique_src_ips": 0,
                "unique_dst_ips": 0,
                "unique_src_ports": 0,
                "unique_dst_ports": 0,
                "tcp_ratio": 0.0,
                "udp_ratio": 0.0,
                "icmp_ratio": 0.0,
                "mean_packet_size": 0.0,
                "std_packet_size": 0.0
            }

        count = len(packets)
        total_bytes = sum(len(p) for p in packets)
        sizes = [len(p) for p in packets]
        
        src_ips = set()
        dst_ips = set()
        src_ports = set()
        dst_ports = set()
        
        tcp_count = 0
        udp_count = 0
        icmp_count = 0
        
        for p in packets:
            if IP in p:
                src_ips.add(p[IP].src)
                dst_ips.add(p[IP].dst)
                
            if TCP in p:
                tcp_count += 1
                src_ports.add(p[TCP].sport)
                dst_ports.add(p[TCP].dport)
            elif UDP in p:
                udp_count += 1
                src_ports.add(p[UDP].sport)
                dst_ports.add(p[UDP].dport)
            elif ICMP in p:
                icmp_count += 1

        import numpy as np
        
        return {
            "packets_per_window": float(count),
            "bytes_per_window": float(total_bytes),
            "unique_src_ips": float(len(src_ips)),
            "unique_dst_ips": float(len(dst_ips)),
            "unique_src_ports": float(len(src_ports)),
            "unique_dst_ports": float(len(dst_ports)),
            "tcp_ratio": tcp_count / count if count > 0 else 0.0,
            "udp_ratio": udp_count / count if count > 0 else 0.0,
            "icmp_ratio": icmp_count / count if count > 0 else 0.0,
            "mean_packet_size": float(np.mean(sizes)),
            "std_packet_size": float(np.std(sizes))
        }
