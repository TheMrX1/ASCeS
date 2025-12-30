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
        results = [] # List of (window_size, feature_dict)
        
        for w in self.window_sizes:
            if self.window_starts[w] is None:
                self.window_starts[w] = timestamp
                # Debug log for first timestamp
                # print(f"DEBUG: Window {w} initialized at {timestamp}")

            # If timestamp goes backward (restarts) or jumps too far, reset?
            # For now assume monotonic increasing timestamp from source.
            
            if timestamp - self.window_starts[w] >= w:
                # Window closed
                # FORCE LOGGING
                print(f"DEBUG: Window {w} CLOSED at {timestamp:.4f} (Start: {self.window_starts[w]:.4f})")
                
                features = FeatureExtractor.extract(self.current_buffers[w])
                self._update_history(w, features)
                results.append((w, features))
                
                # Reset window
                self.current_buffers[w] = []
                # Align next window start to the end of previous window, or current packet time?
                # Ideally: next_start = prev_start + w. 
                # This keeps alignment.
                self.window_starts[w] += w
                
                # Handle case where we skipped multiple windows (empty data)
                while timestamp - self.window_starts[w] >= w:
                     # Fill empty windows with zeros?
                     # For now, just skip to current time to catch up
                     self.window_starts[w] = timestamp
            
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
