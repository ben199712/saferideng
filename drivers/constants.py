import json
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "data"

TRANSPORT_UNION_CHOICES = (
    ("nurtw", "National Union of Road Transport Workers (NURTW)"),
    ("rtean", "Road Transport Employers Association of Nigeria (RTEAN)"),
    ("narto", "Nigerian Association of Road Transport Owners (NARTO)"),
    ("auaton", "Amalgamated Union of App-Based Transporters of Nigeria (AUATON)"),
    ("namtob", "National Association of Motorcycle and Tricycle Owners and Riders Board (NAMTOB)"),
    ("other_vetted", "Other Vetted Union"),
)

GENDER_CHOICES = (
    ("male", "Male"),
    ("female", "Female"),
    ("prefer_not_to_say", "Prefer not to say"),
)


@lru_cache(maxsize=1)
def get_state_lga_mapping():
    primary_path = PROJECT_ROOT / "nigeria_lgas.json"
    fallback_path = DATA_DIR / "nigeria_states_lgas.json"

    if primary_path.exists():
        with open(primary_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        states = payload.get("states", [])
        mapping = {}
        for state in states:
            state_name = state["name"].replace("-", " ").strip()
            lgas = [
                lga.get("name", lga) if isinstance(lga, dict) else lga
                for lga in state.get("lgas", [])
            ]
            mapping[state_name] = tuple(
                sorted(
                    {
                        " ".join(str(lga).replace("\t", " ").replace("/", " / ").split())
                        for lga in lgas
                        if str(lga).strip()
                    }
                )
            )

        if "Federal Capital Territory" not in mapping:
            mapping["Federal Capital Territory"] = (
                "Abaji",
                "Abuja Municipal Area Council",
                "Bwari",
                "Gwagwalada",
                "Kuje",
                "Kwali",
            )
        return dict(sorted(mapping.items()))

    with open(fallback_path, "r", encoding="utf-8") as handle:
        rows = json.load(handle)

    mapping = {}
    for row in rows:
        state_name = row["name"].replace("-", " ").strip()
        if state_name == "Cross River":
            state_name = "Cross River"
        mapping[state_name] = tuple(
            sorted(
                {
                    " ".join(str(lga).replace("\t", " ").replace("/", " / ").split())
                    for lga in row["lgas"]
                    if str(lga).strip()
                }
            )
        )

    mapping["Federal Capital Territory"] = (
        "Abaji",
        "Abuja Municipal Area Council",
        "Bwari",
        "Gwagwalada",
        "Kuje",
        "Kwali",
    )
    return dict(sorted(mapping.items()))


@lru_cache(maxsize=1)
def get_country_choices():
    with open(DATA_DIR / "countries.json", "r", encoding="utf-8") as handle:
        rows = json.load(handle)

    names = sorted({row["name"]["common"] for row in rows})
    return tuple((name, name) for name in names)


STATE_CHOICES = tuple((state, state) for state in get_state_lga_mapping().keys())
COUNTRY_CHOICES = get_country_choices()
STATE_LGA_MAPPING = get_state_lga_mapping()
STATE_LGA_JSON = json.dumps(STATE_LGA_MAPPING)
