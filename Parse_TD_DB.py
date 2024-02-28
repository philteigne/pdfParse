import pdfplumber
from datetime import datetime
import re

# SUBSTRING IDENTIFIERS
td_DB_ID = "for 24-hour Bank-by-Phone services or connect to www.tdbank.com"


# TD CHECKING PARSER
def summary_pull(lst):
    opening_date = None
    opening_bal = None
    closing_date = None
    closing_bal = None
    stmt_period_key = re.compile(r'(.*) (Statement Period:) (.*)(-)(.*)')
    ob_key = re.compile(r'(Beginning Balance) (-?.*\.\d+) (.*)')
    cb_key = re.compile(r'(Ending Balance) (-?[\d,]*\.\d{2})')
    for item in lst:
        # Opening Date and Closing Date
        if "Statement Period: " in item and opening_date is None:
            stmt_period_match = stmt_period_key.match(item)
            opening_date = stmt_period_match.group(3)
            opening_date = datetime.strptime(opening_date, '%b %d %Y')
            closing_date = stmt_period_match.group(5)
            closing_date = datetime.strptime(closing_date, '%b %d %Y')
        # Opening Balance
        if "Beginning Balance " in item:
            ob_match = ob_key.match(item)
            opening_bal = ob_match.group(2)
            opening_bal = opening_bal.replace(',', '')
            opening_bal = float(opening_bal)
        # Closing Balance
        if "Ending Balance " in item and closing_bal is None:
            cb_match = cb_key.match(item)
            closing_bal = cb_match.group(2)
            closing_bal = closing_bal.replace(',', '')
            print(closing_bal)
            closing_bal = float(closing_bal)

    return opening_date, opening_bal, closing_date, closing_bal


def transaction_clean(txn_list, first_line, fee_section):  # TODO set up custom clean up
    # CLEAN UP REGEX
    prefix_01 = re.compile(r'(CCD|ACH) (DEPOSIT, |DEBIT, )(.*)')
    prefix_02 = re.compile(r'(5CD DEBIT, )(.*)')
    prefix_03 = re.compile(r'(ELECTRONIC PMT-)(WEB, ?|TEL, ?)(.*)')
    prefix_04 = re.compile(r'(DEBIT CARD )(PURCHASE, |PAYMENT, )(AUT \d{6} VISA DDA PUR)')
    prefix_05 = re.compile(r'(DEBIT POS, AUT \d{6} DDA PURCHASE)')
    prefix_06 = re.compile(r'(INTL DEBIT CARD) (PMT,|PUR,) (AUT \d{6} INTL DDA PUR)')
    suffix_01 = re.compile(r'(.* )(\* )([A-Z]{2})')
    suffix_02 = re.compile(r'(^\d{16}$)')
    transfer_key_01 = re.compile(r'(eTransfer)( \w+\, )(\w+) (Xfer)')
    transfer_key_02 = re.compile(r'(Transfer) (to CC \d+|from \w+ \d+)')
    transfer_key_03 = re.compile(r'(Transfer) (to \w+ \d+|from \w+ \d+)')
    payment_key = re.compile(r'(.*) (Payment|PAYMENT) (Received |RECEIVED )?(-) ([a-zA-Z ]+)')
    fee_key = re.compile(r'(.*) (Fee|FEE)')
    fee_key_02 = re.compile(r'(INTL TXN FEE, INTL TXN FEE)')
    check_key = re.compile(r'(^\d+\*?$)')
    atm_key = re.compile(r'(TD ATM DEBIT, AUT \d{6} DDA WITHDRAW)')
    atm_key_02 = re.compile(r'(ATM) (.*) (DEPOSIT), (AUT \d{6}) (ATM) (.*) (DEPOSIT)')

    txn_clean = []

    for line in txn_list:
        if len(txn_clean) == 0:  # is empty?
            if payment_key.match(first_line) is not None:
                payment_match = payment_key.match(first_line)
                line = 'Payment - ' + payment_match.group(1)
                txn_clean.append(line)
            elif prefix_01.match(first_line) is not None:
                txn_clean.append(prefix_01.match(first_line).group(3))
            elif prefix_02.match(first_line) is not None:
                txn_clean.append(prefix_02.match(first_line).group(2))
            elif prefix_03.match(first_line) is not None:
                if first_line not in line:
                    txn_clean.append(line)
                if len(prefix_03.match(first_line).group(3)) > 0:
                    txn_clean.append(prefix_03.match(first_line).group(3))
            elif prefix_04.match(first_line) is not None:
                if first_line not in line:
                    if suffix_01.match(line):
                        txn_clean.append(suffix_01.match(line).group(1) + suffix_01.match(line).group(3))
                    else:
                        txn_clean.append(line)
                continue
            elif prefix_05.match(first_line) is not None:
                txn_clean.append("")
            elif prefix_06.match(first_line) is not None:
                txn_clean.append("")
            elif transfer_key_01.match(first_line) is not None:
                txn_clean.append(transfer_key_01.match(first_line).group(3))
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
            elif fee_key_02.match(first_line) is not None:
                txn_clean.append("Fee - INTL TXN")
            elif atm_key.match(first_line) is not None:
                txn_clean.append("Withdrawal - ATM TD")
            elif atm_key_02.match(first_line) is not None:
                txn_clean.append("Deposit - ATM " + atm_key_02.match(first_line).group(2))
            else:
                txn_clean.append(first_line)
        else:
            if suffix_02.match(line):
                continue
            elif transfer_key_02.match(line):
                txn_clean.insert(0, "Payment - " + transfer_key_02.match(line).group(2))
            elif transfer_key_03.match(line):
                txn_clean.insert(0, "Transfer - " + transfer_key_03.match(line).group(2))
            else:
                txn_clean.append(line)
    return txn_clean


def transaction_manage(txn_list, transaction_type, multi_year, opening_date, closing_date, fee_section_check):
    reg_key = re.compile(r'(\d+/\d+) (.*) (-?.*.\d+)')  # Transaction regex key
    re_match = reg_key.match(txn_list[0])

    transaction_year = closing_date.year

    trans_amt = re_match.group(3)
    trans_amt = trans_amt.replace('$', '')  # format value into float
    trans_amt = trans_amt.replace(',', '')
    trans_amt = float(trans_amt)
    if transaction_type == "Debit":
        trans_amt = trans_amt * -1

    trans_date = re_match.group(1)
    trans_date = trans_date.replace('*', '')
    trans_date = datetime.strptime(trans_date, '%m/%d')
    if multi_year == True:
        if trans_date.month >= opening_date.month:
            trans_date = trans_date.replace(year=transaction_year - 1)
        elif trans_date.month <= closing_date.month:
            trans_date = trans_date.replace(year=transaction_year)
    else:
        trans_date = trans_date.replace(year=transaction_year)

    txn_name = re_match.group(2)
    txn_name = transaction_clean(txn_list, txn_name, fee_section_check)
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
    check_count = 0

    multi_year = False
    if opening_date.year != closing_date.year:
        multi_year = True

    with pdfplumber.open(stmt) as pdf:
        page_total = len(pdf.pages)
        for count, entry in enumerate(pdf.pages):
            if count + transaction_page > (page_total - 1):
                break
            page = pdf.pages[count + transaction_page]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')

            reg_key = re.compile(r'(\d+/\d+) (.*) (-?.*.\d+)')  # Transaction regex key
            reg_key_checks = r'\d+\/\d+ \d+\*? -?[0-9\,]+\.\d\d'
            fx_code_key = re.compile(r'([A-Z]{3})\s?')
            interest_key = re.compile(r'(Interest Charge on [a-zA-Z\s]+)(-?\s?\$.*.\d+)')

            transaction_type = "Credit"  # Credit or Debit
            transaction_section = "Normal"  # Normal, Interest, or Fee

            debit_key = re.compile(r'(Checks Paid|Payments|Electronic Payments|Other Withdrawals|Service Charges)')
            credit_key = re.compile(r'(Deposits|Electronic Deposits|Other Credits)')

            fee_key = "Service Charges"
            checks_key = re.compile(r'(^Checks Paid)')
            normal_key = "Electronic Payments"
            # int_key = "Interest Charged "

            fee_section_check = 0

            current_transaction = []

            for a in pull_list:
                # Define if transaction is a Credit or Debit
                if debit_key.match(a) is not None:
                    transaction_type = "Debit"
                    transaction_section = "Normal"
                if credit_key.match(a) is not None:
                    transaction_type = "Credit"
                    transaction_section = "Normal"
                # Find list item that begins transaction
                if a == fee_key:
                    transaction_section = "Fee"
                if checks_key.match(a) is not None:
                    transaction_section = "Checks"
                if a == normal_key or a[0:9] == "Subtotal:":
                    if transaction_section == "Fee":
                        fee_section_check = 1
                    transaction_section = "Normal"
                if a == "DAILY BALANCE SUMMARY":
                    break

                if reg_key.match(a) is not None or "or connect to www.tdbank.com" in a or fee_key in a or "Subtotal:" in a:
                    if transaction_section != "Checks":
                        # if checks_list1 is filled, Checks section has just ended
                        if len(checks_list1) == 0:
                            # fee_section_check = 0
                            if transaction_section == "Fee":
                                fee_section_check = 1
                            if len(current_transaction) > 0:
                                re_match = reg_key.match(current_transaction[0])

                                if re_match is None:  # remove instances where fees/interest ends right before page does
                                    current_transaction = []
                                else:
                                    list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                                            transaction_type,
                                                                                            multi_year, opening_date,
                                                                                            closing_date,
                                                                                            fee_section_check)
                                    list1.append(list_item1)
                                    list2.append(list_item2)
                                    list3.append(list_item3)

                                    current_transaction = []
                            current_transaction.append(a)
                        # Checks section has just ended
                        elif len(checks_list1) > 0:
                            checks_list1 += checks_list2
                            check_count += len(checks_list1)
                            for b in checks_list1:
                                list_item1, list_item2, list_item3 = transaction_manage([b], transaction_type, multi_year,
                                                                                        opening_date, closing_date,
                                                                                        fee_section_check)
                                list1.append(list_item1)
                                list2.append(list_item2)
                                list3.append(list_item3)

                            checks_list1 = []

                    elif transaction_section == "Checks":
                        re_match_list = re.findall(reg_key_checks, a)
                        if len(re_match_list) > 0:
                            if len(re_match_list) > 1:
                                checks_list2.append(re_match_list[1])
                            checks_list1.append(re_match_list[0])
                    # current_transaction.append(a)

                elif len(current_transaction) > 0:
                    current_transaction.append(a)

                # Find end of fee section
                if fee_key in a:
                    fee_section_check = 0

    # For each transaction in list 3 replace value in name_list with ''
    return list1, list2, list3, check_count


def transaction_finder(stmt):
    with pdfplumber.open(stmt) as pdf:
        for count, item in enumerate(pdf.pages):
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')
            transaction_page = -1
            if transaction_page == -1:
                for entry in pull_list:
                    if 'DAILY ACCOUNT ACTIVITY' in entry:
                        transaction_page = count
                        return transaction_page
                        break
        transaction_page = 1
        return transaction_page


def td_db_parse(statement):
    with pdfplumber.open(statement) as pdf:
        page = pdf.pages[0]
        # PULL DATA FROM text AMEX CC
        text = page.extract_text(x_tolerance=1)
        # Convert text to list separated by \n
        pull_list = text.split('\n')

        opening_date, opening_bal, closing_date, closing_bal = summary_pull(pull_list)
        print(opening_date, closing_date, opening_bal, closing_bal)

        # find first transaction page
        transaction_page = transaction_finder(statement)

        # parse through transaction page and pull out relevant information
        trans_amt, trans_date, trans_desc, check_count = transaction_fetch(transaction_page, statement, opening_date, closing_date)

        # repeat closing date entries to match number of transactions
        closing_date = [closing_date] * len(trans_desc)

    return opening_date, opening_bal, closing_date, closing_bal, trans_amt, trans_date, trans_desc, check_count
