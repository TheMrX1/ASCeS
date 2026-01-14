import yaml
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import logging

class AscesConfig(BaseModel):
    interface: str = "eth0"
    bpf_filter: str = "ip"
    windows: List[int] = [5, 15, 60, 120]
    features_enabled: List[str] = Field(default_factory=list)
    hurst_methods: List[str] = ["rs", "dfa"]
    train_duration_seconds: int = 240
    z_threshold: float = 3.0
    cooldown_seconds: int = 1
    db_path: str = "data/asces.db"
    baselines_dir: str = "data/baselines"
    log_path: str = "logs/asces.log"

def load_config(path: str = "config.yaml") -> AscesConfig:
    """Load configuration from a YAML file."""
    if not os.path.exists(path):
        # Fallback to example config if main config doesn't exist, or defaults
        example_path = "configs/config.example.yaml"
        if os.path.exists(example_path):
            logging.warning(f"Config file {path} not found. Loading {example_path}")
            path = example_path
        else:
            logging.warning(f"Config file {path} not found. Using defaults.")
            return AscesConfig()

    with open(path, "r") as f:
        data = yaml.safe_load(f)
    
    return AscesConfig(**data)

def setup_logging(config: AscesConfig):
    """Configure logging."""
    log_dir = os.path.dirname(config.log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(config.log_path),
            logging.StreamHandler()
        ]
    )
