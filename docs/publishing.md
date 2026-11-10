# Step 5: publishing integrations

Publishing is the step that touches the outside world, so it gets the strictest rules. The sample
publishes to YouTube; the same rules fit any destination.

## Rules for any publish tool

1. **A script, not a prompt.** The agent runs `python tools/<publish>.py ...`; it never calls the
   service's API itself. What can go out is what the script allows.
2. **An account guard in the script.** Before doing anything, the script asks the service "which
   account am I?" and exits unless it is the one this project is for. A PC with several projects has
   several sign-ins; a guard makes the wrong one harmless.
3. **Its own token.** One token file per project, in that project's `secrets/`. Never shared.
4. **Schedule, never publish now.** Everything goes up private with a publish time. A person can
   still pull it before it is public.
5. **Refuse duplicates.** The script searches the destination for the same title first and reports
   `already_on_youtube` instead of uploading twice. Runs repeat.
6. **Sign-in is a person's job.** OAuth opens a browser. When the script says `Not authorized`, the
   playbook moves the card to "Waiting on You" with the exact command to run.
7. **A go-live check.** A timer after each release slot moves Scheduled cards to Published once the
   destination says they are public, and raises a Task for anything overdue or unknown.

## YouTube (the sample's `tools/youtube.py`)

One-time, by a person:

1. Google Cloud Console: a project, enable **YouTube Data API v3**, configure the OAuth consent
   screen, create an OAuth client of type **Desktop app**, download the JSON to
   `secrets/client_secret.json`. One client can serve several projects.
2. Publish the OAuth app (not "Testing"), or tokens expire every 7 days.
3. `secrets/channel.json` with the channel id (YouTube Studio → Settings → Channel → Advanced settings).
4. `pip install -r requirements.txt`, then `python tools/youtube.py auth` and pick the channel.

Then agents use:

```
python tools/youtube.py find "<exact title>"
python tools/youtube.py list
python tools/youtube.py upload output/<slug>/<slug>.mp4 output/<slug>/youtube.txt --publish-at 2030-01-15 --time 11:00
```

Each upload costs about 1,600 of the API's default 10,000 quota units a day: about six uploads a day.

## Steps only a browser can do

Some things have no API (on YouTube: community posts, end screens, the "related video" on a Short).
Options, in order of preference:

1. **Leave it to the person.** The agent makes a Task: what to click, with the links and text ready
   to paste. Cheapest and most reliable.
2. **A browser agent.** A role started in a visible window with Claude in Chrome
   (`role_commands`, [receiver-config.md](receiver-config.md)). Its playbook must: check which account
   the page is signed in to before every action, do one card at a time, take a screenshot as evidence,
   and stop at anything unexpected. The PC must be signed in and unlocked, and the run takes over a
   Chrome window.

Don't give a browser agent a job the API can do.

## Other destinations

Same shape: `tools/<service>.py` with `auth`, `list`, `find` and one write command that schedules.
Add its command prefix to the allow-list only if it isn't already covered by `python tools/`.
