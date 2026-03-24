import pandas as pd
import sqlite3 
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

conn=sqlite3.connect("data/workout.db")

import matplotlib
matplotlib.use('Agg')  # add this before importing pyplot
import matplotlib.pyplot as plt
import pandas as pd

def plot_progress(workout='*'):
    df = pd.read_sql_query(f"SELECT * FROM training_log WHERE lift='{workout}'", conn)
    df['w_date'] = pd.to_datetime(df['w_date'])  # 👈 add this
    df = df[~df['train_day'].isin(['VOLUME', 'LIGHT'])]
    best = df.groupby('w_date')['epley_1rm'].max().reset_index()
    
    plt.figure(figsize=(10, 4))
    plt.plot(
        best['w_date'],
        best['epley_1rm'],
        color='#e8ff47',
        marker='o',
        markersize=5,
        linestyle='--',
        linewidth=2,
        label='Est. 1RM',
    )
    plt.xticks(rotation=45)  # 👈 stops dates overlapping each other
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{workout}_progress.png", dpi=150)
    plt.close()
    print(f"saved {workout}_progress.png")
    best.to_csv('stuff.csv',index=False)

plot_progress('Bench')