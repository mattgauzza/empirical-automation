# empirical-automation

Run a project as a board. Each card moving into a column starts **one small Claude Code agent** on
your PC, which does that column's job and moves the card on. You approve with the buttons on an open
card (Approve, Send back, Reject), or by dragging it.

- **The board** is an [Empirical](https://empirical.gauzza.com) workspace. Cards are the work items;
  Agent cards hold every agent's playbook; Task cards are how agents ask for you.
- **The receiver** (`receiver/`) is one small Python program on your PC, reached through a tunnel.
  It verifies Empirical's signed webhook and starts the agent mapped to the card's new column.
- **The agents** are Claude Code background sessions: one role each, a fixed allow-list of commands,
  a chosen model. They read and write the board with the `empirical` command line tool.
- **The project folder** holds the tools the agents run, their outputs, secrets and lock files.

```
you drag a card ─▶ Empirical ─signed webhook─▶ receiver ─▶ claude (one role) ─▶ does the job,
                                                                                 moves the card ─▶ next agent
```

Use it when work moves through stages (idea, build, review, publish), each stage can be done by one
agent with one playbook, and a person wants to approve at a few points. Don't use it for one-off tasks.

## What's here

| Path | What |
| --- | --- |
| [`receiver/`](receiver/) | The webhook receiver, an example config, and Windows start-up scripts |
| [`docs/`](docs/) | How to build a pipeline, step by step |
| [`examples/recipe-shorts/`](examples/recipe-shorts/) | A complete made-up project: two boards, eight playbooks, three tools |
| [`BOOTSTRAP.md`](BOOTSTRAP.md) | Prompts to paste into Claude Code to build yours |

Everything in the example is invented (a recipe channel). No real workspace, card, channel or
secret is in this repo.

## Build one

**The sample's board shape is the sample's.** Yours can be anything: it comes from what you are
doing, and it is decided before anything is built, because the route, the playbooks and the tools are
all written against it.

| Step | Doc |
| --- | --- |
| How it fits together | [architecture.md](docs/architecture.md) |
| 1. Design and create the board: types, columns, owners, fields | [board.md](docs/board.md) |
| 2. The rules card and the role playbooks, with templates | [playbooks.md](docs/playbooks.md) |
| 3. Wire the receiver: route, webhook, locks, logs | [receiver-config.md](docs/receiver-config.md) |
| 3b. The allow-list and which model runs which role | [permissions-and-models.md](docs/permissions-and-models.md) |
| 4. Agents on a schedule: timers on Agent cards, with a local backup | [timers.md](docs/timers.md) |
| 5. Publishing: API tools with an account guard; browser-only steps | [publishing.md](docs/publishing.md) |
| Install, and the bring-up checklist | [install.md](docs/install.md) |
| When it doesn't work, and lessons learned | [troubleshooting.md](docs/troubleshooting.md) |
| Example prompts | [BOOTSTRAP.md](BOOTSTRAP.md) |

The short way: install the receiver ([install.md](docs/install.md), "Once per PC"), then paste the
prompt in [BOOTSTRAP.md](BOOTSTRAP.md) into Claude Code in your project folder. It proposes a board
for your project and waits for your yes before creating anything.

## Needs

- Windows for the start-up scripts (`receiver.py` itself is plain Python 3.9+, no packages)
- Claude Code, signed in
- An Empirical account on a plan with webhooks, timers and attachments, and the `empirical` CLI
- A public https address for the receiver (the docs use a Cloudflare tunnel)
- Whatever your own tools need (the sample: ffmpeg; Google API packages for uploads)

## Try the sample tools

No board needed:

```
cd examples/recipe-shorts
python tools/make_short.py recipes/garlic-butter-toast.json
python tools/make_post.py posts/salt-your-pasta-water.json
```

## Safety, in short

- An event's contents never reach an agent: only a fixed prompt and validated card ids.
- Agents can run only what the allow-list names. Deleting is not on it.
- Publish tools schedule, never publish now, and refuse any account but the project's own.
- Signing secrets and tokens live in gitignored files and are never shown in chat.

MIT licensed.
