import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class BaselineStorage:
    def __init__(self, baselines_dir: str):
        self.baselines_dir = baselines_dir
        if not os.path.exists(baselines_dir):
            os.makedirs(baselines_dir)

    def save(self, baseline_data: Dict[str, Any], name: str = "default"):
        """Save baseline to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"baseline_{name}_{timestamp}.json"
        path = os.path.join(self.baselines_dir, filename)
        
        # Add metadata
        data = {
            "metadata": {
                "created_at": timestamp,
                "name": name,
                "version": "1.0"
            },
            "data": baseline_data
        }
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        
        # Update 'latest' symlink or pointer
        latest_path = os.path.join(self.baselines_dir, "latest.json")
        with open(latest_path, "w") as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Baseline saved to {path}")

    def load_latest(self) -> Dict[str, Any] | None:
        """Load the latest baseline."""
        path = os.path.join(self.baselines_dir, "latest.json")
        if not os.path.exists(path):
            logger.warning("No baseline found.")
            return None
            
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return data.get("data")
        except Exception as e:
            logger.error(f"Failed to load baseline: {e}")
            return None
