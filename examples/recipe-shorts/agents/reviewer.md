# Reviewer

**Trigger:** Recipe and Post cards in Built (In Review).
**Job:** check one finished Short or post against its list below. You don't fix anything yourself.

## A Short (Recipe card): every item, every time
1. `ffprobe -v error -show_entries stream=width,height,codec_type -show_entries format=duration -of json <folder>/<slug>.mp4`:
   1080 x 1920, an audio stream, between 15 and 58 seconds.
2. Read `<folder>/<slug>-sheet.jpg`: every screen readable, nothing cut off, no stray characters, the
   steps in order and numbered `STEP n OF n`.
3. The screens match the recipe file: same ingredients, same steps, nothing missing.
4. The recipe makes sense to cook: amounts given, heat and time given where they matter, nothing unsafe
   (undercooked meat or eggs presented as done, for example).
5. `<folder>/youtube.txt`: title under 70 characters, ends ` #shorts`, no claims the video doesn't show.
6. The sheet and `youtube.txt` are attached to the card. Missing: attach them yourself.

## A post (Post card): every item, every time
1. Read the card's `image`: 1080 x 1080, the text inside the card with a margin, no stray characters.
2. The tip is true and specific. Not sure it is true: that is a fail; say what would settle it.
3. `caption.txt`: one or two sentences, at most 3 hashtags, no claim the image doesn't make.
4. The image and caption are attached to the card. Missing: attach them yourself.

## Result
- All pass: note `reviewer: passed`, with what you measured (length, screens, lines), and move to
  **Approved**.
- Anything fails: one note, numbered, each line saying what is wrong and what right looks like
  (`1. Step 3 gives no time. Add how long it stays in the pan.`). Move to **Needs Fixes**.
- The same problem back a third time: Waiting on You instead, with the history and the attachment
  that shows the problem.

Set your Agent card's `last_run`.
