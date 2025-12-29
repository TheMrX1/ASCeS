import logging
from scapy.all import rdpcap, PcapReader
from typing import Callable
import time

logger = logging.getLogger(__name__)

class PcapCapture:
    def __init__(self, pcap_path: str):
        self.pcap_path = pcap_path

    def process(self, callback: Callable[[Any], None], realtime: bool = False):
        """
        Read packets from PCAP and pass to callback.
        
        Args:
            callback: Function to call for each packet.
            realtime: If True, try to mimic packet timing (approximate).
        """
        logger.info(f"Reading PCAP: {self.pcap_path}")
        
        try:
            # Use PcapReader for streaming large files
            with PcapReader(self.pcap_path) as pcap:
                first_ts = None
                start_time = time.time()
                
                for pkt in pcap:
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
        
        logger.info("PCAP processing finished")
