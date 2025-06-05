import pandas as pd

class BacktestConfig:
    def __init__(self):
        self.ticker = "NVDA"
        self.period = "7d"
        self.start_date = pd.to_datetime("2025-05-06")
        self.end_date = pd.to_datetime("2025-05-26")
        self.initial_cash =10000

