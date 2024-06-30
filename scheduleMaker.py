import pandas as pd
import random

class Guard:
    def __init__(self, name, rank):
        self.name = name
        self.rank = rank
        self.shifts = 0

    def add_shift(self):
        self.shifts += 1

    def __str__(self):
        return f"{self.name}: {self.shifts} shifts (Rank: {self.rank})"

# Read the Excel file
def read_excel(file_path):
    return pd.read_excel(file_path, sheet_name='Sheet1', engine='openpyxl')

# Save the updated schedule to an Excel file
def save_excel(df, file_path):
    df.to_excel(file_path, index=False)

# Generate the schedule
def generate_schedule(df):
    morning_shift = '10:30-3:30'
    afternoon_shift = '3:30-8'
    days = df.columns[2:]  # Skip the first two columns which have names and ranks

    # Initialize guards starting from the 4th row (index 3)
    names = df.iloc[3:, 0].tolist()
    ranks = df.iloc[3:, 1].tolist()
    guards = [Guard(name, rank) for name, rank in zip(names, ranks)]

    for day in days:
        morning_shifts = []
        afternoon_shifts = []

        # Add already assigned guards to morning_shifts and afternoon_shifts
        for idx in range(3, len(df)):
            if df.at[idx, day] == morning_shift:
                guard_name = df.at[idx, df.columns[0]]
                guard = next((g for g in guards if g.name == guard_name), None)
                if guard:
                    morning_shifts.append(guard)
            elif df.at[idx, day] == afternoon_shift:
                guard_name = df.at[idx, df.columns[0]]
                guard = next((g for g in guards if g.name == guard_name), None)
                if guard:
                    afternoon_shifts.append(guard)

        # Separate high-priority guards and other guards who are not already assigned to shifts
        high_priority_guards = [guard for guard in guards if guard.rank in [1, 2] and guard not in morning_shifts and guard not in afternoon_shifts]
        other_guards = [guard for guard in guards if guard.rank not in [1, 2] and guard not in morning_shifts and guard not in afternoon_shifts]

        # Shuffle the guards to ensure randomness
        random.shuffle(high_priority_guards)
        random.shuffle(other_guards)

        # Ensure we have enough available guards
        if len(high_priority_guards) + len(other_guards) < (12 - len(morning_shifts) - len(afternoon_shifts)):
            continue

        available_guards = high_priority_guards + other_guards
        random.shuffle(available_guards)

        # Assign guards to morning shift until there are 6 guards
        while len(morning_shifts) < 6 and available_guards:
            guard = available_guards.pop(0)
            for idx in range(3, len(df)):  # Start from the 4th row (index 3)
                if df.at[idx, day] != 'X' and pd.isna(df.at[idx, day]) and guard.name == df.at[idx, df.columns[0]]:
                    df.at[idx, day] = morning_shift
                    guard.add_shift()
                    morning_shifts.append(guard)
                    break

        # Assign guards to afternoon shift until there are 6 guards
        while len(afternoon_shifts) < 6 and available_guards:
            guard = available_guards.pop(0)
            for idx in range(3, len(df)):  # Start from the 4th row (index 3)
                if df.at[idx, day] != 'X' and pd.isna(df.at[idx, day]) and guard.name == df.at[idx, df.columns[0]]:
                    df.at[idx, day] = afternoon_shift
                    guard.add_shift()
                    afternoon_shifts.append(guard)
                    break

        # Fill remaining cells with 'OFF'
        for idx in range(3, len(df)):  # Start from the 4th row (index 3)
            if pd.isna(df.at[idx, day]):
                df.at[idx, day] = 'OFF'

    return df

# Adjust the schedule for specific days
def adjust_schedule(df):
    days_to_adjust = ['Tuesday', 'Wednesday', 'Thursday']
    friday = 'Friday'
    saturday = 'Saturday'
    sunday = 'Sunday'
    morning_shift = '10:30-3:30'
    afternoon_shift = '3:30-8'
    early_morning_shift = '10:15-3:30'
    normal_morning_shift = '10:30-3:30'
    friday_early_morning_shift = '10:15-4'
    friday_normal_morning_shift = '10:30-4'
    friday_afternoon_shift = '4:00-9'
    saturday_early_morning_shift = '10:00-3:30'
    saturday_normal_morning_shift = '10:15-3:30'
    sunday_early_morning_shift = '10:30-3:30'
    sunday_normal_morning_shift = '10:45-3:30'
    additional_shift = '1:00-6:00'

    # Print column names for debugging
    print("Columns in the DataFrame:", df.columns)

    # Adjust Tuesday, Wednesday, and Thursday
    for day in days_to_adjust:
        if day in df.columns:
            morning_shift_count = 0
            for idx in range(3, len(df)):  # Start from the 4th row (index 3)
                if df.at[idx, day] == normal_morning_shift and morning_shift_count < 3:
                    df.at[idx, day] = early_morning_shift
                    morning_shift_count += 1

    # Adjust Friday
    if friday in df.columns:
        morning_shift_count = 0
        for idx in range(3, len(df)):  # Start from the 4th row (index 3)
            if df.at[idx, friday] == normal_morning_shift:
                if morning_shift_count < 3:
                    df.at[idx, friday] = friday_early_morning_shift
                    morning_shift_count += 1
                else:
                    df.at[idx, friday] = friday_normal_morning_shift
            elif df.at[idx, friday] == afternoon_shift:
                df.at[idx, friday] = friday_afternoon_shift

        # Add additional shift if there's an available slot
        for idx in range(3, len(df)):  # Start from the 4th row (index 3)
            if df.at[idx, friday] == 'OFF':
                df.at[idx, friday] = additional_shift
                break

    # Adjust Saturday
    if saturday in df.columns:
        morning_shift_count = 0
        for idx in range(3, len(df)):  # Start from the 4th row (index 3)
            if df.at[idx, saturday] == normal_morning_shift:
                if morning_shift_count < 3:
                    df.at[idx, saturday] = saturday_early_morning_shift
                    morning_shift_count += 1
                else:
                    df.at[idx, saturday] = saturday_normal_morning_shift

        # Add additional shift if there's an available slot
        for idx in range(3, len(df)):  # Start from the 4th row (index 3)
            if df.at[idx, saturday] == 'OFF':
                df.at[idx, saturday] = additional_shift
                break

    # Adjust Sunday
    if sunday in df.columns:
        morning_shift_count = 0
        for idx in range(3, len(df)):  # Start from the 4th row (index 3)
            if df.at[idx, sunday] == normal_morning_shift:
                if morning_shift_count < 3:
                    df.at[idx, sunday] = sunday_early_morning_shift
                    morning_shift_count += 1
                else:
                    df.at[idx, sunday] = sunday_normal_morning_shift

        # Add additional shift if there's an available slot
        for idx in range(3, len(df)):  # Start from the 4th row (index 3)
            if df.at[idx, sunday] == 'OFF':
                df.at[idx, sunday] = additional_shift
                break

    return df

def main():
    input_file = 'schedule.xlsx'
    output_file = 'updated_schedule.xlsx'

    df = read_excel(input_file)
    updated_df = generate_schedule(df)
    adjusted_df = adjust_schedule(updated_df)

    # Drop the 'rank' column from the DataFrame
    adjusted_df.drop(columns=['Rank'], inplace=True)

    save_excel(adjusted_df, output_file)

if __name__ == "__main__":
    main()
