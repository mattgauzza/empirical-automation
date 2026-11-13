"""One webhook receiver for every board-driven project on this PC.

Each route is a URL path with its own signing secret, project folder and fixed prompt, e.g.
  https://hooks.example.com/empirical/recipe-shorts  ->  C:\\projects\\recipe-shorts
An event with a valid signature for that route waits the route's debounce (so a batch of card moves
is one run), then Claude Code starts in that project's folder with the route's FIXED prompt for the
agent role mapped to the card's new status. Event contents are logged but never handed to Claude
(only validated card ids are), so text on a card can't steer what Claude does.

Python 3.9+ standard library only.   python receiver.py        (config.json next to this file)
"""
import base64, hashlib, hmac, json, logging, os, shutil, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
PORT = int(CFG.get("port", 8787))
LOG = HERE / "logs"; LOG.mkdir(exist_ok=True)
# Log to the file only. Writing to a Windows console window can freeze the whole process if someone
# clicks into the window (QuickEdit selection), which made Empirical's deliveries time out.
_handlers = [logging.FileHandler(LOG / "receiver.log", encoding="utf-8")]
if sys.stderr and sys.stderr.isatty() and os.name != "nt":
    _handlers.append(logging.StreamHandler())
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", handlers=_handlers)
log = logging.info
UNSET = ("", "PASTE_SECRET_HERE")


def find_exe(name):
    """Scheduled tasks often get a shorter PATH, so also look where Claude Code installs itself."""
    if os.path.isabs(name):
        return name
    hit = shutil.which(name)
    if hit:
        return hit
    home, appdata = os.path.expanduser("~"), os.environ.get("APPDATA", "")
    for c in (os.path.join(home, ".local", "bin", name + ".exe"), os.path.join(appdata, "npm", name + ".cmd"),
              os.path.join(home, "AppData", "Roaming", "npm", name + ".cmd"),
              os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "claude", name + ".exe")):
        if os.path.isfile(c):
            return c
    return None


def signature_ok(secret: bytes, body: bytes, header: str) -> bool:
    """HMAC-SHA256 in the common header styles: hex, base64, 'sha256=<hex>', 't=..,v1=..'."""
    if not header:
        return False
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    cands = []
    if "v1" in parts and "t" in parts:
        cands.append((hmac.new(secret, parts["t"].encode() + b"." + body, hashlib.sha256), parts["v1"]))
    sig = header.split("=", 1)[1] if header.startswith("sha256=") else header
    cands.append((hmac.new(secret, body, hashlib.sha256), sig))
    return any(hmac.compare_digest(m.hexdigest(), g.strip()) or
               hmac.compare_digest(base64.b64encode(m.digest()).decode(), g.strip()) for m, g in cands)


def notify(text):
    """Post a line to the Discord channel webhook in config.json ("discord_webhook"), if set."""
    url = CFG.get("discord_webhook", "")
    if not url:
        return
    import urllib.request
    try:
        req = urllib.request.Request(url, data=json.dumps({"content": text[:1900]}).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "board-hooks"})
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:
        log(f"discord notify failed: {e!r}")


ID_RE = __import__("re").compile(r"^[A-Za-z0-9_-]{6,64}$")


_PLOCK = threading.Lock()


def _pending_set(key, ids):
    """Remember runs that are waiting, in logs/pending.json, so a restart re-queues them."""
    f = LOG / "pending.json"
    with _PLOCK:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            d = {}
        if ids is None:
            d.pop(key, None)
        else:
            d[key] = ids
        f.write_text(json.dumps(d, indent=1), encoding="utf-8")


class Runner:
    """One agent role in one project. One run at a time; events during a run queue one more run.
    Card ids collected while waiting are handed to the agent (ids only, validated; never card text)."""
    def __init__(self, route, role):
        self.route, self.role = route, role
        self.lock = threading.Lock(); self.timer = None; self.running = False; self.again = False
        self.ids = set()

    def poke(self, why, ids=(), delay=None):
        delay = self.route.debounce_for(self.role) if delay is None else delay
        with self.lock:
            self.ids.update(i for i in ids if ID_RE.match(i))
            if self.running:
                self.again = True; log(f"[{self.route.name}/{self.role}] running, will run again after ({why})"); return
            if self.timer:
                self.timer.cancel()
            self.timer = threading.Timer(delay, self._run); self.timer.daemon = True; self.timer.start()
            log(f"[{self.route.name}/{self.role}] run in {delay}s ({why})")
        _pending_set(f"{self.route.name}|{self.role}", sorted(self.ids))

    def _lock_busy(self, ids):
        """Same lock rule the agents use (agents/.locks/<role>.lock): busy unless missing, empty, RELEASED,
        or untouched for 3 h. If another run of this role holds it, don't open a second window/session:
        add the cards to <role>.pending (the running agent handles them before it releases) and stop."""
        r = self.route
        if not r.lock_dir:
            return False
        lock = Path(r.dir) / r.lock_dir / f"{self.role}.lock"
        try:
            text = lock.read_text(encoding="utf-8", errors="ignore").strip()
            age = time.time() - lock.stat().st_mtime
        except OSError:
            return False
        if not text or text.split()[0].upper().startswith("RELEASED") or age > 3 * 3600:
            return False
        if ids:
            pend = lock.with_suffix(".pending")
            try:
                have = set(pend.read_text(encoding="utf-8", errors="ignore").split()) if pend.exists() else set()
                with pend.open("a", encoding="utf-8") as f:
                    for i in ids:
                        if i not in have:
                            f.write(i + "\n")
            except OSError as e:
                log(f"[{r.name}/{self.role}] couldn't add to pending: {e!r}")
        log(f"[{r.name}/{self.role}] another run holds the lock ({text[:60]}); "
            f"added {ids or 'nothing'} to its pending list instead of starting a second one")
        return True

    def _run(self):
        r = self.route
        with self.lock:
            self.running, self.timer = True, None
            ids, self.ids = sorted(self.ids), set()
        _pending_set(f"{r.name}|{self.role}", None)
        try:
            prompt = (r.prompt.replace("{role}", self.role)
                      .replace("{ids}", ", ".join(ids) if ids else "none given, check the whole board"))
            if self._lock_busy(ids):
                return
            base = r.role_commands.get(self.role, r.command)
            cmd = [c.replace("{prompt}", prompt).replace("{role}", self.role) for c in base]
            model = r.role_models.get(self.role, r.model)      # never fall back to the account default model
            if model and "--model" not in base and "{prompt}" in base:
                i = base.index("{prompt}") + 1
                cmd[i:i] = ["--model", model]
            exe = find_exe(cmd[0])
            if not exe:
                log(f"[{r.name}/{self.role}] can't find '{cmd[0]}': put its full path in config.json \"command\""); return
            cmd[0] = exe
            out_path = LOG / f"{r.name}-{self.role}-{time.strftime('%Y%m%d-%H%M%S')}.log"
            log(f"[{r.name}/{self.role}] starting Claude in {r.dir}  cards: {ids or 'all'}  (logs/{out_path.name})")
            with open(out_path, "w", encoding="utf-8") as out:
                rc = subprocess.call(cmd, cwd=r.dir, stdout=out, stderr=subprocess.STDOUT,
                                     creationflags=0 if self.role in r.role_commands else NO_WINDOW,
                                     shell=bool(r.role_shell.get(self.role, r.shell)))
            log(f"[{r.name}/{self.role}] launched, exit code {rc}")
        except Exception as e:
            log(f"[{r.name}/{self.role}] run failed: {e!r}")
            notify(f"**{r.name}**: the {self.role} agent failed to start: {e!r}")
        finally:
            with self.lock:
                self.running = False; again, self.again = self.again, False
            if again:
                self.poke("events arrived during the last run")


class Route:
    """One project. `roles` maps a card's new status key to the agent role that handles it."""
    def __init__(self, path, r):
        self.path = path
        self.runners = {}
        self.configure(r)

    def configure(self, r):
        self.name = r.get("name", self.path.strip("/").replace("/", "-"))
        self.secret = r.get("secret", "")
        self.roles = r.get("roles", {})                 # {"queued": "scheduler", ...}
        self.default_role = r.get("default_role")       # role for events with no mapped status
        self.daily = r.get("daily", {})                 # {"06:00": ["publisher", "scheduler"]}
        self.debounce = int(r.get("debounce_seconds", 600))
        self.role_debounce = r.get("role_debounce_seconds", {})
        self.dir, self.prompt = r["project_dir"], r["prompt"]
        self.command = r.get("command", CFG.get("command"))
        self.shell = bool(r.get("shell", CFG.get("shell", False)))
        self.lock_dir = r.get("lock_dir")                      # e.g. "agents/.locks": skip a run while one holds the lock
        self.model = r.get("model", CFG.get("model"))         # e.g. "sonnet": the model every agent here runs on
        self.role_models = r.get("role_models", {})            # per-role override, e.g. {"builder": "opus"}
        self.due_roles = r.get("due_roles", {})               # Agent card id, or "<type key>:due" for work cards -> role
        self.timer_fallback = int(r.get("timer_fallback_minutes", 0))  # >0: "daily" timers are only a backup
        self.role_commands = r.get("role_commands", {})   # e.g. a visible window for a role that drives Chrome
        self.role_shell = r.get("role_shell", {})
        self.alerts = r.get("alerts", {})          # "type:status" -> message for Discord
        self.board_url = r.get("board_url", "")

    def debounce_for(self, role):
        return int(self.role_debounce.get(role, self.debounce))

    def runner(self, role):
        if role not in self.runners:
            self.runners[role] = Runner(self, role)
        return self.runners[role]

    @property
    def ready(self):
        return self.secret not in UNSET


ROUTES = {p: Route(p, r) for p, r in CFG["routes"].items()}
_MTIME = [(HERE / "config.json").stat().st_mtime]
_RELOAD = threading.Lock()


def maybe_reload():
    """Pick up config.json edits (new routes, secrets, prompts) without a restart. Port changes still need one."""
    with _RELOAD:
        m = (HERE / "config.json").stat().st_mtime
        if m == _MTIME[0]:
            return
        _MTIME[0] = m
        try:
            cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
        except ValueError as e:
            log(f"config.json has an error, keeping the old settings: {e}"); return
        CFG.update(cfg)
        for path, r in cfg["routes"].items():
            if path in ROUTES:
                ROUTES[path].configure(r)       # keeps running agents and their timers
            else:
                ROUTES[path] = Route(path, r)
        for path in [p for p in ROUTES if p not in cfg["routes"]]:
            del ROUTES[path]
        log(f"config.json reloaded  routes: {', '.join(ROUTES)}")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _reply(self, code, text="ok"):
        self.send_response(code); self.send_header("Content-Type", "text/plain"); self.end_headers()
        self.wfile.write(text.encode())

    def do_GET(self):
        self._reply(200, "hooks receiver running")

    def do_POST(self):
        maybe_reload()
        route = ROUTES.get(self.path.split("?")[0].rstrip("/"))
        if not route:
            return self._reply(404, "not found")
        body = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
        if not route.ready or not signature_ok(route.secret.encode(), body, self.headers.get("X-Empirical-Signature", "")):
            log(f"[{route.name}] rejected: bad signature"); return self._reply(401, "bad signature")
        try:
            ev = json.loads(body or b"{}")
        except ValueError:
            return self._reply(400, "bad json")
        kind = ev.get("event") or ev.get("type") or ev.get("eventType") or ""
        try:   # answer first so Empirical never waits on us (it gives up after 10 s)
            self._reply(200, "pong" if kind == "ping" else "ok")
        except OSError:
            pass
        with (LOG / f"{route.name}-events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev) + "\n")
        log(f"[{route.name}] event {kind or '?'}")
        if kind == "ping":
            return
        item = (ev.get("data") or {}).get("item") or {}
        status = ((item.get("status") or {}).get("key")) or ""
        itype = ((item.get("type") or {}).get("key")) or ""
        alert = route.alerts.get(f"{itype}:{status}")
        if alert and kind in ("item.status_changed", "item.created"):
            threading.Thread(target=notify, daemon=True, args=(
                f"**{route.name}**: {alert} (card `{item.get('id', '?')}`). {route.board_url}",)).start()
        if kind == "item.due":
            card_id = str(item.get("id", ""))
            due_role = route.due_roles.get(card_id)
            if due_role:
                # An Agent card's own timer: a scheduled run of that role, with no card ids.
                for one in (due_role if isinstance(due_role, list) else [due_role]):
                    _mark_due(route.name, one)
                    route.runner(one).poke("Empirical timer (item.due)")
                return
            # A due time on a WORK card (an ad's step-down day): the role mapped to its type, started
            # with that card's id like a column move.
            due_role = route.due_roles.get(f"{itype}:due") if itype else None
            if not due_role:
                log(f"[{route.name}] item.due for {item.get('id', '?')}: not in due_roles, ignored"); return
            for one in (due_role if isinstance(due_role, list) else [due_role]):
                route.runner(one).poke(f"item.due on a {itype} card", ids=[card_id])
            return
        role = route.roles.get(f"{itype}:{status}") or route.roles.get(status) or route.default_role
        if role:
            for one in (role if isinstance(role, list) else [role]):
                route.runner(one).poke(f"{kind} -> {status or '?'}", ids=[str(item.get("id", ""))])
        else:
            log(f"[{route.name}] no agent for status '{status}', ignored")


STATE = LOG / "state.json"
POKES = HERE / "pokes"


_STATE_LOCK = threading.Lock()


def _mark_due(route, role):
    """Remember that Empirical's timer started this role today, so the backup timer skips it."""
    with _STATE_LOCK:
        st = _state(); st[f"due|{route}|{role}"] = time.strftime("%Y-%m-%d")
        STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")


def _state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _due_today(when):
    """'06:00' = daily, 'Sat 09:00' = weekly. Returns today's due time (struct) or None."""
    parts = when.split(); hhmm = parts[-1]
    if len(parts) == 2 and parts[0].lower()[:3] != time.strftime("%a").lower():
        return None
    return time.strftime("%Y-%m-%d") + " " + hhmm


def maintenance():
    """Weekly tidy-up of this receiver: old run logs and a too-big receiver.log."""
    keep = int(CFG.get("keep_log_days", 14)) * 86400
    for f in LOG.glob("*.log"):
        if f.name not in ("receiver.log", "tunnel.log") and time.time() - f.stat().st_mtime > keep:
            try: f.unlink()
            except OSError: pass
    for name in ("receiver.log", "tunnel.log") + tuple(p.name for p in LOG.glob("*-events.jsonl")):
        f = LOG / name
        if f.exists() and f.stat().st_size > 5_000_000:
            old = LOG / (name + ".old")
            try:
                if old.exists(): old.unlink()
                f.rename(old)
            except OSError: pass
    log("maintenance: old logs cleared")


# Windows: run console programs (claude, its background launcher) without flashing a console window.
# pythonw has no console, so every console child would otherwise pop up its own cmd window.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_SWEPT = {}   # session id -> times we've asked it to stop (so a stop that doesn't take isn't re-logged hourly)


def sweep_sessions():
    """Hourly: stop this pipeline's background Claude sessions that are done, or stuck (blocked/idle)
    for more than sweep_hours. Only sessions whose folder is one of the routes' project folders."""
    exe = find_exe("claude")
    if not exe:
        return
    try:
        out = subprocess.run([exe, "agents", "--json"], capture_output=True, text=True, timeout=60,
                             creationflags=NO_WINDOW).stdout
        sessions = json.loads(out or "[]")
    except Exception as e:
        log(f"sweep: couldn't list sessions: {e!r}"); return
    dirs = {os.path.normcase(os.path.normpath(r.dir)) for r in ROUTES.values()}
    max_age = float(CFG.get("sweep_hours", 6)) * 3600
    now = time.time(); stopped = []
    for x in sessions:
        if x.get("kind") != "background" or not x.get("id"):
            continue
        if os.path.normcase(os.path.normpath(x.get("cwd", ""))) not in dirs:
            continue
        state = x.get("state") or x.get("status")
        age = now - (x.get("startedAt", now * 1000) / 1000)
        if state == "done" or (state in ("blocked", "idle") and age > max_age):
            n = _SWEPT.get(x["id"], 0)
            if n >= 2:
                continue          # already tried twice; it's still listed, so don't loop on it every hour
            _SWEPT[x["id"]] = n + 1
            try:
                res = subprocess.run([exe, "stop", x["id"]], capture_output=True, text=True, timeout=60,
                                     creationflags=NO_WINDOW)
                if res.returncode:
                    log(f"sweep: stop {x['id']} returned {res.returncode}: {(res.stderr or res.stdout).strip()[:300]}")
                stopped.append(f'{x["id"]} {x.get("name", "")} ({state}, {age / 3600:.0f}h)')
            except Exception as e:
                log(f"sweep: couldn't stop {x['id']}: {e!r}")
    if stopped:
        log("sweep: stopped " + "; ".join(stopped))
        notify(f"Swept {len(stopped)} finished/stuck agent session(s): " + "; ".join(stopped))


def daily_loop():
    """Timers + catch-up + manual pokes.
    A timer fires once per day as soon as its time has passed and it hasn't fired today, so a
    timer missed while the PC was asleep or the receiver was off runs when it comes back.
    Dropping a file named '<route name>.<role>' into hooks/pokes/ starts that agent now."""
    POKES.mkdir(exist_ok=True)
    while True:
        try:
            maybe_reload()
        except Exception as e:
            log(f"reload failed: {e!r}")
        with _STATE_LOCK:   # released even if something below raises
            st = _state(); now = time.strftime("%Y-%m-%d %H:%M"); today = now[:10]; changed = False
            for r in list(ROUTES.values()):
                if not r.ready:
                    continue
                for when, roles in r.daily.items():
                    due = _due_today(when); key = f"{r.name}|{when}"
                    if due and r.timer_fallback:      # backup mode: wait out Empirical's retries first
                        due = time.strftime("%Y-%m-%d %H:%M", time.localtime(
                            time.mktime(time.strptime(due, "%Y-%m-%d %H:%M")) + 60 * r.timer_fallback))
                    if due and now >= due and st.get(key) != today:
                        st[key] = today; changed = True
                        late = "" if now[11:] == due[11:] else f" (catch-up, was due {due[11:]})"
                        for role in roles:
                            if r.timer_fallback and st.get(f"due|{r.name}|{role}") == today:
                                log(f"[{r.name}/{role}] backup timer {when}: Empirical's timer already ran it today, skipped")
                                continue
                            r.runner(role).poke(f"{'backup ' if r.timer_fallback else ''}timer {when}{late}", delay=5)
            hkey = "sweep|hourly"; hour = now[:13]
            if CFG.get("sweep_sessions", True) and st.get(hkey) != hour:
                st[hkey] = hour; changed = True
                threading.Thread(target=sweep_sessions, daemon=True).start()
            mkey = "maintenance|weekly"
            if time.strftime("%a") == CFG.get("maintenance_day", "Sun") and st.get(mkey) != today:
                st[mkey] = today; changed = True; maintenance()
            if changed:
                STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
        for f in POKES.iterdir():
            name, _, role = f.name.partition(".")
            route = next((x for x in ROUTES.values() if x.name == name), None)
            ids = [i.strip() for i in f.read_text(encoding="utf-8", errors="ignore").split()] if f.is_file() else []
            try: f.unlink()
            except OSError: pass
            if route and role:
                route.runner(role).poke("manual poke", ids=ids, delay=2)
            else:
                log(f"poke ignored: {f.name}")
        time.sleep(20)

if __name__ == "__main__":
    for r in ROUTES.values():
        if not r.ready:
            log(f"[{r.name}] no secret yet: its POSTs are rejected until it's set in config.json")
        elif CFG.get("run_on_start", False):
            for role in sorted(set(r.roles.values())):
                r.runner(role).poke("startup catch-up", delay=60)
    try:
        waiting = json.loads((LOG / "pending.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        waiting = {}
    for key, ids in waiting.items():
        name, _, role = key.partition("|")
        route = next((x for x in ROUTES.values() if x.name == name), None)
        if route and role:
            route.runner(role).poke("re-queued after restart", ids=ids, delay=30)
    threading.Thread(target=daily_loop, daemon=True).start()
    log(f"listening on http://localhost:{PORT}  routes: {', '.join(ROUTES)}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
