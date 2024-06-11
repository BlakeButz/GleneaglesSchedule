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

        # Separate high-priority guards and other guards
        high_priority_guards = [guard for guard in guards if guard.rank in [1, 2] and guard not in morning_shifts and guard not in afternoon_shifts]
        other_guards = [guard for guard in guards if guard.rank not in [1, 2] and guard not in morning_shifts and guard not in afternoon_shifts]

        # Shuffle the guards to ensure randomness
        random.shuffle(high_priority_guards)
        random.shuffle(other_guards)

        # Ensure we have enough available guards
        if len(high_priority_guards) + len(other_guards) < (12 - len(morning_shifts) - len(afternoon_shifts)):
            continue

        # Assign one high-priority guard to each morning and afternoon shift if there are available spots
        for shift_list, shift_label in [(morning_shifts, morning_shift), (afternoon_shifts, afternoon_shift)]:
            if len(shift_list) < 6:
                if high_priority_guards:
                    guard = high_priority_guards.pop(0)
                    for idx in range(3, len(df)):  # Start from the 4th row (index 3)
                        if df.at[idx, day] != 'X' and pd.isna(df.at[idx, day]) and guard.name == df.at[idx, df.columns[0]]:
                            df.at[idx, day] = shift_label
                            guard.add_shift()
                            shift_list.append(guard)
                            break

        # Fill the remaining morning shifts
        available_guards = high_priority_guards + other_guards
        random.shuffle(available_guards)

        for _ in range(6 - len(morning_shifts)):  # Ensure 6 morning shifts
            if available_guards:  # Ensure there are guards available
                guard = available_guards.pop(0)
                for idx in range(3, len(df)):  # Start from the 4th row (index 3)
                    if df.at[idx, day] != 'X' and pd.isna(df.at[idx, day]) and guard.name == df.at[idx, df.columns[0]]:
                        df.at[idx, day] = morning_shift
                        guard.add_shift()
                        morning_shifts.append(guard)
                        break

        # Fill the remaining afternoon shifts
        for _ in range(6 - len(afternoon_shifts)):  # Ensure 6 afternoon shifts
            if available_guards:  # Ensure there are guards available
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

def main():
    input_file = 'schedule.xlsx'
    output_file = 'updated_schedule.xlsx'

    df = read_excel(input_file)
    updated_df = generate_schedule(df)
    save_excel(updated_df, output_file)

if __name__ == "__main__":\
    main()
