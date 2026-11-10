# Step 4: agents on a schedule

Some agents run on a clock, not on a card move: a daily health check, a weekly ideas run, a go-live
check after each release. The schedule lives on the Agent card as a repeating due time; the
receiver's own clock is the backup.

## 1. Let Agent cards carry a due time, firing only while Active

```
empirical command run type.update --workspace-id ws_team_... --args '{"type":"agent","hasDueDate":true,"dueFiresIn":["active"]}'
```

(Previews first; run again with `--confirm <code>`.) A Paused agent's timer then stays quiet.

## 2. Put the timer on the card

```
empirical command run item.update --workspace-id ws_team_... --args '{"id":"<custodian card id>","dueRepeat":"daily 08:00","dueTimeZone":"America/New_York","dueEmail":false}'
```

- `dueEmail: false` makes it a **timer**: it fires the `item.due` webhook and sends no email.
- Repeat rules: `daily 06:00`, `Sat 09:00`, `weekdays 06:15`, `Mon,Wed,Fri 07:30`, `monthly 1 09:00`,
  or an RRULE. Always give `dueTimeZone`.
- The webhook must subscribe to `item.due` (it is opt-in):
  `empirical webhook update <id> --events item.created,item.status_changed,item.due`.

## 3. Tell the receiver which card is which role

```json
"due_roles": {
  "<custodian card id>": "custodian",
  "<publisher card id>": "publisher",
  "<ideas card id>": "ideas"
}
```

An `item.due` for a card not listed here is ignored. A value can be a list of roles.

## 4. Keep the local clock as a backup

```json
"daily": { "08:00": ["custodian"], "11:15": ["publisher"], "Sat 09:00": ["ideas"] },
"timer_fallback_minutes": 40
```

- With `timer_fallback_minutes` above 0, each `daily` entry fires that many minutes **after** its
  time, and only if Empirical's timer didn't already start that role today. 40 minutes sits past
  Empirical's 1, 5 and 30 minute delivery retries.
- With it at 0 (or absent), `daily` entries are the primary timers and fire on time. That is the
  simplest setup if you don't want timers on the board at all.
- A `daily` timer missed while the PC was asleep or off runs once when the receiver is back (the same
  day). Keys are `HH:MM` for daily or `<Day> HH:MM` for weekly, in the PC's local time.

## Test

```
empirical webhook test <webhook id> --event item.due --item <custodian card id>
```

`receiver.log` shows `event item.due` and `[recipe-shorts/custodian] run in 60s (Empirical timer (item.due))`.
To run one right now without waiting, use a poke file ([receiver-config.md](receiver-config.md)).

## Notes

- A timer run gets no card ids; its prompt says "none given, check the whole board". Timed playbooks
  are written that way.
- A role can have both a column trigger and a timer (the sample's publisher). The playbook has a
  section for each.
- Keep the playbook's "Trigger" line, the card's Schedule field, `dueRepeat` and `daily` saying the
  same time. The custodian can check that.
