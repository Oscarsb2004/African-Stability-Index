class Indicator:
    def __init__ (self, variable_name: str, display_name: str, source: str, series_code: str, role: str, polarity: str, pillars: list[str], justification: str):
        self.variable_name = variable_name # eg gdp_pc_current_USD
        self.display_name = display_name # eg GDP per capita (Current USD)
        self.source = source # wb_api or manual or something else
        self.series_code = series_code #world bank dataset code
        self.role = role #scoring or descriptive
        self.polarity = polarity #positive or negative
        self.pillars = pillars # eg ["B"] or ["A", "E"] etc
        self.justification = justification # why this indicator was chosen

    def __repr__(self):
        return f"Indicator(variable_name={self.variable_name}, display_name={self.display_name}, source={self.source}, series_code={self.series_code}, role={self.role}, polarity={self.polarity}, pillars={self.pillars})"
