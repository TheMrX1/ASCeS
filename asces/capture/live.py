import logging
from scapy.all import sniff, Packet
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class LiveCapture:
    def __init__(self, interface: str, bpf_filter: str = "ip"):
        self.interface = interface
        self.bpf_filter = bpf_filter
        self.running = False

    def start(self, callback: Callable[[Packet], None], stop_event=None):
        """
        Start capturing packets.
        
        Args:
            callback: Function to call for each packet.
            stop_event: Optional threading.Event to stop capture.
        """
        logger.info(f"Starting live capture on {self.interface} with filter '{self.bpf_filter}'")
        self.running = True
        
        def stop_filter(_):
            if stop_event and stop_event.is_set():
                return True
            return False

        try:
            sniff(
                iface=self.interface,
                filter=self.bpf_filter,
                prn=callback,
                store=False,
                stop_filter=stop_filter
            )
        except Exception as e:
            logger.error(f"Capture failed: {e}")
            raise
        finally:
            self.running = False
            logger.info("Live capture stopped")
