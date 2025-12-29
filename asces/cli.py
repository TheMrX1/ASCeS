import typer
import logging
import time
import uvicorn
import threading
from typing import Optional
from .config import load_config, setup_logging
from .capture import LiveCapture, PcapCapture
from .features import WindowAggregator
from .baseline import Trainer, BaselineStorage
from .detect import Detector
from .storage import Database, AlertRepo

app = typer.Typer(help="ASCeS - Adaptive Session Control System")

@app.command()
def train(
    iface: Optional[str] = typer.Option(None, help="Network interface"),
    pcap: Optional[str] = typer.Option(None, help="PCAP file path"),
    duration: int = typer.Option(None, help="Duration in seconds")
):
    """Train the baseline model."""
    config = load_config()
    setup_logging(config)
    
    if duration:
        config.train_duration_seconds = duration
    
    logger = logging.getLogger("asces.train")
    logger.info("Starting training mode...")
    
    aggregator = WindowAggregator(config.windows)
    
    def packet_callback(pkt):
        aggregator.add_packet(pkt, time.time())

    # Source selection
    if pcap:
        capture = PcapCapture(pcap)
        # For training on PCAP, we might want to process it faster than realtime?
        # But aggregator relies on time.time(). 
        # Ideally we should mock time in aggregator for PCAP.
        # For now, let's assume realtime replay or we need to refactor aggregator to accept timestamp.
        # Aggregator.add_packet accepts timestamp. PcapCapture needs to pass packet time.
        # But PcapCapture.process passes just pkt.
        # Let's adjust callback to extract time from pkt if available.
        capture.process(lambda p: aggregator.add_packet(p, float(p.time)), realtime=False)
    else:
        interface = iface or config.interface
        capture = LiveCapture(interface, config.bpf_filter)
        
        # Run capture in a thread or just blocking if we use a stop timer
        stop_event = threading.Event()
        t = threading.Thread(target=capture.start, args=(lambda p: aggregator.add_packet(p, time.time()), stop_event))
        t.start()
        
        try:
            time.sleep(config.train_duration_seconds)
        except KeyboardInterrupt:
            pass
        finally:
            stop_event.set()
            t.join()

    logger.info("Computing baseline...")
    trainer = Trainer(aggregator, config.hurst_methods)
    baseline_data = trainer.compute_baseline()
    
    storage = BaselineStorage(config.baselines_dir)
    storage.save(baseline_data, name="manual_train")
    logger.info("Training complete.")

@app.command()
def monitor(
    iface: Optional[str] = typer.Option(None, help="Network interface"),
    pcap: Optional[str] = typer.Option(None, help="PCAP file path")
):
    """Start monitoring for anomalies."""
    config = load_config()
    setup_logging(config)
    
    logger = logging.getLogger("asces.monitor")
    
    # Load baseline
    bs_storage = BaselineStorage(config.baselines_dir)
    baseline = bs_storage.load_latest()
    if not baseline:
        logger.error("No baseline found. Run 'train' first.")
        raise typer.Exit(code=1)
        
    # Init DB
    db = Database(config.db_path)
    db.init_db()
    
    aggregator = WindowAggregator(config.windows)
    detector = Detector(aggregator, baseline, AlertRepo(db.get_session()), config)
    
    # Hook detector into aggregator? 
    # Aggregator returns results when add_packet is called?
    # No, add_packet returns list of closed windows.
    
    def packet_callback(pkt, ts):
        closed_windows = aggregator.add_packet(pkt, ts)
        for win_size, features in closed_windows:
            detector.check_window(win_size, features)

    logger.info("Starting monitor mode...")
    
    if pcap:
        capture = PcapCapture(pcap)
        capture.process(lambda p: packet_callback(p, float(p.time)), realtime=True)
    else:
        interface = iface or config.interface
        capture = LiveCapture(interface, config.bpf_filter)
        capture.start(lambda p: packet_callback(p, time.time()))

@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000
):
    """Start the Web API/UI server."""
    config = load_config()
    # Ensure DB is init
    Database(config.db_path).init_db()
    
    uvicorn.run("asces.api.app:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    app()
