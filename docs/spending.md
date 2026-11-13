# Paid generation: caps, authorization and a ledger

Some roles spend money on every try: an image or video model, a voice, a paid API. An agent retries
when something looks wrong, and nobody is watching, so spending needs the same treatment as
publishing: the person decides, a tool checks, and every cent is written down.

## Four things before any paid call

1. **The person moved the card there.** Paid work is allowed only while the card sits in a column the
   person moved it into for that purpose (Stills Approved, Motion Approved, Queued for a cheap format).
   In every other column, Needs Fixes included, the agent does the free part, dry-runs the rest,
   writes what it would generate and what that would cost in a note, and moves the card to Waiting
   on You. The person approves by moving it back.
2. **A number in the card's spend cap field.** A `spend_cap` number field on the type. Empty or `0`
   means no paid calls. A default in the rules ("$1 for an image") is a guide for the person, never
   an authorization for the agent.
3. **An authorization the tool can check.** Before spending, the agent writes the card id, the cap
   and the time of the person's move into the project (an `approvals.md` line, or a field in the job's
   own file). The paid tool refuses to run without it, and refuses if the job has changed since
   (bind it to a hash of the inputs).
4. **A dry run first.** The tool prints what it would generate and the estimated cost, then spends
   only when asked again. One test output before a batch.

## The ledger

- One append-only file per job (`ledger.jsonl`): `reserve` before a call, `spend` with the real cost
  after, `release` when a reservation is not used. Never edit a line; correct with an `adjust` line.
- After every round the agent writes the ledger total into the card's `spent` field, so the board
  shows it.
- A whole-project ceiling ("stop at $100 across all ledgers") lives in the rules card and in the tool.
  The custodian adds up every ledger daily, warns at 80%, and lists open reservations.
- Check the provider's own balance against the ledgers when it has an API for it. They should agree.

## When a paid call goes wrong

- **At the cap:** stop, note what was spent and what is missing, move to Waiting on You.
- **Three rejected tries on the same output:** stop and move to Waiting on You with a proposal for a
  different approach. More tries of the same approach spend money on the same failure.
- **An unknown outcome** (timeout, connection lost): never resubmit. Recover it by its request id, or
  move to Waiting on You. A blind resubmit can pay twice for one output.

## In the playbooks

Put the rules above in the `rules` card once, under "Spending", and in each spending role's
playbook name its column(s), its default cap and its tool. Say in every `Your move` line when a
move lets an agent spend:

```
Your move: set spend_cap (I suggest $5), then press Approve to let the builder spend up to it,
or press Send back with what to change.
```

Under Codex there is no allow-list to keep an agent away from a paid API ([codex.md](codex.md)), so
the tool's own refusal is the only hard stop. Write it.
