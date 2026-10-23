"""Supported countries, their currencies and a fixed FX table.

Rates are USD per 1 unit of local currency. They are intentionally static
(see docs/requirements.md): deterministic numbers, no external dependency.
Update the table (or the fx_rates DB rows) to refresh them.
"""

# country -> currency (one currency per country; client never supplies currency)
COUNTRY_CURRENCY = {
    "United States": "USD",
    "United Kingdom": "GBP",
    "Germany": "EUR",
    "France": "EUR",
    "India": "INR",
    "Japan": "JPY",
    "Canada": "CAD",
    "Australia": "AUD",
    "Brazil": "BRL",
    "Singapore": "SGD",
    "United Arab Emirates": "AED",
    "Poland": "PLN",
}

USD_PER_UNIT = {
    "USD": 1.0,
    "GBP": 1.27,
    "EUR": 1.08,
    "INR": 0.012,
    "JPY": 0.0067,
    "CAD": 0.73,
    "AUD": 0.66,
    "BRL": 0.20,
    "SGD": 0.74,
    "AED": 0.272,
    "PLN": 0.25,
}


def currency_for(country: str) -> str:
    return COUNTRY_CURRENCY[country]
