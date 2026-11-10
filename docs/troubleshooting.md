# Troubleshooting and lessons learned

Start with `receiver/logs/receiver.log`. It records every event, what the receiver decided, and every
launch. Then `empirical webhook deliveries <id>`, then `claude agents`.

## Nothing happens when a card moves

| `receiver.log` says | Cause and fix |
| --- | --- |
| Nothing at all | The event never arrived. `empirical webhook deliveries <id>`: failing → the tunnel or receiver is down (open `https://<host>/`). No delivery listed → the webhook is off (20 failures in a row turn it off: `empirical webhook update <id> --enable`), doesn't subscribe to that event, or is limited to other item types |
| `rejected: bad signature` | The route's `secret` is wrong, or still `PASTE_SECRET_HERE`. If the secret is lost: `empirical webhook rotate-secret <id>` and store the new one |
| `no agent for status 'x', ignored` | No `roles` entry for `<type key>:<status key>`. Check the real keys with `shape.show` |
| `run in 60s` and then nothing | Still inside the debounce, or the receiver was restarted (waiting runs are re-queued 30 s after start) |
| `another run holds the lock` | A session of that role is working or died holding the lock. The card ids went to `<role>.pending`. A dead lock frees itself after 3 hours; to free it now, write `RELEASED` into the lock file |
| `can't find 'claude'` | Scheduled tasks get a shorter PATH. Put the full path to `claude` first in `command` |
| `launched, exit code 0` but no work | The session started. `claude agents`: `blocked` = it is waiting on a permission (next section) |
| 404 in `webhook deliveries` | The webhook URL's path doesn't match a route key exactly |

Events missed while the PC was off: Empirical retries for about 15 hours (1 min, 5 min, 30 min, 2 h,
12 h). After that, drag the card out of and back into its column, or poke the role.

## An agent starts but can't do its job

- **Blocked on a permission.** A command wasn't on the allow-list. Usual reasons: it was chained
  (`cd x && ...`), used an absolute script path, ran in PowerShell when only `Bash(...)` was listed
  (or the reverse), or was an `empirical` command not on the list. Fix `config.json` (live), then
  re-trigger the card.
- **"All shell commands are blocked."** One refusal made the agent give up. The `rules` card must say
  the exact allowed shape and "reshape and retry".
- **Every `empirical` command fails.** The CLI isn't signed in for the account the task runs as
  (`empirical auth status`), or isn't on the scheduled task's PATH (use its full path in the allow-list
  and the rules). A reply with `error: true` and a code is the server refusing: read the message.
- **An `empirical command run` fails on its arguments.** Inline JSON lost its quotes in the shell.
  Write the JSON to a file and use `--args-file`.
- **A note lost part of its text.** The shell ate a backtick, `$` or quote. Notes are plain one-line
  text; anything else goes in a file that is attached.
- **Background sessions don't start at all.** The project folder was never trusted: open `claude`
  there once and accept.
- **It runs on the wrong model.** Set `model` in `config.json`; the receiver then passes `--model` on
  every launch.
- **Old stuck sessions pile up.** The hourly sweep stops this pipeline's sessions that are done, or
  blocked/idle for more than `sweep_hours`. `claude agents` to see them, `claude stop <id>` to stop one.

## Board mistakes

- **A card or note landed in another project's workspace.** A command without `--workspace-id` fell
  back to the machine-wide selection, which another session had changed. Pass the flag on every
  command, and bind the folder (`empirical workspace use <id> --project`) as a backstop.
- **An agent wiped its own playbook.** It wrote the Agent card's fields with a patch that replaces the
  whole field set (`empirical memory update`), sending only `last_run`. Use `item.update`, which
  merges; leave `memory update` off the allow-list.
- **An agent keeps restarting itself.** The webhook subscribes to `item.updated` or `note.added`, so
  its own notes trigger it. Subscribe to `item.created`, `item.status_changed`, `item.due` only.
- **A status key isn't what you expected.** Keys are made from the first label and never change.
  Never type one from memory; read `shape.show`.
- **Two agents worked the same card.** Two roles are mapped to one column, or an agent worked a card
  outside its column. One owner per column; "only your cards" in the rules.
- **The same thing was published twice.** The publish step wasn't safe to repeat. The tool must look
  for the title first; the playbook must "check before doing".
- **A timer fired twice or not at all.** Twice: `daily` and the card's due time both primary; set
  `timer_fallback_minutes`. Not at all: the webhook doesn't subscribe to `item.due`, the card id isn't
  in `due_roles`, the Agent card isn't Active, or `dueEmail` isn't `false`.
- **The person stopped looking at the board.** Cards arrived with nothing to judge. See "Give the
  person what they need to decide" in [playbooks.md](playbooks.md).

## Receiver and PC

- **The receiver froze and deliveries timed out.** It was run in a console window and someone clicked
  in it (Windows pauses a console program while text is selected). Run it with `pythonw` through
  `start.ps1`; it logs to a file only.
- **A code change to `receiver.py` did nothing.** Config reloads live; code doesn't. Restart the task:
  `Start-ScheduledTask -TaskName "Board hooks receiver"`.
- **`config.json has an error, keeping the old settings`.** A JSON typo. The old settings stay in
  force until the file parses.
- **Clock times in agents' notes are wrong.** Models guess the time. Have them read it with a command
  (`Get-Date`, `date`) that is on the allow-list.
- **A browser agent did nothing.** The PC was locked or Chrome wasn't signed in. Browser roles need a
  signed-in, unlocked desktop; prefer an API or a Task for the person.
- **The publish tool says `Not authorized` every week.** The Google OAuth app is still in "Testing"
  (7-day tokens). Publish the app.

## Security notes

- `config.json` holds signing secrets, `secrets/` holds tokens: both gitignored. Never paste either
  into chat, a card, a note or an issue.
- The receiver listens on 127.0.0.1 only; the tunnel is the only way in, and every POST needs a valid
  signature for its route.
- Agents get card ids from an event, never its text. Keep it that way if you change the prompt.
- The allow-list is the security boundary. Read it as "what could a confused agent do with this?"
