# Recipe Shorts — instructions for Claude

This project makes a YouTube channel of short recipe videos and kitchen-tip posts (a made-up sample).
Each recipe is a JSON file in `recipes/`; `tools/make_short.py` renders it; `tools/youtube.py`
schedules it. Each post is a JSON file in `posts/`; `tools/make_post.py` renders it.

## Board (Empirical)
Workspace **Recipe Shorts**, id `ws_team_REPLACE_ME`, read and written with the `empirical` command
line tool (commands in `agents/rules.md`, "The board").
**Pass `--workspace-id ws_team_REPLACE_ME` on every `empirical` command.** This folder is also bound
to the workspace (`.empirical/workspace.json`), but the flag is the rule: a command without it can
land on another project's board. Every reply must name the Recipe Shorts workspace; if not, stop and fix.

Types: Recipe (a Short) and Post (a community post), each its own board
(Idea → Queued → Built (In Review) → Approved → Scheduled → Published), plus Agent and Task.
Agents and their playbooks are Agent cards on the board (read the `rules` card first). The copies in
`agents/*.md` are where the playbooks are edited and versioned; after editing one, write it to its
Agent card's `playbook` field. The webhook receiver that starts the agents is the `receiver/` folder
of the empirical-automation kit (route `/empirical/recipe-shorts`).

## When working by hand
Keep the board in the state the agents expect: move the card as the work moves, and leave the same
notes an agent would.

## Tools
`tools/*.py`, each with a usage docstring. `tools/youtube.py` only ever touches the channel in
`secrets/channel.json`. Never read, print or commit anything in `secrets/`.
