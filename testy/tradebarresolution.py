from datetime import datetime, timedelta

def find_bar_start_time(trade_time, resolution_seconds):
    # Calculate the number of seconds to subtract to align with resolution
    remainder = trade_time.second % resolution_seconds
    seconds_to_subtract = remainder if remainder < resolution_seconds / 2 else resolution_seconds - remainder

    # Subtract the calculated seconds and microseconds from the trade_time
    bar_start_time = trade_time - timedelta(seconds=seconds_to_subtract, microseconds=trade_time.microsecond)

    return bar_start_time

# Example usage:
trade_time = datetime(2023, 9, 13, 10, 30, 30)  # Replace with the actual trade time
resolution_seconds = 54  # Replace with your desired resolution in seconds

bar_start_time = find_bar_start_time(trade_time, resolution_seconds)
print("Trade Time:", trade_time)
print("Bar Start Time:", bar_start_time)