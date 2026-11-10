"""Render a kitchen-tip post file into a square image card + caption with ffmpeg (sample tool).

Build:   python tools/make_post.py posts/<slug>.json
Check:   python tools/make_post.py posts/<slug>.json --check     # validate only, no render

Writes output/posts/<slug>/<slug>.png (1080x1080) and caption.txt. Prints a JSON summary.
Post file: {"slug", "heading", "text", "caption", "hashtags": [..]}. Text: 160 characters at most.
"""
import argparse, json, os, subprocess, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIZE, LINE_H = 1080, 84
FONTS = ["C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def esc(path):
    return str(path).replace("\\", "/").replace(":", "\\:")


def put(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("post"); p.add_argument("--check", action="store_true"); p.add_argument("--font")
    a = p.parse_args()
    d = json.loads(Path(a.post).read_text(encoding="utf-8"))
    errs = [f"missing '{k}'" for k in ("slug", "text", "caption") if not d.get(k)]
    if len(d.get("text", "")) > 160:
        errs.append("text is over 160 characters")
    if errs:
        sys.exit("Post not valid: " + "; ".join(errs))
    if a.check:
        print(json.dumps({"ok": True, "slug": d["slug"]})); sys.exit(0)
    font = a.font or next((f for f in FONTS if os.path.isfile(f)), None)
    if not font:
        sys.exit("No font found. Pass --font <path to a .ttf file>.")
    out = ROOT / "output" / "posts" / d["slug"]; work = out / "work"; work.mkdir(parents=True, exist_ok=True)
    lines = textwrap.wrap(d["text"], 26); draws = []
    for j, line in enumerate(lines):          # one drawtext per line, each centred
        txt = work / f"l{j:02d}.txt"; put(txt, line)
        y = (SIZE - len(lines) * LINE_H) // 2 + j * LINE_H
        draws.append(f"drawtext=fontfile='{esc(font)}':textfile='{esc(txt)}':fontcolor=0x111827:fontsize=60:"
                     f"x=(w-text_w)/2:y={y}")
    head = work / "head.txt"; put(head, d.get("heading", "KITCHEN TIP").upper())
    draws.append(f"drawtext=fontfile='{esc(font)}':textfile='{esc(head)}':fontcolor=0xC2410C:fontsize=40:"
                 f"x=(w-text_w)/2:y=150")
    png = out / f"{d['slug']}.png"
    r = subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0xFEF3C7:s={SIZE}x{SIZE}", "-vf",
                        ",".join(draws), "-frames:v", "1", str(png)], capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed:\n" + r.stderr[-1500:])
    tags = " ".join("#" + t.lstrip("#") for t in d.get("hashtags", []))
    put(out / "caption.txt", (d["caption"] + ("\n\n" + tags if tags else "")).strip() + "\n")
    print(json.dumps({"slug": d["slug"], "image": png.relative_to(ROOT).as_posix(),
                      "caption_txt": (out / "caption.txt").relative_to(ROOT).as_posix(), "lines": len(lines)}, indent=1))
