"""Render a recipe JSON file into a 9:16 text-card Short with ffmpeg (sample tool).

Build:   python tools/make_short.py recipes/<slug>.json
Check:   python tools/make_short.py recipes/<slug>.json --check     # validate only, no render

Writes output/<slug>/<slug>.mp4 (1080x1920, 30 fps, silent audio track), <slug>-sheet.jpg (one frame
per screen, for the reviewer) and youtube.txt (line 1 = title, rest = description). Prints a JSON
summary. Needs ffmpeg and ffprobe on PATH. Font: --font <ttf path>, else a common system bold font.

Recipe file: {"slug", "title", "hook", "ingredients": [..], "steps": [{"text", "seconds"}], "outro",
"hashtags": [..]}. This is a stand-in for whatever your project really makes: swap it for your tool.
"""
import argparse, json, os, subprocess, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
LINE_H = 78               # pixels per line of body text (font size 56)
BG = {"hook": "0xC2410C", "ingredients": "0x1F2937", "step": "0x111827", "outro": "0x065F46"}
FONTS = ["C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
MAX_SECONDS = 58          # Shorts must stay under a minute


def load(path):
    r = json.loads(Path(path).read_text(encoding="utf-8"))
    errs = [f"missing '{k}'" for k in ("slug", "title", "hook", "ingredients", "steps") if not r.get(k)]
    if len(r.get("title", "")) > 70:
        errs.append("title is over 70 characters")
    for i, s in enumerate(r.get("steps", []), 1):
        if not s.get("text") or not 2 <= float(s.get("seconds", 0)) <= 10:
            errs.append(f"step {i}: needs text and seconds between 2 and 10")
    return r, errs


def screens(r):
    """[(kind, heading, body, seconds)] in play order."""
    out = [("hook", "", r["hook"], 3.0),
           ("ingredients", "YOU NEED", "\n".join(r["ingredients"]), 4.0)]
    n = len(r["steps"])
    out += [("step", f"STEP {i} OF {n}", s["text"], float(s["seconds"])) for i, s in enumerate(r["steps"], 1)]
    if r.get("outro"):
        out.append(("outro", "", r["outro"], 3.0))
    return out


def wrap(text, width=28):
    return "\n".join("\n".join(textwrap.wrap(line, width)) or "" for line in text.split("\n"))


def put(path, text):
    """Write one line of text with no line ending, for drawtext's textfile."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def esc(path):
    """A path inside an ffmpeg filter: forward slashes, the drive colon escaped."""
    return str(path).replace("\\", "/").replace(":", "\\:")


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"ffmpeg failed: {' '.join(map(str, cmd))}\n{p.stderr[-1500:]}")


def build(r, font):
    out = ROOT / "output" / r["slug"]; work = out / "work"; work.mkdir(parents=True, exist_ok=True)
    segs = []
    for i, (kind, head, body, secs) in enumerate(screens(r)):
        # One drawtext per line, each centred: some ffmpeg builds draw a line break as an empty box.
        lines = wrap(body).split("\n"); draws = []
        for j, line in enumerate(lines):
            txt = work / f"s{i:02d}-l{j:02d}.txt"; put(txt, line)
            y = (H - len(lines) * LINE_H) // 2 + j * LINE_H
            draws.append(f"drawtext=fontfile='{esc(font)}':textfile='{esc(txt)}':fontcolor=white:"
                         f"fontsize=56:x=(w-text_w)/2:y={y}")
        if head:
            head_txt = work / f"s{i:02d}-head.txt"; put(head_txt, head)
            draws.append(f"drawtext=fontfile='{esc(font)}':textfile='{esc(head_txt)}':fontcolor=0xFBBF24:"
                         f"fontsize=40:x=(w-text_w)/2:y=260")
        vf = ",".join(draws)
        seg = work / f"s{i:02d}.mp4"
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={BG[kind]}:s={W}x{H}:r={FPS}:d={secs}",
             "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf, "-t", str(secs),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(seg)])
        run(["ffmpeg", "-y", "-ss", str(secs / 2), "-i", str(seg), "-frames:v", "1", "-vf", "scale=270:480",
             str(work / f"s{i:02d}.jpg")])
        segs.append(seg)
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), encoding="utf-8")
    mp4 = out / f"{r['slug']}.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(mp4)])
    sheet = out / f"{r['slug']}-sheet.jpg"
    frames = [x for s in segs for x in ("-i", str(s.with_suffix(".jpg")))]
    run(["ffmpeg", "-y", *frames, "-filter_complex", f"hstack=inputs={len(segs)}", str(sheet)])
    tags = " ".join("#" + t.lstrip("#") for t in r.get("hashtags", ["recipe", "shorts"]))
    title = r["title"] if r["title"].endswith("#shorts") else r["title"] + " #shorts"
    desc = [r["hook"], "", "You need: " + ", ".join(r["ingredients"]) + ".", "", tags]
    (out / "youtube.txt").write_text("\n".join([title] + desc) + "\n", encoding="utf-8")
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                         capture_output=True, text=True).stdout.strip()
    return {"slug": r["slug"], "mp4": mp4.relative_to(ROOT).as_posix(), "sheet": sheet.relative_to(ROOT).as_posix(),
            "youtube_txt": (out / "youtube.txt").relative_to(ROOT).as_posix(),
            "seconds": round(float(dur or 0), 1), "screens": len(segs), "title": title}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("recipe"); p.add_argument("--check", action="store_true"); p.add_argument("--font")
    a = p.parse_args()
    recipe, errors = load(a.recipe)
    total = sum(s[3] for s in screens(recipe)) if not errors else 0
    if total > MAX_SECONDS:
        errors.append(f"total length {total:.0f} s is over {MAX_SECONDS} s")
    if errors:
        sys.exit("Recipe not valid: " + "; ".join(errors))
    if a.check:
        print(json.dumps({"ok": True, "slug": recipe["slug"], "seconds": total})); sys.exit(0)
    font = a.font or next((f for f in FONTS if os.path.isfile(f)), None)
    if not font:
        sys.exit("No font found. Pass --font <path to a .ttf file>.")
    print(json.dumps(build(recipe, font), indent=1))
