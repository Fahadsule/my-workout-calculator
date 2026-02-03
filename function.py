import pandas as pd
import numpy as np

x = np.arange(0, 600.5, 0.5)
z = list(range(0,13 ))

# Create lists to store data
weights = []
reps = []
one_rm = []

for xs in x:
    for zs in z:
        weights.append(xs)
        reps.append(zs)
        one_rm.append(xs * (1 + (zs / 30)))

# Create DataFrame once
df = pd.DataFrame({
    'weight': weights,
    'reps': reps,
    '1RM': one_rm
})

print(df.shape)  # (20300, 3) = 203 weights × 100 reps
print(df.head())
print(df)