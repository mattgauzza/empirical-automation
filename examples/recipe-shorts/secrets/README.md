# secrets/

Everything in this folder except this file is gitignored. Nothing here is ever pasted into chat, a
card, a note or a log.

| File | Where it comes from |
| --- | --- |
| `client_secret.json` | Google Cloud Console → APIs & Services → Credentials → Create OAuth client ID → **Desktop app** → Download JSON. Enable **YouTube Data API v3** on the same project. One client can be copied into several projects. |
| `channel.json` | You write it: the one channel this project may touch (below). |
| `youtube-token.json` | Written by `python tools/youtube.py auth`. One per project; never copy it between projects. |

`channel.json`:

```json
{"id": "UCxxxxxxxxxxxxxxxxxxxxxx", "name": "Your Channel", "timezone": "America/New_York", "category": "26"}
```

`id` is the channel id from YouTube Studio → Settings → Channel → Advanced settings. `category` is a
YouTube category id (26 = Howto & Style, 22 = People & Blogs).

The sign-in (`auth`) opens a browser, so a person runs it once. If the wrong channel is picked, the
script says `WRONG CHANNEL`, sets the token aside and changes nothing: run `auth` again.

While the Google OAuth app is in "Testing", its tokens expire after 7 days. Publish the app (and
verify it if Google asks) so the agents don't lose their sign-in every week.
