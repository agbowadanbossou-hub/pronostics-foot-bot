

import os
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")


def get_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise RuntimeError(
            "Il manque TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID dans les secrets GitHub."
        )

    url = (
        "https://api.telegram.org/bot"
        + TELEGRAM_TOKEN
        + "/sendMessage"
    )
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=25) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not result.get("ok"):
        raise RuntimeError("Telegram n'a pas accepté le message.")


def main():
    if not FOOTBALL_API_KEY:
        send_telegram(
            "⚠️ Ton bot Telegram est connecté, mais la source football "
            "n'est pas encore configurée. Aucun pronostic n'a été inventé."
        )
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url = (
        "https://v3.football.api-sports.io/fixtures?"
        + urllib.parse.urlencode({"date": today})
    )
    data = get_json(url, {
        "x-apisports-key": FOOTBALL_API_KEY
    })

    fixtures = data.get("response", [])
    if not fixtures:
        send_telegram(
            "⚽ Pronostics du jour\n"
            "Aucun match n'a été retourné par la source pour aujourd'hui. "
            "Cela ne signifie pas forcément qu'il n'y a aucun match."
        )
        return

    lines = [
        "⚽ MATCHS DU JOUR",
        "Date UTC : " + today,
        "",
        "Les données de match sont récupérées. Les pronostics ne seront "
        "publiés qu'après configuration et vérification des cotes."
    ]

    for item in fixtures[:15]:
        teams = item.get("teams", {})
        home = teams.get("home", {}).get("name", "Équipe domicile")
        away = teams.get("away", {}).get("name", "Équipe extérieure")
        time = item.get("fixture", {}).get("date", "")
        lines.append(f"• {home} – {away} ({time})")

    send_telegram("\n".join(lines))


if __name__ == "__main__":
    main()
