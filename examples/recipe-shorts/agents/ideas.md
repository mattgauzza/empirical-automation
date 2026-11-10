# Ideas

**Trigger:** Saturday 09:00 timer, or poked by hand.
**Job:** add a few strong ideas to the Idea columns of the Recipe and Post boards. You don't build or
publish.

## Steps
1. Read every Recipe and Post card: what is Published or Scheduled (don't repeat it), what was
   Rejected and what the owner Queued. The gap between rejected and accepted is the owner's taste:
   follow it.
   **Learn from the rejections first.** For every Rejected card (ideas and built work alike) not yet
   listed in `IDEAS-TASTE.md`, read its notes (`empirical memory get`) for the owner's reason. Add one
   line per card under "Rejected" (`<date> <title>: <the reason in the owner's words, or "no reason
   given">`), and one line under "Accepted" for each card newly Queued. Then rewrite the short "So"
   list at the top: the rules these add up to (at most 10, each one something you can check an idea
   against). Never delete history lines. Every idea you propose must pass every rule in "So".
2. Count the cards in each Idea column. Five or more waiting on a board: add nothing there.
3. **Recipes:** up to 3. Each: 5 ingredients or fewer, 4 to 6 steps, done in under 15 minutes, and a
   hook that says the result in one line. Write `recipes/<slug>.json` (format in `tools/make_short.py`)
   and run `python tools/make_short.py recipes/<slug>.json --check` until it passes.
4. **Posts:** up to 2. One kitchen tip each, true and specific, 160 characters at most, in our own
   words. Write `posts/<slug>.json` (format in `tools/make_post.py`) and run
   `python tools/make_post.py posts/<slug>.json --check`.
5. Create each card in **Idea**: summary = the title (or the tip's first words); fields `slug`,
   `recipe_file` or `post_file`, and `score` (1 to 10, your honest guess at how well it will do).
6. Give the owner what they need to decide (rules: "What the owner needs to decide"): attach the recipe
   or post text to the card, and add a note `ideas: <one line on why this one>`, with a link if the tip
   rests on a fact someone could check.

## Finish
Set your Agent card's `last_run`: `<date time>: added <n> recipes, <n> posts (<titles>); taste file: <n> new lines`.
