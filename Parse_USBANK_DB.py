import pdfplumber
from datetime import datetime
import re

# SUBSTRING IDENTIFIERS
usbank_DB_ID = "U.S. Bank accepts Relay Calls"
usbank_DB_ID_2 = "Banking at 800-USBANKS (872-2657). We accept relay calls."
usbank_DB_ID_3 = "U.S. Bank 24-hour Banking at 800-673-3555. We accept relay calls."


def summary_pull(stmt):
    opening_date = None
    opening_bal = None
    closing_date = None
    closing_bal = None

    opening_date_key = re.compile(r'([A-Za-z]{3}) (\d+), (\d{4})')
    closing_date_key = re.compile(r'([10]+) (\w ?\w ?\w )(\d ?\d? ?, )(\d ?\d ?\d ?\d)')
    closing_date_key_02 = re.compile(r'([A-Za-z]{3}) (\d+), (\d{4})')
    ob_key = re.compile(r'(Beginning Balance on \w{3} \d+ \$) ([0-9,]+.\d\d ?-?)')
    cb_key = re.compile(r'(Ending Balance on .* \$) ([0-9,]+.\d\d ?-?)')

    with pdfplumber.open(stmt) as pdf:
        for count, entry in enumerate(pdf.pages):
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')

            print(text)
            for item in pull_list:
                # Opening Date
                if opening_date_key.match(item) is not None:
                    if opening_date is None:
                        opening_date_match = opening_date_key.match(item)
                        opening_date = opening_date_match.group()
                        opening_date = datetime.strptime(opening_date, '%b %d, %Y')
                        print("Opening Date: ")
                        print(opening_date)
                        continue

                # Closing Date
                if closing_date_key.match(item) is not None:
                    if closing_date is None:
                        closing_date_match = closing_date_key.match(item)
                        closing_date_month = closing_date_match.group(2)
                        closing_date_month = closing_date_month.replace(" ", "")
                        closing_date_day = closing_date_match.group(3)
                        closing_date_day = closing_date_day.replace(" ", "")
                        closing_date_year = closing_date_match.group(4)
                        closing_date_year = closing_date_year.replace(" ", "")
                        closing_date = closing_date_month + " " + closing_date_day + " " + closing_date_year
                        closing_date = datetime.strptime(closing_date, '%b %d, %Y')
                        print("Closing Date: ")
                        print(closing_date)

                # Backup Closing Date Catch
                if opening_date is not None and closing_date is None:
                    if closing_date_key_02.match(item) is not None:
                        closing_date_match = closing_date_key_02.match(item)
                        closing_date = closing_date_match.group()
                        closing_date = datetime.strptime(closing_date, '%b %d, %Y')
                        print("Closing Date: ")
                        print(closing_date)

                # Opening Balance
                if ob_key.match(item) is not None:
                    ob_match = ob_key.match(item)
                    opening_bal = ob_match.group(2)
                    opening_bal = opening_bal.replace(',', '')
                    if opening_bal[-1] == "-":
                        opening_bal = opening_bal[:-1]
                        opening_bal = float(opening_bal) * -1
                    else:
                        opening_bal = float(opening_bal)
                    amount_summary_check = 0
                    print("Opening Balance: ")
                    print(opening_bal)

                # Closing Balance
                if cb_key.match(item) is not None:
                    cb_match = cb_key.match(item)
                    closing_bal = cb_match.group(2)
                    closing_bal = closing_bal.replace(',', '')
                    if closing_bal[-1] == "-":
                        closing_bal = closing_bal[:-1]
                        closing_bal = float(closing_bal) * -1
                    else:
                        closing_bal = float(closing_bal)
                    amount_summary_check = 0
                    print("Closing Balance: ")
                    print(closing_bal)

            if closing_bal is not None:
                if opening_bal is not None:
                    if opening_date is not None:
                        if closing_date is not None:
                            break

    return opening_date, opening_bal, closing_date, closing_bal


def transaction_clean(txn_list, transaction_section):

    txn_clean = []
    txn_reverse_order = ""

    section_totals_identifiers = [
        "Card xxxx-xxxx-xxxx-\d{4} Deposit Subtotal",
        "Card \d{4} Withdrawals Subtotal",
        "Deposit Subtotal",
        "Total Deposits / Credits",
        "Total Other Deposits",
        "Total Other Withdrawals",
    ]

    deposit_identifiers = [
        "Image Cash Letter",
        "Mobile Check"
    ]

    withdrawal_identifiers = [
        "Customer"
    ]

    payment_identifiers = [
        "Internet",
        "Mobile"
    ]

    misc_prefix_identifiers = [
        "Debit Purchase - VISA",
        "Debit Purchase Ret - VISA",
        "Recurring Debit Purchase"
    ]

    fee_identifiers = [
        "Extended Overdraft",
        "Overdraft Paid",
        "Overdraft Returned"
    ]

    section_totals_key = re.compile(fr"({'|'.join(section_totals_identifiers)}) (.*)")
    deposit_key = re.compile(fr"({'|'.join(deposit_identifiers)}) (Deposit) (.*)")
    withdrawal_key = re.compile(fr"({'|'.join(withdrawal_identifiers)}) (Withdrawal) (.*)")
    payment_key = re.compile(fr"({'|'.join(payment_identifiers)}) (Banking Payment) (To Credit) (.*)")
    prefix_01 = re.compile(r'(Electronic) (Withdrawal|Deposit|Settlement) (To|From) (.*)')
    prefix_02 = re.compile(fr"({'|'.join(misc_prefix_identifiers)}) (On \d{{6}}) (.*)")
    prefix_03 = re.compile(r'(Debit Purchase|Ext TFR Withdrawal) (.*)')
    prefix_04 = re.compile(r'(ATM) (Deposit|Withdrawal) (.*)')
    cleanup_01 = re.compile(r'(REF=[0-9A-Z]{18}) (.*)')
    cleanup_02 = re.compile(r'(REF=[0-9A-Z]{20}) (.*)')
    cleanup_03 = re.compile(r'(.*)? (REF # \d{10,30})')
    fee_01 = re.compile(r'(.*)?(Service Charge)')
    fee_02 = re.compile(r'(Fee) (ATM Withdrawal|ATM Deposit) ?(.*)?')
    fee_03 = re.compile(fr"({'|'.join(fee_identifiers)}) (Fee) ?(.*)?")
    fee_04 = re.compile(r'(ATM) (Fee) (Balance Inquiry .*)')
    fee_05 = re.compile(r'(Quicken/QuickBooks Access Monthly Service) (Fee)')
    transfer_01 = re.compile(r'(\w+) (Banking Transfer|Account Transfer) (To|From) (Account \d{12})')

    txn_list[0] = txn_list[0].replace(" $", "")

    for line in txn_list:
        line = line.replace("**", "")
        if section_totals_key.match(line) is not None:
            break
        elif deposit_key.match(line) is not None:
            match = deposit_key.match(line)
            txn_clean.append("Deposit - " + match.group(1) + " " + match.group(3))
        elif withdrawal_key.match(line) is not None:
            match = withdrawal_key.match(line)
            txn_clean.append("Withdrawal - " + match.group(1) + " " + match.group(3))
        elif payment_key.match(line) is not None:
            match = payment_key.match(line)
            txn_clean.append("Payment - " + match.group(3) + " " + match.group(4) + " " + match.group(1))
        elif prefix_01.match(line) is not None:
            match = prefix_01.match(line)
            txn_clean.append(match.group(4))
        elif prefix_02.match(line) is not None:
            match = prefix_02.match(line)
            txn_reverse_order = match.group(3)
        elif prefix_03.match(line) is not None:
            match = prefix_03.match(line)
            txn_clean.append(match.group(2))
        elif prefix_04.match(line) is not None:
            match = prefix_04.match(line)
            txn_clean.append(match.group(2) + " - " + match.group(1) + " " + match.group(3))
        elif transfer_01.match(line) is not None:
            match = transfer_01.match(line)
            txn_clean.append("Transfer - " + match.group(3) + " " + match.group(4) + " " + match.group(1))
        elif cleanup_01.match(line) is not None:
            match = cleanup_01.match(line)
            txn_clean.append(match.group(2))
        elif cleanup_02.match(line) is not None:
            match = cleanup_02.match(line)
            txn_clean.append(match.group(2))
        elif cleanup_03.match(line):
            match = cleanup_03.match(line)
            txn_clean.append(match.group(1))
        elif fee_01.match(line) is not None:
            txn_clean.append("Fee - " + line)
        elif fee_02.match(line) is not None:
            match = fee_02.match(line)
            txn_clean.append("Fee - " + match.group(2) + " " + match.group(3))
        elif fee_03.match(line) is not None:
            match = fee_03.match(line)
            txn_clean.append("Fee - " + match.group(1) + " " + match.group(3))
        elif fee_04.match(line) is not None:
            match = fee_04.match(line)
            txn_clean.append("Fee - " + match.group(1) + " " + match.group(3))
        elif fee_05.match(line) is not None:
            match = fee_05.match(line)
            txn_clean.append("Fee - " + match.group(1))
        else:
            txn_clean.append(line)

    if txn_reverse_order != "":
        txn_clean.append(txn_reverse_order)

    return txn_clean

def transaction_manage(txn_list, multi_year, opening_date, closing_date, transaction_section):
    reg_key_deposits = re.compile(r'([A-Za-z]{3} \d+) (\d*) ([\d,]+.\d\d-?)')
    reg_key = re.compile(r'([A-Za-z]{3} \d+) (.*) (\$? ?[\d,]+\.\d\d-?)')  # Transaction regex key
    reg_key_checks = re.compile(r'(\d+\*?) ([A-Za-z]{3} \d+) (\d*) ([\d,]+.\d\d-?)')
    reg_key_checks_elec = re.compile(r'(\d+) ([A-Za-z]{3} \d\d?) ([\d,]+.\d\d) (.*)')

    transaction_year = closing_date.year

    transaction_type = "Credit"
    transaction_section_debits = ["Debits", "Checks_con", "Checks_elec"]

    if transaction_section in transaction_section_debits:
        transaction_type = "Debit"

    txn_clean = []

    if transaction_section == "Deposits":
        re_match = reg_key_deposits.match(txn_list[0])
        trans_amt = re_match.group(3)
        trans_date = re_match.group(1)
        txn_name = "Deposit"

    if transaction_section == "Debits" or transaction_section == "Credits":
        for line in txn_list:
            if reg_key.match(line) is not None:
                re_match = reg_key.match(line)
                trans_amt = re_match.group(3)
                trans_date = re_match.group(1)
                txn_clean.append(re_match.group(2))
            else:
                txn_clean.append(line)
        txn_name = transaction_clean(txn_clean, transaction_section)
        txn_name = ' '.join(txn_name)

    if transaction_section == "Checks_con":
        re_match = reg_key_checks.match(txn_list[0])
        trans_amt = re_match.group(4)
        trans_date = re_match.group(2)
        txn_name = "Check " + re_match.group(1)
        txn_name = txn_name.replace("*", "")

    if transaction_section == "Checks_elec":
        re_match = reg_key_checks_elec.match(txn_list)
        trans_amt = re_match.group(3)
        trans_date = re_match.group(2)
        txn_name = re_match.group(4) + " | " + re_match.group(1)

    trans_amt = trans_amt.replace(',', '')
    trans_amt = trans_amt.replace('-', '')
    trans_amt = float(trans_amt)
    if transaction_type == "Debit":
        trans_amt = trans_amt * -1

    trans_date = datetime.strptime(trans_date, '%b %d')

    if multi_year == True:
        if trans_date.month >= opening_date.month:
            trans_date = trans_date.replace(year=transaction_year - 1)
        elif trans_date.month <= closing_date.month:
            trans_date = trans_date.replace(year=transaction_year)
    else:
        trans_date = trans_date.replace(year=transaction_year)

    return trans_amt, trans_date, txn_name

def transaction_fetch(stmt, opening_date, closing_date):
    list1 = []
    list2 = []
    list3 = []
    # list3_clean = []

    deposits_list1 = []
    deposits_list2 = []

    checks_list1 = []
    checks_list2 = []

    check_count = 0

    multi_year = False
    if opening_date.year != closing_date.year:
        multi_year = True

    with pdfplumber.open(stmt) as pdf:
        page_total = len(pdf.pages)

        transaction_section = "Summary"  # Summary, Deposits, Credits, Debits, Checks_con, or Checks_elec
        current_transaction = []
        check_count = 0

        for count, entry in enumerate(pdf.pages):
            if count > (page_total - 1):
                break
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')

            if len(current_transaction) > 0 and current_transaction[0] != "Date Description of Transaction Ref Number Amount":
                list_item1, list_item2, list_item3 = transaction_manage(current_transaction,
                                                                        multi_year, opening_date,
                                                                        closing_date,
                                                                        transaction_section)
                list1.append(list_item1)
                list2.append(list_item2)
                list3.append(list_item3)

                current_transaction = []

            reg_key_deposits = r'[A-Za-z]{3} \d+ \d* [\d,]+.\d\d-?'
            reg_key = re.compile(r'([A-Za-z]{3} \d+) (.*) (\$? ?[\d,]+\.\d\d-?)')  # Transaction regex key
            reg_key_checks_flag = re.compile(r'\d+\*? [A-Za-z]{3} \d+ \d* [\d,]+.\d\d-?')
            reg_key_checks = r'\d+\*? [A-Za-z]{3} \d+ \d* [\d,]+.\d\d-?'
            reg_key_checks_elec = re.compile(r'(\d+) ([A-Za-z]{3} \d\d?) ([\d,]+.\d\d) (.*)')

            deposit_section_key = re.compile(r'(Customer Deposits)')
            credit_section_key = re.compile(r'(Other Deposits|Deposits / Credits|Card Deposits)')
            debit_section_key = re.compile(r'(Card Withdrawals|Other Withdrawals)')
            checks_con_section_key = re.compile(r'(Checks Presented Conventionally)')
            checks_elec_section_key = re.compile(r'(Checks Presented Electronically)')

            for a in pull_list:
                if "Ending Balance on " in a:
                    transaction_section = "Deposits"
                    continue
                if transaction_section == "Summary":
                    continue

                # Determine transactions section of statement
                if deposit_section_key.match(a):
                    transaction_section = "Deposits"
                    continue
                if debit_section_key.match(a):
                    transaction_section = "Debits"
                    continue
                if credit_section_key.match(a):
                    transaction_section = "Credits"
                    continue
                if checks_con_section_key.match(a):
                    transaction_section = "Checks_con"
                    continue
                if checks_elec_section_key.match(a):
                    transaction_section = "Checks_elec"
                    continue

                # Find list item that begins transaction
                if a == "Balance Summary" or a == "Balance Summary (continued)":
                    if len(deposits_list1) > 0:
                        temp_transaction_section = "Deposits"
                        deposits_list1 += deposits_list2
                        for b in deposits_list1:
                            list_item1, list_item2, list_item3 = transaction_manage([b], multi_year,
                                                                                    opening_date, closing_date,
                                                                                    temp_transaction_section)
                            list1.append(list_item1)
                            list2.append(list_item2)
                            list3.append(list_item3)

                            deposits_list1 = []
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
                        temp_transaction_section = "Checks_con"
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
                    break
                if transaction_section == "Deposits":
                    re_dep_match_list = re.findall(reg_key_deposits, a)
                    if len(re_dep_match_list) > 0:
                        if len(re_dep_match_list) > 1:
                            deposits_list2.append(re_dep_match_list[1])
                        deposits_list1.append(re_dep_match_list[0])
                if transaction_section == "Checks_con":
                    if len(deposits_list1) > 0:
                        temp_transaction_section = "Deposits"
                        deposits_list1 += deposits_list2
                        for b in deposits_list1:
                            list_item1, list_item2, list_item3 = transaction_manage([b], multi_year,
                                                                                    opening_date, closing_date,
                                                                                    temp_transaction_section)
                            list1.append(list_item1)
                            list2.append(list_item2)
                            list3.append(list_item3)

                            deposits_list1 = []
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
                if transaction_section == "Checks_elec":
                    if len(deposits_list1) > 0:
                        temp_transaction_section = "Deposits"
                        deposits_list1 += deposits_list2
                        for b in deposits_list1:
                            list_item1, list_item2, list_item3 = transaction_manage([b], multi_year,
                                                                                    opening_date, closing_date,
                                                                                    temp_transaction_section)
                            list1.append(list_item1)
                            list2.append(list_item2)
                            list3.append(list_item3)

                            deposits_list1 = []
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
                        temp_transaction_section = "Checks_con"
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
                    if reg_key_checks_elec.match(a) is not None:
                        list_item1, list_item2, list_item3 = transaction_manage(a, multi_year, opening_date,
                                                                                closing_date, transaction_section)
                        list1.append(list_item1)
                        list2.append(list_item2)
                        list3.append(list_item3)
                if transaction_section == "Debits" or transaction_section == "Credits":
                    if len(deposits_list1) > 0:
                        temp_transaction_section = "Deposits"
                        deposits_list1 += deposits_list2
                        for b in deposits_list1:
                            list_item1, list_item2, list_item3 = transaction_manage([b], multi_year,
                                                                                    opening_date, closing_date,
                                                                                    temp_transaction_section)
                            list1.append(list_item1)
                            list2.append(list_item2)
                            list3.append(list_item3)

                            deposits_list1 = []
                    if a == "Date Description of Transaction Ref Number Amount" and len(current_transaction) > 0:
                        if current_transaction[0][-1] == "-":
                            temp_transaction_section = "Debits"
                        else:
                            temp_transaction_section = "Credits"
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
                        continue
                if len(current_transaction) > 0:
                    current_transaction.append(a)

    return list1, list2, list3, check_count

def usbank_db_parse(statement):
    with pdfplumber.open(statement) as pdf:
        page = pdf.pages[0]
        # PULL DATA FROM text AMEX CC
        text = page.extract_text(x_tolerance=1)
        # Convert text to list separated by \n
        pull_list = text.split('\n')

        opening_date, opening_bal, closing_date, closing_bal = summary_pull(statement)

        # find first transaction page
        # transaction_page = transaction_finder(statement)

        # parse through transaction page and pull out relevant information
        trans_amt, trans_date, trans_desc, check_count = transaction_fetch(statement, opening_date, closing_date)

        # repeat closing date entries to match number of transactions
        closing_date = [closing_date] * len(trans_desc)

    return opening_date, opening_bal, closing_date, closing_bal, trans_amt, trans_date, trans_desc, check_count
