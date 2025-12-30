import numpy as np
import logging

logger = logging.getLogger(__name__)

def compute_hurst_rs(series: list[float] | np.ndarray) -> float | None:
    """
    Compute the Hurst exponent using the Rescaled Range (R/S) analysis.
    
    Args:
        series: A time series (list or numpy array).
        
    Returns:
        float: The estimated Hurst exponent, or None if calculation fails/insufficient data.
    """
    series = np.array(series)
    if len(series) < 3:  # Minimal length check lowered
        return None
    
    # Ensure no zero variance in the whole series to avoid immediate issues
    if np.std(series) == 0:
        return None

    # Log-log plot points
    x_vals = []
    y_vals = []
    
    # Sub-series lengths (powers of 2 or logarithmic spacing)
    # We use a range of divisors
    N = len(series)
    min_chunk = 2 # Lowered from 4
    max_chunk = N // 2
    
    if max_chunk < min_chunk:
        # If N is small (e.g. 4), max=2, min=2. allow equal
        if max_chunk < 2:
            return None

    # Create chunk sizes
    chunk_sizes = np.unique(np.logspace(np.log10(min_chunk), np.log10(max_chunk), num=10).astype(int))
    chunk_sizes = chunk_sizes[chunk_sizes >= 2] # Filter very small chunks

    for n in chunk_sizes:
        # Split into chunks of size n
        num_chunks = N // n
        if num_chunks < 1:
            continue
            
        rs_values = []
        for i in range(num_chunks):
            chunk = series[i*n : (i+1)*n]
            
            mean = np.mean(chunk)
            # Deviations
            y = chunk - mean
            # Cumulative deviations
            z = np.cumsum(y)
            # Range
            R = np.max(z) - np.min(z)
            # Standard deviation
            S = np.std(chunk, ddof=1)
            
            if S == 0:
                continue
                
            rs_values.append(R / S)
        
        if rs_values:
            avg_rs = np.mean(rs_values)
            if avg_rs > 0:
                x_vals.append(np.log(n))
                y_vals.append(np.log(avg_rs))

    if len(x_vals) < 2: # Relaxed from 3 to 2
        return None

    # Linear regression
    try:
        H, _ = np.polyfit(x_vals, y_vals, 1)
        return float(H)
    except Exception as e:
        logger.debug(f"R/S fitting failed: {e}")
        return None
