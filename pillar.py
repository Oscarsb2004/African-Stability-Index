from .indicator import Indicator

class Pillar:
    def __init__(self, key: str, name: str, justification: str):
        self.key = key # e "A"
        self.name = name # eg Political/Governance
        self.justification = justification
        self.indicators = []

    def add_indicator(self, indicator: Indicator):
        self.indicators.append(indicator)