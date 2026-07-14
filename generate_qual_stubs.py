"""
generate_qual_stubs.py — create qualitative note stubs for all 54 AU countries.

Run once:  python generate_qual_stubs.py
Creates:   qualitative/countries/{ISO3}.yaml  for every country not yet present.
Existing files are NEVER overwritten.
"""

from pathlib import Path

COUNTRIES = [
    ("DZA","Algeria"), ("AGO","Angola"), ("BEN","Benin"), ("BWA","Botswana"),
    ("BFA","Burkina Faso"), ("BDI","Burundi"), ("CMR","Cameroon"), ("CPV","Cabo Verde"),
    ("CAF","Central African Republic"), ("TCD","Chad"), ("COM","Comoros"),
    ("COD","DR Congo"), ("COG","Republic of Congo"), ("CIV","Côte d'Ivoire"),
    ("DJI","Djibouti"), ("EGY","Egypt"), ("GNQ","Equatorial Guinea"), ("ERI","Eritrea"),
    ("SWZ","Eswatini"), ("ETH","Ethiopia"), ("GAB","Gabon"), ("GMB","Gambia"),
    ("GHA","Ghana"), ("GIN","Guinea"), ("GNB","Guinea-Bissau"), ("KEN","Kenya"),
    ("LSO","Lesotho"), ("LBR","Liberia"), ("LBY","Libya"), ("MDG","Madagascar"),
    ("MWI","Malawi"), ("MLI","Mali"), ("MRT","Mauritania"), ("MUS","Mauritius"),
    ("MAR","Morocco"), ("MOZ","Mozambique"), ("NAM","Namibia"), ("NER","Niger"),
    ("NGA","Nigeria"), ("RWA","Rwanda"), ("STP","Sao Tome and Principe"),
    ("SEN","Senegal"), ("SYC","Seychelles"), ("SLE","Sierra Leone"), ("SOM","Somalia"),
    ("ZAF","South Africa"), ("SSD","South Sudan"), ("SDN","Sudan"), ("TZA","Tanzania"),
    ("TGO","Togo"), ("TUN","Tunisia"), ("UGA","Uganda"), ("ZMB","Zambia"), ("ZWE","Zimbabwe"),
]

STUB = """\
# Qualitative country notes — {name} ({iso3})
# Edit this file to add your own analysis.
# All fields are optional; leave empty strings or empty lists as placeholders.
# last_updated: use ISO date format YYYY-MM-DD

overview: ""

recent_developments: ""

strengths:
  - ""

challenges:
  - ""

historical_notes: ""

key_figures: []

external_sources: []

last_updated: ""
"""

def main():
    out_dir = Path("qualitative/countries")
    out_dir.mkdir(parents=True, exist_ok=True)
    created = 0
    skipped = 0
    for iso3, name in COUNTRIES:
        path = out_dir / f"{iso3}.yaml"
        if path.exists():
            skipped += 1
            continue
        path.write_text(STUB.format(iso3=iso3, name=name), encoding="utf-8")
        created += 1
    print(f"Created {created} stubs, skipped {skipped} existing files.")
    print(f"Edit files in: {out_dir.resolve()}")

if __name__ == "__main__":
    main()
