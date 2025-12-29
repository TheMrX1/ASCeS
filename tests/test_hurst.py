import pytest
import numpy as np
from asces.hurst import compute_hurst_rs, compute_hurst_dfa

def generate_fbm(H, n):
    """Generate fractional Brownian motion (approximate)"""
    # Simple random walk for H=0.5
    if H == 0.5:
        return np.cumsum(np.random.randn(n))
    # This is a placeholder. Generating real fBm is complex.
    # We'll test with white noise (H ~ 0.5 for accumulated? No, white noise series H ~ 0.5)
    # R/S on white noise -> H=0.5
    return np.random.randn(n)

def test_hurst_rs_white_noise():
    # White noise should have H approx 0.5
    np.random.seed(42)
    series = np.random.randn(1000)
    h = compute_hurst_rs(series)
    assert h is not None
    # R/S on pure white noise is usually close to 0.5
    assert 0.4 < h < 0.6

def test_hurst_dfa_white_noise():
    np.random.seed(42)
    series = np.random.randn(1000)
    h = compute_hurst_dfa(series)
    assert h is not None
    assert 0.4 < h < 0.6

def test_hurst_short_series():
    series = np.random.randn(10)
    assert compute_hurst_rs(series) is None
    assert compute_hurst_dfa(series) is None
