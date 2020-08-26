import pandas as pd
import numpy as np
from scipy.stats import norm


def daterange(series: pd.Series) -> dict:
    return {"start_date": series.index[0].date(), "end_date": series.index[-1].date()}


def returns(series: pd.Series) -> dict:
    return {returns.__name__: (series[-1] / series[0]) - 1}


def annualized_returns(series: pd.Series) -> dict:
    return {annualized_returns.__name__: (series[-1] / series[0]) ** (252 / len(series)) - 1}


def std(series: pd.Series) -> dict:
    return {std.__name__: np.std(series.pct_change(), ddof=1) * np.sqrt(252)}


def sharpe(series: pd.Series) -> dict:
    mean = annualized_returns(series)["annualized_returns"]
    sd = std(series)["std"]
    ex_return = mean
    return {sharpe.__name__: ex_return / sd}


def var(series: pd.Series) -> dict:
    series = series.pct_change().dropna()
    mean = np.mean(series)
    sd = np.std(series)

    return {var.__name__: norm.ppf(0.01, loc=mean, scale=sd)}


def cvar(series: pd.Series) -> dict:
    series = series.pct_change()
    mean = np.mean(series)
    sd = np.std(series)

    return {cvar.__name__: mean - 0.01 ** (-1) * sd * norm.pdf(norm.ppf(0.01))}


def max_drawdown(series: pd.Series) -> dict:
    window = len(series)
    roll_max = series.rolling(window, min_periods=1).max()
    daily_drawdown = series / roll_max - 1
    max_daily_drawdown = daily_drawdown.rolling(window, min_periods=1).min()

    return {max_drawdown.__name__: min(max_daily_drawdown)}
