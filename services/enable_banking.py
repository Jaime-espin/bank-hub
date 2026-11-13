import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from pprint import pprint

import requests
import jwt as pyjwt


API_ORIGIN = "https://api.enablebanking.com"

def get_config():
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
    with open(file_path, "r") as f:
        return json.load(f)

def jwt():
    config = get_config()
    iat = int(datetime.now().timestamp())
    jwt_body = {
        "iss": "enablebanking.com",
        "aud": "api.enablebanking.com",
        "iat": iat,
        "exp": iat + 3600,
    }
    jwt = pyjwt.encode(
        jwt_body,
        open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', config["keyPath"])).read(),
        algorithm="RS256",
        headers={"kid": config["applicationId"]},
    )
    return jwt

def authenticate():
    base_headers = {"Authorization": f"Bearer {jwt()}"}
    
    # Requesting application details
    # Autenticación de la app
    r = requests.get(f"{API_ORIGIN}/application", headers=base_headers)
    if r.status_code == 200:
        app = r.json()
        print("Application details:")
        pprint(app)
    else:
        print(f"Error response {r.status_code}:", r.text)
        return
     # Requesting available ASPSPs
    # Desubre los bancos disponibles
    r = requests.get(f"{API_ORIGIN}/aspsps", headers=base_headers)
    if r.status_code == 200:
        aspsps = r.json().get("aspsps", [])
        es_banks = [a["name"] for a in aspsps if a.get("country") == "ES"]
        print("Bancos disponibles en España:", es_banks)
    else:
        print(f"Error response {r.status_code}:", r.text)
        return
     # Starting authorization
    config = get_config()
    aspsp_name = config.get("aspspName")
    aspsp_country = config.get("aspspCountry")
    body = {
        "access": {
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        },
        "aspsp": {"name": aspsp_name, "country": aspsp_country},
        "state": str(uuid.uuid4()),
        "redirect_url": app["redirect_urls"][0],
        "psu_type": "personal",
    }
    r = requests.post(f"{API_ORIGIN}/auth", json=body, headers=base_headers)
    if r.status_code == 200:
        auth_url = r.json()["url"]
        return auth_url
    else:
        print(f"Error response {r.status_code}:", r.text)
        return


def bank_session(auth_code):
    base_headers = {"Authorization": f"Bearer {jwt()}"}
    # Reading auth code and creating user session
    r = requests.post(f"{API_ORIGIN}/sessions", json={"code": auth_code}, headers=base_headers)
    if r.status_code == 200:
        session = r.json()
        print("New user session has been created:")
        pprint(session)
        return session
    else:
        print(f"Error response {r.status_code}:", r.text)
        return None

def get_balances(account_uid):
    base_headers = {"Authorization": f"Bearer {jwt()}"}
    # Retrieving account balances
    r = requests.get(f"{API_ORIGIN}/accounts/{account_uid}/balances", headers=base_headers)
    if r.status_code == 200:
        print("Balances:")
        return r.json()
    else:
        print(f"Error response {r.status_code}:", r.text)
        return

def get_transactions(account_uid):
    base_headers = {"Authorization": f"Bearer {jwt()}"}
    # Retrieving account transactions (since 365 days ago)
    query = {
        "date_from": (datetime.now(timezone.utc) - timedelta(days=365)).date().isoformat(),
    }
    continuation_key = None
    todas = []
    while True:
        if continuation_key:
            query["continuation_key"] = continuation_key
        r = requests.get(
            f"{API_ORIGIN}/accounts/{account_uid}/transactions",
            params=query,
            headers=base_headers,
        )
        if r.status_code == 200:
            resp_data = r.json()
            print("Transactions:")
            transactions = resp_data["transactions"]
            continuation_key = resp_data.get("continuation_key")
            todas.extend(resp_data["transactions"])
            if not continuation_key:
                print("No continuation key. All transactions were fetched")
                break
            print(f"Going to fetch more transactions with continuation key {continuation_key}")
            
        else:
            print(f"Error response {r.status_code}:", r.text)
            return
    
    print("All done!")
    return todas

def get_session_details(session_id):
    base_headers = {"Authorization": f"Bearer {jwt()}"}
    r = requests.get(f"{API_ORIGIN}/sessions/{session_id}", headers=base_headers)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"Error {r.status_code}:", r.text)
        return None


if __name__ == "__main__":
    pass
