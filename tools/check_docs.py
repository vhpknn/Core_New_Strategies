# -*- coding: utf-8 -*-
# check_docs.py : ตรวจความสอดคล้องของเอกสาร (อ่านอย่างเดียว ไม่แก้ไฟล์ใด)
#   python tools/check_docs.py
# ตรวจ: เลขมติซ้ำ/ตกหล่น, ไฟล์มติไม่อยู่ในดัชนี, เอกสารอ้างเลขมติที่ไม่มี,
#       เลข D-20.x เก่าที่ตกค้าง, ป้ายเตือนเอกสารเก่า, ป้าย ARCHIVED ติดผิดไฟล์,
#       เอกสารเก่าหลุดเข้า Bundle, path ที่เอกสารหลักอ้างถึงแต่ไม่มีไฟล์
# รหัสออก: 0 ไม่มี ERROR | 1 มี ERROR
import fnmatch
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEC = ROOT / "docs" / "decisions"
INDEX = DEC / "DECISIONS_INDEX.md"
P1 = "docs/PHASE 1_Final_Complete/"

LIVE_FIXED = [
    "docs/START_HERE.md",
    "Core/README.md",
    "tools/README_tools.md",
    P1 + "TEST_MATRIX_ผลสรุปรอบที่1.md",
    P1 + "คู่มือทดสอบทีละขั้น_ฉบับ2.md",
]
LIVE_GLOBS = ["docs/handoff/*.md", "docs/decisions/*.md", "Strategies/*/README.md", "Strategies/*/doc/*.md", "docs/work/*.md", P1 + "TEST_MATRIX_*.md"]

# (path, ต้องมีป้ายเตือน, ห้ามอยู่ใน Bundle)
ARCHIVED = [
    (P1 + "PROJECT_HANDOFF_v4.1.md", True, True),
    (P1 + "ส่งงานต่อให้ AI ตัวอื่นตรวจสอบ/PROJECT_HANDOFF_v4.2_TESTING.md", True, True),
    (P1 + "ส่งงานสร้างกลยุทธใหม่ ให้ AI ตัวใหม่ทำต่อ/HANDOFF_NEW_STRATEGY_TEMPLATE.md", True, True),
    (P1 + "TEST_MATRIX_Core_v1.0.0.md", True, True),
    (P1 + "TEST_GUIDE_Core_v1.0.0.md", True, True),
    (P1 + "คู่มือทดสอบทีละขั้น_7ชุด.md", True, True),
    ("docs/decisions/PHASE1_DECISIONS.md", True, False),
    (P1 + "CORE_BLUEPRINT_v4.1.md", True, False),
]
PATH_CHECK_DOCS = ["docs/START_HERE.md", "docs/handoff/PROJECT_HANDOFF_v5.md"]

ID_RE = re.compile(r"\bD-(\d{2})(?:\.\d+)?\b")
ROW_RE = re.compile(r"^\|\s*(D-\d{2})\s*\|")
TICK_RE = re.compile(r"`([^`\n]+)`")
EXT_RE = re.compile(r"\.[A-Za-z0-9]{2,4}$")

errors = []
warns = []


def err(msg):
    errors.append("[ERROR] " + msg)


def warn(msg):
    warns.append("[WARN] " + msg)


def read(p):
    try:
        return p.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def rel(p):
    return p.relative_to(ROOT).as_posix()


def parse_index():
    text = read(INDEX)
    if text is None:
        err("ไม่พบ docs/decisions/DECISIONS_INDEX.md")
        return {}
    ids = {}
    for n, line in enumerate(text.splitlines(), 1):
        m = ROW_RE.match(line)
        if not m:
            continue
        did = m.group(1)
        if did in ids:
            err("เลขมติซ้ำในดัชนี %s (บรรทัด %d และ %d)" % (did, ids[did][0], n))
            continue
        paths = [t for t in TICK_RE.findall(line) if "/" in t and t.lower().endswith(".md")]
        ids[did] = (n, paths[0] if paths else "")
    nums = sorted(int(k[2:]) for k in ids)
    if nums:
        for i in range(nums[0], nums[-1]):
            if i not in nums:
                warn("เลขมติ D-%02d ไม่มีในดัชนี (ตกหล่น?)" % i)
        print("เลขมติสูงสุดในดัชนี D-%02d | เลขถัดไปที่ว่าง D-%02d" % (nums[-1], nums[-1] + 1))
    return ids


def check_decision_files(ids):
    seen = {}
    for f in sorted(DEC.glob("D-[0-9][0-9]_*.md")):
        did = f.name[:4]
        if did in seen:
            err("ไฟล์มติเลขซ้ำ %s: %s และ %s" % (did, rel(seen[did]), rel(f)))
        seen[did] = f
        if did not in ids:
            err("ไฟล์ %s ไม่อยู่ในดัชนี (เพิ่มแถว %s)" % (rel(f), did))
        elif ids[did][1] and ids[did][1] != rel(f):
            err("ดัชนีชี้ %s ไปที่ %s แต่ไฟล์จริงคือ %s" % (did, ids[did][1], rel(f)))
    for did, (n, path) in ids.items():
        if path and not (ROOT / path).is_file():
            err("ดัชนีบรรทัด %d: %s ชี้ไปไฟล์ที่ไม่มี (%s)" % (n, did, path))


def live_docs():
    out = []
    for p in LIVE_FIXED:
        f = ROOT / p
        if f.is_file():
            out.append(f)
    for g in LIVE_GLOBS:
        out.extend(sorted(ROOT.glob(g)))
    uniq = []
    for f in out:
        if f not in uniq:
            uniq.append(f)
    return uniq


def check_references(ids):
    for f in live_docs():
        text = read(f)
        if text is None:
            continue
        is_index = (f == INDEX)
        for n, line in enumerate(text.splitlines(), 1):
            where = "%s:%d" % (rel(f), n)
            for m in ID_RE.finditer(line):
                did = "D-" + m.group(1)
                if ids and did not in ids and not is_index:
                    err("%s อ้างเลขมติ %s ที่ไม่มีในดัชนี" % (where, did))
            if is_index:
                continue
            if re.search(r"D-20\.\d", line):
                err("%s ใช้ D-20.x แบบเก่า (ต้องเป็น D-26.x)" % where)
            elif "D-20" in line and "D-26" not in line:
                warn("%s มี D-20 โดยไม่มีหมายเหตุ D-26 (D-20 คือ ไฟล์ Core ที่เพิ่ม ตรวจว่าตั้งใจ)" % where)


def banner_ok(text):
    lines = [ln for ln in text.splitlines() if ln.strip()][:6]
    return any(ln.lstrip().startswith(">") for ln in lines)


def check_banners():
    for path, need, _ in ARCHIVED:
        f = ROOT / path
        if not f.is_file():
            continue
        text = read(f)
        if text is not None and need and not banner_ok(text):
            warn("%s ยังไม่มีป้ายเตือนเอกสารเก่า (บรรทัดที่ขึ้นต้น > ที่หัวไฟล์)" % path)
    guards = ["docs/START_HERE.md"] + [rel(p) for p in sorted(ROOT.glob("docs/handoff/*.md"))]
    for path in guards:
        f = ROOT / path
        text = read(f) if f.is_file() else None
        if text is None:
            continue
        head = [ln for ln in text.splitlines() if ln.strip()][:6]
        if any("ARCHIVED" in ln for ln in head):
            err("%s เป็นเอกสารปัจจุบัน แต่มีป้าย ARCHIVED ที่หัวไฟล์ (ติดผิดไฟล์?)" % path)


def check_bundle_lists():
    script = ROOT / "tools" / "make_ai_bundle.py"
    if not script.is_file():
        warn("ไม่พบ tools/make_ai_bundle.py ข้ามการตรวจรายการ Bundle")
        return
    try:
        spec = importlib.util.spec_from_file_location("make_ai_bundle", str(script))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        listed = list(mod.DOCS_STRATEGY) + list(mod.DOCS_CORE_EXTRA) + list(mod.CODE_STRATEGY) + list(mod.CODE_CORE_EXTRA)
    except Exception as e:
        warn("อ่านรายการไฟล์จาก make_ai_bundle ไม่ได้: %s" % e)
        return
    banned = set(p for p, _, b in ARCHIVED if b)
    for p in listed:
        if p in banned:
            err("เอกสารเก่าอยู่ในรายการ Bundle: %s" % p)
    index_listed = ("docs/decisions/DECISIONS_INDEX.md" in listed)
    if not index_listed:
        warn("DECISIONS_INDEX.md ยังไม่อยู่ในรายการ Bundle ของ make_ai_bundle.py (เพิ่มใน DOCS_STRATEGY)")


SCOPE = ROOT / "docs" / "AI_READ_SCOPE.md"


STATE_FILE = ROOT / "docs" / "work" / "CURRENT_STATE.md"
STATE_MAX_BEHIND = 3
COMMIT_RE = re.compile(r"Commit ที่ Push แล้ว:\s*([0-9a-fA-F]{7,40})")


def git_out(args):
    try:
        p = subprocess.run(["git"] + args, cwd=str(ROOT), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    return p.stdout.strip()


def check_state():
    text = read(STATE_FILE)
    if text is None:
        warn("ไม่พบ docs/work/CURRENT_STATE.md (บันทึกสถานะงานสำหรับต่อจากแชตเก่า)")
        return
    m = COMMIT_RE.search(text)
    if not m:
        warn("docs/work/CURRENT_STATE.md ไม่มี 'Commit ที่ Push แล้ว: <รหัสจริง>' (ยังเป็นตัวอย่างหรือรูปแบบผิด)")
        return
    sha = m.group(1)
    if git_out(["rev-parse", "--git-dir"]) is None:
        return
    if git_out(["cat-file", "-e", sha + "^{commit}"]) is None:
        warn("CURRENT_STATE.md อ้าง Commit %s ที่ไม่พบใน Repo นี้" % sha)
        return
    behind = git_out(["rev-list", "--count", sha + "..HEAD"])
    if behind is None or not behind.isdigit():
        return
    if int(behind) > STATE_MAX_BEHIND:
        warn("CURRENT_STATE.md บันทึก Commit %s ตามหลัง HEAD อยู่ %s Commit (เกิน %d) ตรวจว่าบันทึกยังเป็นปัจจุบัน"
             % (sha, behind, STATE_MAX_BEHIND))


def parse_scope():
    """อ่านตารางใน AI_READ_SCOPE.md คอลัมน์แรก คืน (allowed, forbidden) เป็นรายการ (path, เลขบรรทัด)"""
    text = read(SCOPE)
    if text is None:
        warn("ไม่พบ docs/AI_READ_SCOPE.md ข้ามการตรวจขอบเขตการอ่าน")
        return None
    allowed, forbidden = [], []
    mode = None
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            if "ห้ามอ่าน" in line:
                mode = "forbidden"
            elif "ทุกงาน" in line or "งาน A" in line or "งาน B" in line or "งาน Core" in line or "งาน Hedge" in line or "งาน Pending" in line or "งาน TradeDesk" in line:
                mode = "allowed"
            else:
                mode = None
            continue
        if mode is None or not line.startswith("|") or line.count("|") < 2:
            continue
        first_cell = line.split("|")[1]
        for tok in TICK_RE.findall(first_cell):
            t = tok.strip().replace("\\", "/")
            if "/" not in t or re.search(r"[<>{}]", t):
                continue
            (forbidden if mode == "forbidden" else allowed).append((t, n))
    return allowed, forbidden


def scope_exists(path):
    p = path.rstrip("/")
    if "*" in p or "?" in p:
        return bool(list(ROOT.glob(p)))
    return (ROOT / p).exists()


def scope_match(path, pattern):
    p = path.rstrip("/")
    q = pattern.rstrip("/")
    if p == q or p.startswith(q + "/"):
        return True
    return fnmatch.fnmatch(p, q) or fnmatch.fnmatch(p, q + "/*")


def bundle_listed():
    script = ROOT / "tools" / "make_ai_bundle.py"
    if not script.is_file():
        return []
    try:
        spec = importlib.util.spec_from_file_location("make_ai_bundle_scope", str(script))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return (list(mod.DOCS_STRATEGY) + list(mod.DOCS_CORE_EXTRA)
                + list(mod.CODE_STRATEGY) + list(mod.CODE_CORE_EXTRA))
    except Exception:
        return []


def check_scope():
    parsed = parse_scope()
    if parsed is None:
        return
    allowed, forbidden = parsed
    if not allowed or not forbidden:
        warn("AI_READ_SCOPE.md อ่านรายการไม่ได้ (ตารางต้องมี path เต็มใน backtick ที่คอลัมน์แรก)")
        return
    forb_paths = [p for p, _ in forbidden]
    allow_paths = [p for p, _ in allowed]
    for path, n in allowed:
        if not scope_exists(path):
            warn("AI_READ_SCOPE.md:%d รายการอนุญาตชี้ไปที่ไม่มี: %s" % (n, path))
        for bad, bn in forbidden:
            if scope_match(path, bad):
                err("AI_READ_SCOPE.md:%d อยู่ทั้งรายการอนุญาต (%s) และห้ามอ่าน (บรรทัด %d: %s)" % (n, path, bn, bad))
    for path, need, ban in ARCHIVED:
        if ban and not any(scope_match(path, f) for f in forb_paths):
            warn("%s เป็นเอกสารเก่าที่ห้ามอยู่ใน Bundle แต่ไม่อยู่ในรายการห้ามอ่านของ AI_READ_SCOPE.md" % path)
    for p in bundle_listed():
        if any(scope_match(p, f) for f in forb_paths):
            err("Bundle รวมไฟล์ที่ AI_READ_SCOPE.md ห้ามอ่าน: %s" % p)
        elif not any(scope_match(p, a) for a in allow_paths):
            warn("Bundle รวม %s ซึ่งไม่อยู่ในรายการอนุญาตของ AI_READ_SCOPE.md" % p)


def check_paths():
    for p in PATH_CHECK_DOCS:
        f = ROOT / p
        text = read(f) if f.is_file() else None
        if text is None:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for tok in TICK_RE.findall(line):
                t = tok.strip().replace("\\", "/")
                if "/" not in t or not EXT_RE.search(t) or re.search(r"[<>*{}]", t) or t.startswith("..."):
                    continue
                if t.startswith("ai_bundle") or t.startswith("tools/out"):
                    continue
                if not (ROOT / t).exists():
                    warn("%s:%d อ้างถึง %s แต่ไม่พบไฟล์" % (p, n, t))


def main():
    ids = parse_index()
    check_decision_files(ids)
    check_references(ids)
    check_banners()
    check_bundle_lists()
    check_paths()
    check_scope()
    check_state()
    for line in errors + warns:
        print(line)
    print("สรุป: ERROR %d | WARN %d" % (len(errors), len(warns)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
