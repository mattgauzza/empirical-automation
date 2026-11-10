# Step 1: design and create the board

**Decide the shape before you build anything.** The sample's shape (Recipe, Agent, Task) fits the
sample. Yours comes from your own work, and everything else (the route's `roles` map, the playbooks,
the tools) is written against it. Changing a status key later means editing all three.

## Design it on paper first

Answer these, with the person who will approve the cards, and write the answers down:

1. **What is the work item?** One card type per thing that moves through stages (a video, a post, a
   lead, an order). Things that feed it (a source to watch, a client) get their own type only if they
   have their own stages.
2. **What are the stages?** Each column is either *owned by one agent* (it does work there), *owned by
   the person* (they decide there), or *a resting place* (done, rejected).
3. **Where does the person approve?** Usually: ideas → queued, and a "Waiting on You" column for
   anything an agent can't do.
4. **What does each agent need to hand the next?** Those are the fields (a folder, a file, a URL, a date).
5. **What runs on a clock?** A daily health check, a weekly idea run, a go-live check.
6. **What must the person see to decide?** For every column they own: the attachment, link and note
   a card must carry when it arrives ([playbooks.md](playbooks.md)).

Then write the table that becomes the heart of the `rules` card:

| Card / column (status key) | Owner | Next |
| --- | --- | --- |
| Recipe Idea `idea` | ideas creates; **you approve** | Queued / Rejected |
| Recipe Queued `queued` | **builder** | Built (In Review) |
| ... | ... | ... |

Columns that work in almost every pipeline: an idea column agents fill and the person drains, a queued
column (the approval), a built-in-review / needs-fixes pair, an approved column for the publisher, a
"Waiting on You" column, a scheduled and a done column, and a rejected column the ideas agent learns from.

**More than one kind of output? One type each.** Every item type is its own board with its own
columns, inside the same workspace. The sample has a Recipe board (Shorts) and a Post board (community
posts): the same stages, different builders and publishers (`post:queued` → post-builder,
`post:approved` → poster), and one shared ideas agent, reviewer and custodian. Add a second board
when the thing is made or published differently; keep one board when only the content differs.

Every workspace also gets two fixed types:

- **Agent**: statuses Active / Paused / Retired; fields Playbook (longText), Trigger, Schedule,
  Last run; due times on, firing only in Active. One card per role, plus one named `rules`.
- **Task**: To do / Doing / Done. How agents tell you something needs you.

## Create it

Everything is an `empirical` CLI command (`empirical command list` shows them all, `empirical command
help <name>` one in detail). The examples show `--args '<json>'` for reading; in practice, and always
on Windows PowerShell, put the JSON in a file and pass `--args-file <path>`: quotes don't survive the shell.

```
empirical command run workspace.create --args '{"name":"Recipe Shorts","description":"Pipeline for ..."}'
# → workspaceId: ws_team_...   Use it on EVERY call from here on.

empirical command run type.add --workspace-id ws_team_... --args-file recipe-type.json
empirical command run type.add --workspace-id ws_team_... --args-file agent-type.json
empirical command run type.add --workspace-id ws_team_... --args-file task-type.json
empirical command run type.update --workspace-id ws_team_... --args '{"type":"agent","hasDueDate":true,"dueFiresIn":["active"]}'
empirical command run shape.show --workspace-id ws_team_...
```

A `type.add` argument file (the sample's are in `examples/recipe-shorts/board/shape.json`):

```json
{
  "label": "Recipe", "labelPlural": "Recipes",
  "statuses": [{ "label": "Idea" }, { "label": "Queued" }, { "label": "Published", "done": true }],
  "fields": [{ "label": "Folder", "kind": "text" }, { "label": "Publish date", "kind": "date" }]
}
```

- Statuses are in board order; at least one must be `done: true`.
- Field kinds: text, longText, number, date, select, multiSelect, person, link, url.
- **Keys are made from the labels once and never change** ("Built (In Review)" → `built_in_review`).
  Read the real keys from `shape.show`; never guess them. Renaming a label later keeps the key.
- `type.update` previews first and returns a confirm code; run it again with `--confirm <code>`.
- Later changes: `status.add` (`after` / `before` to place it), `field.add`, `status.rename`.

## Cards

```
empirical command run item.create --workspace-id ws_team_... --args '{"type":"recipe","summary":"5-Minute Garlic Butter Toast","status":"idea","fields":{"slug":"garlic-butter-toast","score":7}}'
empirical command run item.list   --workspace-id ws_team_... --args '{"type":"recipe","status":"queued"}'
empirical command run item.update --workspace-id ws_team_... --args '{"id":"<id>","fields":{"folder":"output/garlic-butter-toast"}}'
empirical command run item.move   --workspace-id ws_team_... --args '{"id":"<id>","status":"built_in_review"}'
```

- `item.update` **merges** `fields`: name only the ones you change. `empirical memory update` on a
  card can replace the whole field set, which wipes a playbook. Agents use `item.update`.
- `item.move` is the same as dragging the card, and fires the webhook the same way.
- Agent cards: summary `<role>: <one line>`, the playbook text in `fields.playbook`. The sample's are
  listed in `examples/recipe-shorts/board/sample-cards.json`.

Notes, attachments and reading one card use the card's id with the `memory` commands:

```
empirical memory get  --memory-id <id> --workspace-id ws_team_... --pretty        # the card with its notes
empirical memory note --memory-id <id> --workspace-id ws_team_... --text "builder: built garlic-butter-toast, 27 s, 7 screens"
empirical memory attachment add  --memory-id <id> --workspace-id ws_team_... --file output/garlic-butter-toast/garlic-butter-toast-sheet.jpg --author-type agent
empirical memory attachment list --memory-id <id> --workspace-id ws_team_...
```

## Pin the workspace

Every command, by an agent or by you, carries `--workspace-id`. Without it the CLI falls back to the
`EMPIRICAL_WORKSPACE_ID` variable, then the folder's binding, then a machine-wide selection that any
other session can change; a card created that way can land on another project's board.

- Put the id in the project's `CLAUDE.md`, in the route's prompt and in the `rules` card.
- Bind the project folder as a second line of defence:
  `empirical workspace use ws_team_... --project` (writes `.empirical/workspace.json` there).
- Have agents check that each reply names the right workspace (`workspaceName` / `workspaceId`).
