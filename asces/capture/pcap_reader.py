import logging
from scapy.all import rdpcap, PcapReader
from typing import Callable, Any
import time
import sys

logger = logging.getLogger(__name__)

class PcapCapture:
    def __init__(self, pcap_path: str):
        self.pcap_path = pcap_path

    def _count_packets(self) -> int:
        """Pre-count packets for progress bar."""
        count = 0
        try:
            with PcapReader(self.pcap_path) as pcap:
                for _ in pcap:
                    count += 1
        except Exception:
            pass
        return count

    def process(self, callback: Callable[[Any], None], realtime: bool = False):
        """
        Read packets from PCAP and pass to callback.
        
        Args:
            callback: Function to call for each packet.
            realtime: If True, try to mimic packet timing (approximate).
        """
        logger.info(f"Reading PCAP: {self.pcap_path}")
        
        # Pre-count for progress bar
        total_packets = self._count_packets()
        logger.info(f"Total packets to process: {total_packets}")
        
        try:
            with PcapReader(self.pcap_path) as pcap:
                first_ts = None
                start_time = time.time()
                
                count = 0
                for pkt in pcap:
                    count += 1
                    
                    # Progress Bar (every 100 packets)
                    if count % 100 == 0 or count == total_packets:
                        progress = (count / total_packets) * 100 if total_packets > 0 else 100
                        bar_len = 30
                        filled = int(bar_len * count / total_packets) if total_packets > 0 else bar_len
                        bar = '█' * filled + '░' * (bar_len - filled)
                        sys.stdout.write(f"\r[{bar}] {progress:.1f}% ({count}/{total_packets})")
                        sys.stdout.flush()

                    if realtime:
                        if first_ts is None:
                            first_ts = float(pkt.time)
                        
                        target_delay = float(pkt.time) - first_ts
                        elapsed = time.time() - start_time
                        
                        if target_delay > elapsed:
                            time.sleep(target_delay - elapsed)
                            
                    callback(pkt)
                    
        except Exception as e:
            logger.error(f"Error reading PCAP: {e}")
            raise
        
        print() # Newline after progress bar
        logger.info("PCAP processing finished")
