from typing import Optional

class AnomalyRule:
    """
    Base class for anomaly detection rules.
    """
    def check(self, value: float, baseline_mean: float, baseline_std: float) -> Optional[float]:
        """
        Check if value is anomalous. Returns Z-score if anomalous, None otherwise.
        """
        raise NotImplementedError

class ZScoreRule(AnomalyRule):
    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold

    def check(self, value: float, baseline_mean: float, baseline_std: float) -> Optional[float]:
        if baseline_std < 1e-6:
            # Avoid division by zero, treat as 0 variance
            # If value is different from mean, it's infinite Z
            if abs(value - baseline_mean) > 1e-6:
                return float('inf')
            return 0.0

        z = (value - baseline_mean) / baseline_std
        if abs(z) >= self.threshold:
            return z
        return None
