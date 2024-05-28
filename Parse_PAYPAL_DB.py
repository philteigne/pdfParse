import pdfplumber
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re

# SUBSTRING IDENTIFIERS
paypal_DB_ID = "Available beginning Available ending Withheld beginning Withheld ending"

def summary_pull(stmt):
    opening_date = None
    opening_bal = None
    closing_date = None
    closing_bal = None
    stmt_period_key = re.compile(r'(.*) (\d?\d\/\d?\d\/\d{4}) - (\d?\d\/\d?\d\/\d{4})')
    stmt_period_key_02 = re.compile(r'(.*) (\d?\d\/\d?\d\/\d{2}) - (\d?\d\/\d?\d\/\d{2})')
    stmt_balance_key = re.compile(r'(USD) (-?[0-9,]+.\d\d) (-?[0-9,]+.\d\d) (-?[0-9,]+.\d\d) (-?[0-9,]+.\d\d)')
    with pdfplumber.open(stmt) as pdf:
        for count, entry in enumerate(pdf.pages):
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')
            # print(pull_list)

            for item in pull_list:
                # Opening Date and Closing Date
                if stmt_period_key.match(item) is not None:
                    stmt_period_match = stmt_period_key.match(item)
                    if opening_date is None:
                        opening_date = stmt_period_match.group(2)
                        opening_date = datetime.strptime(opening_date, '%m/%d/%Y')
                        print("Opening Date: ")
                        print(opening_date)
                    if closing_date is None:
                        closing_date = stmt_period_match.group(3)
                        closing_date = datetime.strptime(closing_date, '%m/%d/%Y')
                        print("Closing Date: ")
                        print(closing_date)
                if stmt_period_key_02.match(item) is not None:
                    stmt_period_match = stmt_period_key_02.match(item)
                    if opening_date is None:
                        opening_date = stmt_period_match.group(2)
                        opening_date = datetime.strptime(opening_date, '%m/%d/%y')
                        print("Opening Date: ")
                        print(opening_date)
                    if closing_date is None:
                        closing_date = stmt_period_match.group(3)
                        closing_date = datetime.strptime(closing_date, '%m/%d/%y')
                        print("Closing Date: ")
                        print(closing_date)
                # Opening Balance and Closing Balance
                if stmt_balance_key.match(item) is not None:
                    stmt_balance_match = stmt_balance_key.match(item)
                    opening_bal = stmt_balance_match.group(2)
                    opening_bal = opening_bal.replace(',', '')
                    opening_bal = float(opening_bal)
                    closing_bal = stmt_balance_match.group(3)
                    closing_bal = closing_bal.replace(',', '')
                    closing_bal = float(closing_bal)
                    print("Opening Balance: ")
                    print(opening_bal)
                    print("Closing Balance: ")
                    print(closing_bal)

            if closing_bal is not None:
                if opening_bal is not None:
                    if opening_date is not None:
                        if closing_date is not None:
                            break

    return opening_date, opening_bal, closing_date, closing_bal

def transaction_clean(txn_list):
    txn_clean = []
    end_page_key = re.compile(r'Page \d+')
    end_statement_key = "To report an unauthorized transaction"
    pp_id_key_isolated = re.compile(r'(ID: [0-9A-Z]{17})')
    pp_id_key_grouped = re.compile(r'(ID: [0-9A-Z]{17}) (.*)')

    for a in txn_list:
        if end_page_key.match(a) is not None:
            break
        if pp_id_key_isolated.match(a) is not None:
            if pp_id_key_grouped.match(a) is not None:
                re_match = pp_id_key_grouped.match(a)
                txn_clean.append(re_match.group(2))
            continue
        if end_statement_key in a:
            break
        txn_clean.append(a)


    final_txn = (' ').join(txn_clean)

    return final_txn

def transaction_manage(txn_list):
    reg_key = re.compile(r'(\d?\d\/\d?\d\/\d{4}) ?(.*) (-?[0-9,]+.\d\d) (-?[0-9,]+.\d\d) (-?[0-9,]+.\d\d)')  # Transaction regex key
    reg_key_02 = re.compile(r'(\d?\d\/\d?\d\/\d{2}) ?(.*) (-?[0-9,]+.\d\d) (-?[0-9,]+.\d\d) (-?[0-9,]+.\d\d)')
    reg_key_03 = re.compile(r'(\d?\d\/\d?\d\/\d{2}) ?(.*) (-?[0-9,]+.\d\d) (-?[0-9,]+.\d\d)( -?[0-9,]+.\d\d)?')

    date_key = re.compile(r'(\d?\d\/\d?\d\/\d{4})')

    txn_name_list = []

    for a in txn_list:
        if reg_key.match(a) is not None or reg_key_02.match(a) is not None or reg_key_03.match(a) is not None:
            if reg_key.match(a) is not None:
                re_match = reg_key.match(a)
            elif reg_key_02.match(a) is not None:
                re_match = reg_key_02.match(a)
            elif reg_key_03.match(a) is not None:
                re_match = reg_key_03.match(a)
            trans_date = re_match.group(1)
            trans_amt = re_match.group(3)
            trans_fee_amt = re_match.group(4)
            txn_name_list.append(re_match.group(2))
        else:
            txn_name_list.append(a)

    trans_amt = trans_amt.replace(',', '')
    trans_amt = float(trans_amt)

    trans_fee_amt = trans_fee_amt.replace(',', '')
    trans_fee_amt = float(trans_fee_amt)

    if date_key.match(trans_date) is not None:
        trans_date = datetime.strptime(trans_date, '%m/%d/%Y')
    else:
        trans_date = datetime.strptime(trans_date, '%m/%d/%y')

    txn_name = transaction_clean(txn_name_list)

    return trans_amt, trans_date, txn_name, trans_fee_amt

def transaction_fetch(stmt, transaction_page):
    list1 = []
    list2 = []
    list3 = []
    fee_list = []

    with pdfplumber.open(stmt) as pdf:
        page_total = len(pdf.pages)

        current_transaction = []
        check_count = 0

        transaction_start_tokens = [
            'Account Hold for Open Authorization',
            'ACH funding for Funds Recovery from',
            'Bank Deposit to PP Account',
            'BML Credit - Transfer from BML',
            'BML Withdrawal - Transfer to BML',
            'Buyer Credit Payment Withdrawal -',
            'Cancellation of Hold for Dispute',
            'Chargeback',
            'Credit Card Deposit for Negative',
            'Debit Card Cash Back Bonus',
            'Direct Credit Card Payment',
            'Dispute Fee',
            'Donation Payment',
            'Express Checkout Payment',
            'Fee Reversal',
            'Funds collected for disbursement',
            'Funds disbursed',
            'General Bonus',
            'General Card Deposit',
            'General Card Withdrawal',
            'General Credit Card Deposit',
            'General Credit Card Withdrawal',
            'General Currency Conversion',
            'General Hold',
            'General Hold Release',
            'General Payment',
            'General PayPal Debit Card',
            'General Reversal',
            'General Withdrawal - Bank Account',
            'General withdrawal to non-bank entity',
            'Hold on Balance for Dispute',
            'Hold on Available Balance',
            'Instant Payment Review \(IPR\) reversal',
            'Mass Pay Payment',
            'Mobile Payment',
            'MSB Redemption',
            'Non Reference Credit Payment',
            'Other',
            'Partner Fee',
            'Payment Hold',
            'Payment Refund',
            'Payment Release',
            'Payment Reversal',
            'Payment Review Hold',
            'Payment Review Release',
            'PayPal Debit Card Withdrawal to ATM',
            'PayPal Here Payment',
            'PayPal Protection Bonus, Payout for',
            'PayPal Seller Profiles',
            'PreApproved Payment Bill User',
            'Reserve Hold',
            'Reserve Release',
            'Reversal of ACH Deposit',
            'Reversal of ACH Withdrawal',
            'Reversal of General Account Hold',
            'Subscription Payment',
            'User Initiated Withdrawal',
            'Virtual Terminal Payment',
            'Website Payment',
            'Web Site Payment Pro Account'
        ]

        transaction_start_key = re.compile(fr"({'|'.join(transaction_start_tokens)})(.*)")

        page_end_key = re.compile(r'Page \d+')
        reg_key = re.compile(r'(\d?\d\/\d?\d\/\d{4}) ?(.*) (-?[0-9,]+.\d\d) (-?[0-9,]+.\d\d) (-?[0-9,]+.\d\d)')  # Transaction regex key

        for count, entry in enumerate(pdf.pages):
            if count + transaction_page > (page_total - 1):
                break
            page = pdf.pages[count + transaction_page]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')

            for a in pull_list:
                # Don't pull transactions from other currencies
                if "Transaction History -" in a:
                    if "USD" not in a:
                        if len(current_transaction) > 0:
                            list_item1, list_item2, list_item3, list_item4 = transaction_manage(current_transaction)

                            if len(list2) > 0:
                                fee_list.append(list_item4)
                                fee_month = list2[-1].strftime("%B")
                                fee_year = list2[-1].strftime("%Y")
                                fee_txn_name = "Paypal | Monthly Merchant Fee | " + fee_month + " " + fee_year
                                fee_txn_date = list2[-1] + relativedelta(day=31)
                                fee_txn_amt = sum(fee_list)

                                if fee_txn_amt != 0:
                                    list1.append(fee_txn_amt)
                                    list2.append(fee_txn_date)
                                    list3.append(fee_txn_name)

                                    fee_list = []

                            list1.append(list_item1)
                            list2.append(list_item2)
                            list3.append(list_item3)

                            current_transaction = []
                        break
                    continue

                # Find list item that begins transaction
                if transaction_start_key.match(a) is not None:
                    if len(current_transaction) > 0:
                        list_item1, list_item2, list_item3, list_item4 = transaction_manage(current_transaction)

                        if len(list2) > 0:
                            if list2[-1].month != list_item2.month or list2[-1].year != list_item2.year:
                                fee_month = list2[-1].strftime("%B")
                                fee_year = list2[-1].strftime("%Y")
                                fee_txn_name = "Paypal | Monthly Merchant Fee | " + fee_month + " " + fee_year
                                fee_txn_date = list2[-1] + relativedelta(day=31)
                                fee_txn_amt = sum(fee_list)
                                if fee_txn_amt != 0:
                                    list1.append(fee_txn_amt)
                                    list2.append(fee_txn_date)
                                    list3.append(fee_txn_name)

                                    fee_list = []

                        list1.append(list_item1)
                        list2.append(list_item2)
                        list3.append(list_item3)
                        fee_list.append(list_item4)

                        current_transaction = []

                    current_transaction.append(a)
                    continue

                if len(current_transaction) > 0:
                    if page_end_key.match(a) is not None or "To report an unauthorized transaction" in a:
                        current_transaction.append(a)
                        list_item1, list_item2, list_item3, list_item4 = transaction_manage(current_transaction)

                        if "To report an unauthorized transaction" in a:
                            list1.append(list_item1)
                            list2.append(list_item2)
                            list3.append(list_item3)

                            if len(list2) > 0:
                                fee_list.append(list_item4)
                                fee_month = list2[-1].strftime("%B")
                                fee_year = list2[-1].strftime("%Y")
                                fee_txn_name = "Paypal | Monthly Merchant Fee | " + fee_month + " " + fee_year
                                fee_txn_date = list2[-1] + relativedelta(day=31)
                                fee_txn_amt = sum(fee_list)
                                if fee_txn_amt != 0:
                                    list1.append(fee_txn_amt)
                                    list2.append(fee_txn_date)
                                    list3.append(fee_txn_name)

                                    fee_list = []

                            current_transaction = []
                        continue

                if len(current_transaction) > 0:
                    current_transaction.append(a)

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
                    if entry == 'Transaction History - USD':
                        transaction_page = count
                        return transaction_page
                        break
        transaction_page = 0
        return transaction_page

def paypal_db_parse(statement):
    with pdfplumber.open(statement) as pdf:
        page = pdf.pages[0]
        # PULL DATA FROM text AMEX CC
        text = page.extract_text(x_tolerance=1)
        # Convert text to list separated by \n
        pull_list = text.split('\n')

        opening_date, opening_bal, closing_date, closing_bal = summary_pull(statement)

        # find first transaction page
        transaction_page = transaction_finder(statement)

        # parse through transaction page and pull out relevant information
        trans_amt, trans_date, trans_desc, check_count = transaction_fetch(statement, transaction_page)

        # repeat closing date entries to match number of transactions
        closing_date = [closing_date] * len(trans_desc)

    return opening_date, opening_bal, closing_date, closing_bal, trans_amt, trans_date, trans_desc, check_count