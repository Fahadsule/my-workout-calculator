import pandas as pd
import sqlite3 

conn=sqlite3.connect("data/workout.db")
df = pd.read_sql_query("SELECT * FROM training_log", conn)
print(df)
bench_df=pd.read_sql_query("SELECT * FROM training_log WHERE lift='Bench'", conn)
print(bench_df)
current_max_df = df.groupby("lift", as_index=False)["epley_1rm"].max()
squat_df=pd.read_sql_query("SELECT * FROM training_log WHERE lift='Squat'", conn)
print(squat_df)
print(current_max_df)
deadlift_df=pd.read_sql_query("SELECT * FROM training_log WHERE lift='Deadlift'",conn)
print(deadlift_df)