# Step 3: wire the receiver (config.json)

`receiver/config.json` is gitignored: it holds signing secrets. Start from `config.example.json`.
Edits are picked up live (within about 20 seconds, or on the next event). Only a `port` change or a
change to `receiver.py` needs a restart.

## Top level

| Key | Meaning |
| --- | --- |
| `port` | Local port the receiver listens on (127.0.0.1 only). Default 8787 |
| `public_host`, `tunnel_name` | Your tunnel's hostname and name; used by `start.ps1` |
| `model` | Model every agent runs on unless a route or role overrides it. Set it: an agent never falls back to your account's default model |
| `command` | Default launch command for routes that have none |
| `shell` | `true` if `claude` is an npm `.cmd` shim rather than an `.exe` |
| `run_on_start` | `true`: one catch-up run of every mapped role a minute after the receiver starts |
| `sweep_sessions`, `sweep_hours` | Hourly: stop this pipeline's background sessions that are done, or blocked/idle longer than `sweep_hours` (default 6) |
| `keep_log_days`, `maintenance_day` | Weekly log clean-up (default 14 days, Sunday) |
| `discord_webhook` | Optional. A Discord channel webhook URL for `alerts` and failures |
| `routes` | One entry per project, keyed by URL path |

## A route

```json
"/empirical/recipe-shorts": {
  "name": "recipe-shorts",
  "secret": "PASTE_SECRET_HERE",
  "project_dir": "C:\\projects\\recipe-shorts",
  "prompt": "You are the {role} agent for this project. Your instructions are on the Empirical board Recipe Shorts (workspace id ws_team_...), which you read with the empirical command line tool. Run exactly: empirical command run item.list --workspace-id ws_team_... --args-file agents/args/list-agents.json Read the playbook field of the card named rules first, then the playbook of the card named {role}, and do exactly that job and nothing else. If your card is Paused or Retired, stop. Cards that triggered this run: {ids}.",
  "roles": { "recipe:queued": "builder", "recipe:built_in_review": "reviewer" }
}
```

| Key | Meaning |
| --- | --- |
| `name` | Short name used in log file names, pokes and alerts |
| `secret` | The webhook's signing secret. While it is empty or `PASTE_SECRET_HERE`, every POST to the route is rejected |
| `project_dir` | Folder the agent starts in (it loads that folder's `CLAUDE.md` and settings) |
| `prompt` | The fixed prompt. `{role}` and `{ids}` are filled in. It must name the workspace id. Nothing from the event except validated card ids ever goes in |
| `roles` | `"<type key>:<status key>"` → role, or a list of roles. A bare `"<status key>"` also works. Keys come from `shape.show` |
| `default_role` | Role for events whose status has no entry (rarely wanted) |
| `debounce_seconds` | Quiet time after the last event before the run (default 600). 60 suits a board you drag by hand |
| `role_debounce_seconds` | Per-role override, e.g. a longer wait for a role that should batch |
| `daily` | Local-clock timers: `"08:00": ["custodian"]`, `"Sat 09:00": ["ideas"]`. See [timers.md](timers.md) |
| `due_roles` | Agent card id → role (or list), for an Agent card's own timer. Also `"<type key>:due"` → role, for a due time on a work card, started with that card's id ([timers.md](timers.md)) |
| `timer_fallback_minutes` | Above 0: the `daily` timers are only a backup, firing this many minutes late and only if Empirical's timer didn't |
| `lock_dir` | e.g. `agents/.locks`. A run is skipped while `<role>.lock` there is held; its card ids go to `<role>.pending` |
| `model`, `role_models` | Model for the route, and per role: `{"ideas": "opus"}` |
| `command` | The launch command for this route (below) |
| `role_commands`, `role_shell` | A different launch command for one role, e.g. a visible window (below) |
| `alerts` | `"<type>:<status>"` → message posted to Discord when a card enters that column |
| `board_url` | Link added to alerts |

## The launch command

A list; `{prompt}` is replaced by the route's prompt, and `--model <model>` is inserted right after it.

```json
"command": ["claude", "{prompt}", "--bg", "--permission-mode", "dontAsk",
            "--allowedTools", "Read", "Edit", "Write", "Glob", "Grep",
            "Bash(python tools/:*)", "PowerShell(python tools/:*)",
            "Bash(empirical command run item.list:*)", "PowerShell(empirical command run item.list:*)",
            "Bash(empirical command run item.move:*)", "PowerShell(empirical command run item.move:*)",
            "Bash(empirical memory note:*)", "PowerShell(empirical memory note:*)"]
```

(`config.example.json` has the full list.)

- `--bg` starts a background session: no window, listed by `claude agents`.
- `--permission-mode dontAsk` + `--allowedTools`: what's on the list runs, everything else is
  refused without asking. See [permissions-and-models.md](permissions-and-models.md).
- Add `--add-dir <path>` if agents must write outside the project folder (for example the receiver's
  `pokes/` folder, so one agent can start another).

A role that must drive a browser needs a visible window instead of a background session:

```json
"role_commands": {
  "poster": ["cmd", "/c", "start", "Recipe Shorts {role}", "/D", "C:\\projects\\recipe-shorts",
             "claude", "{prompt}", "--chrome", "--permission-mode", "dontAsk",
             "--allowedTools", "mcp__claude-in-chrome", "Read", "Write",
             "PowerShell(empirical command run item.list:*)", "..."]
},
"role_shell": { "poster": false }
```

## Register the webhook

```
empirical webhook add https://hooks.example.com/empirical/recipe-shorts --events item.created,item.status_changed,item.due --workspace-id ws_team_...
```

- It prints the signing secret **once**. Write it straight into the route's `secret`. Never paste it
  into chat, a card or a log.
- Subscribe to `item.created`, `item.status_changed` and `item.due` only. With `item.updated` or
  `note.added`, every note or field an agent writes on a card in its own column starts that agent again.
- `--item-types recipe,agent` limits it further if the board has types no agent handles.

Test it:

```
empirical webhook test <webhook id>                                  # a ping
empirical webhook test <webhook id> --event item.due --item <agent card id>
empirical webhook deliveries <webhook id>                            # delivered? what did we answer?
```

`receiver/logs/receiver.log` should show `event ping`, then for the second `run in 60s (Empirical timer (item.due))`.

## Starting an agent by hand

Drop a file named `<route name>.<role>` into `receiver/pokes/` (card ids inside, one per line, or
empty). The receiver picks it up within 20 seconds:

```
New-Item receiver\pokes\recipe-shorts.custodian
```

## Logs

| File | What |
| --- | --- |
| `logs/receiver.log` | Every event, decision and launch, for all routes |
| `logs/<route>-<role>-<time>.log` | The launch output of one run (for `--bg`, the session id) |
| `logs/<route>-events.jsonl` | Every event received, as sent |
| `logs/pending.json`, `logs/state.json` | Runs waiting; which timers fired today |
| `logs/tunnel.log` | cloudflared |

What an agent actually did is in its session: `claude agents`, then open it.
