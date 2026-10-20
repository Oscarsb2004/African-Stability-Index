"""
asi.core.countries — the country registry for this edition: the 54 African Union member states scored, each with
the display name used everywhere in the UI.

Groupings live in registry/groups.yaml: the African Union's eight Regional Economic Communities (the owner's
compilation, moved there on 2026-10-20) and the organisations the Data tab compares. Edition 1's own regions, its
island-state flag and its regional-mean imputation are not carried over (P105): no state is treated differently
for being small, an island or data-poor.
"""

COUNTRIES = {
    "DZA": {"name": "Algeria"},
    "EGY": {"name": "Egypt"},
    "LBY": {"name": "Libya"},
    "MAR": {"name": "Morocco"},
    "SDN": {"name": "Sudan"},
    "TUN": {"name": "Tunisia"},
    "BEN": {"name": "Benin"},
    "BFA": {"name": "Burkina Faso"},
    "CPV": {"name": "Cabo Verde"},
    "GMB": {"name": "The Gambia"},
    "GHA": {"name": "Ghana"},
    "GIN": {"name": "Guinea"},
    "GNB": {"name": "Guinea-Bissau"},
    "CIV": {"name": "Cote d'Ivoire"},
    "LBR": {"name": "Liberia"},
    "MLI": {"name": "Mali"},
    "MRT": {"name": "Mauritania"},
    "NER": {"name": "Niger"},
    "NGA": {"name": "Nigeria"},
    "SEN": {"name": "Senegal"},
    "SLE": {"name": "Sierra Leone"},
    "TGO": {"name": "Togo"},
    "AGO": {"name": "Angola"},
    "CMR": {"name": "Cameroon"},
    "CAF": {"name": "Central African Republic"},
    "TCD": {"name": "Chad"},
    "COG": {"name": "Republic of Congo"},
    "COD": {"name": "Democratic Rep. Congo"},
    "GNQ": {"name": "Equatorial Guinea"},
    "GAB": {"name": "Gabon"},
    "BDI": {"name": "Burundi"},
    "DJI": {"name": "Djibouti"},
    "ERI": {"name": "Eritrea"},
    "ETH": {"name": "Ethiopia"},
    "KEN": {"name": "Kenya"},
    "MWI": {"name": "Malawi"},
    "MOZ": {"name": "Mozambique"},
    "RWA": {"name": "Rwanda"},
    "SOM": {"name": "Somalia"},
    "SSD": {"name": "South Sudan"},
    "TZA": {"name": "Tanzania"},
    "UGA": {"name": "Uganda"},
    "ZMB": {"name": "Zambia"},
    "ZWE": {"name": "Zimbabwe"},
    "BWA": {"name": "Botswana"},
    "LSO": {"name": "Lesotho"},
    "NAM": {"name": "Namibia"},
    "SWZ": {"name": "Eswatini"},
    "ZAF": {"name": "South Africa"},
    "COM": {"name": "Comoros"},
    "MDG": {"name": "Madagascar"},
    "MUS": {"name": "Mauritius"},
    "SYC": {"name": "Seychelles"},
    "STP": {"name": "Sao Tome & Principe"},
}

#: AU member states this edition does not score, and why. Kept as data rather
#: than prose so the union total shown to a reader stays derived: the AU count
#: is the scored set plus these, and neither number is ever typed into a string.
EXCLUDED_AU_MEMBERS = {
    "Western Sahara": (
        "the Sahrawi Arab Democratic Republic, an AU member since 1984 — the "
        "admission that caused Morocco to leave the OAU until 2017"
    ),
}
