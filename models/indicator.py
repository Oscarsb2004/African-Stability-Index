class Indicator:
    def __init__(self, variable_name: str, display_name: str, source: str, series_code: str,
                 role: str, polarity: str, pillars: list[str], year_start: int, year_end: int,
                 aggregation: str, database: str = "wdi", log_transform: bool = False):
        self.variable_name = variable_name
        self.display_name  = display_name
        self.source        = source
        self.series_code   = series_code
        self.role          = role
        self.polarity      = polarity
        self.pillars       = pillars
        self.year_start    = year_start
        self.year_end      = year_end
        self.aggregation   = aggregation
        self.database      = database      # "wdi" (wbgapi db=2) or "wgi" (wbgapi db=3)
        self.log_transform = log_transform # apply log1p before min-max normalization
        self.justification = ""

    def __repr__(self):
        return (f"Indicator(variable_name={self.variable_name}, source={self.source}, "
                f"database={self.database}, role={self.role}, polarity={self.polarity}, "
                f"pillars={self.pillars})")

    def set_justification(self, text: str):
        self.justification = text