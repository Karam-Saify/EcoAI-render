from __future__ import annotations

from typing import Any, Dict


COUNTRY_METADATA: Dict[str, Dict[str, float | str]] = {
    "AF": {"name": "Afghanistan", "lat": 33.9391, "lon": 67.71},
    "AL": {"name": "Albania", "lat": 41.1533, "lon": 20.1683},
    "AM": {"name": "Armenia", "lat": 40.0691, "lon": 45.0382},
    "AO": {"name": "Angola", "lat": -11.2027, "lon": 17.8739},
    "AR": {"name": "Argentina", "lat": -38.4161, "lon": -63.6167},
    "AZ": {"name": "Azerbaijan", "lat": 40.1431, "lon": 47.5769},
    "BA": {"name": "Bosnia and Herzegovina", "lat": 43.9159, "lon": 17.6791},
    "BD": {"name": "Bangladesh", "lat": 23.685, "lon": 90.3563},
    "BF": {"name": "Burkina Faso", "lat": 12.2383, "lon": -1.5616},
    "BI": {"name": "Burundi", "lat": -3.3731, "lon": 29.9189},
    "BJ": {"name": "Benin", "lat": 9.3077, "lon": 2.3158},
    "BO": {"name": "Bolivia", "lat": -16.2902, "lon": -63.5887},
    "BR": {"name": "Brazil", "lat": -14.235, "lon": -51.9253},
    "BW": {"name": "Botswana", "lat": -22.3285, "lon": 24.6849},
    "BY": {"name": "Belarus", "lat": 53.7098, "lon": 27.9534},
    "CF": {"name": "Central African Republic", "lat": 6.6111, "lon": 20.9394},
    "CG": {"name": "Congo", "lat": -0.228, "lon": 15.8277},
    "CI": {"name": "Cote d'Ivoire", "lat": 7.54, "lon": -5.5471},
    "CL": {"name": "Chile", "lat": -35.6751, "lon": -71.543},
    "CM": {"name": "Cameroon", "lat": 7.3697, "lon": 12.3547},
    "CN": {"name": "China", "lat": 35.8617, "lon": 104.1954},
    "CO": {"name": "Colombia", "lat": 4.5709, "lon": -74.2973},
    "CR": {"name": "Costa Rica", "lat": 9.7489, "lon": -83.7534},
    "CU": {"name": "Cuba", "lat": 21.5218, "lon": -77.7812},
    "CV": {"name": "Cabo Verde", "lat": 16.5388, "lon": -23.0418},
    "CD": {"name": "Democratic Republic of the Congo", "lat": -4.0383, "lon": 21.7587},
    "DJ": {"name": "Djibouti", "lat": 11.8251, "lon": 42.5903},
    "DO": {"name": "Dominican Republic", "lat": 18.7357, "lon": -70.1627},
    "DZ": {"name": "Algeria", "lat": 28.0339, "lon": 1.6596},
    "EC": {"name": "Ecuador", "lat": -1.8312, "lon": -78.1834},
    "EG": {"name": "Egypt", "lat": 26.8206, "lon": 30.8025},
    "ER": {"name": "Eritrea", "lat": 15.1794, "lon": 39.7823},
    "ET": {"name": "Ethiopia", "lat": 9.145, "lon": 40.4897},
    "FJ": {"name": "Fiji", "lat": -17.7134, "lon": 178.065},
    "GA": {"name": "Gabon", "lat": -0.8037, "lon": 11.6094},
    "GE": {"name": "Georgia", "lat": 42.3154, "lon": 43.3569},
    "GH": {"name": "Ghana", "lat": 7.9465, "lon": -1.0232},
    "GM": {"name": "Gambia", "lat": 13.4432, "lon": -15.3101},
    "GN": {"name": "Guinea", "lat": 9.9456, "lon": -9.6966},
    "GQ": {"name": "Equatorial Guinea", "lat": 1.6508, "lon": 10.2679},
    "GT": {"name": "Guatemala", "lat": 15.7835, "lon": -90.2308},
    "GW": {"name": "Guinea-Bissau", "lat": 11.8037, "lon": -15.1804},
    "HT": {"name": "Haiti", "lat": 18.9712, "lon": -72.2852},
    "HN": {"name": "Honduras", "lat": 15.2, "lon": -86.2419},
    "ID": {"name": "Indonesia", "lat": -0.7893, "lon": 113.9213},
    "IN": {"name": "India", "lat": 20.5937, "lon": 78.9629},
    "IQ": {"name": "Iraq", "lat": 33.2232, "lon": 43.6793},
    "IR": {"name": "Iran", "lat": 32.4279, "lon": 53.688},
    "JM": {"name": "Jamaica", "lat": 18.1096, "lon": -77.2975},
    "JO": {"name": "Jordan", "lat": 30.5852, "lon": 36.2384},
    "KE": {"name": "Kenya", "lat": -0.0236, "lon": 37.9062},
    "KG": {"name": "Kyrgyzstan", "lat": 41.2044, "lon": 74.7661},
    "KH": {"name": "Cambodia", "lat": 12.5657, "lon": 104.991},
    "KP": {"name": "North Korea", "lat": 40.3399, "lon": 127.5101},
    "LA": {"name": "Laos", "lat": 19.8563, "lon": 102.4955},
    "LB": {"name": "Lebanon", "lat": 33.8547, "lon": 35.8623},
    "LK": {"name": "Sri Lanka", "lat": 7.8731, "lon": 80.7718},
    "LR": {"name": "Liberia", "lat": 6.4281, "lon": -9.4295},
    "LS": {"name": "Lesotho", "lat": -29.61, "lon": 28.2336},
    "LY": {"name": "Libya", "lat": 26.3351, "lon": 17.2283},
    "MA": {"name": "Morocco", "lat": 31.7917, "lon": -7.0926},
    "MD": {"name": "Moldova", "lat": 47.4116, "lon": 28.3699},
    "MG": {"name": "Madagascar", "lat": -18.7669, "lon": 46.8691},
    "ML": {"name": "Mali", "lat": 17.5707, "lon": -3.9962},
    "MM": {"name": "Myanmar", "lat": 21.9162, "lon": 95.956},
    "MN": {"name": "Mongolia", "lat": 46.8625, "lon": 103.8467},
    "MR": {"name": "Mauritania", "lat": 21.0079, "lon": -10.9408},
    "MU": {"name": "Mauritius", "lat": -20.3484, "lon": 57.5522},
    "MW": {"name": "Malawi", "lat": -13.2543, "lon": 34.3015},
    "MX": {"name": "Mexico", "lat": 23.6345, "lon": -102.5528},
    "MY": {"name": "Malaysia", "lat": 4.2105, "lon": 101.9758},
    "MZ": {"name": "Mozambique", "lat": -18.6657, "lon": 35.5296},
    "NA": {"name": "Namibia", "lat": -22.9576, "lon": 18.4904},
    "NE": {"name": "Niger", "lat": 17.6078, "lon": 8.0817},
    "NG": {"name": "Nigeria", "lat": 9.082, "lon": 8.6753},
    "NI": {"name": "Nicaragua", "lat": 12.8654, "lon": -85.2072},
    "NP": {"name": "Nepal", "lat": 28.3949, "lon": 84.124},
    "PA": {"name": "Panama", "lat": 8.538, "lon": -80.7821},
    "PE": {"name": "Peru", "lat": -9.19, "lon": -75.0152},
    "PH": {"name": "Philippines", "lat": 12.8797, "lon": 121.774},
    "PK": {"name": "Pakistan", "lat": 30.3753, "lon": 69.3451},
    "PS": {"name": "Palestine", "lat": 31.9522, "lon": 35.2332},
    "PY": {"name": "Paraguay", "lat": -23.4425, "lon": -58.4438},
    "RW": {"name": "Rwanda", "lat": -1.9403, "lon": 29.8739},
    "SD": {"name": "Sudan", "lat": 12.8628, "lon": 30.2176},
    "SL": {"name": "Sierra Leone", "lat": 8.4606, "lon": -11.7799},
    "SN": {"name": "Senegal", "lat": 14.4974, "lon": -14.4524},
    "SO": {"name": "Somalia", "lat": 5.1521, "lon": 46.1996},
    "SS": {"name": "South Sudan", "lat": 6.877, "lon": 31.307},
    "SV": {"name": "El Salvador", "lat": 13.7942, "lon": -88.8965},
    "SY": {"name": "Syria", "lat": 34.8021, "lon": 38.9968},
    "SZ": {"name": "Eswatini", "lat": -26.5225, "lon": 31.4659},
    "TD": {"name": "Chad", "lat": 15.4542, "lon": 18.7322},
    "TG": {"name": "Togo", "lat": 8.6195, "lon": 0.8248},
    "TH": {"name": "Thailand", "lat": 15.87, "lon": 100.9925},
    "TL": {"name": "Timor-Leste", "lat": -8.8742, "lon": 125.7275},
    "TN": {"name": "Tunisia", "lat": 33.8869, "lon": 9.5375},
    "TR": {"name": "Turkey", "lat": 38.9637, "lon": 35.2433},
    "TZ": {"name": "Tanzania", "lat": -6.369, "lon": 34.8888},
    "UA": {"name": "Ukraine", "lat": 48.3794, "lon": 31.1656},
    "UG": {"name": "Uganda", "lat": 1.3733, "lon": 32.2903},
    "UY": {"name": "Uruguay", "lat": -32.5228, "lon": -55.7658},
    "VE": {"name": "Venezuela", "lat": 6.4238, "lon": -66.5897},
    "VN": {"name": "Vietnam", "lat": 14.0583, "lon": 108.2772},
    "XK": {"name": "Kosovo", "lat": 42.6026, "lon": 20.903},
    "YE": {"name": "Yemen", "lat": 15.5527, "lon": 48.5164},
    "ZA": {"name": "South Africa", "lat": -30.5595, "lon": 22.9375},
    "ZM": {"name": "Zambia", "lat": -13.1339, "lon": 27.8493},
    "ZW": {"name": "Zimbabwe", "lat": -19.0154, "lon": 29.1549},
}

COUNTRY_ALIASES = {
    "afghanistan": "AF",
    "albania": "AL",
    "algeria": "DZ",
    "angola": "AO",
    "argentina": "AR",
    "armenia": "AM",
    "azerbaijan": "AZ",
    "bangladesh": "BD",
    "belarus": "BY",
    "benin": "BJ",
    "bhutan": "BT",
    "bolivia": "BO",
    "botswana": "BW",
    "brazil": "BR",
    "burkina faso": "BF",
    "burundi": "BI",
    "cabo verde": "CV",
    "cambodia": "KH",
    "cameroon": "CM",
    "car": "CF",
    "central african republic": "CF",
    "chad": "TD",
    "china": "CN",
    "colombia": "CO",
    "comoros": "KM",
    "congo": "CG",
    "congo the democratic republic of the": "CD",
    "costa rica": "CR",
    "cote d'ivoire": "CI",
    "cote divoire": "CI",
    "democratic republic of the congo": "CD",
    "djibouti": "DJ",
    "dominican republic": "DO",
    "ecuador": "EC",
    "egypt": "EG",
    "el salvador": "SV",
    "equatorial guinea": "GQ",
    "eritrea": "ER",
    "eswatini": "SZ",
    "ethiopia": "ET",
    "fiji": "FJ",
    "gabon": "GA",
    "gambia": "GM",
    "georgia": "GE",
    "ghana": "GH",
    "guatemala": "GT",
    "guinea": "GN",
    "guinea-bissau": "GW",
    "haiti": "HT",
    "honduras": "HN",
    "india": "IN",
    "indonesia": "ID",
    "iran": "IR",
    "iraq": "IQ",
    "jamaica": "JM",
    "jordan": "JO",
    "kenia": "KE",
    "kenya": "KE",
    "kosovo": "XK",
    "kyrgyzstan": "KG",
    "laos": "LA",
    "lebanon": "LB",
    "liban": "LB",
    "libanon": "LB",
    "liberia": "LR",
    "libya": "LY",
    "madagascar": "MG",
    "malawi": "MW",
    "mali": "ML",
    "mauritania": "MR",
    "mauritius": "MU",
    "mexico": "MX",
    "moldova": "MD",
    "mongolia": "MN",
    "morocco": "MA",
    "mozambique": "MZ",
    "myanmar": "MM",
    "namibia": "NA",
    "nepal": "NP",
    "nicaragua": "NI",
    "niger": "NE",
    "nigeria": "NG",
    "north korea": "KP",
    "pakistan": "PK",
    "palestine": "PS",
    "panama": "PA",
    "paraguay": "PY",
    "peru": "PE",
    "philippines": "PH",
    "rwanda": "RW",
    "senegal": "SN",
    "sierra leone": "SL",
    "somalia": "SO",
    "south africa": "ZA",
    "south sudan": "SS",
    "sri lanka": "LK",
    "sudan": "SD",
    "syria": "SY",
    "tanzania": "TZ",
    "thailand": "TH",
    "timor-leste": "TL",
    "togo": "TG",
    "tunisia": "TN",
    "turkey": "TR",
    "uganda": "UG",
    "ukraine": "UA",
    "venezuela": "VE",
    "vietnam": "VN",
    "viet nam": "VN",
    "yemen": "YE",
    "zambia": "ZM",
    "zimbabwe": "ZW",
}

IATI_REGION_METADATA: Dict[str, Dict[str, float | str]] = {
    "002": {"name": "Africa", "lat": 7.0, "lon": 20.0},
    "089": {"name": "Europe, Regional", "lat": 54.0, "lon": 18.0},
    "099": {"name": "Global, Regional", "lat": 18.0, "lon": 5.0},
    "189": {"name": "North of Sahara, Regional", "lat": 28.0, "lon": 10.0},
    "289": {"name": "Sub-Saharan Africa, Regional", "lat": 2.0, "lon": 22.0},
    "298": {"name": "Africa, Regional", "lat": 1.0, "lon": 23.0},
    "380": {"name": "Latin America and the Caribbean", "lat": 10.0, "lon": -72.0},
    "389": {"name": "North and Central America, Regional", "lat": 18.0, "lon": -88.0},
    "489": {"name": "South America, Regional", "lat": -16.0, "lon": -60.0},
    "498": {"name": "America, Regional", "lat": 8.0, "lon": -70.0},
    "589": {"name": "Middle East, Regional", "lat": 31.0, "lon": 41.0},
    "619": {"name": "Central Asia, Regional", "lat": 43.0, "lon": 68.0},
    "679": {"name": "South Asia, Regional", "lat": 20.0, "lon": 79.0},
    "689": {"name": "South and Central Asia, Regional", "lat": 28.0, "lon": 73.0},
    "789": {"name": "Far East Asia, Regional", "lat": 29.0, "lon": 111.0},
    "798": {"name": "Asia, Regional", "lat": 28.0, "lon": 92.0},
    "889": {"name": "Oceania, Regional", "lat": -19.0, "lon": 148.0},
    "998": {"name": "Developing Countries, Unspecified", "lat": 12.0, "lon": 14.0},
    "1027": {"name": "Eastern Africa, Regional", "lat": 0.0, "lon": 37.0},
    "1028": {"name": "Middle Africa, Regional", "lat": 1.0, "lon": 20.0},
    "1029": {"name": "Southern Africa, Regional", "lat": -20.0, "lon": 25.0},
    "1030": {"name": "Western Africa, Regional", "lat": 9.0, "lon": -2.0},
    "1031": {"name": "Caribbean, Regional", "lat": 18.0, "lon": -70.0},
    "1032": {"name": "Central America, Regional", "lat": 13.0, "lon": -86.0},
    "1033": {"name": "Melanesia, Regional", "lat": -8.0, "lon": 156.0},
}

for code, entry in list(IATI_REGION_METADATA.items()):
    normalized = str(int(code)) if code.isdigit() else code
    IATI_REGION_METADATA.setdefault(normalized, entry)


def _slug(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def coerce_country_code(value: Any) -> str:
    token = str(value or "").strip()
    if not token:
        return ""
    upper_token = token.upper()
    if upper_token in COUNTRY_METADATA:
        return upper_token
    return COUNTRY_ALIASES.get(_slug(token), "")


def country_name(value: Any) -> str:
    token = str(value or "").strip()
    if not token:
        return ""
    code = coerce_country_code(token)
    if code:
        entry = COUNTRY_METADATA.get(code)
        if entry:
            return str(entry["name"])
    if token.isdigit():
        return ""
    return " ".join(part.capitalize() for part in _slug(token).split())


def region_name(value: Any) -> str:
    token = str(value or "").strip()
    if not token:
        return ""
    entry = IATI_REGION_METADATA.get(token) or IATI_REGION_METADATA.get(token.zfill(3))
    if entry:
        return str(entry["name"])
    return " ".join(part.capitalize() for part in _slug(token).split())


def country_coordinates(value: Any) -> dict[str, float] | None:
    code = coerce_country_code(value)
    if not code:
        return None
    entry = COUNTRY_METADATA.get(code)
    if not entry or "lat" not in entry or "lon" not in entry:
        return None
    return {"lat": float(entry["lat"]), "lon": float(entry["lon"])}


def region_coordinates(value: Any) -> dict[str, float] | None:
    token = str(value or "").strip()
    if not token:
        return None
    entry = IATI_REGION_METADATA.get(token) or IATI_REGION_METADATA.get(token.zfill(3))
    if not entry or "lat" not in entry or "lon" not in entry:
        return None
    return {"lat": float(entry["lat"]), "lon": float(entry["lon"])}
