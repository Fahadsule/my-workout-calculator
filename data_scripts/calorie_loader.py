import pandas as pd
import sqlite3

df=pd.read_csv('data/daily.csv')
conn = sqlite3.connect('data/workout.db') 
cursor=conn.cursor()
cursor.execute("SELECT MAX(l_date) FROM daily_tracker")
result = cursor.fetchone()
if result and result[0]:  # Database has data
    latest_date = result[0]
    print(f"📅 Latest date in database: {latest_date}")
    
    # Filter: Only get workouts with date > latest_date in database
    new_entries = df[df['l_date'] > latest_date]
    
    if len(new_entries) > 0:
        print(f"✅ Found {len(new_entries)} NEW workouts after {latest_date}")
        new_entries.to_sql('daily_tracker', conn, if_exists='append', index=False)
        print(f"📊 Added to database. Total entries: {len(pd.read_sql('SELECT * FROM daily_tracker', conn))}")
    else:
        print(f"ℹ️  No new entries found after {latest_date}")
        
else:  # Database is empty (first time)
    print("📭 Database is empty (first import)")
    df.to_sql('daily_tracker', conn, if_exists='replace', index=False)
    print(f"✅ Added {len(df)} entries to database")

conn.close()
 