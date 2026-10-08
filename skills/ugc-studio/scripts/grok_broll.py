#!/usr/bin/env python3
"""Grok native media pipeline (heavy account, subscription): still (image_gen) -> clip (image_to_video 720p).
Ledger: ../ledger.jsonl. Idempotent: skips jobs whose clip.mp4 exists. CAS write-back of refreshed OAuth like dn-grok."""
import json, os, sys, shutil, subprocess, tempfile, time, fcntl, glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(os.environ.get("BROLL_DIR", "."))  # folder holding prompts.json (see examples/grok_broll_prompts.json); clips land in ROOT/<key>/
PROMPTS = json.loads((ROOT / "prompts.json").read_text())
STYLE = PROMPTS["_style"]
LEDGER = ROOT / "ledger.jsonl"
GROK = Path.home() / ".grok/bin/grok"
ACC = Path.home() / ".grok/accounts" / os.environ.get("GROK_ACC", "heavy.json")
LANES = int(os.environ.get("LANES", "3"))

def log(**kw):
    kw["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(LEDGER, "a") as f:
        f.write(json.dumps(kw, ensure_ascii=False) + "\n")
    print(json.dumps(kw, ensure_ascii=False), flush=True)

def _email(d):
    for v in d.values():
        if isinstance(v, dict) and v.get("email"):
            return v["email"]

def run_grok(prompt, tools, want_glob, timeout):
    tmp = Path(tempfile.mkdtemp(prefix="grokmedia-", dir=tempfile.gettempdir()))
    try:
        before = ACC.read_bytes()
        (tmp / "auth.json").write_bytes(before); (tmp / "auth.json").chmod(0o600)
        ws = tmp / "ws"; ws.mkdir()
        env = {k: v for k, v in os.environ.items() if k not in ("XAI_API_KEY", "OPENROUTER_API_KEY", "GROK_AUTH_PATH", "GROK_HOME")}
        env["GROK_HOME"] = str(tmp)
        cmd = [str(GROK), "--no-auto-update", "-p", prompt, "-m", "grok-4.5", "--output-format", "json",
               "--tools", tools, "--permission-mode", "bypassPermissions", "--no-subagents"]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, cwd=str(ws))
        # CAS write-back of refreshed token (same email, source untouched)
        try:
            new = (tmp / "auth.json").read_bytes()
            if new != before and _email(json.loads(new)) == _email(json.loads(before)):
                with ACC.with_name(ACC.name + ".lock").open("a+") as lk:
                    fcntl.flock(lk, fcntl.LOCK_EX)
                    if ACC.read_bytes() == before:
                        t = ACC.with_name(f".{ACC.name}.{os.getpid()}.tmp"); t.write_bytes(new); t.chmod(0o600); os.replace(t, ACC)
        except Exception:
            pass
        files = sorted(glob.glob(str(tmp / "sessions" / "**" / want_glob), recursive=True), key=os.path.getmtime)
        text = ""
        try: text = json.loads(p.stdout).get("text", "")[:300]
        except Exception: text = (p.stdout or "")[:300]
        return p.returncode, files[-1] if files else None, text, (p.stderr or "")[:300], tmp
    except subprocess.TimeoutExpired:
        return 124, None, "", "timeout", tmp

def job(key):
    spec = PROMPTS[key]
    d = ROOT / key; d.mkdir(exist_ok=True)
    still, clip = d / "still.jpg", d / "clip.mp4"
    for attempt in range(1, 4):
        if not still.exists():
            rc, f, text, err, tmp = run_grok(
                f"Use your image_gen tool exactly once with aspect_ratio 9:16 and this prompt: {spec['still']}, {STYLE}. Then reply only with the file path.",
                "image_gen", "images/*", 300)
            if f:
                shutil.copy2(f, still); log(key=key, step="still", ok=True, attempt=attempt, bytes=still.stat().st_size)
            else:
                log(key=key, step="still", ok=False, attempt=attempt, rc=rc, text=text, err=err)
            shutil.rmtree(tmp, ignore_errors=True)
            if not still.exists():
                time.sleep(20 * attempt); continue
        if not clip.exists():
            tmpimg = Path(tempfile.mkdtemp(prefix="gimg-", dir=tempfile.gettempdir())) / "frame.jpg"
            shutil.copy2(still, tmpimg)
            dur = spec.get("duration", 6)
            rc, f, text, err, tmp = run_grok(
                f"Use your image_to_video tool exactly once with image {tmpimg}, resolution_name 720p, duration {dur}, and prompt: {spec['motion']}. Then reply only with the file path.",
                "image_to_video", "videos/*.mp4", 900)
            if f:
                shutil.copy2(f, clip); log(key=key, step="clip", ok=True, attempt=attempt, bytes=clip.stat().st_size)
            else:
                log(key=key, step="clip", ok=False, attempt=attempt, rc=rc, text=text, err=err)
            shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(tmpimg.parent, ignore_errors=True)
            if clip.exists():
                return key, True
            time.sleep(30 * attempt)
        else:
            return key, True
    return key, False

if __name__ == "__main__":
    keys = sys.argv[1:] or [k for k in PROMPTS if not k.startswith("_")]
    keys = [k for k in keys if not (ROOT / k / "clip.mp4").exists()]
    log(step="start", jobs=len(keys), lanes=LANES)
    with ThreadPoolExecutor(LANES) as ex:
        res = list(ex.map(job, keys))
    log(step="done", ok=sum(1 for _, o in res if o), failed=[k for k, o in res if not o])
