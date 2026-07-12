#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator

PODCAST_PAGE_URL = "https://www.revenudebase.info/podcasts/"
SITE_URL = PODCAST_PAGE_URL
RSS_SELF_URL = "https://TON_USER.github.io/mfrb-podcast-rss/rss.xml"  # à ajuster après activation de Pages


def fetch_episodes():
    resp = requests.get(PODCAST_PAGE_URL, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    episodes = []

    # On cherche des titres d'épisodes (Ep. X ...)
    for h in soup.select("h3"):
        title = h.get_text(strip=True)
        if title in ["À propos", "Contribuer", "Ressources", "Partenaires", "Privacy Preference Center"]:
            continue

        # On collecte le premier paragraphes p de description
        description = None
        p = h.find_next("p")
        if p:
            description = p.get_text(strip=True)

        # On cherche l’URL mp3 dans les balises <audio>
        mp3_url = None
        audio = h.find_next("audio")
        if audio:
            source = audio.find("source")
            if source and source.has_attr("src"):
                mp3_url = source["src"]

        # On extrait la date de l'url
        pub_date = None
        if mp3_url:
            date_parts = mp3_url.split("/")[-3:-1]
            if len(date_parts) == 2:
                try:
                    pub_date = datetime.strptime(f"{date_parts[0]}-{date_parts[1]}", "%Y-%m")
                    # On ajoute l'info de timezone : UTC
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
        if pub_date is None:
            pub_date = datetime.now(timezone.utc)

        episodes.append(
            {
                "title": title,
                "description": description,
                "mp3_url": mp3_url,
                "pub_date": pub_date,
            }
        )

    return episodes


def build_rss(episodes):
    fg = FeedGenerator()
    fg.load_extension("podcast")

    fg.title("Tous Essentiels – Revenu de base")
    fg.link(href=RSS_SELF_URL, rel="self")
    fg.link(href=SITE_URL, rel="alternate")
    fg.description("Podcasts du MFRB sur le revenu de base")

    for ep in episodes:
        fe = fg.add_entry()
        fe.id(ep["mp3_url"] or ep["title"])
        fe.title(ep["title"])

        if ep["description"]:
            fe.description(ep["description"])

        if ep["pub_date"]:
            fe.pubDate(ep["pub_date"])

        if ep["mp3_url"]:
            fe.enclosure(ep["mp3_url"], 0, "audio/mpeg")

    return fg.rss_str(pretty=True)


def main():
    episodes = fetch_episodes()
    xml = build_rss(episodes)

    with open("rss.xml", "wb") as f:
        f.write(xml)


if __name__ == "__main__":
    main()