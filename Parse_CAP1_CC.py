import pdfplumber
from datetime import datetime
import re

# SUBSTRING IDENTIFIERS
cap1_CC_ID = "Please send us this portion of your statement and only one check (or one money order) payable to Capital One"

# CAP1 CREDIT CARD PARSER
def summary_pull(lst):
    opening_date = None
    opening_bal = None
    closing_date = None
    closing_bal = None
    statement_year = []
    od_cd_key = re.compile(r'(\w+\s*\d+,\s*\d*)(\s*-\s*)(\w*\s*\d+,\s*\d*)(\s*\|\s*\d+\s*days in Billing Cycle)')
    ob_key = re.compile(r'(.*) (-?(CR)?\$.*.\d+)')
    cb_key = re.compile(r'(.*) (-?(CR)?\$.*.\d+)')
    for item in lst:
        # Opening Date and Closing Date
        if "days in Billing Cycle" in item and opening_date is None and closing_date is None:
            print(item)
            od_cd_match = od_cd_key.match(item)
            opening_date = od_cd_match.group(1)
            opening_date = datetime.strptime(opening_date, '%b %d, %Y')
            closing_date = od_cd_match.group(3)
            closing_date = datetime.strptime(closing_date, '%b %d, %Y')
            statement_year.append(opening_date)
            statement_year.append(closing_date)
        # Opening Balance
        if "Previous Balance " in item and opening_bal is None:
            ob_match = ob_key.match(item)
            opening_bal = ob_match.group(2)
            opening_bal = opening_bal.replace("CR", "-")
            # opening_bal_location = opening_bal.find('$')
            # opening_bal = opening_bal[opening_bal_location:]
            opening_bal = opening_bal.replace('$', '')
            opening_bal = opening_bal.replace(',', '')
            opening_bal = float(opening_bal)
            opening_bal = opening_bal * -1
        # Closing Balance
        if "New Balance " in item and "=" in item and closing_bal is None:
            cb_key_location = item.find("New Balance")
            cb_location = item.find('$')
            if cb_location > cb_key_location:
                cb_match = cb_key.match(item)
                closing_bal = cb_match.group(2)
                closing_bal = closing_bal.replace('$', '')
                closing_bal = closing_bal.replace(',', '')
                closing_bal = float(closing_bal)
                closing_bal = closing_bal * -1

    return opening_date, opening_bal, closing_date, closing_bal, statement_year

def transaction_clean(first_line):
    # CLEAN UP REGEX
    payment_key = re.compile(r'(CAPITAL\s+ONE\s+.*)\s*(PYMTAuthDate\s+\d*-.*\s*)')

    txn_clean = []

    if payment_key.match(first_line) is not None:
        payment_match = payment_key.match(first_line)
        line = 'Payment - ' + payment_match.group(1)
        txn_clean.append(line)
    else:
        txn_clean.append(first_line)

    return txn_clean

def transaction_fetch(transaction_page, stmt, stmt_year):
    list1 = []
    list2 = []
    list3 = []
    # list3_clean = []
    # name_list = []
    with pdfplumber.open(stmt) as pdf:
        page_total = len(pdf.pages)
        for count, entry in enumerate(pdf.pages):
            if count + transaction_page > (page_total - 1):
                break
            page = pdf.pages[count + transaction_page]
            text = page.extract_text(x_tolerance=2)
            pull_list = text.split('\n')

            reg_key = re.compile(r'(\w+\s*\d+)\s*(\w+\s*\d+)\s*(.*[^-$\s$])\s*(-?\s?\$.*.\d+)')  # Transaction regex key
            fx_code_key = re.compile(r'([A-Z]{3})\s?')
            interest_key = re.compile(r'(Interest Charge on [a-zA-Z\s\/\']+)(-?\s?\$.*.\d+)')

            # name_key_multi = re.compile(
            #     r'(.*) (\d-\d+) (-?\$.*.\d+)')  # 'WINSTON W MCFARLANE 9-31001 $898.02 $0.00 $898.02'
            # name_key_single = re.compile(
            #     r'(.*) (Closing Date \d+\/\d+\/\d+) (Account Ending \d-\d+)')  # 'WINSTON W MCFARLANE Closing Date 03/25/22 Account Ending 9-31001'

            transaction_section = "Normal"

            fee_key = "Fees "
            int_key = "Interest Charged"  # Removed space after Charged, might need two keys

            for a in pull_list:
                # Find list item that begins transaction
                if a == fee_key:
                    transaction_section = "Fee"
                if a == int_key:
                    transaction_section = "Interest"

                if transaction_section == "Normal" or transaction_section == "Fee":
                    if reg_key.match(a) is not None:
                        re_match = reg_key.match(a)
                        trans_amt = re_match.group(4)
                        trans_amt = trans_amt.replace('$', '')  # format value into float
                        trans_amt = trans_amt.replace(',', '')
                        trans_amt = trans_amt.replace(' ', '')
                        trans_amt = float(trans_amt)
                        trans_amt = trans_amt * -1
                        list1.append(trans_amt)  # append txn amount

                        trans_date = re_match.group(2)
                        trans_date = datetime.strptime(trans_date, '%b %d')
                        if stmt_year[0] == stmt_year[1]:
                            if trans_date. month > stmt_year[1]. month + 1:  # if transaction occurs in before scope
                                trans_date = trans_date.replace(year=stmt_year[1]. year - 1)
                            else:
                                trans_date = trans_date.replace(year=stmt_year[1]. year)
                        else:
                            if stmt_year[0]. month == trans_date. month or stmt_year[0]. month - 1 == trans_date. month:
                                trans_date = trans_date.replace(year=stmt_year[0]. year)
                            elif stmt_year[1]. month == trans_date. month or stmt_year[1]. month + 1 == trans_date. month:
                                trans_date = trans_date.replace(year=stmt_year[1]. year)

                        list2.append(trans_date)  # append date value

                        txn_name = re_match.group(3)
                        txn_name = transaction_clean(txn_name)
                        txn_name = ' '.join(txn_name)
                        fx_check_index = pull_list.index(a) + 2
                        if fx_check_index < len(pull_list):
                            fx_check = fx_code_key.match(pull_list[fx_check_index])
                        if fx_check_index + 1 <= len(pull_list):
                            if fx_check is not None and "Exchange" in pull_list[fx_check_index + 1]:
                                txn_name += " " + pull_list[fx_check_index]
                        if transaction_section == "Fee":
                            txn_name = re.sub("(?i)fee", "", txn_name)
                            txn_name = "Fee - " + txn_name
                        txn_name = " ".join(txn_name.split())
                        list3.append(txn_name)
                elif transaction_section == "Interest":
                    if interest_key.match(a) is not None:
                        re_match = interest_key.match(a)
                        trans_amt = re_match.group(2)
                        trans_amt = trans_amt.replace('$', '')  # format value into float
                        trans_amt = trans_amt.replace(',', '')
                        trans_amt = trans_amt.replace(' ', '')
                        trans_amt = float(trans_amt)
                        trans_amt = trans_amt * -1
                        if trans_amt != 0:
                            list1.append(trans_amt)

                            trans_date = stmt_year[1]
                            list2.append(trans_date)

                            txn_name = re_match.group(1)
                            list3.append(txn_name)

                # if name_key_multi.match(a) is not None:
                #     name_match = name_key_multi.match(a)
                #     if name_match.group(1) not in name_list:
                #         name_list.append(name_match.group(1))
                # if name_key_single.match(a) is not None:
                #     name_match = name_key_single.match(a)
                #     if name_match.group(1) not in name_list:
                #         name_list.append(name_match.group(1))

    # for a in list3:
    #     for b in name_list:
    #         if b in a:
    #             a = a.replace(b + ' ', '')
    #     list3_clean.append(a)

    # For each transaction in list 3 replace value in name_list with ''
    return list1, list2, list3

def transaction_finder(stmt):
    with pdfplumber.open(stmt) as pdf:
        for count, item in enumerate(pdf.pages):
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')
            transaction_page = -1
            if transaction_page == -1:
                for entry in pull_list:
                    if 'Visit capitalone.com  to see detailed transactions.' in entry:
                        transaction_page = count
                        return transaction_page
                        break
        transaction_page = 1
        return transaction_page

def cap1_cc_parse(statement):
    with pdfplumber.open(statement) as pdf:
        page = pdf.pages[0]
        # PULL DATA FROM text AMEX CC
        text = page.extract_text(x_tolerance=2)
        # Convert text to list separated by \n
        pull_list = text.split('\n')
        opening_date, opening_bal, closing_date, closing_bal, statement_year = summary_pull(pull_list)

        # find first transaction page
        transaction_page = transaction_finder(statement)

        # parse through transaction page and pull out relevant information
        trans_amt, trans_date, trans_desc = transaction_fetch(transaction_page, statement, statement_year)

        # repeat closing date entries to match number of transactions
        closing_date = [closing_date] * len(trans_desc)

        statement_object = {'1': {
            'opening_date': [opening_date],
            'opening_bal': [opening_bal],
            'closing_date': closing_date,
            'closing_bal': [closing_bal],
            'txn_desc': trans_desc,
            'txn_date': trans_date,
            'txn_amt': trans_amt,
            'check_count': 0,
        }}

    return statement_object