from .indicator import Indicator

class Pillar:
    def __init__(self, key: str, name: str, justification: str, weight: float = 1/7):
        self.key           = key           # e.g. "A"
        self.name          = name          # e.g. "Political / Governance"
        self.justification = justification
        self.weight        = weight        # default equal weighting
        self.indicators    = []

    def add_indicator(self, indicator: Indicator):
        self.indicators.append(indicator)

    def __repr__(self):
        return f"Pillar(key={self.key}, name={self.name}, indicators={len(self.indicators)})"

    def get_scoring_indicators(self) -> list[Indicator]:
        return [i for i in self.indicators if i.role == "scoring"]

    def get_descriptive_indicators(self) -> list[Indicator]:
        return [i for i in self.indicators if i.role == "descriptive"]