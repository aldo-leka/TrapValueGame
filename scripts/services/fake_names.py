import random

SECTOR_PREFIXES = {
    "Technology": ["Tech", "Digital", "Cyber", "Cloud", "Data", "Logic", "Sync", "Net"],
    "Healthcare": ["Med", "Health", "Bio", "Pharma", "Care", "Vital", "Life", "Cure"],
    "Consumer Discretionary": ["Retail", "Consumer", "Lifestyle", "Brand", "Choice", "Style"],
    "Financials": ["Capital", "Finance", "Asset", "Trust", "Wealth", "Fund", "Equity"],
    "Energy": ["Power", "Energy", "Fuel", "Resource", "Solar", "Grid", "Volt"],
    "Industrials": ["Industrial", "Manufacturing", "Engineering", "Build", "Steel", "Forge"],
    "Materials": ["Material", "Chemical", "Mining", "Alloy", "Mineral", "Element"],
    "Utilities": ["Utility", "Grid", "Service", "Power", "Supply", "Electric"],
    "Real Estate": ["Property", "Realty", "Estate", "Land", "Space", "Tower"],
    "Communication Services": ["Media", "Telecom", "Network", "Stream", "Connect", "Signal"],
    "Consumer Staples": ["Staple", "Essential", "Daily", "Basic", "Home", "Fresh"],
}

SUFFIXES = [
    "Alpha", "Beta", "Delta", "Gamma", "Omega", "Prime", "Core", "One", "X", "Plus",
    "Pro", "Max", "Global", "United", "First", "Pacific", "Atlantic", "Apex", "Nova"
]

GENERIC = ["Corp", "Co", "Inc", "Group", "Holdings", "Enterprises", "Industries", "Solutions"]


def generate_fake_name(sector: str | None, used_names: set[str]) -> str:
    """Generate a unique fake company name based on sector."""

    prefixes = SECTOR_PREFIXES.get(sector, ["Company", "Business", "Enterprise"])

    for _ in range(100):  # Max attempts
        prefix = random.choice(prefixes)
        suffix = random.choice(SUFFIXES)
        generic = random.choice(GENERIC)

        # Try different formats
        formats = [
            f"{prefix} {suffix}",
            f"{prefix} {suffix} {generic}",
            f"The {prefix} {generic}",
            f"{suffix} {prefix}",
            f"{prefix}{suffix}",  # No space variant
            f"{suffix} {generic}",
        ]

        name = random.choice(formats)
        if name not in used_names:
            return name

    # Fallback with UUID suffix
    import uuid
    return f"Company {str(uuid.uuid4())[:4].upper()}"
