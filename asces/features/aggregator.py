import time
from collections import deque
from typing import Dict, List, Deque
from scapy.all import Packet
from .extractors import FeatureExtractor

class WindowAggregator:
    """
    Aggregates packets into time windows and extracts features.
    Maintains a history of feature values for Hurst calculation.
    """
    def __init__(self, window_sizes: List[int]):
        self.window_sizes = sorted(window_sizes)
        # Buffers for current incomplete windows: {window_size: [packets]}
        self.current_buffers: Dict[int, List[Packet]] = {w: [] for w in self.window_sizes}
        # Start times for current windows (initialized on first packet)
        self.window_starts: Dict[int, float] = {w: None for w in self.window_sizes}
        
        # History of features: {window_size: {feature_name: deque([values])}}
        # We need enough history to calculate Hurst. 
        # For R/S with min chunk 8 and max chunk N/2, we need decent N. Say 128 points minimum.
        self.history_size = 256 
        self.history: Dict[int, Dict[str, Deque[float]]] = {
            w: {} for w in self.window_sizes
        }

    def add_packet(self, packet: Packet, timestamp: float):
        """Add a packet and check if any windows have closed."""
        results = [] # List of (window_size, feature_dict, metadata_dict)
        
        for w in self.window_sizes:
            if self.window_starts[w] is None:
                self.window_starts[w] = timestamp

            # If timestamp goes backward (restarts) or jumps too far, reset?
            # For now assume monotonic increasing timestamp from source.
            
            if timestamp - self.window_starts[w] >= w:
                # Window closed
                
                features = FeatureExtractor.extract(self.current_buffers[w])
                
                # Metadata Extraction: Unique IPs, Cookies
                meta = {
                    "ips": list(set(p[1].src for p in self.current_buffers[w] if p.haslayer("IP"))),
                    "cookies": [],
                    "start_time": self.window_starts[w],
                    "end_time": timestamp
                }
                
                # Extract Cookies (Raw payload search)
                # Very basic parsing for demo
                seen_cookies = set()
                for p in self.current_buffers[w]:
                    if p.haslayer("Raw"):
                        try:
                            payload = p["Raw"].load.decode('utf-8', errors='ignore')
                            if "Cookie: session=" in payload:
                                # Extract simple value
                                part = payload.split("Cookie: session=")[1].split("\r\n")[0]
                                seen_cookies.add(part)
                        except:
                             pass
                meta["cookies"] = list(seen_cookies)

                self._update_history(w, features)
                results.append((w, features, meta))
                
                # Reset window
                self.current_buffers[w] = []
                self.window_starts[w] += w
                
                # Check for skipped windows
                while timestamp - self.window_starts[w] >= w:
                     self.window_starts[w] += w
            
            # Add packet to current buffer
            self.current_buffers[w].append(packet)
            
        return results

    def _update_history(self, window_size: int, features: Dict[str, float]):
        if not self.history[window_size]:
            # Initialize deques for each feature
            for k in features.keys():
                self.history[window_size][k] = deque(maxlen=self.history_size)
        
        for k, v in features.items():
            self.history[window_size][k].append(v)

    def get_series(self, window_size: int, feature_name: str) -> List[float]:
        if feature_name in self.history[window_size]:
            return list(self.history[window_size][feature_name])
        return []
