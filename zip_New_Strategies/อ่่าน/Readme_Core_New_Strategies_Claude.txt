จากนี้ไปเวลาคุณจะสร้างบอทตัวใหม่ (เช่น EA_SMC):
1. แตกไฟล์ template-v0.1.1.zip ออกมาเป็นโฟลเดอร์ใหม่ตั้งชื่อว่า EA_SMC
2. รันคำสั่ง python tools\make_ai_bundle.py --job consult เพื่อเอาชุดไฟล์ไปปรึกษาและวางแผนกลยุทธ์กับ AI ได้ทันทีครับ

ด้านล่างคือการจำลองใช้งานจริงครั้งแรกตั้งแต่ unzip จนได้โค้ดชุดแรก โดยใช้กลยุทธ์สมมติชื่อ SMC (ตัวอย่างสเปกเป็นเรื่องแต่งขึ้นเพื่อให้เห็นระดับรายละเอียดที่ต้องกรอก ไม่ใช่คำแนะนำการเทรด) ข้อความและคำสั่งในแต่ละขั้นมาจากไฟล์ใน repo จริง ส่วนคำตอบของ AI เป็นตัวอย่างจำลองรูปแบบ

## เฟส 1: ปรึกษา (ยังไม่มี repo)

1. unzip `template-v0.1.1.zip` ไว้ที่ `Core_Strategies\New_Strategies` (ในไฟล์ zip มีโฟลเดอร์ `New_Strategies` ให้อยู่แล้ว)
2. เนื่องจากยังไม่มี repo บน GitHub AI อ่านเองไม่ได้ จึงสร้างชุดไฟล์:
   ```text
   cd Core_Strategies\New_Strategies
   python tools\make_ai_bundle.py --job consult
   ```
   ผลขึ้นประมาณ `โหมด: lite` และสร้าง `ai_bundle\consult_lite_<เวลา>\` (ถ้าไม่ได้ทำแพตช์ M10 ชื่อจะเป็น `consult_<เวลา>`)
3. เปิดแชตใหม่กับ AI วางข้อความข้อ 1 จาก `docs/AI_START_PROMPT.md` (ปรึกษาและสรุปสเปก) แนบ `00_START_PROMPT.txt` (วางเป็นข้อความ) กับ `01_DOCS_BUNDLE.md` และ `02_CODE_BUNDLE.txt`
4. คำตอบแรกของ AI ควรสั้น (ไม่เกิน 12 บรรทัด) ตัวอย่างจำลอง:
   - ฐานงาน: Core v1.1, commit `30c3001` (ตาม `PINNED_FROM.txt`)
   - ข้อจำกัด: v1.1 มี `Core_Pending` (ออเดอร์ค้าง) แต่ยังไม่มี Session Close และ `InpCountExternalClose` (D-30)
   - ไฟล์ที่ผมเปิดอ่านจริง: (รายการ)
   - ขาด: เงื่อนไขเข้า, วิธีคำนวณราคา Limit, SL/TP, นิยาม Basket, พฤติกรรมเมื่อกด OFF กับออเดอร์ค้าง
5. ตอบสเปกทีละข้อตาม `docs/SPEC_FORM.md` ตัวอย่างสมมติที่กรอกแล้ว:
   ```text
   ชื่อกลยุทธ์ / เวอร์ชัน: SMC / 1.0
   TAG / ลำดับ EA: SMC / 3 (Magic ฐาน 30000)
   Core รุ่นและ Commit ฐาน: v1.1 / 30c3001
   ชนิดบัญชี: Hedging
   เงื่อนไขเข้า: (สมมติ) ราคาแตะโซนที่กำหนดด้วย Input ขอบบนและขอบล่าง
   ชนิดออเดอร์: Pending Buy Limit ที่ขอบล่างของโซน
   Lot / ทุน: ใช้ Auto-Lot ของ Core ค่าเริ่มต้นเดิม Lock Profit ปิด
   SL / TP: SL คงที่ 800 Points, TP ตาม Trailing ของ Core
   Basket: หนึ่งออเดอร์ต่อรอบ เปิดรอบใหม่เมื่อไม่มีออเดอร์และไม่มี Pending
   ปุ่ม OFF: หยุดตั้งออเดอร์ใหม่ และลบ Pending ที่รออยู่
   ปุ่มกลยุทธ์: ไม่มี
   เรื่องที่ยังไม่ตัดสิน: ต้องการ Session Close หรือไม่
   ```
6. ผลที่น่าจะได้ (นี่คือประโยชน์ของโหมดปรึกษา): AI สรุปลง `docs/BLUEPRINT.md` และชี้ว่าข้อ "ต้องการ Session Close" ต้องมี D-30 ใน Core ซึ่ง v1.1 ไม่มี จึง**หยุดและแจ้งว่าเป็นงาน Core ที่ `EA_Platform_Core`** ตามกติกา R-1 คุณเลือกได้ว่าเริ่มด้วย v1.1 โดยไม่มี Session Close ก่อน (ใส่ไว้ใน "เรื่องที่ยังไม่ตัดสิน") หรือรอพอร์ต D-30 เข้า Core ก่อน
7. คัดลอกผลสรุปของ AI ลง `docs/BLUEPRINT.md` และเติม `docs/SPEC_FORM.md` ให้ครบ (ถ้ากลัวไฟล์หาย ทำ `git init` ในโฟลเดอร์นี้ได้เลย ยังไม่ต้องมี remote)

## เฟส 2: ตั้งชื่อและสร้าง Repo

```text
python tools\init_strategy.py --name SMC --tag SMC --ordinal 3
```

ผลที่เห็น (รูปแบบเดียวกับที่คุณเห็นตอนทดสอบ Demo):
- แสดงแผน `Strategies/Template -> Strategies/SMC` และ `TAG=SMC ลำดับ=3 Magic ฐาน=30000 ถึง 39999 ถัดไป=30001 Comment=SMC30000 H1 base`
- สแกน repo ข้างเคียง ถ้า TAG, ลำดับ หรือ Magic ซ้ำกับกลยุทธ์อื่นจะขึ้น `[WARN]` และไม่เขียนไฟล์
- ถาม `เขียนไฟล์จริงไหม? (Y/N)` ตอบ Y

จากนั้นทำตามลำดับ:

1. คอมไพล์ `Strategies\SMC\v1.1\SMC_EA_TH.mq5` ต้อง 0 errors 0 warnings
2. เปลี่ยนชื่อโฟลเดอร์ `New_Strategies` เป็น `EA_SMC`
3. รัน `tools\run_checks.bat` ต้อง verify_core ERROR 0 และ check_docs ERROR 0 (WARN เรื่อง `.set` ยังมีตามปกติ)
4. สร้าง repo ว่างชื่อ `EA_SMC` (Private) บน GitHub แล้ว:
   ```text
   git init
   git add .
   git commit -m "init EA_SMC จากแม่แบบ 0.1.1"
   git branch -M main
   git remote add origin [https://github.com/](https://github.com/)<ชื่อผู้ใช้>/EA_SMC.git
   git push -u origin main
   ```
   ถ้า git ฟ้อง "dubious ownership" บนไดรฟ์ W: ให้ใช้คำสั่ง `git config --global --add safe.directory ...` ที่ git แจ้งมา
5. อัปเดต `docs/work/CURRENT_STATE.md` เติมเลข commit ที่ push แล้ว

## เฟส 3: สร้างและทดสอบเป็นชุดๆ

1. ถ้า AI เข้า GitHub ได้ ใช้ข้อความข้อ 2 ใน `docs/AI_START_PROMPT.md` (สร้างและแก้กลยุทธ์) ได้เลย ถ้าเข้าไม่ได้ ใช้ `python tools\make_ai_bundle.py --job build` (โหมด lite ประมาณ 51,000 ตัวอักษร) ถ้า AI ขอไฟล์ที่ตัดออก ให้เพิ่มด้วย `--add` หรือรันซ้ำด้วย `--full`
2. AI ส่ง Folder Tree พร้อมหน้าที่ต่อไฟล์ก่อน (ตัวอย่างจำลอง: แก้ `SMC_Inputs.mqh` เพิ่ม Input ของโซน, แก้ `SMC_Strategy.mqh` ใส่ตรรกะตั้ง Pending) แล้วรอคำว่า "เริ่มงาน" ในขั้นนี้ AI ยังไม่ส่งโค้ด ตรวจแผนก่อน
3. พิมพ์ "เริ่มงาน" AI ส่งงานเป็นชุด (batch):
   - ไฟล์ใหม่: Full Code พร้อม path
   - ไฟล์ที่มีอยู่แล้ว (เช่น `SMC_Strategy.mqh` จากโครงเปล่า): ส่งเป็นแพตช์ FIND/REPLACE ตาม `docs/handoff/JIGSAW_PATCH_RULE.txt` และ AI ต้องขอเนื้อไฟล์ปัจจุบันจากคุณก่อน ห้ามแก้จากความจำ
   - ปิดท้ายด้วยรายการคำสั่งที่คุณต้องรัน
4. วนซ้ำต่อชุด: ทำแพตช์ในไฟล์ > F7 คอมไพล์ 0/0 > `run_checks.bat` > `log_entry.bat` (ร่าง กรอก แล้ว `--append`) > commit > push > ส่ง `RUN_REPORT.txt` กลับให้ AI
5. ทดสอบบน Demo: สร้างไฟล์ `.set` ที่ Comment ขึ้นต้น `SMC30001` และ Magic อยู่ในช่วง 30000 ถึง 39999 (ถ้าผิด `verify_core` ฟ้องทันที) บันทึกผลใน `docs/work/TEST_MATRIX.md` ใช้ PASS เมื่อมี Log หรือภาพแนบ PASS* เมื่อรายงานเป็นข้อความ ทดสอบเสร็จแล้วลบ Global Variable ทดสอบใน F3 และห้ามเก็บค่าทดลองเป็น `.set` ใน repo
6. เมื่อทดสอบผ่านครั้งแรก commit เอกสารปิดงานก่อน แล้วติด tag `smc-v1.1-r0` ที่ commit นั้น การแก้เฉพาะกลยุทธ์ครั้งต่อไปใช้ `smc-v1.1-r1`, `-r2` ฯลฯ ตาม R-4

## เมื่อ Core หลักออกรุ่นใหม่ (ตัวอย่าง)

พอพอร์ต D-30 เข้า Core เป็นรุ่น v1.2 และ checkout `EA_Platform_Core` ตาม tag นั้น:
```text
python tools\update_core.py --platform <โฟลเดอร์ EA_Platform_Core> --version v1.2
```
เครื่องมือแสดงแผนและระดับความเสี่ยงของการเปลี่ยน ถามยืนยัน แล้วสร้าง `Strategies\SMC\v1.2` ข้างของเดิม พร้อม `docs/work/CORE_UPDATE_v1.1_to_v1.2.md` ใช้ข้อความข้อ 3 ใน `docs/AI_START_PROMPT.md` ให้ AI ประเมินผลกระทบ แล้วทำตามรายการตรวจ รุ่น v1.1 ยังอยู่ ย้อนกลับได้

## จุดที่มักพลาดตอนใช้ครั้งแรก

- **อย่ารัน `init_strategy` ใน repo แม่แบบ** เพราะมันลบ `Strategies/Template` รันเฉพาะในสำเนาที่ unzip
- **อย่าแก้ไฟล์ใน `Core/` และสำเนา Core** `verify_core` จับได้ ถ้าต้องการอะไรเพิ่มจาก Core ให้หยุดและเปิดงาน Core
- **รัน `make_ai_bundle` หลายโหมดในนาทีเดียวกันโฟลเดอร์จะชนกัน** (แก้ด้วยแพตช์ M10)
- **สเปกคลุมเครือ AI ควรถามกลับ ไม่ใช่เดา** ถ้า AI เริ่มเขียนโค้ดโดยที่คุณยังไม่พิมพ์ "เริ่มงาน" ให้หยุดและอ้างกติกา R-5

ต้องการให้ผมจำลองต่ออีกส่วนไหนไหมครับ เช่น ตัวอย่างเต็มของ `docs/BLUEPRINT.md` ที่ AI ควรสรุป หรือตัวอย่างหนึ่งชุด (batch) ของแพตช์ Jigsaw สำหรับ `SMC_Strategy.mqh`