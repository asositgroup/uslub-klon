"""build.py --project DIR <uslub> [<uslub2> ...] — har o'rganilgan uslub uchun <DIR>/hf_<uslub>/ HyperFrames loyihasini yig'adi.

Uslub = library/<uslub>/style.py (build() -> dict: faces, css, body, js, sweeps, sfx, ...), kit.py komponentlaridan quriladi.
Loyiha papkasi (DIR) da: project.json, words json (MMS alignment), media (project.json → media):
  base  — 1080x1920 asosiy video (retush qilingan), voice — toza ovoz (Auphonic), avatar — Instagram avatar (ixtiyoriy).
Skill'dan olinadi: shriftlar, GSAP, SFX; uslub papkasidan: fonts/, img/ (bo'lsa).
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--project", default=os.environ.get("UK_PROJECT"), required="UK_PROJECT" not in os.environ)
ap.add_argument("styles", nargs="+", help="library/ dagi uslub nomlari (slug)")
args = ap.parse_args()
PROJECT = Path(args.project).expanduser().resolve()
os.environ["UK_PROJECT"] = str(PROJECT)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402  (UK_PROJECT o'rnatilgandan keyin)
import importlib.util  # noqa: E402

SFXDIR = SKILL / "assets" / "sfx"
HFV = "0.8.171"
CFG = common.CFG


def link(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:  # boshqa disk bo'lsa — nusxa
        import shutil
        shutil.copy2(src, dst)


def sfx_track(out, cues):
    """cues: [(t, file, gain)] -> bitta wav (DUR uzunlikda)."""
    a = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-t", str(common.DUR), "-i", "anullsrc=r=48000:cl=stereo"]
    filt, labels = [], ["[0:a]"]
    for k, (t, f, g) in enumerate(cues, start=1):
        a += ["-i", str(SFXDIR / f)]
        ms = max(0, int(round(t * 1000)))
        filt.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,volume={g},adelay={ms}|{ms}[s{k}]")
        labels.append(f"[s{k}]")
    filt.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first[out]")
    a += ["-filter_complex", ";".join(filt), "-map", "[out]", "-c:a", "pcm_s16le", str(out)]
    subprocess.run(a, check=True)


def load_style(slug):
    p = common.LIBRARY / slug / "style.py"
    if not p.exists():
        raise SystemExit(f"uslub topilmadi: {p} (library/INDEX.md ni ko'r)")
    spec = importlib.util.spec_from_file_location(f"uslub_{slug.replace('-', '_')}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build(slug):
    st = load_style(slug).build()
    hf = PROJECT / f"hf_{slug}"
    (hf / "assets").mkdir(parents=True, exist_ok=True)
    m = CFG["media"]
    link(PROJECT / m["base"], hf / "assets/base.mp4")
    link(PROJECT / m["voice"], hf / "assets/voice.wav")
    if m.get("avatar") and (PROJECT / m["avatar"]).exists():
        link(PROJECT / m["avatar"], hf / "assets/avatar.jpg")
    link(SKILL / "assets/gsap.min.js", hf / "assets/gsap.min.js")
    for f in (SKILL / "assets/fonts").glob("*.ttf"):
        link(f, hf / "assets/fonts" / f.name)
    sdir = common.LIBRARY / slug
    for sub in ("fonts", "img"):
        for f in (sdir / sub).glob("*") if (sdir / sub).is_dir() else []:
            link(f, hf / "assets" / sub / f.name)
    for rel in st.get("media", []):          # loyihadan qo'shimcha media (B-roll va h.k.): project-relative yo'llar
        link(PROJECT / rel, hf / "assets" / Path(rel).name)
    cues = [(t - st.get("sfx_lead", 0.0), st["sfx"], st["sfx_gain"]) for t in st.get("sweeps", [])] if st.get("sfx") else []
    cues += st.get("sfx_extra", [])
    cues = [(t, f, g) for t, f, g in cues if (SFXDIR / f).exists()] or [(0.0, "select_click.wav", 0.0)]
    sfx_track(hf / "assets/sfx.wav", cues)
    html = common.page(f"{CFG.get('name', 'video')} — {slug}", st["faces"], st["css"], st["body"], st["js"], st.get("bg", "#000"))
    (hf / "index.html").write_text(html, encoding="utf-8")
    (hf / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
        "authoringSkill": "general-video"}, indent=2))
    (hf / "package.json").write_text(json.dumps({"name": f"uk-{slug}", "private": True, "type": "module",
        "scripts": {k: f"npx --yes hyperframes@{HFV} {k}" for k in ("preview", "check", "render")}}, indent=2))
    print(f"{slug}: {hf}/index.html ({len(html) // 1024} KB)")


if __name__ == "__main__":
    for s_ in args.styles:
        build(s_)
