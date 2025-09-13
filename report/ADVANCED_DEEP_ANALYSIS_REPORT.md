# Advanced Deep Pattern Analysis Report
## การวิเคราะห์ Pattern อย่างลึกและละเอียดที่สุด

**วันที่วิเคราะห์**: 2025-09-13 22:49:55  
**ข้อมูลที่ใช้**: 4,383 records จากฐานข้อมูล  
**วิธีการวิเคราะห์**: Statistical Significance + Advanced ML + Clustering + Time Series  

---

## 🎯 สรุปผลการวิเคราะห์

### **Overall Performance**
- **Total Records**: 4,383
- **Overall Win Rate**: 47.4%
- **Analysis Period**: 2025-08-28 03:50:05 ถึง 2025-09-13 22:46:03

---

## 📊 Significant Patterns ที่พบ (Statistical Significance)

### **🕐 เวลาที่มีนัยสำคัญทางสถิติ**

**🔥 #1 ชั่วโมง 21:00** 📈
- **Win Rate**: 62.3% (+14.9% จากค่าเฉลี่ย)
- **จำนวนสัญญาณ**: 183 ครั้ง
- **P-value**: 0.000057
- **Effect Size**: 0.300
- **ระดับนัยสำคัญ**: High

**⚡ #2 ชั่วโมง 23:00** 📉
- **Win Rate**: 35.5% (-11.9% จากค่าเฉลี่ย)
- **จำนวนสัญญาณ**: 155 ครั้ง
- **P-value**: 0.002889
- **Effect Size**: 0.243
- **ระดับนัยสำคัญ**: Medium

**🔥 #3 ชั่วโมง 19:00** 📉
- **Win Rate**: 35.7% (-11.8% จากค่าเฉลี่ย)
- **จำนวนสัญญาณ**: 244 ครั้ง
- **P-value**: 0.000229
- **Effect Size**: 0.240
- **ระดับนัยสำคัญ**: High

**⚡ #4 ชั่วโมง 17:00** 📉
- **Win Rate**: 36.4% (-11.0% จากค่าเฉลี่ย)
- **จำนวนสัญญาณ**: 184 ครั้ง
- **P-value**: 0.002757
- **Effect Size**: 0.224
- **ระดับนัยสำคัญ**: Medium

**⚡ #5 ชั่วโมง 15:00** 📈
- **Win Rate**: 57.8% (+10.3% จากค่าเฉลี่ย)
- **จำนวนสัญญาณ**: 161 ครั้ง
- **P-value**: 0.008662
- **Effect Size**: 0.207
- **ระดับนัยสำคัญ**: Medium


## 💡 ข้อเสนอแนะที่สามารถนำไปใช้ได้

**🟡 #1 Pattern Cluster**
- **Pattern**: Cluster 2 Pattern
- **Win Rate**: 0.4%
- **ข้อเสนอแนะ**: Avoid
- **ความเสี่ยง**: Low
- **จำนวนข้อมูล**: 232 records


## 🤖 ผลการวิเคราะห์ Machine Learning

**GradientBoosting**
- **Accuracy**: 0.987 ± 0.010
- **Precision**: 0.989
- **Recall**: 0.983
- **F1-Score**: 0.986

**Top Features**:
- win_streak: 0.4085
- price_change_60min: 0.1683
- strategy_encoded: 0.1435
- rolling_win_rate_10: 0.0701
- loss_streak: 0.0628
- action_encoded: 0.0624
- volatility_60min: 0.0245
- volatility_10min: 0.0137
- volatility_30min: 0.0089
- price_change_10min: 0.0086

**RandomForest**
- **Accuracy**: 0.922 ± 0.012
- **Precision**: 0.921
- **Recall**: 0.913
- **F1-Score**: 0.917

**Top Features**:
- win_streak: 0.2272
- loss_streak: 0.1824
- price_change_60min: 0.1422
- strategy_encoded: 0.0951
- rolling_win_rate_10: 0.0816
- action_encoded: 0.0522
- price_change_30min: 0.0429
- volatility_60min: 0.0366
- rolling_win_rate_20: 0.0312
- price_change_10min: 0.0243

**LogisticRegression**
- **Accuracy**: 0.764 ± 0.011
- **Precision**: 0.763
- **Recall**: 0.732
- **F1-Score**: 0.746

**Top Features**:


---

## 📈 สถิติการวิเคราะห์

- **Significant Hour Patterns**: 5
- **Strategy-Time Interactions**: 20
- **Clustering Configurations**: 5
- **ML Models Tested**: 3
- **Actionable Insights**: 1

---

**รายงานนี้สร้างด้วยการวิเคราะห์ทางสถิติ, Machine Learning, และ Pattern Recognition ขั้นสูง**
