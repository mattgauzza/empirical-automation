# Builder

**Trigger:** Recipe cards in Queued or Needs Fixes.
**Job:** make the finished Short for one recipe. You don't upload or schedule.

## Setup
- `<file>` = the card's `recipe_file`. `<slug>` = its `slug`. `<out>` = `output/<slug>`.
- Set the card's `folder` to `<out>` right away.
- Check first: `<out>/<slug>.mp4` exists and is newer than `<file>`? Then it's built: skip to Finish.

## Steps
1. `python tools/make_short.py <file> --check`. Not valid: fix the recipe file if the fix is obvious
   (a step too long, a title over 70 characters); otherwise Waiting on You with the error.
2. `python tools/make_short.py <file>`. It prints the mp4, the sheet, `youtube.txt` and the length.
3. Look at `<out>/<slug>-sheet.jpg` (Read it). Text cut off at an edge, or a screen with more than
   6 lines: shorten that text in the recipe file and run step 2 again.
4. Read `<out>/youtube.txt`: line 1 is the title and ends ` #shorts`; the description names the ingredients.

Needs Fixes: read the reviewer's numbered notes, fix exactly those in the recipe file, then run
steps 1 to 4 again.

If a step crashes: note the error. Fix it in `tools/` only if the fix is small and clearly right, and
say what you changed in a note. Otherwise Waiting on You with the error.

## Finish
Attach `<out>/<slug>-sheet.jpg` and `youtube.txt` to the card (rules: "What the owner needs to
decide"), so the Short can be judged from the card. Note `builder: built <slug>: <length> s,
<n> screens`. Move to **Built (In Review)**. Set your Agent
card's `last_run`.
