import numpy as np
import logging

logger = logging.getLogger(__name__)

def compute_hurst_dfa(series: list[float] | np.ndarray, order: int = 1) -> float | None:
    """
    Compute the Hurst exponent using Detrended Fluctuation Analysis (DFA).
    
    Args:
        series: A time series.
        order: Order of the polynomial trend to remove (1 = linear).
        
    Returns:
        float: The estimated Hurst exponent, or None.
    """
    series = np.array(series)
    N = len(series)
    if N < 3: # Relaxed
        return None
        
    if np.std(series) == 0:
        return None

    # 1. Integrate the series (cumulative sum minus mean)
    y = np.cumsum(series - np.mean(series))
    
    # 2. Define scales (window sizes)
    min_scale = 2 # Relaxed
    max_scale = N // 2 # Increased range
    if max_scale < min_scale:
        return None
        
    scales = np.unique(np.logspace(np.log10(min_scale), np.log10(max_scale), num=10).astype(int))
    
    fluctuations = []
    valid_scales = []
    
    for scale in scales:
        # Split into segments
        n_segments = N // scale
        if n_segments < 1:
            continue
            
        rms = []
        for i in range(n_segments):
            seg = y[i*scale : (i+1)*scale]
            x = np.arange(scale)
            
            # Fit polynomial
            try:
                coeffs = np.polyfit(x, seg, order)
                trend = np.polyval(coeffs, x)
                
                # RMS fluctuation
                rms_val = np.sqrt(np.mean((seg - trend)**2))
                rms.append(rms_val)
            except Exception:
                continue
                
        if rms:
            f_n = np.mean(rms)
            if f_n > 0:
                fluctuations.append(f_n)
                valid_scales.append(scale)
                
    if len(valid_scales) < 2: # Relaxed to 2
        return None
        
    # 3. Log-log regression
    try:
        x_log = np.log(valid_scales)
        y_log = np.log(fluctuations)
        H, _ = np.polyfit(x_log, y_log, 1)
        return float(H)
    except Exception as e:
        logger.debug(f"DFA fitting failed: {e}")
        return None
