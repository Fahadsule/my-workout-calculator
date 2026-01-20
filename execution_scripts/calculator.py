import pandas as pd
import sqlite3
import itertools

# Load plate combinations from CSV or generate if not exists
try:
    p_df = pd.read_csv("data/plate_combinations.csv")
except FileNotFoundError:
    # Generate plate combinations if CSV doesn't exist
    plates_dict = {'A': 10, 'B': 19.31, 'C': 16.5, 'D': 24.2, 'E': 50}
    all_data = []
    
    for k in range(1, 4):  # 1, 2, or 3 plates
        for combo in itertools.combinations(plates_dict.items(), k):
            plate_names, plate_weights = zip(*combo)
            plate_names = list(plate_names)
            plate_weights = list(plate_weights)
            total_weight = sum(plate_weights)
            
            all_data.append({
                'plate_combination': '+'.join(plate_names),
                'plates': plate_names,
                'weights_kg': plate_weights,
                'total_kg': total_weight,
                'total_x2_kg': total_weight * 2,
                'num_plates': k
            })
    
    p_df = pd.DataFrame(all_data)
    p_df['total_kg'] = p_df['total_kg'].round(2)
    p_df['total_x2_kg'] = p_df['total_x2_kg'].round(2)
    p_df = p_df.sort_values('total_x2_kg').reset_index(drop=True)

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

def calculate_intensity(row):
    if row["lift"].upper() == "BENCH":
        return (row["epley_1rm"] * (6/7)) + 2.5
    else:
        return (row["epley_1rm"] * (6/7)) + 5.0

# Apply the calculation
current_max_df["intensity_day_attempt"] = current_max_df.apply(calculate_intensity, axis=1)
current_max_df["volume_day_attempt"] = current_max_df["epley_1rm"] * (6/7) * 0.9
current_max_df["light_day_attempt"] = current_max_df["volume_day_attempt"] * 0.8

def find_plate_combination(target_weight_kg, exclude_50kg=False):
    """
    Find the best plate combination for a target weight.
    
    Args:
        target_weight_kg: The weight to find plates for (in kg)
        exclude_50kg: If True, exclude combinations with the 50kg plate
    
    Returns:
        Dictionary with the best combination and details
    """
    # Filter plate combinations based on criteria
    filtered_plates = p_df.copy()
    
    if exclude_50kg:
        # Exclude combinations containing plate 'E' (50kg)
        filtered_plates = filtered_plates[~filtered_plates['plate_combination'].str.contains('E')]
    
    if filtered_plates.empty:
        return None
    
    # Calculate difference from target weight (both sides)
    filtered_plates = filtered_plates.copy()
    filtered_plates['difference'] = abs(filtered_plates['total_x2_kg'] - target_weight_kg)
    
    # Find the closest combination
    best_match = filtered_plates.loc[filtered_plates['difference'].idxmin()]
    
    return {
        'target_weight_kg': target_weight_kg,
        'plate_combination': best_match['plate_combination'],
        'plates_per_side': best_match['total_kg'],
        'total_both_sides': best_match['total_x2_kg'],
        'difference': best_match['difference'],
        'num_plates': best_match['num_plates'],
        'weights_per_side': best_match['weights_kg']
    }

def main():
    routine_day = get_training_day()
    
    print(f"\n{'='*60}")
    print(f"TODAY'S {routine_day} DAY - PLATE CALCULATIONS (ALL WEIGHTS IN KG)")
    print(f"{'='*60}")
    
    for _, row in current_max_df.iterrows():
        lift = row["lift"].upper()
        
        # Get target weight based on training day (already in kg)
        if routine_day == "LIGHT":
            target_weight_kg = row["light_day_attempt"]  # Already in kg
        elif routine_day == "VOLUME":
            target_weight_kg = row["volume_day_attempt"]  # Already in kg
        else:  # INTENSITY
            target_weight_kg = row["intensity_day_attempt"]  # Already in kg
        
        # Determine if we should exclude 50kg plates
        # Bench and Squat typically don't use the heaviest plates for safety
        exclude_50kg = (lift in ["BENCH", "SQUAT"])
        
        # Find best plate combination
        plate_info = find_plate_combination(target_weight_kg, exclude_50kg=exclude_50kg)
        
        if plate_info:
            print(f"\n{lift}:")
            print(f"  Target weight: {target_weight_kg:.1f} kg")
            print(f"  Plate combination: {plate_info['plate_combination']}")
            print(f"  Plates per side: {plate_info['plates_per_side']:.1f} kg")
            print(f"    Weights per side: {plate_info['weights_per_side']}")
            print(f"  Total plates (both sides): {plate_info['total_both_sides']:.1f} kg")
            print(f"  Difference from target: {plate_info['difference']:.2f} kg")
            
            if plate_info['difference'] > 2.0:  # If difference > 2kg
                print(f"  ⚠️  Warning: {plate_info['difference']:.1f} kg off target")
                
            # Show alternative if difference is large
            if plate_info['difference'] > 5.0:
                print(f"  Consider adjusting weight to: {plate_info['total_both_sides']:.1f} kg")
        else:
            print(f"\n{lift}:")
            print(f"  Target weight: {target_weight_kg:.1f} kg")
            print(f"  ❌ No suitable plate combination found")
            
            # Try without 50kg restriction if it was applied
            if exclude_50kg:
                print(f"  Trying with all plates...")
                plate_info_all = find_plate_combination(target_weight_kg, exclude_50kg=False)
                if plate_info_all:
                    print(f"  Alternative with 50kg plate: {plate_info_all['plate_combination']}")
                    print(f"  Total: {plate_info_all['total_both_sides']:.1f} kg (diff: {plate_info_all['difference']:.2f} kg)")
    
    # Show available plate combinations summary
    print(f"\n{'='*60}")
    print("AVAILABLE PLATE COMBINATIONS (kg):")
    print(f"Total combinations: {len(p_df)}")
    
    # Always show both sets
    bench_squat_combos = p_df[~p_df['plate_combination'].str.contains('E')]
    print(f"Combinations without 50kg plate (for Bench/Squat): {len(bench_squat_combos)}")
    
    print("\nLightest combinations (without 50kg plate):")
    print(bench_squat_combos[['plate_combination', 'total_x2_kg']].head(5).to_string(index=False))
    
    print("\nHeaviest combinations (without 50kg plate):")
    print(bench_squat_combos[['plate_combination', 'total_x2_kg']].tail(5).to_string(index=False))
    
    print(f"\nAll combinations range: {p_df['total_x2_kg'].min():.1f} to {p_df['total_x2_kg'].max():.1f} kg")
    print(f"Without 50kg plate range: {bench_squat_combos['total_x2_kg'].min():.1f} to {bench_squat_combos['total_x2_kg'].max():.1f} kg")

if __name__ == "__main__":
    main()