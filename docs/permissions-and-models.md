# Permissions and models

## The allow-list

Agents run with `--permission-mode dontAsk` and `--allowedTools <list>`. Nobody is there to approve
anything, so a tool call not on the list is refused. The list is the agents' whole reach: keep it as
short as the playbooks allow.

| Entry | Lets the agent |
| --- | --- |
| `Bash(empirical command run item.list:*)`, `item.create`, `item.update`, `item.move`, `shape.show` | Read and write cards. Each board action is its own entry |
| `Bash(empirical memory get:*)`, `Bash(empirical memory note:*)` | Read one card with its notes; add a note |
| `Bash(empirical webhook list:*)`, `Bash(empirical webhook deliveries:*)` | Check the webhook (the custodian) |
| `Read`, `Edit`, `Write`, `Glob`, `Grep` | Work with files in the project folder |
| `Bash(python tools/:*)` | Run any command that **starts with** `python tools/` |
| `Bash(ffmpeg:*)`, `Bash(ffprobe:*)` | Run those programs |
| `Bash(claude agents:*)` | List sessions (the custodian) |
| `Bash(empirical memory attachment add:*)` | Attach a local file (a frame sheet, an image, a screenshot) to a card |
| `mcp__claude-in-chrome` | Drive Chrome (browser roles only) |

How matching works, and what follows from it:

- Shell rules match on how the command **starts**. `python tools/make_short.py x` matches
  `Bash(python tools/:*)`. `cd tools && python make_short.py x` does not, nor does
  `python C:\projects\...\tools\make_short.py`. The `rules` card tells agents the exact shape.
- A chained command (`a && b`, `a; b`, `a | b`) is checked part by part and usually refused. One
  command per call.
- On Windows an agent may use either the Bash tool or the PowerShell tool. **List every command for
  both**: `Bash(ffmpeg:*)` and `PowerShell(ffmpeg:*)`.
- **List the `empirical` commands one by one, never `Bash(empirical:*)`.** The CLI can also delete
  cards, remove types, rotate the webhook secret and delete a workspace. What isn't listed
  (`item.delete`, `empirical memory delete`, `empirical memory update`, `webhook remove`) is refused.
- Agents pass JSON with `--args-file`, written with the Write tool. Inline `--args '{...}'` breaks
  on quoting, and a model that sees it fail starts improvising.
- An MCP server, if a role needs one (Chrome for a browser role), is allowed as `mcp__<server name>`,
  matched exactly including case.
- Don't allow `Bash(python:*)` or `Bash(python -c:*)` unless you accept that it means "run anything".
  `python tools/` keeps agents to the tools you wrote.
- Don't allow deletes. Playbooks say "never delete"; the allow-list makes it true.
- Give each tool one job and a usage docstring. The agent learns the tool by running it with no
  arguments or reading the top of the file.

Before going live, open `claude` once in the project folder and accept the trust prompt; background
sessions won't start in an untrusted folder. Check `empirical auth status` says authenticated: the
agents use the CLI's sign-in on this PC.

## When an agent is refused

The session waits as `blocked` (or carries on without the command). You'll see it three ways: the
custodian's report, `claude agents`, and a card whose last note says a command was denied. Fix the
allow-list in `config.json` (live, no restart), then drag the card out of and back into its column.

## Models

Set `model` at the top of `config.json` and override per route (`model`) or per role (`role_models`).
The receiver adds `--model` to every launch, so an agent never silently runs on your account default.

| Role kind | Needs | Typical choice |
| --- | --- | --- |
| Follows exact steps (builder of a scripted render, publisher, custodian) | Reliability, low cost | `sonnet` |
| Judges quality (reviewer) | Careful reading | `sonnet`, or `opus` if it misses things |
| Decides what is worth making (ideas), or edits with taste | The best model you have | `opus` or newer |

Use an alias (`sonnet`, `opus`) or a full model id. Start everything on the cheaper model and move a
role up only when its mistakes are judgment mistakes; a missing rule in the playbook is fixed in the
playbook.
