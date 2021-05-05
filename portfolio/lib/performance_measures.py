import pandas as pd
import numpy as np
from scipy.stats import norm


class PerformanceMeasures:

    @staticmethod
    def measure_loop(performance: pd.Series) -> dict:
        """
        Loop through performance measure calculations and return the result of all.
        :param performance: Time series the calculations should be based on
        """
        switcher = {
            1: PerformanceMeasures.returns,
            2: PerformanceMeasures.annualized_returns,
            3: PerformanceMeasures.std,
            4: PerformanceMeasures.sharpe,
            5: PerformanceMeasures.var,
            6: PerformanceMeasures.max_drawdown,
        }

        data = dict()
        for key in switcher.keys():
            measure = switcher.get(key)
            data = {**data, **measure(performance)}

        return data

    @staticmethod
    def date_range(series: pd.Series) -> dict:
        return {"start_date": series.index[0].date(), "end_date": series.index[-1].date()}

    @staticmethod
    def returns(series: pd.Series) -> dict:
        return {PerformanceMeasures.returns.__name__: (series[-1] / series[0]) - 1}

    @staticmethod
    def annualized_returns(series: pd.Series) -> dict:
        return {PerformanceMeasures.annualized_returns.__name__: (series[-1] / series[0]) ** (252 / len(series)) - 1}

    @staticmethod
    def std(series: pd.Series) -> dict:
        return {PerformanceMeasures.std.__name__: np.std(series.pct_change(), ddof=1) * np.sqrt(252)}

    @staticmethod
    def sharpe(series: pd.Series) -> dict:
        mean = PerformanceMeasures.annualized_returns(series)["annualized_returns"]
        sd = PerformanceMeasures.std(series)["std"]
        ex_return = mean
        return {PerformanceMeasures.sharpe.__name__: ex_return / sd}

    @staticmethod
    def var(series: pd.Series) -> dict:
        series = series.pct_change().dropna()
        mean = np.mean(series)
        sd = np.std(series)

        return {PerformanceMeasures.var.__name__: norm.ppf(0.01, loc=mean, scale=sd)}

    @staticmethod
    def cvar(series: pd.Series) -> dict:
        series = series.pct_change()
        mean = np.mean(series)
        sd = np.std(series)

        return {PerformanceMeasures.cvar.__name__: mean - 0.01 ** (-1) * sd * norm.pdf(norm.ppf(0.01))}

    @staticmethod
    def max_drawdown(series: pd.Series) -> dict:
        window = len(series)
        roll_max = series.rolling(window, min_periods=1).max()
        daily_drawdown = series / roll_max - 1
        max_daily_drawdown = daily_drawdown.rolling(window, min_periods=1).min()

        return {PerformanceMeasures.max_drawdown.__name__: min(max_daily_drawdown)}
