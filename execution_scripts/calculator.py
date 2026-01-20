import pandas as pd
import sqlite3

conn = sqlite3.connect("data/workout.db")
df = pd.read_sql_query("SELECT * FROM training_log", conn)

def get_training_day():
    VALID_ANSWERS = ["VOLUME", "LIGHT", "INTENSITY"]
    first_entry = None
    
    while first_entry not in VALID_ANSWERS:
        first_entry = input("What day is today? ").upper()
        if first_entry not in VALID_ANSWERS:
            print("INVALID ENTRY")
            print("PLEASE CHOOSE FROM:")
            print("1. LIGHT")
            print("2. VOLUME")
            print("3. INTENSITY")
        else:
            routine_day = first_entry
    return routine_day

# Get current max for each lift
current_max_df = df.groupby("lift", as_index=False)["epley_1rm"].max()

# Apply different formulas based on the lift
# Use .apply() with a lambda function for row-wise operations
def calculate_intensity(row):
    if row["lift"].upper() == "BENCH":  # Assuming 'lift' column contains strings like "Bench"
        return (row["epley_1rm"] * (6/7)) + 2.5
    else:
        return (row["epley_1rm"] * (6/7)) + 5.0

# Apply the calculation
current_max_df["intensity_day_attempt"] = current_max_df.apply(calculate_intensity, axis=1)
current_max_df["volume_day_attempt"] = current_max_df["epley_1rm"] * (6/7) * 0.9
current_max_df["light_day_attempt"] = current_max_df["volume_day_attempt"] * 0.8

def main():
    routine_day = get_training_day()
    
    if routine_day == "LIGHT":
        light_df = current_max_df[["lift", "light_day_attempt"]]
        print("\nToday's Light Day Attempts:")
        print(light_df.to_string(index=False))
        
    elif routine_day == "VOLUME":
        volume_df = current_max_df[["lift", "volume_day_attempt"]]
        print("\nToday's Volume Day Attempts:")
        print(volume_df.to_string(index=False))
        
    elif routine_day == "INTENSITY":
        intensity_df = current_max_df[["lift", "intensity_day_attempt"]]
        print("\nToday's Intensity Day Attempts:")
        print(intensity_df.to_string(index=False))

if __name__ == "__main__":
    main()