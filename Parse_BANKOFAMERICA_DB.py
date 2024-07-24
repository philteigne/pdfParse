import pdfplumber
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re

# SUBSTRING IDENTIFIERS
bankofamerica_DB_ID = "1.888.BUSINESS (1.888.287.4637)"

def summary_pull(stmt):
    opening_date = None
    opening_bal = None
    closing_date = None
    closing_bal = None

    opening_key = re.compile(r'(Beginning balance on) ([A-Za-z]+ \d+, \d{4}) (\$?[0-9,]+.\d\d)')
    closing_key = re.compile(r'(Ending balance on) ([A-Za-z]+ \d+, \d{4}) (\$?[0-9,]+.\d\d)')

    with pdfplumber.open(stmt) as pdf:
        for count, entry in enumerate(pdf.pages):
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')

            for item in pull_list:
                # Opening Date
                if opening_key.match(item) is not None:
                    if opening_date is None:
                        opening_match = opening_key.match(item)
                        opening_date = opening_match.group(2)
                        opening_date = datetime.strptime(opening_date, '%B %d, %Y')
                        print("Opening Date: ")
                        print(opening_date)
                    if opening_bal is None:
                        opening_match = opening_key.match(item)
                        opening_bal = opening_match.group(3)
                        opening_bal = opening_bal.replace("$", "")
                        opening_bal = opening_bal.replace(",", "")
                        opening_bal = float(opening_bal)
                        print("Opening Balance: ")
                        print(opening_bal)

                # Closing Date
                if closing_key.match(item) is not None:
                    if closing_date is None:
                        closing_match = closing_key.match(item)
                        closing_date = closing_match.group(2)
                        closing_date = datetime.strptime(closing_date, '%B %d, %Y')
                        print("Closing Date: ")
                        print(closing_date)
                    if closing_bal is None:
                        closing_match = closing_key.match(item)
                        closing_bal = closing_match.group(3)
                        closing_bal = closing_bal.replace("$", "")
                        closing_bal = closing_bal.replace(",", "")
                        closing_bal = float(closing_bal)
                        print("Closing Balance: ")
                        print(closing_bal)

            if closing_bal is not None:
                if opening_bal is not None:
                    if opening_date is not None:
                        if closing_date is not None:
                            print("-------------------------------")
                            break

    return opening_date, opening_bal, closing_date, closing_bal

def transaction_manage(txn_list, multi_year, opening_date, closing_date, transaction_section):
    reg_key = re.compile(r'(\d\d\/\d\d\/\d\d) (.*) ([0-9,-]+.\d\d)')  # Transaction regex key
    reg_key_checks = re.compile(r'(\d\d\/\d\d\/\d\d) (\d+) ([0-9,-]+.\d\d)')

    transaction_year = closing_date.year

    txn_clean = []

    print(txn_list)
    if transaction_section == "Transactions":
        for line in txn_list:
            if reg_key.match(line) is not None:
                re_match = reg_key.match(line)
                trans_amt = re_match.group(3)
                trans_date = re_match.group(1)
                txn_clean.append(re_match.group(2))
            else:
                txn_clean.append(line)
        txn_name = (" ").join(txn_clean)

    if transaction_section == "Checks":
        re_match = reg_key_checks.match(txn_list[0])
        trans_amt = re_match.group(3)
        trans_date = re_match.group(1)
        txn_name = "Check " + re_match.group(2)
        txn_name = txn_name.replace("*", "")

    trans_amt = trans_amt.replace(',', '')
    # trans_amt = trans_amt.replace('-', '')
    trans_amt = float(trans_amt)
    # if transaction_type == "Debit":
    #     trans_amt = trans_amt * -1

    trans_date = datetime.strptime(trans_date, '%m/%d/%y')
    if multi_year == True:
        if trans_date.month >= opening_date.month:
            trans_date = trans_date.replace(year=transaction_year - 1)
        elif trans_date.month <= closing_date.month:
            trans_date = trans_date.replace(year=transaction_year)
    else:
        trans_date = trans_date.replace(year=transaction_year)

    # txn_name = transaction_clean(txn_list, txn_name, transaction_section)
    # txn_name = ' '.join(txn_name)

    return trans_amt, trans_date, txn_name

def transaction_fetch(stmt, opening_date, closing_date):
    list1 = []
    list2 = []
    list3 = []
    # list3_clean = []

    checks_list1 = []
    checks_list2 = []


    check_count = 0

    multi_year = False
    if opening_date.year != closing_date.year:
        multi_year = True

    with pdfplumber.open(stmt) as pdf:
        page_total = len(pdf.pages)

        transaction_section = "Summary"  # Summary, Transactions, Fees, Checks
        current_transaction = []
        check_count = 0

        for count, entry in enumerate(pdf.pages):
            if count > (page_total - 1):
                break
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')

            if len(current_transaction) > 0 and current_transaction[0] != "Date Description Amount":
                list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                        multi_year, opening_date,
                                                                        closing_date,
                                                                        transaction_section)
                list1.append(list_item1)
                list2.append(list_item2)
                list3.append(list_item3)

                current_transaction = []

            reg_key = re.compile(r'(\d\d\/\d\d\/\d\d) (.*) ([0-9,-]+.\d\d)')  # Transaction regex key
            # reg_key_checks_flag = re.compile(r'\d+\*? [A-Za-z]{3} \d+ \d* [\d,]+.\d\d-?')
            reg_key_checks = r'\d\d\/\d\d\/\d\d \d+ [0-9,-]+.\d\d'

            # checks_key = re.compile(r'(^Checks and Substitute Checks)')

            transactions_section_key_list = [
                'Deposits and other credits',
                'Withdrawals and other debits'
            ]
            transactions_section_key = re.compile(fr"({'|'.join(transactions_section_key_list)})")
            fees_section_key = re.compile(r'(Service fees)')

            for a in pull_list:
                # print(a)
                if transactions_section_key.match(a) is not None:
                    transaction_section = "Transactions"
                    continue
                if transaction_section == "Summary":
                    continue

                # Determine transactions section of statement
                if "Service fees" in a:
                    transaction_section = "Fees"
                    continue

                # Find list item that begins transaction
                if a == "Daily ledger balances":
                    if len(current_transaction) > 0:
                        list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                                multi_year, opening_date,
                                                                                closing_date,
                                                                                transaction_section)
                        list1.append(list_item1)
                        list2.append(list_item2)
                        list3.append(list_item3)
                        current_transaction = []
                        break
                    if len(checks_list1) > 0:
                        temp_transaction_section = "Checks"
                        checks_list1 += checks_list2
                        check_count += (len(checks_list1))
                        for b in checks_list1:
                            list_item1, list_item2, list_item3 = transaction_manage([b], multi_year,
                                                                                    opening_date, closing_date,
                                                                                    temp_transaction_section)
                            list1.append(list_item1)
                            list2.append(list_item2)
                            list3.append(list_item3)

                            checks_list1 = []

                if transaction_section == "Transactions":
                    if a == "Date Transaction description Amount" and len(current_transaction) > 0:
                        # if current_transaction[0][-1] == "-":
                        #     temp_transaction_section = "Debits"
                        # else:
                        #     temp_transaction_section = "Credits"
                        list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                                multi_year, opening_date,
                                                                                closing_date,
                                                                                temp_transaction_section)
                        list1.append(list_item1)
                        list2.append(list_item2)
                        list3.append(list_item3)

                        current_transaction = []
                        continue
                    if reg_key.match(a) is not None:
                        if len(current_transaction) > 0:
                            re_match = reg_key.match(current_transaction[0])

                            if re_match is None:  # remove instances where fees/interest ends right before page does
                                current_transaction = []
                            else:
                                if len(current_transaction) > 0:
                                    list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                                            multi_year, opening_date,
                                                                                            closing_date,
                                                                                            transaction_section)
                                    list1.append(list_item1)
                                    list2.append(list_item2)
                                    list3.append(list_item3)

                                    current_transaction = []
                        current_transaction.append(a)

                if transaction_section == "Checks":
                    if len(current_transaction) > 0:
                        temp_transaction_section = "Debits"
                        list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                                multi_year, opening_date,
                                                                                closing_date,
                                                                                temp_transaction_section)
                        list1.append(list_item1)
                        list2.append(list_item2)
                        list3.append(list_item3)

                        current_transaction = []
                    re_check_match_list = re.findall(reg_key_checks, a)
                    if len(re_check_match_list) > 0:
                        if len(re_check_match_list) > 1:
                            checks_list2.append(re_check_match_list[1])
                        checks_list1.append(re_check_match_list[0])
                    if len(current_transaction) > 0:
                        temp_transaction_section = "Debits"
                        list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                                multi_year, opening_date,
                                                                                closing_date,
                                                                                temp_transaction_section)
                        list1.append(list_item1)
                        list2.append(list_item2)
                        list3.append(list_item3)

                        current_transaction = []
                    if len(checks_list1) > 0:
                        temp_transaction_section = "Checks"
                        checks_list1 += checks_list2
                        check_count += (len(checks_list1))
                        for b in checks_list1:
                            list_item1, list_item2, list_item3 = transaction_manage([b], multi_year,
                                                                                    opening_date, closing_date,
                                                                                    temp_transaction_section)
                            list1.append(list_item1)
                            list2.append(list_item2)
                            list3.append(list_item3)

                            checks_list1 = []

                elif len(current_transaction) > 0:
                    current_transaction.append(a)

    return list1, list2, list3, check_count

def bankofamerica_db_parse(statement):
    with pdfplumber.open(statement) as pdf:
        page = pdf.pages[0]
        # PULL DATA FROM text AMEX CC
        text = page.extract_text(x_tolerance=1)
        # Convert text to list separated by \n
        pull_list = text.split('\n')

        opening_date, opening_bal, closing_date, closing_bal = summary_pull(statement)

        # parse through transaction page and pull out relevant information
        trans_amt, trans_date, trans_desc, check_count = transaction_fetch(statement, opening_date, closing_date)

        # repeat closing date entries to match number of transactions
        # closing_date = [closing_date] * len(trans_desc)

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

    # return opening_date, opening_bal, closing_date, closing_bal, trans_amt, trans_date, trans_desc, check_count
    return 5