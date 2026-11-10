# receiver

`receiver.py` is one webhook receiver for every board-driven project on this PC. Python 3.9+ standard
library only. Each project is a **route** in `config.json` with its own URL path, signing secret,
folder, fixed prompt, column → role map, models, timers and locks.

```
python receiver.py      # config.json next to it; normally started by install-startup.ps1
```

| File | What |
| --- | --- |
| `receiver.py` | The receiver |
| `config.example.json` | A complete route for the sample project; copy to `config.json` |
| `start.ps1` | Starts the receiver (no window) + your Cloudflare tunnel; stops old copies first |
| `install-startup.ps1` | Run once: a Windows task that runs `start.ps1` at every sign-in |

Install: [../docs/install.md](../docs/install.md). Every config key:
[../docs/receiver-config.md](../docs/receiver-config.md).

Runtime folders (created by the receiver, gitignored): `logs/` (`receiver.log`, one launch log per
run, `pending.json`, `state.json`, `<route>-events.jsonl`) and `pokes/` (drop `<route name>.<role>`
to start an agent now).
