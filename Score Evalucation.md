เกณการประเมินคะแนนมีดังนี้
1. PNL Window 40คะแนน
2. Winrate Window Consistency 30 คะแนน
3. Recent Performance 30 คะแนน
4. Lose Streak 0 คะแนน

โดยวิธีการคิดคะแนนมีดังต่อไปนี้

**สูตรการคำนวนคะแนน PNL Window**
```sh
อ้างอิง PNL_KPI = 1000 และคะแนนแบ่งออกเป็น  แต่ละ WINDOWS ดังต่อไปนี้

72H = 5  คะแนน 
48H = 10 คะแนน 
24H = 15 คะแนน 
12H = 10 คะแนน 


KPI_72h = PNL_KPI * 2.5
Score72h = min((PNL_72h / KPI_72h) * 5, 5)

KPI_48h = PNL_KPI * 2.0
Score48h = min((PNL_48h / KPI_48h) * 10, 10)

KPI_24h = PNL_KPI * 1.0
Score24h = min((PNL_24h / KPI_24h) * 15, 15)

KPI_12h = PNL_KPI * 0.7
Score12h = min((PNL_12h / KPI_12h) * 10, 10)


#ตัวอย่างการคำนวนคะแนน  PNL Window
72H =MWP30 PNL 1550$ = max(0,min((1550 / 2500) * 5, 5)) = 3.1
48H =MWP30 PNL 1100$ = max(min((1100 / 2000) * 10, 10)) = 5.50
24H =MWP30 PNL 700$ =  max(min((700 / 1000) * 15, 15)) = 10.50
12H =MWP30 PNL 500$ =  max(min((500 / 700) * 10, 10)) = 7.14
```

################################################################


**สูตรการคำนวนคะแนน Winrate Window Consistency**

```sh

โดยแบ่งเป็น
72H = 8  คะแนน 
48H = 8  คะแนน 
24H = 8  คะแนน 
Cross-Window-Consistency = 6  คะแนน 

##สูตรคำนวน 24H-72H Windows
คะแนน = max(0, min(8, (Win_Rate - 55) × 8 ÷ 35))
อธิบาย:
- 55 = จุดคุ้มทุน (55.56% ปัดเศษ)
- 35 = ช่วงคะแนน (90-55)  
- 8 = คะแนนเต็ม

#ตัวอย่างการคำนวนคะแนน Winrate Window Consistency
72H = MWP30 WR 67% = max(0, min(8, (67 - 55) × 8 ÷ 35)) = 2.7


##สูตรคำนวน Cross-Window-Consistency

Variance = (WR_24H - WR_72H) + (WR_48H - WR_72H)
Score = max(0, min(6, 6 - (Variance × 6 ÷ (72H+48H+24H))))

#ตัวอย่างการคำนวนคะแนน  Cross-Window-Consistency
WR_24H = 68%
WR_48H = 67% 
WR_72H = 67%

Variance = (68-67) + (67-67) = 1
Score = max(0, min(6, 6 - (1 × 6 ÷ (8+8+8))))
Score = 6 คะแนน


```


################################################################


**สูตรการคำนวนคะแนน Recent Performance**

```sh
#RecentPerformanceScore 30 คะแนน

โดยกำหนดให้ PNL1H - PNL6H มีค่าตามตัวอย่างนี้

A= PNL₁=1,350, PNL₂=1,150, PNL₃=900, PNL₄=700, PNL₅=600, PNL₆=500
B= PNL₁=500, PNL₂=1,350, PNL₃=2,000, PNL₄=200, PNL₅=400, PNL₆=300


##แทนค่าลงสูตร
RecentScore_raw = 5×max(PNL₁−PNL₂,0) + 4×max(PNL₁−PNL₃,0) + 3×max(PNL₁−PNL₄,0) + 2×max(PNL₁−PNL₅,0) + 1×max(PNL₁−PNL₆,0)
Recent_KPI = mean(RecentScore_raw) + std(RecentScore_raw)
RecentScore = min((RecentScore_raw / Recent_KPI) × RecentPerformanceScore, RecentPerformanceScore)

1. หาค่า RecentScore_raw ของแต่ละสัญญาน

RecentScore_raw_A =
  5×max(1350−1150,0) +
  4×max(1350−900,0) +
  3×max(1350−700,0) +
  2×max(1350−600,0) +
  1×max(1350−500,0)
= 5×200 + 4×450 + 3×650 + 2×750 + 1×850
= 1,000 + 1,800 + 1,950 + 1,500 + 850
= 7,100

RecentScore_raw_B =
  5×max(500−1350,0) +
  4×max(500−2000,0) +
  3×max(500−200,0) +
  2×max(500−400,0) +
  1×max(500−300,0)
= 5×0 + 4×0 + 3×300 + 2×100 + 1×200
= 0 + 0 + 900 + 200 + 200
= 1,300

เรามีค่า RecentScore_raw 2 ค่า
r₁ = 7,100
r₂ = 1,300

*********************************************************

2. หา Recent_KPI จากค่าทั้งหมด

2.1 หา mean (μ)
μ = (r₁ + r₂) / 2
  = (7,100 + 1,300) / 2
  = 4,200

2.2 หา variance (ความแปรปรวนแบบ population)
variance = [ (r₁ − μ)² + (r₂ − μ)² ] / 2
         = [ (7,100 − 4,200)² + (1,300 − 4,200)² ] / 2
         = [ (2,900)² + (−2,900)² ] / 2
         = (8,410,000 + 8,410,000) / 2
         = 8,410,000

2.3 หา standard deviation (σ)
σ = √variance
  = √8,410,000
  ≈ 2,900


2.4 คำนวณ Recent_KPI
Recent_KPI = μ + σ
           = 4,200 + 2,900
           = 7,100





 = (7,100 + 1,300) / 2 = 4,200
std ช 

Std = √[((7100-4200)² + (1300-4200)²) / 2] 
    = √[(2900² + 2900²) / 2] 
    = √[16,820,000 / 2] 
    = 2900

Recent_KPI = 4,200 + 2,900 = 7,100

*********************************************************


3. แปลงเป็นคะแนนเต็ม 20

RecentScore_A = min((7,100 / 7,100) × 20, 20) = 20
RecentScore_B = min((1,300 / 7,100) × 20, 20) ≈ 3.66

สรุป: A ได้คะแนนเต็ม 20, B ได้ประมาณ 3.7

```



################################################################

