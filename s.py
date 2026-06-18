import pandas as pd
import requests
import sqlite3
conn = sqlite3.connect('data/workout.db') 
cursor = conn.cursor()
df = pd.read_sql_query("SELECT * FROM training_log", conn)
df.to_csv('Log.csv')