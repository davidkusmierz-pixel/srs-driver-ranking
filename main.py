
import os
import re
import requests
import time
from urllib.parse import quote
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo


# ==================================================
# DISCORD WEBHOOK
# ==================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1540826456802992178/kCh8knUjF5cb1ZXGegpXEV4vNMHtjIFmEzTBx5iTrG_YgsEQ2ekMAhhcWPk40P895muo"


# ==================================================
# PSN ID : NAZWA NA DISCORDZIE
# ==================================================

PLAYERS = {
    "SolidSnakePoland": "RickyK",
    "ALF7": "SRS ALF7_VR2",
