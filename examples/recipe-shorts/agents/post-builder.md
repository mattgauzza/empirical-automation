# Post-builder

**Trigger:** Post cards in Queued or Needs Fixes.
**Job:** make the image card and caption for one community post. You don't post it.

## Setup
- `<file>` = the card's `post_file`. `<slug>` = its `slug`. `<out>` = `output/posts/<slug>`.
- Check first: `<out>/<slug>.png` exists and is newer than `<file>`? Then it's built: skip to Finish.

## Steps
1. `python tools/make_post.py <file> --check`. Not valid: fix the post file if the fix is obvious,
   otherwise Waiting on You with the error.
2. `python tools/make_post.py <file>`.
3. Read `<out>/<slug>.png`: the text fits inside the card with a margin, at most 6 lines, no stray
   characters. Too long: tighten the wording in the post file (keep the meaning) and run step 2 again.
4. Read `<out>/caption.txt`: one or two sentences, ends with a question or a next step, at most 3 hashtags.

Needs Fixes: read the reviewer's numbered notes, fix exactly those, then run steps 1 to 4 again.

## Finish
Set the card's `image` field to `<out>/<slug>.png`. Attach the image and `caption.txt` to the card
(rules: "What the owner needs to decide"). Note `post-builder: built <slug>, <n> lines`. Move to
**Built (In Review)**. Set your Agent card's `last_run`.
