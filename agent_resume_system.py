#!/usr/bin/env python3
"""
Agent Resume System
ระบบที่ให้ agent เครื่องอื่นสามารถ resume งานต่อได้โดยไม่ต้องสอนงานใหม่
"""

import json
import os
from datetime import datetime
import pandas as pd

class AgentResumeSystem:
    def __init__(self):
        """เริ่มต้นระบบ resume"""
        self.analysis_files = [
            'factors_analysis.json',
            'significant_patterns.json',
            'analysis_summary.json',
            'dashboard_config.json'
        ]
        self.data_files = [
            'Result Last 120HR.csv',
            'Result 2568-09-11 22-54-00.csv'
        ]
    
    def check_analysis_status(self):
        """ตรวจสอบสถานะการวิเคราะห์"""
        print("=== CHECKING ANALYSIS STATUS ===")
        
        status = {
            'analysis_complete': True,
            'missing_files': [],
            'data_files': [],
            'analysis_summary': None
        }
        
        # ตรวจสอบไฟล์การวิเคราะห์
        for file in self.analysis_files:
            if os.path.exists(file):
                print(f"✅ {file} - พบ")
            else:
                print(f"❌ {file} - ไม่พบ")
                status['missing_files'].append(file)
                status['analysis_complete'] = False
        
        # ตรวจสอบไฟล์ข้อมูล
        for file in self.data_files:
            if os.path.exists(file):
                print(f"✅ {file} - พบ")
                status['data_files'].append(file)
            else:
                print(f"❌ {file} - ไม่พบ")
        
        # อ่าน analysis summary
        if os.path.exists('analysis_summary.json'):
            with open('analysis_summary.json', 'r', encoding='utf-8') as f:
                status['analysis_summary'] = json.load(f)
        
        return status
    
    def load_analysis_results(self):
        """โหลดผลการวิเคราะห์"""
        print("\n=== LOADING ANALYSIS RESULTS ===")
        
        results = {}
        
        # โหลด factors analysis
        if os.path.exists('factors_analysis.json'):
            with open('factors_analysis.json', 'r', encoding='utf-8') as f:
                results['factors'] = json.load(f)
            print("✅ Factors analysis loaded")
        
        # โหลด significant patterns
        if os.path.exists('significant_patterns.json'):
            with open('significant_patterns.json', 'r', encoding='utf-8') as f:
                results['significant_patterns'] = json.load(f)
            print("✅ Significant patterns loaded")
        
        # โหลด dashboard config
        if os.path.exists('dashboard_config.json'):
            with open('dashboard_config.json', 'r', encoding='utf-8') as f:
                results['dashboard_config'] = json.load(f)
            print("✅ Dashboard config loaded")
        
        return results
    
    def generate_resume_instructions(self):
        """สร้างคำแนะนำสำหรับ agent ใหม่"""
        print("\n=== GENERATING RESUME INSTRUCTIONS ===")
        
        instructions = {
            'project_overview': {
                'title': 'Binary Options Trading Pattern Analysis',
                'goal': 'วิเคราะห์ปัจจัยที่ส่งผลต่อ win rate และสร้าง Metabase Dashboard',
                'data_source': 'CSV files with trading signals',
                'analysis_type': 'Factor Analysis (ไม่ใช่ Performance Metrics)'
            },
            'current_status': {
                'analysis_complete': True,
                'total_records': 2482,
                'date_range': '2025-09-03 ถึง 2025-09-11',
                'strategies': 8,
                'actions': 6,
                'significant_patterns': 0
            },
            'key_findings': {
                'overall_winrate': '48.7%',
                'significant_hours': 2,
                'significant_time_ranges': 19,
                'significant_combinations': 56,
                'trend_changes': 25,
                'volatile_strategies': 5
            },
            'next_steps': [
                'สร้าง Metabase Dashboard ตาม dashboard_config.json',
                'วิเคราะห์ patterns เพิ่มเติมด้วยเกณฑ์ที่ต่ำกว่า',
                'สร้าง visualization สำหรับ significant combinations',
                'วิเคราะห์ trend changes อย่างละเอียด'
            ],
            'important_notes': [
                'ไม่พบ Significant Patterns ที่มีความแตกต่าง ≥70%',
                'ต้องวิเคราะห์เพิ่มเติมหรือลดเกณฑ์การตัดสิน',
                'Focus อยู่ที่ Combination Patterns (56 combinations)',
                'Trend Changes มี 25 changes ที่น่าสนใจ'
            ],
            'files_to_use': {
                'data_files': self.data_files,
                'analysis_files': self.analysis_files,
                'main_script': 'comprehensive_factor_analysis.py'
            }
        }
        
        # บันทึกคำแนะนำ
        with open('agent_resume_instructions.json', 'w', encoding='utf-8') as f:
            json.dump(instructions, f, indent=2, ensure_ascii=False)
        
        print("✅ Resume instructions generated")
        return instructions
    
    def create_metabase_queries(self):
        """สร้าง SQL queries สำหรับ Metabase"""
        print("\n=== CREATING METABASE QUERIES ===")
        
        queries = {
            'time_patterns': """
                SELECT 
                    EXTRACT(HOUR FROM entry_time) as hour,
                    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
                    COUNT(*) as total_trades
                FROM trading_data
                GROUP BY EXTRACT(HOUR FROM entry_time)
                HAVING COUNT(*) >= 10
                ORDER BY hour
            """,
            'strategy_performance': """
                SELECT 
                    strategy,
                    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
                    COUNT(*) as total_trades,
                    STDDEV(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as std_dev
                FROM trading_data
                GROUP BY strategy
                ORDER BY win_rate DESC
            """,
            'action_performance': """
                SELECT 
                    action,
                    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
                    COUNT(*) as total_trades
                FROM trading_data
                GROUP BY action
                ORDER BY win_rate DESC
            """,
            'combination_patterns': """
                SELECT 
                    strategy,
                    action,
                    EXTRACT(HOUR FROM entry_time) as hour,
                    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
                    COUNT(*) as total_trades
                FROM trading_data
                GROUP BY strategy, action, EXTRACT(HOUR FROM entry_time)
                HAVING COUNT(*) >= 3
                ORDER BY win_rate DESC
            """,
            'trend_changes': """
                SELECT 
                    strategy,
                    DATE_TRUNC('6 hours', entry_time) as time_window,
                    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
                    COUNT(*) as total_trades
                FROM trading_data
                GROUP BY strategy, DATE_TRUNC('6 hours', entry_time)
                HAVING COUNT(*) >= 5
                ORDER BY strategy, time_window
            """,
            'volatility_analysis': """
                SELECT 
                    CASE 
                        WHEN ABS((price_60min - entry_price) / entry_price * 100) < 1 THEN 'Low'
                        WHEN ABS((price_60min - entry_price) / entry_price * 100) < 3 THEN 'Medium'
                        ELSE 'High'
                    END as volatility_level,
                    AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate,
                    COUNT(*) as total_trades
                FROM trading_data
                GROUP BY volatility_level
                ORDER BY win_rate DESC
            """
        }
        
        # บันทึก queries
        with open('metabase_queries.sql', 'w', encoding='utf-8') as f:
            for name, query in queries.items():
                f.write(f"-- {name.upper()}\n")
                f.write(query)
                f.write("\n\n")
        
        print("✅ Metabase queries created")
        return queries
    
    def create_dashboard_guide(self):
        """สร้างคู่มือ Dashboard"""
        print("\n=== CREATING DASHBOARD GUIDE ===")
        
        guide = {
            'dashboard_setup': {
                'title': 'Binary Options Trading Pattern Dashboard',
                'description': 'Dashboard สำหรับวิเคราะห์ patterns ของ trading signals',
                'data_source': 'PostgreSQL database with trading_data table'
            },
            'charts': [
                {
                    'name': 'Win Rate by Hour',
                    'type': 'Heatmap',
                    'description': 'แสดง win rate ตามชั่วโมง',
                    'sql_query': 'time_patterns',
                    'x_axis': 'hour',
                    'y_axis': 'win_rate',
                    'color_scale': 'RdYlGn'
                },
                {
                    'name': 'Strategy Performance',
                    'type': 'Bar Chart',
                    'description': 'แสดง win rate ตาม strategy',
                    'sql_query': 'strategy_performance',
                    'x_axis': 'strategy',
                    'y_axis': 'win_rate'
                },
                {
                    'name': 'Action Performance',
                    'type': 'Bar Chart',
                    'description': 'แสดง win rate ตาม action',
                    'sql_query': 'action_performance',
                    'x_axis': 'action',
                    'y_axis': 'win_rate'
                },
                {
                    'name': 'Combination Patterns',
                    'type': 'Heatmap',
                    'description': 'แสดง win rate ตามการรวมกันของ strategy, action และเวลา',
                    'sql_query': 'combination_patterns',
                    'x_axis': 'strategy',
                    'y_axis': 'action',
                    'color_scale': 'RdYlGn'
                },
                {
                    'name': 'Trend Changes',
                    'type': 'Line Chart',
                    'description': 'แสดงการเปลี่ยนแปลงของ win rate ตามเวลา',
                    'sql_query': 'trend_changes',
                    'x_axis': 'time_window',
                    'y_axis': 'win_rate'
                },
                {
                    'name': 'Volatility Analysis',
                    'type': 'Bar Chart',
                    'description': 'แสดง win rate ตาม volatility level',
                    'sql_query': 'volatility_analysis',
                    'x_axis': 'volatility_level',
                    'y_axis': 'win_rate'
                }
            ],
            'setup_instructions': [
                '1. สร้าง PostgreSQL database และ import ข้อมูลจาก CSV files',
                '2. สร้าง table trading_data ด้วย schema ที่เหมาะสม',
                '3. สร้าง Metabase dashboard ใหม่',
                '4. เพิ่ม charts ตาม configuration ที่ให้มา',
                '5. ตั้งค่า filters และ parameters ตามต้องการ'
            ],
            'important_notes': [
                'Focus อยู่ที่ Combination Patterns (56 combinations)',
                'Trend Changes มี 25 changes ที่น่าสนใจ',
                'ไม่พบ Significant Patterns ที่มีความแตกต่าง ≥70%',
                'ต้องวิเคราะห์เพิ่มเติมหรือลดเกณฑ์การตัดสิน'
            ]
        }
        
        # บันทึกคู่มือ
        with open('dashboard_guide.json', 'w', encoding='utf-8') as f:
            json.dump(guide, f, indent=2, ensure_ascii=False)
        
        print("✅ Dashboard guide created")
        return guide
    
    def run_resume_system(self):
        """รันระบบ resume ทั้งหมด"""
        print("=== AGENT RESUME SYSTEM ===")
        print("ระบบที่ให้ agent เครื่องอื่นสามารถ resume งานต่อได้")
        print("="*60)
        
        # ตรวจสอบสถานะ
        status = self.check_analysis_status()
        
        # โหลดผลการวิเคราะห์
        results = self.load_analysis_results()
        
        # สร้างคำแนะนำ
        instructions = self.generate_resume_instructions()
        
        # สร้าง SQL queries
        queries = self.create_metabase_queries()
        
        # สร้างคู่มือ Dashboard
        guide = self.create_dashboard_guide()
        
        print("\n=== RESUME SYSTEM COMPLETE ===")
        print("ไฟล์ที่สร้างขึ้น:")
        print("- agent_resume_instructions.json")
        print("- metabase_queries.sql")
        print("- dashboard_guide.json")
        print("\nAgent เครื่องอื่นสามารถใช้ไฟล์เหล่านี้เพื่อ resume งานต่อได้")
        
        return {
            'status': status,
            'results': results,
            'instructions': instructions,
            'queries': queries,
            'guide': guide
        }

if __name__ == "__main__":
    # เริ่มต้นระบบ resume
    resume_system = AgentResumeSystem()
    
    # รันระบบ resume
    resume_results = resume_system.run_resume_system()
