import os

import requests
from dotenv import load_dotenv

from auth_user_service import authenticate_user

load_dotenv(override=True)


def get_all_enzymes(username: str, secret: str):

    token, error = authenticate_user(username, secret)
    if error:
        return False, True

    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'{os.getenv("PLASTICOME_METADATA_URL")}/enzyme_find',
        headers=headers,
    )

    data = response.json()
    if response.status_code == 200:
        return data, False
    return False, data


def get_all_enzymes_by_ec_number(username: str, secret: str, ec_number: str):

    token, error = authenticate_user(username, secret)
    if error:
        return False, True

    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'{os.getenv("PLASTICOME_METADATA_URL")}/enzyme_find/ec/{ec_number}',
        headers=headers,
    )

    data = response.json()
    if response.status_code == 200:
        return data, False
    return False, data


def get_all_plastics_with_enzymes(username: str, secret: str):

    token, error = authenticate_user(username, secret)
    if error:
        return False, True

    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'{os.getenv("PLASTICOME_METADATA_URL")}/plastic_enzyme_find',
        headers=headers,
    )

    data = response.json()
    if response.status_code == 200:
        return data, False
    return False, data


def get_all_plastic_types_by_enzyme(
    username: str, secret: str, enzyme_id: int
):

    token, error = authenticate_user(username, secret)
    if error:
        return False, True

    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'{os.getenv("PLASTICOME_METADATA_URL")}/plastic_enzyme_find/{enzyme_id}',
        headers=headers,
    )

    data = response.json()
    if response.status_code == 200:
        plastic_values = [item['plastic'] for item in data]
        return plastic_values, False
    return False, data
