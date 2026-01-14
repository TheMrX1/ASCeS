import logging
import time
import numpy as np
from typing import Dict, Any, List
from ..hurst import compute_hurst_rs, compute_hurst_dfa
from ..features.aggregator import WindowAggregator
from ..storage.repo import AlertRepo

logger = logging.getLogger(__name__)

class Detector:
    def __init__(self, 
                 aggregator: WindowAggregator, 
                 baseline: Dict[str, Any], 
                 alert_repo: AlertRepo,
                 config: Any):
        self.aggregator = aggregator
        self.baseline = baseline
        self.alert_repo = alert_repo
        self.config = config
        self.last_alert_time: Dict[str, float] = {} # Key: "window:feature:method"

    def check_window(self, window_size: int, features: Dict[str, float], metadata: Dict[str, Any] = None):
        """
        Called when a window closes. Calculates H for recent history and compares to baseline.
        """
        if str(window_size) not in self.baseline:
            # print(f"DEBUG: Window {window_size} not in baseline keys: {list(self.baseline.keys())}")
            return

        # We need the series history to compute current H
        # Use a reasonable history length for H calculation (e.g., 64)
        min_h_len = 4
        max_h_history = 64
        
        for feature_name in features.keys():
            series = self.aggregator.get_series(window_size, feature_name)
            if len(series) < min_h_len:
                # print(f"DEBUG: Series too short for {feature_name}: {len(series)} < {min_h_len}")
                continue
                
            # Take the most recent chunk, up to max_history
            recent_series = list(series)[-max_h_history:]
            # print(f"DEBUG: Checking {feature_name} window={window_size} len={len(recent_series)}")
            
            # Check for each method
            for method in self.config.hurst_methods:
                # Get baseline stats
                try:
                    stats = self.baseline[str(window_size)][feature_name][method]
                except (KeyError, TypeError):
                    # print(f"DEBUG: No stats keys for {feature_name} {method}")
                    continue
                    
                if not stats:
                    # print(f"DEBUG: Stats is None/Empty for {feature_name} {method}")
                    continue
                    
                # Compute current H
                current_h = None
                if method == "rs":
                    current_h = compute_hurst_rs(recent_series)
                elif method == "dfa":
                    current_h = compute_hurst_dfa(recent_series)
                    
                if current_h is None:
                    # print(f"DEBUG: H is None for {feature_name} {method} (Std={np.std(recent_series):.4f})")
                    continue
                
                # print(f"DEBUG: Computed H={current_h:.4f} for {feature_name}")
                    
                # Calculate Z-score
                mean_h = stats["mean"]
                std_h = stats["std"]
                if std_h < 0.001: std_h = 0.001 # Avoid div by zero
                
                z_score = (current_h - mean_h) / std_h
                
                if abs(z_score) >= self.config.z_threshold:
                    self._trigger_alert(window_size, feature_name, method, current_h, mean_h, std_h, z_score, metadata)
                else:
                    # Debug log to see values even if no alert
                    logger.info(f"CHECK: {feature_name} (W{window_size}) H={current_h:.3f} Avg={mean_h:.3f} Z={z_score:.2f}")

    def _trigger_alert(self, window, feature, method, h, mean, std, z, metadata: Dict[str, Any] = None):
        key = f"{window}:{feature}:{method}"
        # Use end_time from metadata if available, else current time
        now = time.time()
        if metadata and "end_time" in metadata:
            now = metadata["end_time"]
            
        # Cooldown check
        if key in self.last_alert_time:
            if now - self.last_alert_time[key] < self.config.cooldown_seconds:
                return
                
        self.last_alert_time[key] = now
        
        level = "WARN"
        if abs(z) > 50.0:
            level = "CRIT"
        elif abs(z) < 3.5:
            level = "INFO"
            
        msg = f"Anomaly detected in {feature} (Window {window}s). H={h:.3f} (Baseline: {mean:.3f}±{std:.3f}), Z={z:.2f}"
        
        # Attack Classification Logic
        # Heuristics based on feature type and Z-score magnitude
        attack_type = None
        
        if "packets" in feature or "bytes" in feature:
            if abs(z) > 10.0 and h < mean: # H drop usually means stronger correlation/regularity (like a flood)
                attack_type = "Possible DDoS Attack (High Volume)"
            elif abs(z) > 5.0:
                attack_type = "Suspicious Traffic Surge"
                
        elif "unique_src_ips" in feature:
            if abs(z) > 3.0:
                 # Check metadata for robust confirmation
                 # Hijacking Signature: Multiple IPs sharing one Cookie
                 metadata_confirmed = False
                 if metadata and "cookies" in metadata and "ips" in metadata:
                     unique_cookies = set(metadata["cookies"])
                     unique_ips = set(metadata["ips"])
                     if len(unique_ips) > 1 and len(unique_cookies) == 1:
                         msg += " [CONFIRMED: Multiple IPs using same Cookie]"
                         attack_type = "Session Hijacking (High Confidence)"
                         metadata_confirmed = True
                 
                 if not metadata_confirmed:
                     attack_type = "Possible Session Hijacking / Unauthorized Access"
                 
        elif "unique_dst_ports" in feature or "unique_src_ports" in feature:
             if abs(z) > 5.0:
                 attack_type = "Possible Port Scanning"
                 
        if attack_type:
            msg += f" - [{attack_type}]"
            
        logger.warning(msg)
        
        import json
        meta_json = json.dumps(metadata) if metadata else ""
        
        from datetime import datetime
        alert_time = datetime.fromtimestamp(now)
        
        self.alert_repo.create_alert({
            "timestamp": alert_time,
            "level": level,
            "window_size": window,
            "feature": feature,
            "hurst_method": method,
            "current_h": h,
            "baseline_mean": mean,
            "baseline_std": std,
            "z_score": z,
            "message": msg,
            "assessment": attack_type, # New field
            "metadata_json": meta_json
        })
