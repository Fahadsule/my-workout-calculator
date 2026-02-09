import pandas as pd
import requests
import sqlite3
#input data from published google sheets
sheet_url="https://docs.google.com/spreadsheets/d/e/2PACX-1vQ48jbUaNV-Qz-oZv5q8M7RPccVvci-dLN4uW5qiLB9ZDQEG--s1fU_c6FmB1MfVw8ua69BdUQ7ZJRH/pub?output=csv"
df=pd.read_csv(sheet_url, skiprows=1)# formatting and skipping the top unnamed columns
#renaming the columns to my liking, actually it's to fit the database structure🤣🤣
df=df.rename(columns={
    "DATE":"w_date",
    "DAY":"train_day",
    "LIFT":"lift",
    "REPS":"reps",
    "WEIGHT ":"weight",
    "EPLEYS 1RM":"epley_1rm",
    "RPE":"rpe"
})
#dropping the week column
df=df.drop(columns=["WEEK"])
#formatting w_date
df['w_date'] = pd.to_datetime(df['w_date'], format='%A, %b %d, %y').dt.strftime('%Y-%m-%d')
print(df)
conn = sqlite3.connect('data/workout.db') 
#get most recent date
cursor = conn.cursor()
cursor.execute("SELECT MAX(w_date) FROM training_log")
result = cursor.fetchone()
if result and result[0]:  # Database has data
    latest_date = result[0]
    print(f"📅 Latest date in database: {latest_date}")
    
    # Filter: Only get workouts with date > latest_date in database
    new_workouts = df[df['w_date'] > latest_date]
    
    if len(new_workouts) > 0:
        print(f"✅ Found {len(new_workouts)} NEW workouts after {latest_date}")
        new_workouts.to_sql('training_log', conn, if_exists='append', index=False)
        print(f"📊 Added to database. Total workouts: {len(pd.read_sql('SELECT * FROM training_log', conn))}")
    else:
        print(f"ℹ️  No new workouts found after {latest_date}")
        
else:  # Database is empty (first time)
    print("📭 Database is empty (first import)")
    df.to_sql('training_log', conn, if_exists='replace', index=False)
    print(f"✅ Added {len(df)} workouts to database")

conn.close()