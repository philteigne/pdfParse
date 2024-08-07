import pdfplumber
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re

# SUBSTRING IDENTIFIERS
square_DB_ID = "3165 E. Millrock Drive Suite 160"

def summary_pull(pull_list, square_statements):
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
                square_statements[acct_id]['acct_id'] = acct_id
            print("Account ID: ")
            print(acct_id)

        if closing_bal is not None and opening_bal is not None and opening_date is not None and closing_date is not None and acct_id is not None:
            square_statements[acct_id]["closing_bal"] = [closing_bal]
            square_statements[acct_id]["opening_bal"] = [opening_bal]
            square_statements[acct_id]["opening_date"] = [opening_date]
            square_statements[acct_id]["closing_date"] = [closing_date]
            square_statements[acct_id]["txn_desc"] = []
            square_statements[acct_id]["txn_date"] = []
            square_statements[acct_id]["txn_amt"] = []
            break

    return acct_id


def transaction_fetch(pull_list, acct_id, square_statements):
    pull_list.append("--END OF PAGE--")

    txn_start_key = re.compile(r'(\d\d?\/\d\d?\/\d{4}) (.+?)( --)? (\(?\$[0-9,\.]*\)?)( --)? (\(?\$[0-9,\.]*\)?)')
    txn_time_key = re.compile(r'\d\d?:\d\d? [AP]M ?(.*)?')

    current_txn = None
    current_date = None
    current_amt = None

    for item in pull_list:
        if "Beginning Balance" in item:
            continue

        # Found start of transaction
        if txn_start_key.match(item) is not None or "--END OF PAGE--" in item or "Ending Balance" in item or "No activity this month" in item:
            if current_txn is not None:
                square_statements[acct_id]["txn_desc"].append(current_txn)
                square_statements[acct_id]["txn_date"].append(current_date)
                square_statements[acct_id]["txn_amt"].append(current_amt)

            if "--END OF PAGE--" in item or 'Ending Balance' in item or "No activity this month" in item:
                return

            txn_match = txn_start_key.match(item)

            current_txn = txn_match.group(2)
            current_date = datetime.strptime(txn_match.group(1), '%m/%d/%Y')
            current_amt = txn_match.group(4)
            current_amt = current_amt.replace("$", "")
            current_amt = current_amt.replace(",", "")
            current_amt = current_amt.replace("(", "-")
            current_amt = current_amt.replace(")", "")
            current_amt = float(current_amt)

        # Transaction has started and continuation is found
        elif current_txn is not None:
            if txn_time_key.match(item) is not None:
                txn_match = txn_time_key.match(item)
                current_txn = current_txn + " " + txn_match.group(1)
            else:
                current_txn = current_txn + " " + item

def transaction_combine(txn_desc, txn_date, txn_amt):
    curr_desc = None
    curr_date = None
    curr_amt = 0

    comb_desc = []
    comb_date = []
    comb_amt = []

    for i in range(len(txn_desc)):
        if txn_date[i] != curr_date:
            # Date has changed, write stored values
            if curr_desc is not None and curr_amt != 0:
                comb_desc.append(curr_desc + " | Daily Total")
                comb_date.append(curr_date)
                comb_amt.append(curr_amt)
                curr_amt = 0
            # If desired description, record new values
            if "Automated savings" in txn_desc[i]:
                curr_desc = txn_desc[i]
                curr_date = txn_date[i]
                curr_amt += txn_amt[i]
                continue

        # If target description, add transaction value to sum
        if "Automated savings" in txn_desc[i]:
            curr_amt += txn_amt[i]
        # If non-target description, record transaction
        else:
            comb_desc.append(txn_desc[i])
            comb_date.append(txn_date[i])
            comb_amt.append(txn_amt[i])

    if curr_amt != 0:
        # There are leftover transactions, write them
        comb_desc.append(curr_desc + " | Daily Total")
        comb_date.append(curr_date)
        comb_amt.append(curr_amt)
        curr_amt = 0

    return comb_desc, comb_date, comb_amt


def square_db_parse(statement):
    square_statements = {}
    with pdfplumber.open(statement) as pdf:
        for count, entry in enumerate(pdf.pages):
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')
            # print(pull_list)

            if "BALANCE INFORMATION" in text:
                acct_id = summary_pull(pull_list, square_statements)

            else:
                # parse through transaction page and pull out relevant information
                transaction_fetch(pull_list, acct_id, square_statements)

        # extend closing dates
        for key in square_statements:
            square_statements[key]["txn_desc"], square_statements[key]["txn_date"], square_statements[key]["txn_amt"] = transaction_combine(square_statements[key]["txn_desc"], square_statements[key]["txn_date"], square_statements[key]["txn_amt"])
            square_statements[key]["closing_date"] = square_statements[key]["closing_date"] * len(square_statements[key]["txn_desc"])
            # also add in check count
            square_statements[key]["check_count"] = 0

    return square_statements
