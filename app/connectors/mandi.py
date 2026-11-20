"""Mandi prices from data.gov.in (AGMARKNET data). Needs DATA_GOV_API_KEY and MANDI_RESOURCE_ID.
Field names (state, district, market, commodity, arrival_date, min/max/modal_price) must be
verified against the dataset you select; access is NOT assumed operational until you test it."""

class ConnectorNotConfigured(RuntimeError):
    pass

class MandiConnector:
    BASE = "https://api.data.gov.in/resource/"

    def __init__(self, api_key: str | None, resource_id: str | None):
        self.api_key, self.resource_id = api_key, resource_id

    def fetch(self, state: str | None, district: str | None, commodity: str, limit: int = 20) -> list[dict]:
        if not (self.api_key and self.resource_id):
            raise ConnectorNotConfigured("DATA_GOV_API_KEY / MANDI_RESOURCE_ID not set")
        import requests
        params = {"api-key": self.api_key, "format": "json", "limit": limit,
                  "filters[commodity]": commodity.title()}
        if state:
            params["filters[state]"] = state.title()
        if district:
            params["filters[district]"] = district.title()
        r = requests.get(self.BASE + self.resource_id, params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("records", [])
