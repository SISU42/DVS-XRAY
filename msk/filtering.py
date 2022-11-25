import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.signal import butter, sosfiltfilt


def low_pass_filter(x: np.ndarray, order: int = 2, cutoff_freq: float = 1/15) -> np.ndarray:
    # Low - pass butterworth filter
    sos = butter(order, cutoff_freq, output='sos')
    y = sosfiltfilt(sos, x)
    return y


def outlier_filter(x: pd.Series, quantile: float = 0.99) -> np.ndarray:
    # Apply outlier removal filter to eliminate points beyond 99 percentile
    ser = x.dropna()

    diff_abs_ser = ser.diff().abs()

    # Get 99 percentile value
    p99 = diff_abs_ser.quantile(quantile)

    # Replace above p99 values with None and then forward fill
    ser[diff_abs_ser >= p99] = None
    x = ser.fillna(method='ffill').to_numpy()

    return x


def lowess_filter(x: np.ndarray) -> np.ndarray:
    # Non parametric curve smoother - lowess filter
    lowess = sm.nonparametric.lowess
    y = lowess(x, np.arange(len(x)), frac=0.08)[:, 1]
    return y


def filter_signal(x: pd.Series) -> np.ndarray:
    """
    Returns a filtered signal output
    """

    # Lowpass filter
    # x = outlier_filter(x)
    x = low_pass_filter(x)

    return x
