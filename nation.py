
class Nation:
    def __init__(self, iso3: str, name: str, region: str, rec: list[str]):
        self.iso3 = iso3
        self.name = name
        self.region = region
        self.rec = rec

        self.values = {} # {variable_name: raw value}
        self.pillar_scores = {} # {pillar_key: score}
        self.overall_score = None

        def __repr__(self):
            return f"Nation(iso3={self.iso3}, name={self.name}, region={self.region}, rec={self.rec})"




