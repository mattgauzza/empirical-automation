# Publisher

**Trigger:** Recipe cards in Approved. Daily 11:15 timer: go-live check (after the 11:00 release).
**Job:** get approved Shorts onto the channel, scheduled, through the API (no browser):
`python tools/youtube.py find "<title>"`, `python tools/youtube.py list`,
`python tools/youtube.py upload <mp4> <youtube.txt> --publish-at <YYYY-MM-DD> --time 11:00`.
The script checks it is signed in to the right channel and refuses otherwise. Subscriber
notifications stay off (no `--notify`).

**Rhythm: Tuesday, Thursday and Saturday, 11:00 AM.** One Short per slot, never two on a day, nothing
on other days (unless the owner set that date on the card).

If a command says `Not authorized` or `WRONG CHANNEL`: move the card to **Waiting on You** with the note
`publisher: run in the project folder: python tools/youtube.py auth (pick the right channel), then drag this back to Approved`.

## Approved (oldest card first)
1. Check first: `find` the title (line 1 of `<folder>/youtube.txt`). Already there? Record its id and
   date and skip to step 4.
2. Date: the card's `publish_date` if the owner set one (keep it unless that day already has a Short).
   Otherwise the next free Tue/Thu/Sat slot: check every Scheduled and Published card's `publish_date`
   AND `list` (`publishAt`). Today's slot only counts if 11:00 is more than 30 minutes away.
3. `upload <folder>/<slug>.mp4 <folder>/youtube.txt --publish-at <date> --time 11:00`.
4. Set `youtube_url` (the full `https://youtube.com/shorts/<id>` link) and `publish_date`. Note
   `publisher: scheduled <date> 11:00 AM <url>`, so the owner can open it and pull it before it is
   public. Move to **Scheduled**.

## Daily 11:15 go-live check
- `list`. Every Scheduled card whose video is now `public`: move to **Published**.
- A Scheduled card whose date has passed but isn't public: note it and make a Task in To do.
- Anything on the channel with no card: a Task in To do.

Set your Agent card's `last_run`.
