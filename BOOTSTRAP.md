# Bootstrap prompt

Open Claude Code in your new, empty project folder (trust it when asked), make sure this repo is
cloned somewhere on the PC, and paste the prompt below with the three blanks filled in. It builds a
board-driven pipeline for **your** project, using this kit's receiver and the sample as a pattern.

```
Build a board-driven agent pipeline for this project, using the kit at <PATH TO empirical-automation>.

The project: <WHAT IT MAKES OR DOES, WHERE IT PUBLISHES, HOW OFTEN>.
The receiver is (or will be) at <RECEIVER FOLDER>, public address https://<HOST>/.

Read first, in this order: README.md, docs/architecture.md, docs/board.md, docs/playbooks.md,
docs/receiver-config.md, docs/permissions-and-models.md, docs/timers.md, docs/publishing.md,
docs/install.md, docs/troubleshooting.md, then examples/recipe-shorts/ as a worked example.
The sample's board shape (Recipe, Post, Agent, Task) is the SAMPLE's. Do not copy it.

Use the `empirical` command line tool for everything on the board (empirical command list,
empirical command help <name>, empirical doc webhook). Do not use an MCP server for it. Pass
--workspace-id on every command and put JSON arguments in a file (--args-file).

Work in this order and stop where it says stop:

1. DESIGN, then STOP. Before creating or building anything, propose the board for THIS project:
   the item types (one board per kind of thing that is made or published differently), each type's
   columns with the one owner of each (an agent role, me, or nobody), the fields each agent hands the
   next, the timers, the release rhythm, the two rejection loops (how work is sent back and fixed, and
   how my rejections and their reasons reach the ideas agent), and for every column I own, what a card must carry so I can
   decide from the card alone (attachments, links, notes). Show it as the column table from
   docs/board.md plus a list of agent roles with a one-line job each. Ask me what you can't know.
   Wait for my yes. Everything after this is written against the agreed shape.
2. Create the workspace, types, statuses and fields. Read the real keys back with shape.show.
   Bind this folder: empirical workspace use <workspace id> --project.
3. Scaffold the folder: CLAUDE.md, tools/, agents/, agents/.locks/, agents/args/list-agents.json,
   secrets/README.md, .gitignore (secrets/ never committed).
4. Write the tools: one script per job, a usage docstring at the top, safe to run twice, printing
   JSON. A build tool also writes the thing I will look at (a frame sheet, an image, a preview).
   A publish tool has an account guard, schedules only, and refuses duplicates. Run each one and show
   me the output.
5. Write agents/rules.md and one playbook per role from the templates in docs/playbooks.md, including
   the exact empirical commands table and the "what the owner needs to decide" section. Create one
   Agent card per file with the playbook in its playbook field.
6. Add the route to the receiver's config.json: path, project_dir, the fixed prompt, roles (from the
   real keys), debounce, lock_dir, models, alerts, and the shortest allow-list the playbooks need,
   every shell command listed for both Bash and PowerShell, every empirical command listed by name.
7. Register the webhook (events item.created, item.status_changed, item.due). Write the signing
   secret straight into config.json. Never show it to me or put it anywhere else. Send a test ping
   and confirm it in receiver.log.
8. Timers: due times on the Agent cards that run on a clock (dueEmail false), due_roles, the daily
   backup with timer_fallback_minutes.
9. Tell me exactly which sign-ins I must do myself, with the commands, and wait.
10. Walk the bring-up checklist in docs/install.md with one test card, one stage at a time, and report
    each line as passed or failed with the evidence from receiver.log. Do not publish anything real
    without asking me.

Rules throughout: never print, paste or commit secrets; never delete anything on the board; if a
step fails, say what failed and what you tried, don't work around it.
```

## Smaller prompts for later

Add a role:

```
Add a <role> agent to this project's pipeline: it owns the <Type> <Column> column and <one-line job>.
Follow docs/playbooks.md in the empirical-automation kit: write agents/<role>.md, create its Agent
card, add "<type>:<status>": "<role>" to the route's roles, and add only the commands it needs to
the allow-list. Then test it with one card and show me receiver.log.
```

Add a second board:

```
Add a <Type> board to this project's workspace for <what it is and where it goes>. Propose its
columns, owners, fields and what I need on a card to approve it, and wait for my yes. Then add the
type, the roles, the playbooks and the route entries, and walk one test card through it.
```

Change how an agent behaves:

```
The <role> agent keeps <what it does wrong>. Read its playbook (agents/<role>.md) and the last three
cards it handled, tell me which line of the playbook allows this, propose the smallest edit, and
after I agree update the file and the Agent card's playbook field.
```

Find out why nothing happened:

```
I dragged card "<title>" to <Column> at about <time> and no agent ran. Use docs/troubleshooting.md in
the empirical-automation kit: check receiver.log, the webhook's deliveries, claude agents and the
role's lock file, and tell me the cause and the fix. Don't change anything yet.
```

Run an agent now:

```
Start the <role> agent for this project now with a poke file in the receiver's pokes folder, then
tell me what it did from its notes and its Agent card's last_run.
```
