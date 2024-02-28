import pdfplumber
from datetime import datetime
import re

# SUBSTRING IDENTIFIERS
pnc_DB_ID = "For customer service call 1-877-BUS-BNKG"
pnc_DB_ID_2 = "For customer service call 1-888-PNC-BANK"


# PNC CHECKING PARSER
def summary_pull(stmt):
    opening_date = None
    opening_bal = None
    closing_date = None
    closing_bal = None
    amount_summary_check = 0
    stmt_period_key = re.compile(r'(.*[Pp]eriod )(.*\/\d\d\d\d)( to )(.*\/\d\d\d\d)(.*)')
    ob_key = re.compile(r'(.*) (.*) (.*) (.*)')
    with pdfplumber.open(stmt) as pdf:
        for count, entry in enumerate(pdf.pages):
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')
            # print(pull_list)

            for item in pull_list:
                # Opening Date and Closing Date
                if "For the Period " in item or "For the period " in item:
                    if opening_date is None:
                        stmt_period_match = stmt_period_key.match(item)
                        opening_date = stmt_period_match.group(2)
                        opening_date = datetime.strptime(opening_date, '%m/%d/%Y')
                        closing_date = stmt_period_match.group(4)
                        closing_date = datetime.strptime(closing_date, '%m/%d/%Y')
                        print("Opening Date: ")
                        print(opening_date)
                        print("Closing Date: ")
                        print(closing_date)
                # Opening Balance and Closing Balance
                if amount_summary_check == 1:
                    ob_match = ob_key.match(item)
                    opening_bal = ob_match.group(1)
                    opening_bal = opening_bal.replace(',', '')
                    opening_bal = float(opening_bal)
                    closing_bal = ob_match.group(4)
                    closing_bal = closing_bal.replace(',', '')
                    closing_bal = float(closing_bal)
                    amount_summary_check = 0
                    print("Opening Balance: ")
                    print(opening_bal)
                    print("Closing Balance: ")
                    print(closing_bal)
                if "balance other additions deductions balance" in item:
                    amount_summary_check = 1

            if closing_bal is not None:
                if opening_bal is not None:
                    if opening_date is not None:
                        if closing_date is not None:
                            break

    return opening_date, opening_bal, closing_date, closing_bal


def transaction_clean(txn_list, first_line, transaction_section):  # TODO set up custom clean up
    # CLEAN UP REGEX
    fee_section = 0
    if transaction_section == "Fee":
        fee_section = 1

    prefix_keys = [
        "ACH Debit ",
        "ACH Pmt ",
        "ACH Tel Utility ",
        "ACH Web ",
        "ACH Web-Recur ",
        "Corporate ACH ACH Pmt ",
        "Corporate ACH Purchase ",
        "Corporate ACH ",
        "POS Purchase "
    ]

    prefix_01 = re.compile(r'(\d{4} Debit Card Purchase )(.*)')
    prefix_02 = re.compile(fr"({'|'.join(prefix_keys)})(.*)")
    prefix_numbers = re.compile(r'(^\d*$)')
    prefix_03 = re.compile(r'(\d{4} Recurring Debit Card )(.*)')
    prefix_04 = re.compile(r'(DEBIT CARD )(PURCHASE, |PAYMENT, )(AUT \d{6} VISA DDA PUR)')
    prefix_05 = re.compile(r'(ATM Deposit )(.*)')
    prefix_06 = re.compile(r'(ATM Withdrawal )(.*)')
    prefix_07 = re.compile(r'(Deposit|Withdrawal) (\d{9})')
    suffix_01 = re.compile(r'(.* )(\* )([A-Z]{2})')
    suffix_02 = re.compile(r'(^\d{16}$)')
    transfer_key_01 = re.compile(r'(\w*)(\s+)(Transfer) (To|From)(\s+)([A-Za-z]*)?(\s+)?(\d{16}|\d{10}) (.*)')
    payment_key = re.compile(r'(.*) (Payment|PAYMENT) (Received |RECEIVED )?(-) ([a-zA-Z ]+)')
    fee_key = re.compile(r'(.*) (Fee|FEE)')
    check_key = re.compile(r'(^\d+\*?$)')

    section_headers_keys = [
        "ATM Deposits and Additions"
        "ACH Additions",
        "ACH Deductions",
        "ATM/Misc. Debit Card Transactions",
        "Fee Refunds",
        "Other Additions",
        "POS Purchases",
        "Service Charges and Fees"
    ]

    txn_clean = []

    for line in txn_list:
        if len(txn_clean) == 0:  # is empty?
            if payment_key.match(first_line) is not None:
                payment_match = payment_key.match(first_line)
                line = 'Payment - ' + payment_match.group(1)
                txn_clean.append(line)
            elif prefix_01.match(first_line) is not None:
                txn_clean.append(prefix_01.match(first_line).group(2))
            elif prefix_02.match(first_line) is not None:
                only_numbers = prefix_02.match(first_line).group(2)
                if prefix_numbers.match(only_numbers) is not None:
                    txn_clean.append("")
                else:
                    txn_clean.append(prefix_02.match(first_line).group(2))
            elif prefix_03.match(first_line) is not None:
                if first_line not in line:
                    txn_clean.append(line)
                if len(prefix_03.match(first_line).group(2)) > 0:
                    txn_clean.append(prefix_03.match(first_line).group(2))
            elif prefix_04.match(first_line) is not None:
                if first_line not in line:
                    if suffix_01.match(line):
                        txn_clean.append(suffix_01.match(line).group(1) + suffix_01.match(line).group(3))
                    else:
                        txn_clean.append(line)
                continue
            elif prefix_05.match(first_line) is not None:
                if fee_section == 0:
                    txn_clean.append("Deposit - ATM " + prefix_05.match(first_line).group(2))
                else:
                    txn_clean.append("Fee - " + first_line)
            elif prefix_06.match(first_line) is not None:
                if fee_section == 0:
                    txn_clean.append("Withdrawal - ATM " + prefix_06.match(first_line).group(2))
                else:
                    txn_clean.append("Fee - " + first_line)
            elif prefix_07.match(first_line) is not None:
                txn_clean.append(prefix_07.match(first_line).group(1))
            elif transfer_key_01.match(first_line) is not None:
                txn_clean.append("Transfer - " + transfer_key_01.match(first_line).group(4) + " " + transfer_key_01.match(first_line).group(6) + " " + transfer_key_01.match(first_line).group(8) + " " + transfer_key_01.match(first_line).group(9))
            elif check_key.match(first_line) is not None:
                txn_clean.append("Check " + check_key.match(first_line).group(1))
            elif fee_section == 1:
                if fee_key.match(first_line) is not None:
                    fee_match = fee_key.match(first_line)
                    line = 'Fee - ' + fee_match.group(1)
                    txn_clean.append(line)
                else:
                    line = 'Fee - ' + first_line
                    txn_clean.append(line)
            else:
                txn_clean.append(first_line)
        else:
            if suffix_02.match(line):
                continue
            if line in section_headers_keys:
                break
            if "continued on next page" in line:
                break
            else:
                txn_clean.append(line)
    return txn_clean


def transaction_manage(txn_list, transaction_type, multi_year, opening_date, closing_date, transaction_section):
    reg_key = re.compile(r'(\d{2}\/\d{2}) ([0-9,]*\.\d{2}) (.*)')  # Transaction regex key
    reg_key_checks = re.compile(r'(\d{2}\/\d{2}) (\d*)( \*? ?)([0-9\,]+\.\d\d)')

    transaction_year = closing_date.year

    if transaction_section == "Checks":
        re_match = reg_key_checks.match(txn_list[0])
        trans_amt = re_match.group(4)
        txn_name = "Check " + re_match.group(2)
    else:
        re_match = reg_key.match(txn_list[0])
        trans_amt = re_match.group(2)
        txn_name = re_match.group(3)

    trans_amt = trans_amt.replace(',', '')
    trans_amt = float(trans_amt)
    if transaction_type == "Debit":
        trans_amt = trans_amt * -1

    trans_date = re_match.group(1)
    trans_date = datetime.strptime(trans_date, '%m/%d')

    if multi_year == True:
        if trans_date.month >= opening_date.month:
            trans_date = trans_date.replace(year=transaction_year - 1)
        elif trans_date.month <= closing_date.month:
            trans_date = trans_date.replace(year=transaction_year)
    else:
        trans_date = trans_date.replace(year=transaction_year)

    txn_name = transaction_clean(txn_list, txn_name, transaction_section)
    txn_name = ' '.join(txn_name)
    if len(txn_name) > 1:
        if txn_name[0] == " ":
            txn_name = txn_name[1:]

    return trans_amt, trans_date, txn_name


def transaction_fetch(transaction_page, stmt, opening_date, closing_date):
    list1 = []
    list2 = []
    list3 = []
    # list3_clean = []
    # name_list = []

    checks_list1 = []
    checks_list2 = []
    checks_list3 = []

    multi_year = False
    if opening_date.year != closing_date.year:
        multi_year = True

    with pdfplumber.open(stmt) as pdf:
        page_total = len(pdf.pages)

        transaction_section = "Summary"  # Summary, Normal, Fee, or Check
        transaction_type = "Credit"  # Credit or Debit
        current_transaction = []
        check_count = 0

        for count, entry in enumerate(pdf.pages):
            if count + transaction_page > (page_total - 1):
                break
            page = pdf.pages[count + transaction_page]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')

            if len(current_transaction) > 0 and current_transaction[0] != "Date Transaction Reference":
                list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                        transaction_type,
                                                                        multi_year, opening_date,
                                                                        closing_date,
                                                                        transaction_section)
                list1.append(list_item1)
                list2.append(list_item2)
                list3.append(list_item3)

                current_transaction = []

            reg_key = re.compile(r'(\d{2}\/\d{2}) ([0-9,]*\.\d{2}) (.*)')  # Transaction regex key
            reg_key_checks_flag = re.compile(r'\d{2}\/\d{2} \d* \*? ?[0-9\,]+\.\d\d')
            reg_key_checks = r'\d{2}\/\d{2} \d* \*? ?[0-9\,]+\.\d\d'

            debit_section_key = "Checks and Other Deductions"
            debit_section_key_02 = "Other Deductions"

            fee_section_key = "Service Charges and Fees"
            checks_key = re.compile(r'(^Checks and Substitute Checks)')

            for a in pull_list:
                if transaction_section != "Fee":
                    if a == "Date Transaction Reference":
                        transaction_section = "Normal"
                    if a == "Activity Detail" or a == "Debit Card Purchases" or a == debit_section_key_02:
                        transaction_section = "Normal"
                        continue
                if transaction_section == "Summary":
                    continue

                # Find list item that begins transaction
                if a == fee_section_key:
                    if len(current_transaction) > 0:
                        list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                                transaction_type,
                                                                                multi_year, opening_date,
                                                                                closing_date,
                                                                                transaction_section)
                        list1.append(list_item1)
                        list2.append(list_item2)
                        list3.append(list_item3)
                        current_transaction = []

                    transaction_section = "Fee"
                if checks_key.match(a) is not None:
                    transaction_section = "Checks"

                if a == "Detail of Services Used During Current Period":
                    if len(current_transaction) > 0:
                        list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                                transaction_type,
                                                                                multi_year, opening_date,
                                                                                closing_date,
                                                                                transaction_section)
                        list1.append(list_item1)
                        list2.append(list_item2)
                        list3.append(list_item3)
                        current_transaction = []
                        break
                if a == debit_section_key or a == debit_section_key_02 or "Online and Electronic Banking Deductions" in a:
                    if len(current_transaction) > 0:
                        list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                                transaction_type,
                                                                                multi_year, opening_date,
                                                                                closing_date,
                                                                                transaction_section)
                        list1.append(list_item1)
                        list2.append(list_item2)
                        list3.append(list_item3)
                        current_transaction = []
                    transaction_section = "Normal"
                    transaction_type = "Debit"

                if reg_key.match(a) is not None or a == "Date Transaction Reference" or reg_key_checks_flag.match(a) is not None:
                    if transaction_section != "Checks":
                        # if checks_list1 is filled, Checks section has just ended
                        if len(checks_list1) == 0:
                            if len(current_transaction) > 0:
                                re_match = reg_key.match(current_transaction[0])

                                if re_match is None:  # remove instances where fees/interest ends right before page does
                                    current_transaction = []
                                else:
                                    if len(current_transaction) > 0:
                                        list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                                                transaction_type,
                                                                                                multi_year, opening_date,
                                                                                                closing_date,
                                                                                                transaction_section)
                                        list1.append(list_item1)
                                        list2.append(list_item2)
                                        list3.append(list_item3)

                                        current_transaction = []
                            current_transaction.append(a)
                        # Checks section has just ended
                        elif len(checks_list1) > 0:
                            transaction_section = "Checks"
                            checks_list1 += checks_list2
                            checks_list1 += checks_list3
                            check_count += len(checks_list1)
                            for b in checks_list1:
                                list_item1, list_item2, list_item3 = transaction_manage([b], transaction_type, multi_year,
                                                                                        opening_date, closing_date,
                                                                                        transaction_section)
                                list1.append(list_item1)
                                list2.append(list_item2)
                                list3.append(list_item3)

                                checks_list1 = []
                            transaction_section = "Normal"

                    elif transaction_section == "Checks":
                        re_match_list = re.findall(reg_key_checks, a)
                        if len(re_match_list) > 0:
                            if len(re_match_list) > 2:
                                checks_list2.append(re_match_list[1])
                                checks_list3.append(re_match_list[2])
                            elif len(re_match_list) > 1:
                                checks_list2.append(re_match_list[1])
                            checks_list1.append(re_match_list[0])


                elif len(current_transaction) > 0:
                    current_transaction.append(a)

                if fee_section_key in a:
                    transaction_section = "Fee"

    return list1, list2, list3, check_count


def transaction_finder(stmt):
    with pdfplumber.open(stmt) as pdf:
        for count, item in enumerate(pdf.pages):
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')
            # print(pull_list)
            transaction_page = -1
            if transaction_page == -1:
                for entry in pull_list:
                    if entry == 'Activity Detail':
                        transaction_page = count
                        return transaction_page
                        break
        transaction_page = 0
        return transaction_page


def pnc_db_parse(statement):
    with pdfplumber.open(statement) as pdf:
        page = pdf.pages[0]
        # PULL DATA FROM text AMEX CC
        text = page.extract_text(x_tolerance=1)
        # Convert text to list separated by \n
        pull_list = text.split('\n')
        # print(pull_list)

        opening_date, opening_bal, closing_date, closing_bal = summary_pull(statement)

        # find first transaction page
        transaction_page = transaction_finder(statement)

        # parse through transaction page and pull out relevant information
        trans_amt, trans_date, trans_desc, check_count = transaction_fetch(transaction_page, statement, opening_date, closing_date)

        # repeat closing date entries to match number of transactions
        closing_date = [closing_date] * len(trans_desc)

    return opening_date, opening_bal, closing_date, closing_bal, trans_amt, trans_date, trans_desc, check_count