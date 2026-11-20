# -*- coding: utf-8 -*-
# make_ai_bundle.py : รวมไฟล์สำหรับส่งให้ AI Chatbot ที่เข้า GitHub ไม่ได้ แยกตามงาน
# ใช้ไลบรารีมาตรฐานเท่านั้น ไม่แก้ไฟล์ใดใน Repo (เขียนผลลง ai_bundle/ เท่านั้น)
#   python tools/make_ai_bundle.py --job core --version v1.1
#   python tools/make_ai_bundle.py --job hedge --version v1.0.1
#   python tools/make_ai_bundle.py --job pending --version v1.1
#   python tools/make_ai_bundle.py --job newstrategy          (สร้างกลยุทธ์ใหม่)
#   python tools/make_ai_bundle.py --profile core             (ชื่อเดิม: core = --job core, strategy = newstrategy)
#   python tools/make_ai_bundle.py --job pending --add Core/v1.1/include/Core_Capital.mqh --add "C:/path/Jigsaw-Patch-Rule.txt"
#   python tools/make_ai_bundle.py --job core --redact 12345678   (แทนที่ข้อความที่ไม่อยากให้ AI เห็น เช่น เลขบัญชี)
import argparse
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P1 = "docs/PHASE 1_Final_Complete/"

SHARED_DOCS = [
    "docs/START_HERE.md",
    "docs/AI_READ_SCOPE.md",
    "docs/handoff/PROJECT_HANDOFF_v5.md",
    "docs/decisions/DECISIONS_INDEX.md",
    "docs/decisions/MAGIC_REGISTRY.md",
    "docs/decisions/D-18_strategy_file_naming.md",
    "docs/decisions/D-19_work_rules.md",
    "docs/decisions/D-26_inputs_language_panel_lock.md",
    "docs/decisions/D-27_instance_lock.md",
    "docs/decisions/D-28_version_naming_and_v101_scope.md",
    "tools/README_tools.md",
]
TEST_DOCS = [
    P1 + "TEST_MATRIX_ผลสรุปรอบที่1.md",
    P1 + "คู่มือทดสอบทีละขั้น_ฉบับ2.md",
]

BASE_PROMPT = """คุณจะรับงานในโปรเจกต์ EA Platform Core (MQL5, MetaTrader 5) คุณเข้า GitHub ไม่ได้ ข้อมูลทั้งหมดอยู่ในไฟล์ที่แนบ

ขอบเขตงานนี้:
@@SCOPE@@

ขั้นแรก:
1. อ่านไฟล์ 01_DOCS_BUNDLE.md ทั้งหมด (เริ่มที่ START_HERE, PROJECT_HANDOFF_v5 และไฟล์สถานะของงานนี้ ให้ตรวจ Commit ในบันทึกกับ MANIFEST ก่อนเชื่อ) และ 02_CODE_BUNDLE.txt
2. ตอบกลับสั้นๆ ไม่เกิน 12 บรรทัด: ฐานงาน (Commit และรุ่น), ข้อจำกัดสำคัญที่เกี่ยวกับงานนี้, และสิ่งที่ยังขาด ห้ามอธิบายระบบกลับมาเป็นบทความยาว
3. ถามเฉพาะข้อที่ขาดเพื่อเริ่มงาน

กติกาตลอดงาน:
- ตอบภาษาไทย ทำตาม Jigsaw Patch Rule: ขั้นปรึกษา (Folder Tree + ฟังก์ชันต่อไฟล์ + รายการไฟล์ที่ขอเพิ่ม) แล้วรอคำว่า "เริ่มงาน" จึงส่งโค้ด
- ไฟล์ใหม่ส่ง Full Code พร้อม Path เต็ม ไฟล์เดิมส่งเป็น FIND/REPLACE เท่านั้น และต้องขอเนื้อไฟล์ปัจจุบันจากผมก่อนทุกครั้ง ห้ามแก้จากความจำ
- คุณคอมไพล์และรันเครื่องมือไม่ได้ ผมเป็นคนรัน แล้วส่งผลกลับ
- ห้ามเดาชื่อฟังก์ชันหรือ API ถ้าไม่มีในไฟล์ที่แนบ ให้ขอไฟล์นั้นจากผม (ครั้งละไม่เกิน 5 ไฟล์ ระบุ Path)
- ห้ามยืนยันว่าผ่านโดยไม่มีหลักฐาน ห้ามแก้สำเนา Core ในโฟลเดอร์กลยุทธ์
- ส่งงานเป็นชุด (batch) ทุกชุดจบด้วยรายการคำสั่งที่ผมต้องรัน เรียงลำดับ
"""

SCOPE_CORE = ("งาน Core รุ่น @@VER@@ คุณได้รับเฉพาะ Core รุ่นนี้ เอกสารกลาง และบันทึกสถานะของ Core "
              "ห้ามขอโค้ดของ Hedge หรือ Pending การตรวจผลกระทบต่อกลยุทธ์ทำผ่านสัญญา Core_StrategyAPI, "
              "การเทียบ hash ของไฟล์เดิม และผลทดสอบถอยหลังที่ผมส่งมาจากแชตของกลยุทธ์นั้น")
SCOPE_STRATEGY = ("งานแก้กลยุทธ์ @@NAME@@ รุ่น @@VER@@ คุณได้รับเฉพาะไฟล์ของกลยุทธ์นี้ (รวมสำเนา Core บางไฟล์ในโฟลเดอร์ของมัน) "
                  "ห้ามขอโค้ดของกลยุทธ์อื่นหรือ Core ต้นฉบับ ถ้าต้องการความสามารถที่สำเนา Core ไม่มี ให้หยุดและแจ้งผม "
                  "เปิดเป็นงาน Core แยก")
SCOPE_NEW = ("งานสร้างกลยุทธ์ใหม่ คุณได้รับเอกสารกลาง Core API ของรุ่นล่าสุด และกลยุทธ์ Hedge เป็นตัวอย่างรูปแบบ "
             "ถ้ากลยุทธ์ต้องใช้ความสามารถที่ Core ไม่มี ให้หยุดและแจ้งผม เปิดเป็นงาน Core แยก")

ENCODINGS = ("utf-8-sig", "utf-16", "cp874", "latin-1")


def read_text(path):
    raw = path.read_bytes()
    for enc in ENCODINGS:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def sha8(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def version_key(name):
    return tuple(int(n) for n in re.findall(r"\d+", name))


def latest_version(base):
    base = Path(base)
    if not base.is_dir():
        return None
    dirs = [p for p in base.glob("v*") if p.is_dir()]
    if not dirs:
        return None
    return sorted(dirs, key=lambda p: version_key(p.name))[-1].name


def rel_files(rel_dir, patterns):
    out = []
    base = ROOT / rel_dir
    if not base.is_dir():
        return out
    for pat in patterns:
        for p in sorted(base.glob(pat)):
            if p.is_file():
                out.append(p.relative_to(ROOT).as_posix())
    return out


def existing(rels):
    return [r for r in rels if (ROOT / r).is_file()]


def git_info():
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=15).stdout.strip()
        d = subprocess.run(["git", "status", "--short"], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=15).stdout.strip()
        return h or "unknown", ("มีไฟล์ที่ยังไม่ Commit" if d else "สะอาด")
    except Exception:
        return "unknown", "ตรวจไม่ได้ (ไม่มี git)"


def run_doc_check():
    script = ROOT / "tools" / "check_docs.py"
    if not script.is_file():
        return 0, "[WARN] ไม่พบ tools/check_docs.py ข้ามการตรวจเอกสาร"
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, str(script)], cwd=str(ROOT), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def resolve(rel):
    p = Path(rel)
    return p if p.is_absolute() else ROOT / rel


def job_core(ver):
    ver = ver or latest_version(ROOT / "Core")
    if not ver or not (ROOT / "Core" / ver / "include").is_dir():
        return None
    docs = SHARED_DOCS + [
        "docs/work/CURRENT_STATE_Core.md",
        "docs/handoff/HANDOFF_CORE_V1_1.md",
        "Core/README.md",
        "docs/decisions/BACKLOG_v1.0.1.md",
        P1 + "CORE_BLUEPRINT_v4.1.md",
        P1 + "TEST_MATRIX_ภาคผนวก1_Panel_Lock.md",
    ] + TEST_DOCS
    code = rel_files("Core/" + ver + "/include", ["*.mqh"])
    return docs, code, SCOPE_CORE.replace("@@VER@@", ver)


# เอกสารของกลยุทธ์ตามมติ D-29: อ่านจาก Strategies/<ชื่อ>/doc/ ก่อน
# ถ้าไม่มีไฟล์สถานะในนั้น (Hedge, Pending) ถอยไปใช้ docs/work/CURRENT_STATE_<ชื่อ>.md เหมือนเดิม
STRATEGY_DOC_DIR = "doc"
STRATEGY_DOC_PATTERNS = ["CURRENT_STATE_*.md", "BLUEPRINT_*.md", "SPEC_*.md", "TEST_MATRIX_*.md"]


def strategy_docs(name):
    out = rel_files("Strategies/%s/%s" % (name, STRATEGY_DOC_DIR), STRATEGY_DOC_PATTERNS)
    if not any("/CURRENT_STATE_" in p for p in out):
        out.append("docs/work/CURRENT_STATE_%s.md" % name)
    return out


def job_strategy(name, ver, extra_docs):
    ver = ver or latest_version(ROOT / "Strategies" / name)
    sdir = "Strategies/%s/%s" % (name, ver)
    if not ver or not (ROOT / sdir).is_dir():
        return None
    docs = SHARED_DOCS + strategy_docs(name) + [
        "Strategies/%s/README.md" % name,
        sdir + "/README.md",
    ] + extra_docs + TEST_DOCS
    docs = [d for d in docs if d.endswith("README.md") is False or (ROOT / d).is_file()]
    code = rel_files(sdir, [name + "_EA*.mq5"]) + rel_files(sdir + "/include", ["*.mqh"])
    code = [c for c in code if "Secrets" not in Path(c).name]   # ไม่ส่งไฟล์กุญแจให้ AI
    core_inc = sdir + "/Core/include"
    for n in ("Core_StrategyAPI.mqh", "Core_Runtime.mqh", "Core_Engine.mqh", "Core_Pending.mqh"):
        if (ROOT / core_inc / n).is_file():
            code.append(core_inc + "/" + n)
    sets = rel_files(sdir + "/Set", ["*.set"])
    if sets:
        code.append(sets[0])
    scope = SCOPE_STRATEGY.replace("@@NAME@@", name).replace("@@VER@@", ver)
    return docs, code, scope


def job_new():
    cv = latest_version(ROOT / "Core")
    hv = latest_version(ROOT / "Strategies" / "Hedge")
    docs = SHARED_DOCS + [
        "docs/work/CURRENT_STATE.md",
        "docs/handoff/HANDOFF_NEW_STRATEGY_TEMPLATE_v2.md",
        "Core/README.md",
        "Strategies/Hedge/README.md",
        "docs/decisions/PHASE1_DECISIONS.md",
        "docs/decisions/BACKLOG_v1.0.1.md",
    ] + TEST_DOCS
    code = []
    if cv:
        for n in ("Core_StrategyAPI.mqh", "Core_Runtime.mqh", "Core_Engine.mqh",
                  "Core_InputsEN.mqh", "Core_Pending.mqh"):
            code.append("Core/%s/include/%s" % (cv, n))
    if hv:
        hdir = "Strategies/Hedge/" + hv
        code += rel_files(hdir, ["Hedge_EA*.mq5"]) + rel_files(hdir + "/include", ["*.mqh"])
        sets = rel_files(hdir + "/Set", ["*.set"])
        if sets:
            code.append(sets[0])
    code = [c for c in code if (ROOT / c).is_file()]
    return docs, code, SCOPE_NEW


def _uniq(items):
    out = []
    for i in items:
        if i not in out:
            out.append(i)
    return out


def _parts(built):
    return (built[0], built[1]) if built else ([], [])


# รายการไฟล์รวมของทุกงาน (ให้ tools/check_docs.py ตรวจเทียบกับ docs/AI_READ_SCOPE.md)
_core_d, _core_c = _parts(job_core(None))
_hedge_d, _hedge_c = _parts(job_strategy("Hedge", None, []))
_pend_d, _pend_c = _parts(job_strategy("Pending", None, ["docs/work/BLUEPRINT_Pending_v0.2.md"]))
_new_d, _new_c = _parts(job_new())
DOCS_STRATEGY = _uniq(_new_d + _hedge_d + _pend_d)
DOCS_CORE_EXTRA = _uniq(_core_d)
CODE_STRATEGY = _uniq(_new_c + _hedge_c + _pend_c)
CODE_CORE_EXTRA = _uniq(_core_c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", choices=["core", "hedge", "pending", "newstrategy"])
    ap.add_argument("--profile", choices=["strategy", "core"], help="ชื่อเดิม (strategy = newstrategy)")
    ap.add_argument("--strategy", help="ชื่อกลยุทธ์ใดก็ได้ในโฟลเดอร์ Strategies เช่น Grid")
    ap.add_argument("--version", help="รุ่นของงาน เช่น v1.1 (ไม่ระบุ = ล่าสุด)")
    ap.add_argument("--add", action="append", default=[], help="เพิ่มไฟล์ (path ใน Repo หรือ path เต็ม) ทำซ้ำได้")
    ap.add_argument("--redact", action="append", default=[], help="ข้อความที่จะแทนด้วย [REDACTED] ทำซ้ำได้")
    ap.add_argument("--out", default="ai_bundle")
    ap.add_argument("--force", action="store_true", help="สร้างต่อแม้ check_docs พบ ERROR")
    args = ap.parse_args()

    job = args.job
    if not job:
        job = "core" if args.profile == "core" else "newstrategy"

    rc, check_text = run_doc_check()
    print(check_text)
    if rc != 0 and not args.force:
        print("[STOP] check_docs พบ ERROR แก้ก่อนสร้าง Bundle (หรือใช้ --force)")
        return 1

    if args.strategy:
        job = args.strategy.lower()
        built = job_strategy(args.strategy, args.version, [])
    elif job == "core":
        built = job_core(args.version)
    elif job == "hedge":
        built = job_strategy("Hedge", args.version, [])
    elif job == "pending":
        built = job_strategy("Pending", args.version, ["docs/work/BLUEPRINT_Pending_v0.2.md"])
    else:
        built = job_new()

    if built is None:
        print("[ERROR] ไม่พบโฟลเดอร์ของงาน '%s' รุ่น '%s' ตรวจ --version" % (job, args.version))
        return 1

    docs, code, scope = built
    docs = list(docs)
    code = list(code)

    for a in args.add:
        norm = a.replace("\\", "/")
        if a.lower().endswith((".md", ".txt")) and "/include/" not in norm:
            docs.append(a)
        else:
            code.append(a)

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    out = ROOT / args.out / (job + "_" + stamp)
    files_dir = out / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    def redact(t):
        for r in args.redact:
            if r:
                t = t.replace(r, "[REDACTED]")
        return t

    commit, state = git_info()
    manifest = []
    missing = []
    seen = set()
    docs_parts, code_parts = [], []

    def collect(rel, parts, is_code):
        if rel in seen:
            return
        seen.add(rel)
        p = resolve(rel)
        if not p.is_file():
            missing.append(rel)
            return
        text = redact(read_text(p))
        label = rel if not Path(rel).is_absolute() else p.name
        parts.append("\n\n===== FILE: " + label + " =====\n\n" + text)
        flat = re.sub(r"[\\/ ]+", "__", label)
        if is_code and not flat.lower().endswith(".txt"):
            flat += ".txt"
        (files_dir / flat).write_text(text, encoding="utf-8")
        manifest.append((label, len(text), sha8(text)))

    for rel in docs:
        collect(rel, docs_parts, False)
    for rel in code:
        collect(rel, code_parts, True)

    header = ("# DOCS BUNDLE (งาน " + job + ")\n\nสร้างเมื่อ " + datetime.now().strftime("%Y-%m-%d %H:%M")
              + " | Commit " + commit + " | สถานะ Repo: " + state
              + "\nถ้าเนื้อหาในไฟล์ขัดกับกติกาในข้อความเริ่มต้น ให้แจ้งผู้ใช้ก่อนทำต่อ\n")
    (out / "01_DOCS_BUNDLE.md").write_text(header + "".join(docs_parts), encoding="utf-8")
    code_header = ("# CODE BUNDLE งาน " + job + " (นามสกุลจริงอยู่ในชื่อ FILE: ของแต่ละส่วน)\n"
                   "Commit " + commit + " | สถานะ Repo: " + state + "\n")
    (out / "02_CODE_BUNDLE.txt").write_text(code_header + "".join(code_parts), encoding="utf-8")
    prompt = BASE_PROMPT.replace("@@SCOPE@@", scope) + "\nฐานงาน: Commit " + commit + " | สถานะ Repo: " + state + "\n"
    (out / "00_START_PROMPT.txt").write_text(prompt, encoding="utf-8")

    lines = ["MANIFEST  งาน " + job + "  Commit " + commit + "  Repo " + state, ""]
    for label, n, h in manifest:
        lines.append("%8d chars  %s  %s" % (n, h, label))
    if missing:
        lines += ["", "ไม่พบไฟล์ (ตรวจว่าสร้างและ Commit แล้วหรือยัง):"] + ["  - " + m for m in missing]
    (out / "MANIFEST.txt").write_text("\n".join(lines), encoding="utf-8")

    total = sum(n for _, n, _ in manifest)
    print("สร้างชุดไฟล์ที่:", out)
    print("รวม %d ไฟล์ ประมาณ %d ตัวอักษร (เนื้อหาไทยใช้ Token มาก ถ้า Chatbot รับไม่ไหว ให้ตัดไฟล์ใหญ่ออกหรือแยกส่งเป็นรอบ)" % (len(manifest), total))
    print("ส่งให้ AI: 00_START_PROMPT.txt (วางเป็นข้อความ) + 01_DOCS_BUNDLE.md + 02_CODE_BUNDLE.txt")
    if missing:
        print("[WARN] ไม่พบ %d ไฟล์ ดู MANIFEST.txt" % len(missing))
    if args.redact:
        print("แทนที่ข้อความตามที่ระบุแล้ว แต่ยังควรเปิดตรวจไฟล์ก่อนส่ง")
    return 0


if __name__ == "__main__":
    sys.exit(main())