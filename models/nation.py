
class Nation:
    def __init__(self, iso3: str, name: str, region: str, rec: list[str]):
        self.iso3 = iso3
        self.name = name
        self.region = region
        self.rec = rec

        self.normalized_scores = {}  # {variable_name: normalized_value} — written by 03_normalize.py
        self.pillar_scores     = {}  # {pillar_key: score}             — written by 04_score.py
        self.overall_score     = None                                  # written by 04_score.py

    def __repr__(self):
        return f"Nation(iso3={self.iso3}, name={self.name}, region={self.region}, rec={self.rec})"

    def get_normalized_score(self, variable_name: str) -> float | None:
        return self.normalized_scores.get(variable_name)

    def get_pillar_score(self, pillar_key: str) -> float | None:
        return self.pillar_scores.get(pillar_key)




