import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Set the Matplotlib backend to 'Agg'
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from fpdf import FPDF, XPos, YPos
from datetime import datetime
from io import BytesIO
import v2realbot.controller.services as cs
from rich import print
def create_trading_report_pdf(id, direct = True, output_file='trading_report.pdf'):
    
    #get runner
    res, set =cs.get_archived_runner_header_byID(id)
    if res != 0:
        return -1, f"no runner {id} found"
    
    print("archrunner")
    print(set)
    
    # Parse JSON data
    data = set.metrics
    profit_data = data["profit"]
    pos_cnt_data = data["pos_cnt"]
    prescr_trades_data = data["prescr_trades"]

    # PDF setup
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=10)

    # Start the first page for plots
    pdf.add_page()

    # Create a combined figure for all plots (adjusting the layout to 3x3)
    fig, axs = plt.subplots(3, 3, figsize=(15, 15))

    # Plot 1: Overall Profit Summary Chart
    sns.barplot(x=['Total Wins', 'Total Losses', 'Net Profit'],
                y=[profit_data["sum_wins"], profit_data["sum_losses"],
                   profit_data["sum_wins"] - profit_data["sum_losses"]],
                ax=axs[0, 0])
    axs[0, 0].set_title('Overall Profit Summary')

    # Plot 2: Profit Distribution by Trade Type
    axs[0, 1].pie([profit_data["long_profit"], profit_data["short_profit"]],
                  labels=['Long Profit', 'Short Profit'], autopct='%1.1f%%')
    axs[0, 1].set_title('Profit Distribution by Trade Type')

    # Plot 3: Cumulative Profit Over Time Line Chart
    exit_times = [datetime.fromtimestamp(trade["exit_time"]) for trade in prescr_trades_data]
    cumulative_profits = [trade["profit_sum"] for trade in prescr_trades_data]
    sns.lineplot(x=exit_times, y=cumulative_profits, ax=axs[0, 2])
    axs[0, 2].set_title('Cumulative Profit Over Time')
    axs[0, 2].tick_params(axis='x', rotation=45)

    # Plot 4: Cumulative Profit Over Time with Max Profit Point
    sns.lineplot(x=exit_times, y=cumulative_profits, label='Cumulative Profit', ax=axs[1, 0])
    max_profit_time = datetime.fromisoformat(profit_data["max_profit_cum_time"])
    max_profit = profit_data["max_profit_cum"]
    axs[1, 0].scatter(max_profit_time, max_profit, color='green', label='Max Profit')
    axs[1, 0].set_title('Cumulative Profit Over Time with Max Profit Point')
    axs[1, 0].tick_params(axis='x', rotation=45)
    axs[1, 0].legend()

    # Plot 5: Trade Counts Bar Chart
    sns.barplot(x=['Long Trades', 'Short Trades'],
                y=[profit_data["long_cnt"], profit_data["short_cnt"]],
                ax=axs[1, 1])
    axs[1, 1].set_title('Trade Counts')

    # Plot 6: Position Size Distribution
    sns.barplot(x=list(pos_cnt_data.keys()), y=list(pos_cnt_data.values()), ax=axs[1, 2])
    axs[1, 2].set_title('Position Size Distribution')

    # Plot 7: Daily Relative Profit Chart
    sns.lineplot(x=range(len(profit_data["daily_rel_profit_list"])), y=profit_data["daily_rel_profit_list"], ax=axs[2, 0])
    axs[2, 0].set_title('Daily Relative Profit')
    axs[2, 0].set_xlabel('Trade Number')
    axs[2, 0].set_ylabel('Relative Profit')

    # Adjust layout, save the combined plot, and add it to the PDF
    # plt.tight_layout()
    # plt.savefig("combined_plot.png", format="png", bbox_inches="tight")
    # plt.close()
    # pdf.image("combined_plot.png", x=10, y=20, w=180)

    plt.tight_layout()
    plot_buffer = BytesIO()
    plt.savefig(plot_buffer, format="png")
    plt.close()
    plot_buffer.seek(0)
    pdf.image(plot_buffer, x=10, y=20, w=180)
    plot_buffer.close()

    # Start a new page for the table and additional information
    pdf.add_page()

    # 8. Individual Trade Details Table
    pdf.set_font("Helvetica", size=8)
    trade_fields = ['id', 'direction', 'entry_time', 'exit_time', 'profit', 'profit_sum', 'rel_profit']
    trades_table_data = [{field: trade[field] for field in trade_fields} for trade in prescr_trades_data]
    trades_table = pd.DataFrame(trades_table_data)
    for row in trades_table.values:
        for cell in row:
            pdf.cell(40, 10, str(cell), border=1)
        pdf.ln()

    # Profit/Loss Ratio and Relative Profit Metrics
    profit_loss_ratio = "N/A" if profit_data["sum_losses"] == 0 else str(profit_data["sum_wins"] / profit_data["sum_losses"])
    relative_profit = profit_data["daily_rel_profit_sum"]
    pdf.cell(0, 10, f"Profit/Loss Ratio: {profit_loss_ratio}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"Total Relative Profit: {relative_profit}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Summary of Key Metrics
    pdf.cell(0, 10, "\nSummary of Key Metrics:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"Total Number of Trades: {profit_data['long_cnt'] + profit_data['short_cnt']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"Total Profit: {profit_data['sum_wins']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 10, f"Total Loss: {profit_data['sum_losses']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    best_trade_profit = max(profit_data["long_wins"], profit_data["short_wins"])
    pdf.cell(0, 10, f"Best Trade Profit: {best_trade_profit}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    worst_trade_profit = min(trade["profit"] for trade in prescr_trades_data)
    pdf.cell(0, 10, f"Worst Trade Profit: {worst_trade_profit}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Save PDF
    pdf.output(output_file)

    if direct is False:
        # Save PDF
        pdf.output(output_file)
    else:
        # Instead of saving to a file, write to a BytesIO buffer
        pdf_buffer = BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)  # Move to the beginning of the BytesIO buffer
        return 0, pdf_buffer

# Example usage:
if __name__ == '__main__':
    id = "c3e31cb5-ddf9-467e-a932-2118f6844355"
    res, val = create_trading_report_pdf(id, True)

    print(res,val)
