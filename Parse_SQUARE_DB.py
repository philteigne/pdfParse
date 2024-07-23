import pdfplumber
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re

# SUBSTRING IDENTIFIERS
square_DB_ID = "3165 E. Millrock Drive Suite 160"

square_statements = {}

def summary_pull(pull_list):
    opening_date = None
    opening_bal = None
    closing_date = None
    closing_bal = None
    acct_id = None
    stmt_period_key = re.compile(r'.* \d{4} (\d\d?\/\d\d?\/\d{4}) - (\d\d?\/\d\d?\/\d{4}) Page .*')
    stmt_opening_balance_key = re.compile(r'Beginning Balance on \d\d?\/\d\d?\/\d{4} [\d:\sAPM]*(-?\$[\d,.]*)')
    stmt_closing_balance_key = re.compile(r'Ending Balance on \d\d?\/\d\d?\/\d{4} [\d:\sAPM]*(-?\$[\d,.]*)')
    acct_id_key = re.compile(r'\*{13}(\d{4})')

    for item in pull_list:
        # Opening Date and Closing Date
        if stmt_period_key.match(item) is not None:
            stmt_period_match = stmt_period_key.match(item)
            if opening_date is None:
                opening_date = stmt_period_match.group(1)
                opening_date = datetime.strptime(opening_date, '%m/%d/%Y')
                print("Opening Date: ")
                print(opening_date)
            if closing_date is None:
                closing_date = stmt_period_match.group(2)
                closing_date = datetime.strptime(closing_date, '%m/%d/%Y')
                print("Closing Date: ")
                print(closing_date)
        # Opening Balance
        if stmt_opening_balance_key.match(item) is not None:
            stmt_opening_balance_match = stmt_opening_balance_key.match(item)
            opening_bal = stmt_opening_balance_match.group(1)
            opening_bal = opening_bal.replace(',', '')
            opening_bal = opening_bal.replace('$', '')
            opening_bal = float(opening_bal)
            print("Opening Balance: ")
            print(opening_bal)
        # Closing Balance
        if stmt_closing_balance_key.match(item) is not None:
            stmt_closing_balance_match = stmt_closing_balance_key.match(item)
            closing_bal = stmt_closing_balance_match.group(1)
            closing_bal = closing_bal.replace(',', '')
            closing_bal = closing_bal.replace('$', '')
            closing_bal = float(closing_bal)
            print("Closing Balance: ")
            print(closing_bal)
        # Acct ID
        if acct_id_key.match(item) is not None:
            acct_id_match = acct_id_key.match(item)
            acct_id = acct_id_match.group(1)
            if acct_id not in square_statements:
                square_statements[acct_id] = {}
            print("Account ID: ")
            print(acct_id)

        if closing_bal is not None and opening_bal is not None and opening_date is not None and closing_date is not None and acct_id is not None:
            square_statements[acct_id]["closing_bal"] = closing_bal
            square_statements[acct_id]["opening_bal"] = opening_bal
            square_statements[acct_id]["opening_date"] = opening_date
            square_statements[acct_id]["closing_date"] = closing_date
            break

    return acct_id





def square_db_parse(statement):
    with pdfplumber.open(statement) as pdf:
        for count, entry in enumerate(pdf.pages):
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')
            # print(pull_list)

            if "BALANCE INFORMATION" in text:
                acct_id = summary_pull(pull_list)
                print(square_statements[acct_id])

            else:
                # parse through transaction page and pull out relevant information
                transaction_fetch(pull_list, acct_id)


            # repeat closing date entries to match number of transactions
            square_statements[acct_id]["closing_date"] = [square_statements[acct_id]["closing_date"]] * len(square_statements[acct_id]["trans_desc"])

    # return opening_date, opening_bal, closing_date, closing_bal, trans_amt, trans_date, trans_desc, check_count