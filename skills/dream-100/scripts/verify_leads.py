#!/usr/bin/env python3
"""Batched verification for the Dream 100 skill (YouTube-platform candidates).

Verifies ALL YouTube candidates in one run: canonical handle, subscriber
count, last-upload date (activity gate), plus emails and link-in-bio URLs
mined from the channel description and the last 5 video descriptions.
Prints ONE compact TSV line per candidate — raw API JSON never reaches chat.

Instagram/LinkedIn/other candidates aren't covered by this script (no free
API) — verify those manually via a live page fetch or search snippet per the
skill's Step 3.

Usage:
  python verify_leads.py --candidates candidates.json --env "[C] api-keys.env" [--range 10000-100000] [--months 6]

candidates.json: [{"name": "...", "handle": "@x" | "youtube.com/... url", "channelId": "UC..."}]
(handle/channelId optional — but only include them if seen on a live page.)
Non-YouTube entries (platform != youtube, or no handle/channelId) are skipped
with DROP_not_youtube — verify those by hand instead.

API cost: ~1-3 units per candidate (channels batched 50/call + 1 playlistItems each).
"""
import argparse, json, re, subprocess, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

API = "https://www.googleapis.com/youtube/v3"
FIELDS_CH = "items(id,snippet(title,customUrl,description),statistics(subscriberCount,hiddenSubscriberCount),contentDetails/relatedPlaylists/uploads)"

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
JUNK = re.compile(r"\.(png|jpe?g|gif|webp|svg)$|example\.|sentry|wixpress|schema\.org|w3\.org|youtube\.com|gstatic|googleusercontent|@2x|no-?reply|^test@", re.I)
BIO_RE = re.compile(r"https?://(?:www\.)?(?:linktr\.ee|beacons\.(?:ai|page)|stan\.store|bio\.link|linkin\.bio|taplink\.cc|solo\.to|hoo\.be|withkoji\.com)/[^\s\"'<>)\]]+", re.I)
URL_RE = re.compile(r"https?://(?:www\.)?([a-z0-9-]+(?:\.[a-z0-9-]+)+)", re.I)
SOCIAL = {"youtube.com", "youtu.be", "instagram.com", "tiktok.com", "twitter.com", "x.com",
          "facebook.com", "discord.gg", "discord.com", "t.me", "open.spotify.com",
          "goo.gl", "google.com", "bit.ly", "amzn.to", "amazon.com", "linkedin.com",
          "whatsapp.com", "patreon.com", "twitch.tv"}


def http_get(url):
    """curl first (sandboxes often allow curl but reset python sockets), urllib fallback."""
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "30", url],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
    except FileNotFoundError:
        pass
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8")  # googleapis puts the error details in the body


def api(endpoint, **params):
    data = json.loads(http_get(f"{API}/{endpoint}?{urllib.parse.urlencode(params)}"))
    if isinstance(data, dict) and data.get("error"):
        err = data["error"]
        if err.get("code") in (400, 401, 403, 429):
            sys.exit(f"API_ERROR {err.get('code')}: {err.get('message', '')} — key missing/invalid "
                     f"or quota exhausted; fall back to the curl method in SKILL.md")
        raise RuntimeError(f"API error: {err}")
    return data


def mine(text):
    """Emails + contact links from free text, junk-filtered, deduped, capped."""
    emails, links, seen = [], [], set()
    for e in EMAIL_RE.findall(text or ""):
        el = e.lower()
        if el not in seen and not JUNK.search(el):
            seen.add(el); emails.append(el)
    for u in BIO_RE.findall(text or ""):
        if u.lower() not in seen:
            seen.add(u.lower()); links.append(u)
    extras = []
    for m in URL_RE.finditer(text or ""):
        d = m.group(1).lower()
        if d not in SOCIAL and d not in seen and not any(d in l.lower() for l in links):
            seen.add(d); extras.append(d)
    return emails[:3], (links + extras[:2])[:4]


def norm_candidate(c):
    h = (c.get("handle") or "").strip()
    if "youtube.com" in h or "youtu.be" in h:
        m = re.search(r"/channel/(UC[\w-]+)", h)
        if m:
            c["channelId"] = m.group(1); h = ""
        else:
            m = re.search(r"@([^/?\s]+)", h)
            h = m.group(1) if m else ""
    c["handle"] = h.lstrip("@")
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--env", help="path to api-keys.env containing YOUTUBE_API_KEY=...")
    ap.add_argument("--key", help="API key directly (prefer --env, keeps the key out of chat)")
    ap.add_argument("--range", default="", help="optional subscriber-count filter, e.g. 10000-100000")
    ap.add_argument("--months", type=int, default=6, help="activity gate in months")
    a = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    key = a.key
    if not key and a.env:
        for line in open(a.env, encoding="utf-8-sig"):
            if line.strip().startswith("YOUTUBE_API_KEY"):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("API_ERROR: no key — pass --env or --key, or fall back to the curl method")

    lo = hi = None
    if a.range:
        lo, hi = (int(x) for x in a.range.replace(",", "").replace("K", "000").split("-"))

    raw = json.load(open(a.candidates, encoding="utf-8-sig"))
    yt = [c for c in raw if c.get("platform", "youtube").lower() == "youtube"
          and (c.get("handle") or c.get("channelId"))]
    skipped_non_yt = len(raw) - len(yt)
    cands = [norm_candidate(c) for c in yt]

    # Resolve channels: batch by channelId (50/call), then per-handle for the rest
    info = {}
    by_id = [(i, c["channelId"]) for i, c in enumerate(cands) if c.get("channelId")]
    for j in range(0, len(by_id), 50):
        chunk = by_id[j:j + 50]
        data = api("channels", part="snippet,statistics,contentDetails",
                   id=",".join(cid for _, cid in chunk), fields=FIELDS_CH, key=key)
        found = {it["id"]: it for it in data.get("items", [])}
        for i, cid in chunk:
            if cid in found:
                info[i] = found[cid]
    for i, c in enumerate(cands):
        if i in info or not c.get("handle"):
            continue
        data = api("channels", part="snippet,statistics,contentDetails",
                   forHandle="@" + c["handle"], fields=FIELDS_CH, key=key)
        items = data.get("items", [])
        if items:
            info[i] = items[0]

    now = datetime.now(timezone.utc)
    kept = dropped = 0
    print("name\thandle\tsubs\tlast_upload\tverdict\temails\tlinks")
    for i, c in enumerate(cands):
        name = c.get("name", "?")
        it = info.get(i)
        if not it:
            print(f"{name}\t-\t-\t-\tDROP_not_found\t\t")
            dropped += 1
            continue
        handle = (it.get("snippet", {}).get("customUrl") or "").lstrip("@") or "-"
        st = it.get("statistics", {})
        subs = None if st.get("hiddenSubscriberCount") else int(st.get("subscriberCount", 0) or 0)
        subs_s = str(subs) if subs is not None else "?"
        text = it.get("snippet", {}).get("description", "") or ""
        last = None
        up = it.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        if up:
            try:
                pl = api("playlistItems", part="snippet", playlistId=up, maxResults=5,
                         fields="items/snippet(publishedAt,description)", key=key)
                sn = [x["snippet"] for x in pl.get("items", [])]
                if sn:
                    last = max(s["publishedAt"] for s in sn)
                    text += "\n" + "\n".join(s.get("description", "") for s in sn)
            except SystemExit:
                raise
            except Exception:
                pass
        emails, links = mine(text)
        if not last:
            print(f"{name}\t@{handle}\t{subs_s}\t-\tDROP_no_uploads\t{';'.join(emails)}\t{' '.join(links)}")
            dropped += 1
            continue
        d = datetime.fromisoformat(last.replace("Z", "+00:00"))
        ym = d.strftime("%Y-%m")
        if (now - d).days / 30.44 > a.months:
            print(f"{name}\t@{handle}\t{subs_s}\t{ym}\tDROP_dormant\t\t")
            dropped += 1
            continue
        verdict = "OK"
        if subs is None:
            verdict = "OK_subs_hidden"
        elif lo and subs < lo:
            verdict = "OK_size_low"
        elif hi and subs > hi:
            verdict = "OK_size_high"
        kept += 1
        print(f"{name}\t@{handle}\t{subs_s}\t{ym}\t{verdict}\t{';'.join(emails)}\t{' '.join(links)}")
    if skipped_non_yt:
        print(f"# {skipped_non_yt} non-YouTube candidate(s) skipped — verify those manually")
    print(f"# kept {kept} / dropped {dropped} of {len(cands)}")


if __name__ == "__main__":
    main()
