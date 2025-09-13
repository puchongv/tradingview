#!/usr/bin/env python3
"""
Database Connection Script for TradingView PostgreSQL
เชื่อมต่อกับฐานข้อมูล PostgreSQL และสำรวจโครงสร้างข้อมูล
"""

import psycopg2
import pandas as pd
from datetime import datetime
import sys

# Database connection configuration
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

class TradingViewDB:
    def __init__(self):
        """Initialize database connection"""
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            print("🔗 Connecting to TradingView PostgreSQL database...")
            self.connection = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor()
            print("✅ Successfully connected to database!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("🔒 Database connection closed")
    
    def test_connection(self):
        """Test database connection"""
        try:
            self.cursor.execute("SELECT version();")
            version = self.cursor.fetchone()
            print(f"📊 PostgreSQL Version: {version[0]}")
            
            self.cursor.execute("SELECT current_database();")
            db_name = self.cursor.fetchone()
            print(f"🗄️ Current Database: {db_name[0]}")
            
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def list_tables(self):
        """List all tables in the database"""
        try:
            query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """
            self.cursor.execute(query)
            tables = self.cursor.fetchall()
            
            print("📋 Available Tables:")
            for table in tables:
                print(f"  - {table[0]}")
            
            return [table[0] for table in tables]
        except Exception as e:
            print(f"❌ Error listing tables: {e}")
            return []
    
    def describe_table(self, table_name):
        """Describe table structure"""
        try:
            query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position;
            """
            self.cursor.execute(query, (table_name,))
            columns = self.cursor.fetchall()
            
            print(f"\n📊 Table Structure: {table_name}")
            print("-" * 60)
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f"DEFAULT {col[3]}" if col[3] else ""
                print(f"  {col[0]:<20} {col[1]:<15} {nullable:<8} {default}")
            
            return columns
        except Exception as e:
            print(f"❌ Error describing table {table_name}: {e}")
            return []
    
    def sample_data(self, table_name, limit=5):
        """Get sample data from table"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT %s;"
            df = pd.read_sql_query(query, self.connection, params=[limit])
            
            print(f"\n📄 Sample Data from {table_name} (first {limit} rows):")
            print("-" * 80)
            print(df.to_string(index=False))
            
            return df
        except Exception as e:
            print(f"❌ Error getting sample data from {table_name}: {e}")
            return None
    
    def count_records(self, table_name):
        """Count total records in table"""
        try:
            query = f"SELECT COUNT(*) FROM {table_name};"
            self.cursor.execute(query)
            count = self.cursor.fetchone()[0]
            print(f"📊 Total records in {table_name}: {count:,}")
            return count
        except Exception as e:
            print(f"❌ Error counting records in {table_name}: {e}")
            return 0
    
    def explore_database(self):
        """Complete database exploration"""
        print("🔍 Starting database exploration...")
        print("=" * 60)
        
        # Test connection
        if not self.test_connection():
            return False
        
        # List all tables
        tables = self.list_tables()
        if not tables:
            print("⚠️ No tables found in database")
            return False
        
        # Explore each table
        for table in tables:
            print("\n" + "=" * 60)
            self.describe_table(table)
            self.count_records(table)
            self.sample_data(table, limit=3)
        
        return True
    
    def find_trading_signals_table(self):
        """Find the main trading signals table"""
        tables = self.list_tables()
        
        # Look for tables with trading-related names
        trading_keywords = ['signal', 'trade', 'trading', 'result', 'data']
        
        for table in tables:
            table_lower = table.lower()
            for keyword in trading_keywords:
                if keyword in table_lower:
                    print(f"🎯 Found potential trading table: {table}")
                    self.describe_table(table)
                    self.count_records(table)
                    self.sample_data(table, limit=5)
                    return table
        
        # If no obvious table found, check the first table
        if tables:
            print(f"🔍 Checking first table: {tables[0]}")
            self.describe_table(tables[0])
            self.count_records(tables[0])
            self.sample_data(tables[0], limit=5)
            return tables[0]
        
        return None

def main():
    """Main function to explore TradingView database"""
    db = TradingViewDB()
    
    try:
        # Connect to database
        if not db.connect():
            sys.exit(1)
        
        # Explore database
        print(f"🚀 TradingView Database Explorer")
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Full exploration
        if db.explore_database():
            print("\n🎉 Database exploration completed successfully!")
        else:
            print("\n❌ Database exploration failed!")
        
        # Try to find main trading signals table
        print("\n" + "=" * 60)
        print("🎯 Looking for main trading signals table...")
        main_table = db.find_trading_signals_table()
        
        if main_table:
            print(f"\n✅ Main trading table identified: {main_table}")
        else:
            print("\n⚠️ Could not identify main trading table")
        
    except KeyboardInterrupt:
        print("\n⏹️ Exploration interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()
