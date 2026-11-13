# Running the agents with Codex

The receiver doesn't care which program an agent is: it runs the route's `command` with the role's
prompt and model. The rest of the kit is written for Claude Code. This page is what changes when a
route runs OpenAI's Codex CLI instead, or when one route mixes the two.

## The launch command

```json
"command": [
  "C:\\Users\\<you>\\AppData\\Roaming\\npm\\node_modules\\@openai\\codex\\node_modules\\@openai\\codex-win32-x64\\vendor\\x86_64-pc-windows-msvc\\bin\\codex.exe",
  "-a", "never",
  "exec",
  "--skip-git-repo-check",
  "--sandbox", "workspace-write",
  "--add-dir", "C:\\projects\\recipe-tools",
  "-c", "model_reasoning_effort=\"medium\"",
  "{prompt}"
],
"shell": false
```

| Part | Why |
| --- | --- |
| The full path to `codex.exe` | The npm `codex` on PATH is a `.cmd` shim; calling the real `.exe` lets `shell` stay `false` |
| `-a never` | Never ask for approval: nobody is there to answer. A step that would need approval fails instead |
| `exec` | One non-interactive run that ends when the job is done. There is no background session to sweep |
| `--skip-git-repo-check` | The project folder doesn't have to be a git repository |
| `--sandbox workspace-write` | The agent may write only inside the project folder and the `--add-dir` folders |
| `--add-dir <folder>` | Each extra folder the agent must write to (a tools repo, a poke folder, an export folder). Give one per folder |
| `-c model_reasoning_effort="medium"` | Reasoning effort for every role on this route |
| `{prompt}` last | The receiver adds `--model <model>` right after `{prompt}`, which `codex exec` accepts |

Find the `.exe` once with `where codex` and follow the shim, or look under
`%APPDATA%\npm\node_modules\@openai\codex`. An update can move it; the custodian's "Agent cards whose
last run is old" check is how you notice.

## Models

`model` and `role_models` work as for Claude Code ([permissions-and-models.md](permissions-and-models.md)),
with Codex model ids:

```json
"model": "gpt-6.1-terra",
"role_models": {
  "ideas": "gpt-6-astra",
  "builder": "gpt-6.1-terra",
  "reviewer": "gpt-6.1-sol"
}
```

A pattern that works: the strongest model for roles that decide what to make or plan creatively, a
fast reliable one for builders and publishers, and one careful model shared by every reviewer, so all
stages are judged the same way. Write the split into the `rules` card too, so whoever adds a role
also adds its `role_models` line.

## One route, two runners

`role_commands` gives one role a different launch command. A Codex route can run one role on Claude
Code (to compare models, or because the role needs a Claude-only tool) and the other way round:

```json
"role_commands": {
  "concept-test": ["claude", "{prompt}", "--model", "claude-fable-5-2", "--permission-mode", "dontAsk", "--allowedTools", "Read,Write,Bash(empirical command run item.list:*)"]
}
```

## What keeps a Codex agent in bounds

This is the real difference. **Codex has no per-command allow-list.** The Claude Code safety story
in this kit ("an agent can run only what the allow-list names; deleting is not on it") does not hold
under Codex. What you have instead:

- **The sandbox**: writes only in the project folder and the `--add-dir` folders.
- **No approvals** (`-a never`): anything the sandbox refuses simply fails.
- **The board's own rules**: Empirical refuses what the signed-in account may not do, and a writer
  can't change the board's shape.
- **The playbooks and the `rules` card**: "never delete", spending rules, who moves past an
  approval column. Under Codex these are instructions, not enforcement.
- **Your tools**: anything dangerous (publishing, spending, deleting) should go through a tool that
  checks for itself: an account guard, a spend cap and authorization check ([spending.md](spending.md)),
  a refusal to publish now.

So under Codex, move every safety rule that matters out of the playbook and into a tool that
refuses. And sign the `empirical` CLI in as an account with only the access the pipeline needs.

## Network, MCP servers and instructions

- **Network.** The agents need the network for the `empirical` CLI. On Windows with
  `[windows] sandbox = "elevated"` in `~/.codex/config.toml`, CLI calls worked in our runs. On
  macOS and Linux the `workspace-write` sandbox blocks the network by default; allow it with
  `[sandbox_workspace_write] network_access = true`, or every board call fails. Check with one test
  card before going live.
- **MCP servers** (Chrome, a design tool) come from `~/.codex/config.toml`, for every Codex run on
  the PC, not from the route. Any role can reach any configured server, so keep the list short.
- **Instructions.** Codex reads `AGENTS.md`, not `CLAUDE.md`. Either keep the project's instructions
  in `AGENTS.md`, or start the route's prompt with "Read `CLAUDE.md` in this folder for the project
  policies; they apply to you as well."

## What else changes

| | Claude Code | Codex |
| --- | --- | --- |
| A run | A background session (`--bg`), swept hourly | One `exec` process that exits |
| Stuck runs | `claude agents` lists them | Look for a long-running `codex.exe` and its log |
| Logs | The session | `receiver/logs/<route>-<role>-<time>.log` (the receiver captures stdout) |
| A refused step | The session waits as `blocked` | The step fails and the agent carries on or stops |
| Trusting the folder | Open `claude` once and accept the prompt | Not needed with `--skip-git-repo-check` |

The receiver's log line says "starting Claude" whatever the runner is. Trust the command in
`config.json`, and the per-run log.
