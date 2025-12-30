import logging
import numpy as np
from typing import Dict, List, Any
from ..features.aggregator import WindowAggregator
from ..hurst import compute_hurst_rs, compute_hurst_dfa

logger = logging.getLogger(__name__)

class Trainer:
    def __init__(self, aggregator: WindowAggregator, hurst_methods: List[str]):
        self.aggregator = aggregator
        self.hurst_methods = hurst_methods
        
    def compute_baseline(self) -> Dict[str, Any]:
        """
        Compute baseline statistics (mean H, std H) for all windows/features.
        Should be called after feeding data to aggregator.
        """
        baseline = {}
        
        for window_size in self.aggregator.window_sizes:
            baseline[str(window_size)] = {}
            
            # Get all features tracked
            # We assume at least one window has triggered to populate keys, 
            # or we iterate known features if config provided.
            # Here we check what's in history.
            features = self.aggregator.history[window_size].keys()
            
            for feature in features:
                series = self.aggregator.get_series(window_size, feature)
                if not series:
                    continue
                
                # We need to compute H over moving windows of this series?
                # Actually, the requirement says: "collect benchmarks... mean_H, std_H".
                # To get mean_H, we need multiple H values.
                # So we should split the gathered series into chunks and compute H for each chunk?
                # OR does it mean H of the whole series?
                # "On the 'training' stage... collect standards... mean_H, std_H".
                # This implies we calculate H repeatedly.
                
                # Let's implement a sliding window over the series to get a distribution of H values.
                # If the series is length L, we can take sub-windows.
                # However, H requires a decent length.
                # If we trained for 4 minutes, and window=5s, we have ~48 points.
                # That's barely enough for one H calc.
                # If window=1s, we have 240 points.
                
                # Strategy:
                # If series is long enough, compute H on the whole thing and store it as the "mean" with std=0 (or small epsilon).
                # Ideally, we'd have enough data to compute multiple Hs.
                # For this prototype, if data is short, we compute one H.
                # If data is long, we can split it.
                
                h_values = {m: [] for m in self.hurst_methods}
                
                # Let's try to get at least a few samples if possible.
                # Minimum size for H is ~50-100 points.
                series_len = len(series)
                min_h_len = 4
                
                if series_len < min_h_len:
                    logger.warning(f"Insufficient data for baseline: window={window_size}, feature={feature}, len={series_len}")
                    continue
                
                # We will compute H on the full series for accuracy in this version,
                # as splitting 4 mins of data into smaller chunks for H calc might be too noisy.
                # But to get std_H, we need variation.
                # Let's use a rolling window if possible, or just split in half.
                
                # Simple approach: Compute H on the whole series. Set std_H to a default heuristic or 0.1.
                # Better approach: Bootstrapping or overlapping windows.
                
                # Let's use overlapping windows of size min_h_len with step 10.
                # print(f"DEBUG: Trainer processing {feature} window={window_size} len={series_len}")

                # Use overlapping windows of reasonable size for H calculation
                h_window_size = 64
                if series_len < h_window_size:
                    # If series is short but > min_h_len, use whole series as one chunk
                    h_window_size = series_len

                step = 10
                for i in range(0, series_len - h_window_size + 1, step):
                    sub_series = list(series)[i : i + h_window_size]
                    
                    if "rs" in self.hurst_methods:
                        h = compute_hurst_rs(sub_series)
                        if h is not None: 
                            h_values["rs"].append(h)
                        # else:
                            # print(f"DEBUG: RS failed for {feature} chunk len {len(sub_series)}")
                        
                    if "dfa" in self.hurst_methods:
                        h = compute_hurst_dfa(sub_series)
                        if h is not None: 
                            h_values["dfa"].append(h)
                        # else:
                            # print(f"DEBUG: DFA failed for {feature} chunk len {len(sub_series)}")
                
                # Aggregate
                feat_stats = {}
                for method, vals in h_values.items():
                    if vals:
                        feat_stats[method] = {
                            "mean": float(np.mean(vals)),
                            "std": float(np.std(vals)) if len(vals) > 1 else 0.05,
                            "count": len(vals)
                        }
                        # print(f"DEBUG: Trainer computed {feature} {method}: {feat_stats[method]}")
                    else:
                        # Fallback if we couldn't compute H (e.g. flat line)
                        feat_stats[method] = None
                        # print(f"DEBUG: Trainer produced None for {feature} {method} (Inputs: {len(vals)} chunks)")
                
                baseline[str(window_size)][feature] = feat_stats
                
        return baseline
