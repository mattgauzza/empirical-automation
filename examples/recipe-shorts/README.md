# Sample project: Recipe Shorts

A made-up project that shows every piece of a board-driven pipeline in its smallest working form.
Nothing here is a real channel, workspace or card.

**This board shape is the sample's.** Yours can be anything: it comes from the work you are doing,
and you agree it before anything is built ([../../docs/board.md](../../docs/board.md)).

One workspace, two boards (each item type has its own columns), sharing the ideas agent, the reviewer
and the custodian:

```
Recipe board (Shorts, through the YouTube API)
Idea ──(you drag)──▶ Queued ──builder──▶ Built (In Review) ──reviewer──▶ Approved ──publisher──▶ Scheduled ──▶ Published
 ▲ ideas (Sat 09:00)            ▲                     │
                                └──── Needs Fixes ◀───┘

Post board (community posts, through a Chrome window: no API)
Idea ──(you drag)──▶ Queued ──post-builder──▶ Built (In Review) ──reviewer──▶ Approved ──poster──▶ Scheduled ──▶ Published

custodian (daily 08:00) watches all of it and reports as a Task
```

Every card that lands in front of you carries what you need to decide: the frame sheet or image, the
text, the link, the why, and the exact next step (`agents/rules.md`, "What the owner needs to decide").

| Path | What |
| --- | --- |
| `CLAUDE.md` | Project instructions every session loads |
| `agents/rules.md` | Shared rules; becomes the `rules` Agent card |
| `agents/<role>.md` | One playbook per role; each becomes an Agent card |
| `agents/.locks/` | Lock files the agents and the receiver share (runtime) |
| `board/shape.json` | The types, columns and fields, as `type.add` arguments |
| `board/sample-cards.json` | Starter cards, as `item.create` arguments |
| `recipes/*.json` | The work items' source files |
| `tools/make_short.py` | The "build" tool: recipe JSON → 9:16 mp4 + frame sheet + `youtube.txt` |
| `tools/youtube.py` | The "publish" tool: schedule-only uploads with a channel guard |
| `posts/*.json`, `tools/make_post.py` | The Post board's source files and build tool: tip JSON → 1080 x 1080 image + caption |
| `secrets/` | OAuth client, token, channel id (gitignored) |

Try the build tool without any board (needs Python 3.9+ and ffmpeg):

```
python tools/make_short.py recipes/garlic-butter-toast.json
python tools/make_post.py posts/salt-your-pasta-water.json
```

To stand the whole sample up (workspace, cards, webhook, route), follow
[../../docs/install.md](../../docs/install.md) or paste [../../BOOTSTRAP.md](../../BOOTSTRAP.md) into
Claude Code.
