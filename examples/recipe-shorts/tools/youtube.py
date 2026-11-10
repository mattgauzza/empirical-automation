"""YouTube uploads for ONE channel, with a channel guard (refuses any other channel).

One-time:  python tools/youtube.py auth          # a person does this: Google sign-in, pick the channel
Upload:    python tools/youtube.py upload <mp4> <youtube.txt> --publish-at 2030-01-15 [--time 11:00] [--notify]
Find:      python tools/youtube.py find "<exact title>"
List:      python tools/youtube.py list           # every upload: id, title, privacy, publishAt

youtube.txt: first line = title, rest = description. Always scheduled (private until publishAt), never
public immediately. Refuses a title that is already on the channel. Subscriber notifications are off
unless --notify.

Setup (see secrets/README.md): secrets/client_secret.json (a Google Cloud "Desktop app" OAuth client
with the YouTube Data API v3 enabled) and secrets/channel.json:
  {"id": "UCxxxxxxxxxxxxxxxxxxxxxx", "name": "Your Channel", "timezone": "America/New_York", "category": "26"}
The token is saved to secrets/youtube-token.json. Keep one token per project: never share it.
  pip install -r requirements.txt
"""
import argparse, datetime, json, sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "secrets"
CLIENT, TOKEN, CHANNEL = SECRETS / "client_secret.json", SECRETS / "youtube-token.json", SECRETS / "channel.json"
SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]


def channel():
    if not CHANNEL.exists():
        sys.exit("No secrets/channel.json. See secrets/README.md.")
    c = json.loads(CHANNEL.read_text(encoding="utf-8"))
    if not str(c.get("id", "")).startswith("UC") or "x" * 6 in c["id"]:
        sys.exit("secrets/channel.json still has the placeholder channel id. Put your real one in.")
    return c


def _creds(interactive=False):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = Credentials.from_authorized_user_file(str(TOKEN)) if TOKEN.exists() else None
    if creds and not set(SCOPES) <= set(creds.scopes or []):
        creds = None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request()); TOKEN.write_text(creds.to_json())
    if not creds or not creds.valid:
        if not interactive:
            sys.exit("Not authorized. A person runs once: python tools/youtube.py auth")
        from google_auth_oauthlib.flow import InstalledAppFlow
        creds = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES).run_local_server(port=0)
        SECRETS.mkdir(exist_ok=True); TOKEN.write_text(creds.to_json())
    return creds


def api(interactive=False):
    """The API client, but only if the signed-in channel is the one in secrets/channel.json."""
    from googleapiclient.discovery import build
    want = channel()
    yt = build("youtube", "v3", credentials=_creds(interactive), cache_discovery=False)
    ch = yt.channels().list(part="snippet", mine=True).execute().get("items", [])
    got = (ch[0]["id"], ch[0]["snippet"]["title"]) if ch else ("none", "none")
    if got[0] != want["id"]:
        if interactive and TOKEN.exists():
            TOKEN.replace(TOKEN.with_name("wrong-channel-token.json.old"))
        sys.exit(f"WRONG CHANNEL: signed in as {got[1]} ({got[0]}), expected {want.get('name', '?')} "
                 f"({want['id']}). Nothing was changed. Run auth again and pick the right channel.")
    return yt


def my_videos(yt):
    pl = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    out, tok = [], None
    while True:
        r = yt.playlistItems().list(part="snippet", playlistId=pl, maxResults=50, pageToken=tok).execute()
        ids = [i["snippet"]["resourceId"]["videoId"] for i in r["items"]]
        if ids:
            v = yt.videos().list(part="snippet,status", id=",".join(ids)).execute()
            out += [{"id": x["id"], "title": x["snippet"]["title"], "privacy": x["status"]["privacyStatus"],
                     "publishAt": x["status"].get("publishAt")} for x in v["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            return out


def publish_at(date, hhmm):
    tz = ZoneInfo(channel().get("timezone", "America/New_York"))
    d = datetime.datetime.fromisoformat(f"{date}T{hhmm}:00").replace(tzinfo=tz)
    if d <= datetime.datetime.now(tz) + datetime.timedelta(minutes=15):
        sys.exit(f"Publish time {d} is less than 15 min away; pick a later time.")
    return d.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def upload(mp4, txt, date, hhmm, notify=False):
    from googleapiclient.http import MediaFileUpload
    lines = Path(txt).read_text(encoding="utf-8").splitlines()
    title, desc = lines[0].strip(), "\n".join(lines[1:]).strip()
    when = publish_at(date, hhmm)
    yt = api()
    dup = [v for v in my_videos(yt) if v["title"].strip() == title]
    if dup:
        print(json.dumps({"already_on_youtube": dup}, indent=1)); return
    body = {"snippet": {"title": title, "description": desc, "categoryId": str(channel().get("category", "22"))},
            "status": {"privacyStatus": "private", "publishAt": when, "selfDeclaredMadeForKids": False}}
    req = yt.videos().insert(part="snippet,status", body=body, notifySubscribers=notify,
                             media_body=MediaFileUpload(str(mp4), chunksize=16 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st:
            print(f"uploading {int(st.progress() * 100)}%", flush=True)
    print(json.dumps({"id": resp["id"], "url": f"https://youtube.com/shorts/{resp['id']}", "title": title,
                      "publishAt": when, "notifySubscribers": notify}, indent=1))


if __name__ == "__main__":
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("auth")
    f = s.add_parser("find"); f.add_argument("title")
    s.add_parser("list")
    u = s.add_parser("upload"); u.add_argument("mp4"); u.add_argument("txt")
    u.add_argument("--publish-at", required=True); u.add_argument("--time", default="11:00")
    u.add_argument("--notify", action="store_true")
    a = p.parse_args()
    if a.cmd == "auth":
        api(interactive=True); print(f"Authorized for {channel().get('name')} ({channel()['id']})")
    elif a.cmd == "list":
        print(json.dumps(my_videos(api()), indent=1))
    elif a.cmd == "find":
        print(json.dumps([v for v in my_videos(api()) if v["title"].strip() == a.title.strip()], indent=1))
    else:
        upload(a.mp4, a.txt, a.publish_at, a.time, a.notify)
