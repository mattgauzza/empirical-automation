# Install and bring-up

Written for Windows (the start-up scripts are PowerShell). `receiver.py` itself runs anywhere Python
does; on another OS, start it and the tunnel your own way.

## What only a person can do

An agent can do everything else in this file. These need you:

- Browser sign-ins: `cloudflared tunnel login`, `claude` login, the `empirical` CLI login, the
  publish tool's OAuth (`python tools/youtube.py auth`).
- Accepting the trust prompt the first time `claude` opens the project folder.
- Running `install-startup.ps1` once, and restarting the task after a change to `receiver.py`.
- Agreeing the board shape, and approving cards.

## Once per PC

1. **Python 3.9+** on PATH (`python --version`). The receiver needs no packages.
2. **Claude Code** on PATH (`claude --version`), signed in.
3. **Empirical**: an account on a plan with webhooks, timers and attachments, and the `empirical`
   CLI on PATH and signed in (`empirical install`; check with `empirical auth status` and
   `empirical command list`). The whole kit uses the CLI; no MCP server is needed.
4. **A public https address for the receiver.** With Cloudflare Tunnel and a domain on Cloudflare:
   ```
   winget install --id Cloudflare.cloudflared
   cloudflared tunnel login                         # browser: pick your domain
   cloudflared tunnel create board-hooks
   cloudflared tunnel route dns board-hooks hooks.example.com
   ```
   Open a new PowerShell window after the winget install so `cloudflared` is on PATH.
5. **The receiver.** Copy this repo's `receiver/` folder somewhere permanent (for example
   `C:\projects\hooks`). Copy `config.example.json` to `config.json`; set `public_host` and
   `tunnel_name`; leave the route's secret as `PASTE_SECRET_HERE` for now.
6. `powershell -ExecutionPolicy Bypass -File install-startup.ps1`, once. It starts the receiver and
   tunnel now and at every sign-in.
7. Check: `https://hooks.example.com/` in a browser says `hooks receiver running`.
8. Whatever your tools need (the sample: `ffmpeg` on PATH; for uploads `pip install -r requirements.txt`).

## Once per project

Do these in order. Step 1 comes first for a reason: everything after it is written against the shape.

1. **Agree the board shape** with the person who will approve cards: types, columns and who owns
   each, fields, timers, what a card must carry when it reaches them. [board.md](board.md)
2. **Create the workspace, types, statuses and fields.** Read the real keys back with `shape.show`.
3. **Project folder**: `CLAUDE.md` (with the workspace id), `tools/`, `agents/`, `agents/.locks/`,
   `agents/args/list-agents.json`, `secrets/`, a `.gitignore` covering `secrets/`. Bind it:
   `empirical workspace use ws_team_... --project`. Open `claude` in it once and accept the trust prompt.
4. **Tools**: one script per job, each with a usage docstring, each safe to run twice. Run each by hand.
5. **Playbooks**: `agents/rules.md` and one per role, then an Agent card for each. [playbooks.md](playbooks.md)
6. **Route** in `config.json`: path, `project_dir`, prompt (with the workspace id), `roles`, allow-list,
   models, `lock_dir`. [receiver-config.md](receiver-config.md), [permissions-and-models.md](permissions-and-models.md)
7. **Webhook**: `empirical webhook add ...`; put the secret in the route; `empirical webhook test <id>`.
8. **Timers**: due times on Agent cards, `due_roles`, the `daily` backup. [timers.md](timers.md)
9. **Publishing**: secrets in place, the person signs in once. [publishing.md](publishing.md)
10. **Bring-up** (below).

## Bring-up checklist

Go one stage at a time. Don't drag a card to the next column until the stage before it is clean.

- [ ] `receiver.log` shows `listening on http://localhost:8787  routes: ...` with your route.
- [ ] `empirical webhook test <id>` → `receiver.log` shows `event ping`; `webhook deliveries` says delivered.
- [ ] A request with a wrong signature is rejected (`rejected: bad signature` in the log).
- [ ] Poke the simplest agent (`pokes\<route>.custodian`). `claude agents` lists a session in the
      project folder; it finishes; its Agent card's `last_run` is set; nothing was refused.
- [ ] Create one test card and drag it into the first agent-owned column. Within the debounce the log
      shows `run in 60s (item.status_changed -> queued)`, then `starting Claude`. The agent leaves a
      "started" note, does the work, attaches what the rules ask for, and moves the card on.
- [ ] That move starts the next agent by itself. Follow the card to the last column before publishing.
- [ ] Send one back: make the reviewer fail something on purpose, and watch Needs Fixes → the builder →
      back to review.
- [ ] Drag the same card out and in twice quickly: one run, not two (debounce), and no second session
      while the first holds the lock.
- [ ] Publish one for real, scheduled far enough ahead to pull it. Check it on the destination.
- [ ] `empirical webhook test <id> --event item.due --item <agent card id>` starts the timed role.
- [ ] Pause an Agent card and trigger it: the agent stops at once. Set it back to Active.
- [ ] Sign out and in (or restart the PC): the receiver and tunnel come back by themselves.
- [ ] Leave it for a day: the custodian's morning Task is either absent (all clear) or accurate.

When something doesn't happen, read `receiver.log` first: it says what arrived and what it decided.
Then [troubleshooting.md](troubleshooting.md).
