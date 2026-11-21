ทั้งสองไฟล์ด้านล่างเป็นตัวอย่างจำลอง กลยุทธ์ "SMC" ที่ใช้เป็นกฎที่ผมแต่งให้ง่ายที่สุด ไม่ใช่คำแนะนำการเทรด ส่วนชื่อฟังก์ชัน Core ทั้งหมด (`RawPendingPlace`, `CorePendingDeleteAll`, `CanOpenAuto` ฯลฯ) ผมเปิดอ่านจาก `Core_Pending.mqh` ใน repo จริงและ `Pending_Strategy.mqh` ของ platform แล้ว แต่ยังไม่ได้คอมไพล์แพตช์นี้ ในการใช้งานจริง AI ต้องขอเนื้อไฟล์ปัจจุบันจากคุณก่อนเขียนแพตช์ ที่ผมเขียน FIND ได้เพราะเป็นโครงเปล่าที่ผมสร้างเอง

## ตัวอย่าง `docs/BLUEPRINT.md` (จำลอง)

````markdown
# BLUEPRINT: SMC

สถานะ: สรุปแล้ว รอผู้ใช้พิมพ์ "เริ่มงาน" | อัปเดต: 2026-11-20

## 1. เป้าหมายและแนวคิดกลยุทธ์
(ตัวอย่างจำลอง) วาง Buy Limit หนึ่งออเดอร์ที่ขอบล่างของโซนราคาที่ผู้ใช้กำหนดผ่าน Input เมื่อราคาลงมาแตะและออเดอร์ถูก Fill ให้ Core Protect ดูแลไม้ต่อ (Cut Loss, BE, R:R, Trailing TP) กลยุทธ์ไม่ตรวจหาโซนเอง เวอร์ชันแรกกำหนดโซนด้วยมือเท่านั้น

## 2. สเปก (ตามฟอร์ม)
| หัวข้อ | ค่าที่ตกลง |
|---|---|
| ชื่อ / เวอร์ชัน | SMC / 1.0.0 |
| TAG / ลำดับ EA | SMC / 3 (Magic ฐาน 30000) Comment `SMC30000 H1 base` |
| Core ฐาน | v1.1 commit 30c3001 (ตาม `Core/v1.1/PINNED_FROM.txt`) |
| ชนิดบัญชี | Hedging เท่านั้น |
| เงื่อนไขเข้า | 1) โซนถูกต้อง: ขอบล่าง > 0 และขอบบน > ขอบล่าง 2) ราคาเข้า = ขอบล่าง + Offset (Points) ต้องไม่เกินขอบบน 3) ผ่านประตู `CanOpenAuto` ของ Core (OFF, รายงาน, ทุน, Session, Timeout, สเปรด) 4) ไม่มี Position และไม่มี Pending ค้าง |
| ชนิดออเดอร์ | Pending Buy Limit ราคา = ขอบล่าง + Offset ถ้าราคาตลาดไม่อยู่ฝั่งที่ถูกหรือใกล้เกิน Stops Level Core ปฏิเสธและกลยุทธ์พัก 60 วินาที |
| Lot / ทุน | Auto-Lot ของ Core ตามค่าเริ่มต้น Lock Profit ปิด |
| SL / TP | SL = ราคาเข้า − Cut Loss ส่งไปกับ Pending ตั้งแต่แรก TP ไม่ตั้ง ให้ Protect ปิดตาม R:R / Trailing |
| Basket | หนึ่งออเดอร์ต่อรอบ รอบจบเมื่อไม่มี Position และไม่มี Pending เปิดรอบใหม่หลัง Timeout ของ Core |
| ปุ่ม OFF | หยุดตั้งออเดอร์ใหม่ และลบ Pending ที่รออยู่ (Position ที่เปิดแล้ว Protect ดูแลต่อ) |
| ช่วง Session Block | ลบ Pending ที่รออยู่ ไม่ตั้งใหม่จนพ้นช่วง |
| CLOSE ALL | ลบ Pending ก่อน แล้วปิด Position และเริ่มนับ Timeout ใหม่ |
| ปุ่มของกลยุทธ์ | ไม่มี (`Strategy_ButtonCount` = 0) |
| ถอด EA / ปิดกราฟ | ลบ Pending ที่ค้าง (เปลี่ยน Timeframe, F7, ปิด MT5 ไม่ลบ) |

### Inputs เฉพาะกลยุทธ์ (กลุ่ม H)
| ชื่อ | ชนิด | ค่าเริ่มต้น | ป้ายไทย | ป้ายอังกฤษ |
|---|---|---|---|---|
| `InpZoneLower` | double | 0.0 | ราคาขอบล่างของโซน (0 = ปิด) | Zone lower edge price (0 = disabled) |
| `InpZoneUpper` | double | 0.0 | ราคาขอบบนของโซน | Zone upper edge price |
| `InpEntryOffset` | int | 0 | ระยะเหนือขอบล่างสำหรับราคาเข้า (Points) | Points above the lower edge for entry |

## 3. ผลกระทบต่อ Core
- ใช้ API เดิมของ v1.1 ได้ทั้งหมด ไม่ต้องแก้ Core: `RawPendingPlace`, `CorePendingTotal`, `CorePendingDeleteAll` (Core_Pending), `CanOpenAuto`, `BeginBasketCycle`, `TryGetVirtualEquity`, `GetEffectiveLotForEquity`, `CoreIsPaused`, `IsAutoBlockedBySession`
- EA หลักต้อง include `Core_Pending.mqh` เพิ่ม (โครงเปล่าไม่ได้ include ไว้)
- ข้อจำกัดของ Core ที่ต้องรู้: Pending ที่ Core วางเป็นแบบ GTC ไม่มีวันหมดอายุ และ TP ของ Pending เป็น 0 เสมอ
- ไม่มี Session Close และ `InpCountExternalClose` (D-30 ยังไม่อยู่ใน v1.1) ถ้าต้องการให้เปิดเป็นงาน Core ที่ `EA_Platform_Core`

## 4. แผนไฟล์ (Folder Tree และหน้าที่ต่อไฟล์)
```text
Strategies/SMC/v1.1/
  SMC_EA.mq5               แก้: include Core_Pending, ลบ Pending ตอนถอด EA
  include/SMC_Inputs.mqh   แก้: เพิ่ม Input โซน 3 ตัว (ไทย/อังกฤษ)
  include/SMC_Strategy.mqh แก้: ตรรกะตั้ง Buy Limit, ยกเลิกตามกติกา OFF/Session, ผูก Strategy_* ให้ครบ
```
ไม่แตะ `Core/` และไม่แตะ `SMC_EA_EN.mq5`, `SMC_EA_TH.mq5`

## 5. แผนทดสอบ (Demo XAUUSD, Magic ทดลองนอกโฟลเดอร์ Set)
| ข้อ | ทดสอบ | ผลที่คาดหวัง |
|---|---|---|
| Z-01 | โซนถูกต้อง ราคาอยู่เหนือโซน | วาง Buy Limit 1 ออเดอร์ Entry แสดง ARMED |
| Z-02 | ปล่อยให้ราคาลงมา Fill | Entry แสดง RUNNING Protect ตั้ง SL/BE ตามปกติ |
| Z-03 | โซนผิด (ขอบบน <= ขอบล่าง) | ไม่วาง Entry แสดง ZONE_INVALID |
| Z-04 | กด OFF ขณะมี Pending | Pending ถูกลบ Entry แสดง PAUSED |
| Z-05 | อยู่ในช่วง Session Block | Pending ถูกลบ ไม่วางใหม่ |
| Z-06 | CLOSE ALL | Pending ถูกลบและปิดไม้ นับ Timeout ใหม่ |
| Z-07 | ถอด EA | Pending ที่ค้างถูกลบ |
| Z-08 | ราคาตลาดต่ำกว่าราคาเข้า (ผิดฝั่ง Limit) | Core ปฏิเสธ มี Log `PENDING PLACE BLOCKED` กลยุทธ์พัก 60 วินาที (COOLDOWN) |
| Z-09 | รีสตาร์ท EA ขณะมี Pending | Pending ยังอยู่ กลยุทธ์ไม่วางซ้ำ |

## 6. เรื่องที่ยังไม่ตัดสิน
- ต้องการ Session Close หรือไม่ (ถ้าต้องการ ต้องรอ Core รุ่นที่มี D-30)
- ต้องการ Pending หมดอายุตามเวลาหรือไม่ (Core ยังไม่รองรับ)
- ฝั่ง Sell และหลายโซน (ยังไม่อยู่ในเวอร์ชัน 1.0)
````

## ตัวอย่างหนึ่งชุด (batch 1): วางตรรกะตั้ง Buy Limit

ชุดนี้แก้ 3 ไฟล์ รวม 9 จุด FIND ทุกจุดต้องเจอ 1 รายการพอดี ไฟล์ทั้งหมดอยู่ใต้ `Strategies/SMC/v1.1/` (ข้อความในโครงเปล่าหลัง `init_strategy` คำว่า Template กลายเป็น SMC แล้ว)

### ไฟล์ 1/3: `SMC_EA.mq5`

[PATCH 1.1] include Core_Pending (ต้องอยู่หลัง Core_Engine และก่อน Core_StrategyAPI)

FIND:
```text
#include "Core/include/Core_Engine.mqh"
```
REPLACE:
```text
#include "Core/include/Core_Engine.mqh"
#include "Core/include/Core_Pending.mqh"
```

[PATCH 1.2] ถอด EA หรือปิดกราฟ = ลบ Pending ที่ค้าง

FIND:
```text
void OnDeinit(const int reason)
  {
   CoreOnDeinit(reason);
  }
```
REPLACE:
```text
void OnDeinit(const int reason)
  {
   //--- ถอด EA หรือปิดกราฟ = ลบ Pending ที่ค้าง (F7 / เปลี่ยน TF / ปิด MT5 ไม่ลบ)
   if(reason == REASON_REMOVE || reason == REASON_CHARTCLOSE)
      CorePendingDeleteAll("SMC-REMOVE");

   CoreOnDeinit(reason);
  }
```

### ไฟล์ 2/3: `include/SMC_Inputs.mqh`

[PATCH 2.1] เพิ่ม Input โซน (ไทยและอังกฤษ ชื่อ ชนิด ลำดับ ค่าเริ่มต้นเหมือนกัน)

FIND:
```text
//--- (ยังไม่มี Input เฉพาะกลยุทธ์)
```
REPLACE:
```text
input group "=== H. SMC Zone ==="
#ifdef INPUT_LANG_EN
input double InpZoneLower   = 0.0;   // InpZoneLower - Zone lower edge price (0 = disabled)
input double InpZoneUpper   = 0.0;   // InpZoneUpper - Zone upper edge price (must be above lower)
input int    InpEntryOffset = 0;     // InpEntryOffset - Points above the lower edge for entry
#else
input double InpZoneLower   = 0.0;   // ราคาขอบล่างของโซน (0 = ปิด)
input double InpZoneUpper   = 0.0;   // ราคาขอบบนของโซน (ต้องมากกว่าขอบล่าง)
input int    InpEntryOffset = 0;     // ระยะเหนือขอบล่างสำหรับราคาเข้า (Points)
#endif
```

### ไฟล์ 3/3: `include/SMC_Strategy.mqh`

[PATCH 3.1] เพิ่มฟังก์ชันของกลยุทธ์ (วางก่อน `Strategy_Title`)

FIND:
```text
string Strategy_Title()
```
REPLACE:
```text
#define SMC_FAIL_COOLDOWN 60   // วินาทีพักหลังวาง Pending ล้มเหลว

datetime g_smcLastFail   = 0;
datetime g_smcLastCancel = 0;

//--- โซนถูกต้องหรือไม่ (why = เหตุผลที่แสดงบนแถว Entry)
bool SmcZoneValid(string &why)
  {
   why = "";

   if(InpZoneLower <= 0.0 || InpZoneUpper <= InpZoneLower)
     {
      why = "ZONE_INVALID";
      return(false);
     }

   if(InpEntryOffset < 0 || PointsToPrice(InpEntryOffset) > (InpZoneUpper - InpZoneLower))
     {
      why = "ENTRY_OUTSIDE_ZONE";
      return(false);
     }

   return(true);
  }

double SmcEntryPrice()
  {
   return(InpZoneLower + PointsToPrice(InpEntryOffset));
  }

//--- วาง Buy Limit หนึ่งออเดอร์ (SL ส่งไปกับ Pending, Protect ปรับต่อหลัง Fill)
bool SmcPlaceBuyLimit()
  {
   if(!g_engineReady)
      return(false);

   if(CoreIsPaused())
     {
      Print(CORE_LOG_PREFIX, " SMC ENTRY BLOCKED | PAUSED");
      return(false);
     }

   if(g_reportBlocksEntry)
     {
      Print(CORE_LOG_PREFIX, " SMC ENTRY BLOCKED | WAIT_REPORT");
      return(false);
     }

   double equity = 0.0;

   if(!TryGetVirtualEquity(equity))
     {
      Print(CORE_LOG_PREFIX, " SMC ENTRY BLOCKED | CAPITAL_UNAVAILABLE");
      return(false);
     }

   if(equity <= 0.0)
     {
      Print(CORE_LOG_PREFIX, " SMC ENTRY BLOCKED | CAPITAL_DEAD | Equity=", DoubleToString(equity, 2));
      return(false);
     }

   double lot = GetEffectiveLotForEquity(equity);

   if(!MathIsValidNumber(lot) || lot <= 0.0)
     {
      Print(CORE_LOG_PREFIX, " SMC ENTRY BLOCKED | INVALID_LOT");
      return(false);
     }

   //--- รอบใหม่ (ไม่มี Position) บันทึกฐาน Cycle ก่อนส่งออเดอร์แรก
   if(CoreBasketPositions() == 0 && !BeginBasketCycle())
      return(false);

   double price  = SmcEntryPrice();
   double sl     = price - PointsToPrice(InpCutLossPoints);
   ulong  ticket = RawPendingPlace(ORDER_TYPE_BUY_LIMIT, lot, price, sl, "SMC");

   if(ticket == 0)
      return(false);

   g_emptySince = 0;

   Print(CORE_LOG_PREFIX, " SMC PENDING PLACED #", ticket,
         " | entry=", DoubleToString(price, _Digits),
         " | lot=", DoubleToString(lot, 2));
   return(true);
  }

//--- เรียกทุก Tick (หลัง Protect ทำงานเสร็จ)
void SmcOnTick()
  {
   if(!g_engineReady)
      return;

   datetime now       = TimeCurrent();
   int      positions = CoreBasketPositions();
   int      pendings  = CorePendingTotal();

   //--- มี Position = Basket ไม่ว่าง ให้ Core เริ่มนับ Timeout ใหม่ตอนว่าง
   if(positions > 0)
      g_emptySince = 0;

   //--- ปุ่ม OFF หรือช่วง Session Block: ลบ Pending ที่รออยู่ (ถ่วงอย่างน้อย 2 วินาที)
   if(pendings > 0 && (CoreIsPaused() || IsAutoBlockedBySession()))
     {
      string tag = CoreIsPaused() ? "SMC-OFF" : "SMC-SESSION";

      if(now - g_smcLastCancel >= 2)
        {
         g_smcLastCancel = now;
         CorePendingDeleteAll(tag);
         g_emptySince = now;
        }

      g_gateReason = CoreIsPaused() ? "PAUSED" : "SESSION_BLOCK";
      return;
     }

   if(positions > 0 || pendings > 0)
     {
      g_gateReason = (positions > 0) ? "RUNNING" : "ARMED";
      return;
     }

   //--- ว่าง: ตรวจโซน แล้วผ่านประตู Core ก่อนวาง
   string why = "";

   if(!SmcZoneValid(why))
     {
      g_gateReason = why;
      return;
     }

   if(g_smcLastFail > 0 && now - g_smcLastFail < SMC_FAIL_COOLDOWN)
     {
      g_gateReason = "COOLDOWN";
      return;
     }

   string reason = "";

   if(!CanOpenAuto(g_emptySince, reason))
     {
      g_gateReason = reason;
      return;
     }

   Print(CORE_LOG_PREFIX, " AUTO READY -> วาง Buy Limit | Spread=",
         DoubleToString(GetSpreadPoints(), 1),
         " / Max=", InpMaxSpreadPoints,
         " | Timeout=", InpTimeoutSeconds, " sec");

   if(SmcPlaceBuyLimit())
     {
      g_smcLastFail = 0;
      g_gateReason  = "ARMED";
     }
   else
      g_smcLastFail = now;
  }

string Strategy_Title()
```

[PATCH 3.2] เลขรุ่นกลยุทธ์

FIND:
```text
   return("0.0.0");
```
REPLACE:
```text
   return("1.0.0");
```

[PATCH 3.3] บัญชี Hedging เท่านั้น

FIND:
```text
   return(ACCT_ANY);
```
REPLACE:
```text
   return(ACCT_HEDGING_ONLY);
```

[PATCH 3.4] ตรวจ Input ตอนเริ่ม

FIND:
```text
bool Strategy_Init()
  {
   return(true);
  }
```
REPLACE:
```text
bool Strategy_Init()
  {
   if(InpZoneLower < 0.0 || InpZoneUpper < 0.0 || InpEntryOffset < 0)
     {
      Alert(CORE_LOG_PREFIX, " ค่าโซนและ Offset ต้องไม่ติดลบ");
      return(false);
     }

   Print(CORE_LOG_PREFIX, " SMC พร้อม | โซน=", DoubleToString(InpZoneLower, _Digits),
         " ถึง ", DoubleToString(InpZoneUpper, _Digits),
         " | offset=", InpEntryOffset, " pts");
   return(true);
  }
```

[PATCH 3.5] ผูกตรรกะเข้ากับ Tick

FIND:
```text
   g_gateReason = "NO_STRATEGY";
```
REPLACE:
```text
   SmcOnTick();
```

[PATCH 3.6] CLOSE ALL ลบ Pending ก่อน

FIND:
```text
void Strategy_CloseAll(string tag)
  {
```
REPLACE:
```text
void Strategy_CloseAll(string tag)
  {
   CorePendingDeleteAll(tag);
   g_emptySince = TimeCurrent();   // เริ่มนับ Timeout ใหม่หลัง CLOSE ALL
```

### คำสั่งที่ต้องรันหลังทำแพตช์ (เรียงลำดับ)

1. บันทึกทั้ง 3 ไฟล์ (`.mq5` และ `.mqh` เป็น UTF-8 with BOM)
2. กด F7 คอมไพล์ `SMC_EA_TH.mq5` และ `SMC_EA_EN.mq5` ต้อง 0 errors 0 warnings
3. `tools\run_checks.bat` ต้อง verify_core ERROR 0 และ check_docs ERROR 0
4. `python tools\log_entry.py` กรอกร่าง แล้ว `--append`
5. commit และ push แล้วส่ง `tools\out\RUN_REPORT.txt` กลับให้ AI

## สิ่งที่ควรเห็นเมื่อทดสอบ (ตรงกับ Z-01 ถึง Z-04)

- ตั้ง `InpZoneLower`, `InpZoneUpper` บนกราฟ ถ้าเป็นค่า 0 แถว Entry แสดง `ZONE_INVALID` ยังไม่วางอะไร
- ผ่านประตู Core แล้ว Log แสดง `AUTO READY -> วาง Buy Limit` ตามด้วย `PENDING PLACED #...` (จาก Core) และ `SMC PENDING PLACED #...` (จากกลยุทธ์) Entry เป็น `ARMED`
- กด OFF ขณะมี Pending: Log `PENDING DELETED #...` และ Entry เป็น `PAUSED`
- ถ้า Limit ถูกวางผิดฝั่ง Core บันทึก `PENDING PLACE BLOCKED | TOO_CLOSE_OR_WRONG_SIDE ...` แล้วกลยุทธ์พัก 60 วินาที (`COOLDOWN`)

## ข้อสังเกตเรื่องรูปแบบ

ชุดงานนี้ตั้งใจให้เล็กพอที่คุณตรวจเองได้ในรอบเดียว ชุดต่อไปที่ควรมีคือ Preset `.set`, คู่มือทดสอบ Z-01 ถึง Z-09 และการอัปเดต `docs/work/TEST_MATRIX.md` ถ้าอยากเห็นตัวอย่างชุดถัดไป หรือให้ผมปรับ BLUEPRINT ให้เหมือนกลยุทธ์จริงของคุณ (เช่น เพิ่มฝั่ง Sell หรือหลายโซน) บอกกติกาเข้าที่ต้องการมา ผมจะเขียนใหม่ให้ครับ