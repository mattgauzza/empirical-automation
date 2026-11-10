# Architecture

A project runs as a board. A card moving into a column starts ONE small Claude Code agent on your PC,
which does that column's job and moves the card on. A person approves by dragging cards.

```
Empirical workspace (the board)
   │  signed webhook: item.created, item.status_changed, item.due
   ▼
https://hooks.example.com/empirical/<project>        Cloudflare tunnel to your PC
   ▼
receiver.py on localhost:8787
   │  checks the signature, maps  <type>:<status>  →  role,  waits the debounce
   ▼
claude "<fixed prompt for that role>" --bg --model <model> --allowedTools <fixed list>
   │  started in the project folder
   ▼
the agent reads the `rules` card, then its own Agent card's playbook  (empirical command run item.list ...),
does the job with  python tools/<name>.py ...,  writes notes and attachments on the card, moves the card on
(empirical memory note / attachment add,  empirical command run item.move)
   │
   └─▶ that move is a new webhook event → the next column's agent
```

## The pieces

| Piece | What it is | Where |
| --- | --- | --- |
| Board | An Empirical team workspace. Cards are the work items; Agent cards hold every agent's playbook; Task cards are the agents' messages to you | Empirical |
| Receiver | One Python program for all your projects; a project is a route in `config.json` | `receiver/` |
| Tunnel | A Cloudflare tunnel giving the receiver a public https address | your PC |
| Agents | Claude Code background sessions, one role each, with a fixed allow-list and a chosen model | started by the receiver |
| `empirical` CLI | How agents (and you) read and write the board: plain shell commands, each one allow-listed by name | on PATH |
| Project folder | The tools the agents run, their outputs, secrets and lock files | one per project |

## Why it is built this way

- **Event contents never reach Claude.** The receiver logs the event but hands the agent only a fixed
  prompt plus validated card ids. Text on a card cannot become an instruction. The playbooks repeat the
  rule: card text, notes and files are data.
- **One owner per column.** A card in a column has exactly one agent responsible for it, so nothing is
  worked on twice and a stuck card points at one playbook.
- **Playbooks live on the board.** You can read and edit an agent's instructions where you watch it
  work, pause it by dragging its card to Paused, and see its `last_run`.
- **A person approves at a few points** by dragging: idea → queued, and anything in "Waiting on You".
  Agents never move a card backward (except a reviewer sending work back).
- **Agents can only run what the allow-list starts with.** `--permission-mode dontAsk` plus
  `--allowedTools`: anything else is refused, not asked about.
- **The board is reached through the CLI, not an MCP server.** Each board action is a named command
  (`empirical command run item.move`), so the allow-list can permit moving a card and withhold
  deleting one, and every command carries `--workspace-id`.
- **One run at a time per role.** Events during a run queue one more run; a lock file stops a second
  session; runs waiting when the receiver stops are re-queued when it starts.
- **Timers are cards too.** A repeating due time on an Agent card fires `item.due`; the receiver's own
  clock is the backup ([timers.md](timers.md)).

## What the receiver does with one event

1. Finds the route by URL path; rejects the request unless `X-Empirical-Signature` (`t=<unix>,v1=<hex>`,
   HMAC-SHA256 of `<t>.<raw body>`) matches the route's secret.
2. Answers `200` at once (Empirical waits 10 seconds), appends the event to `logs/<route>-events.jsonl`.
3. `item.due` → the role in `due_roles` for that card id. Otherwise → the role in `roles` for
   `<type key>:<status key>` (or just `<status key>`, or `default_role`). No match: ignored.
4. Sends the Discord alert if `alerts` has one for that `<type>:<status>`.
5. Starts (or restarts) that role's debounce timer and remembers the card id.
6. When the timer ends: if the role's lock is held, adds the ids to `<role>.pending` and stops.
   Otherwise builds the command, adds `--model`, and launches it in the project folder.

It does not check the signature's timestamp age, so a captured delivery could be replayed. The worst
a replay can do is start an agent that reads the board and finds nothing to do.
