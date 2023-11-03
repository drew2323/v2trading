

def calculate_relative_profit_loss(entry_price, exit_price):
  """Calculates the relative profit/loss in percents.

  Args:
    entry_price: The entry price.
    exit_price: The exit price.

  Returns:
    The relative profit/loss in percents.
  """

  relative_profit_loss = (exit_price - entry_price) / entry_price * 100
  return relative_profit_loss

