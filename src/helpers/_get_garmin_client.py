import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from garminconnect import Garmin


@dataclass(frozen=True)
class GarminConfiguration:
    activity_fetch_limit: int


def get_garmin_client() -> tuple[Garmin, GarminConfiguration]:
    load_dotenv()

    print("Initializing Garmin client...")

    garmin_client = _get_garmin_client()
    garmin_configuration = _get_garmin_configuration()

    print("Garmin client authenticated successfully.")

    return garmin_client, garmin_configuration


# Vernieuwde tokens bewaren we tussen de stappen (en, via de workflow, tussen runs).
# Garmin geeft bij het verversen een nieuwe refresh token uit; wie de oude blijft
# gebruiken krijgt na een paar dagen 401 "Failed to retrieve social profile".
TOKEN_FILE = Path(os.getenv("GARMIN_TOKEN_FILE", "~/.garmin_token.json")).expanduser()


def _login(token: str) -> Garmin:
    garmin_client = Garmin()
    garmin_client.login(tokenstore=token)
    return garmin_client


def _save_token(garmin_client: Garmin) -> None:
    try:
        TOKEN_FILE.write_text(garmin_client.client.dumps())
    except Exception as e:  # opslaan mag de sync nooit laten falen
        print(f"Kon vernieuwde Garmin-token niet opslaan: {e}")


def _get_garmin_client() -> Garmin:
    secret_token = os.getenv("GARMIN_AUTH_TOKEN")
    saved_token = TOKEN_FILE.read_text().strip() if TOKEN_FILE.exists() else ""

    if not saved_token and not secret_token:
        raise ValueError(
            "GARMIN_AUTH_TOKEN is required. "
            "See README_AUTH_SETUP.md for instructions on generating a token."
        )

    # 1. De laatst bewaarde (vernieuwde) token; 2. anders de token uit de GitHub-secret.
    if saved_token:
        try:
            garmin_client = _login(saved_token)
            print("Ingelogd met de bewaarde, vernieuwde token.")
            _save_token(garmin_client)
            return garmin_client
        except Exception as e:
            print(f"Bewaarde token werkt niet ({e}); probeer GARMIN_AUTH_TOKEN.")
            if not secret_token:
                raise

    garmin_client = _login(secret_token)
    print("Ingelogd met GARMIN_AUTH_TOKEN.")
    _save_token(garmin_client)
    return garmin_client


def _get_garmin_configuration():
    return GarminConfiguration(
        activity_fetch_limit=int(os.getenv("GARMIN_ACTIVITIES_FETCH_LIMIT", "10")),
    )
