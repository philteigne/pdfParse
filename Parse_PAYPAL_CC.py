#!/usr/bin/env python
# coding: utf-8

# In[25]:


import pdfplumber
from datetime import datetime, timedelta
import re
from Print_Debug import *

# SUBSTRING IDENTIFIERS
paypal_CC_ID = "View your account online at paypal.com"


# PAYPAL CREDIT CARD PARSER
def summary_pull(lst):
    opening_date = None
    opening_bal = None
    closing_date = None
    closing_bal = None
    #ClosingYear = None
    ob_key = re.compile('Previous Balance -?\$(.+) New Balance -?\$(.+)')
    Dates = re.compile('Statement Closing Date: (\d{2}/\d{2}/\d{2})')
    Year = re.compile('(\d{4}) Totals Year-To-Date')
    for item in lst:
        if "Statement Closing Date:" in item:
            date_match = Dates.match(item)
            year_match = Year.search(item)
            #opening_date = date_match.group(1) if date_match.group(1) is not None else date_match.group(5)
            closing_date = date_match.group(1)
            # OpenYear = item.group(2) if item.group(2) is not None else item.group(6)
            #ClosingYear = year_match.group(1)
            closing_date = datetime.strptime(closing_date, '%m/%d/%y')
            #closing_date = closing_date.strftime("%Y-%m-%d")
            #opening_date = datetime.strptime(opening_date, '%b %d, %Y')
        
        if "Previous Balance" in item:
            OB_match = ob_key.match(item)
            opening_bal = OB_match.group(1)
            opening_bal = opening_bal.replace('$', '')
            opening_bal = opening_bal.replace(',', '')
            opening_bal = opening_bal.replace(' ', '')
            opening_bal = float(opening_bal)
            opening_bal = opening_bal * -1
            
            closing_bal = OB_match.group(2)
            closing_bal = closing_bal.replace('$', '')
            closing_bal = closing_bal.replace(',', '')
            closing_bal = closing_bal.replace(' ', '')
            closing_bal = float(closing_bal)
            closing_bal = closing_bal * -1   


    debug_statement_description(opening_date, closing_date, opening_bal, closing_bal)

    return opening_date, opening_bal, closing_date, closing_bal


def transaction_clean(txn_list, first_line, fee_section):
    # CLEAN UP REGEX
    payment_key_01 = re.compile(r'(.*) (Payment - )(Thank You)')
    suffix_key_01 = re.compile(r'(.*)( No Interest If Paid In Full)')

    txn_clean = []

    for line in txn_list:
        if len(txn_clean) == 0:  # is empty?
            if payment_key_01.match(first_line) is not None:
                payment_match = payment_key_01.match(first_line)
                line = 'Payment - ' + payment_match.group(1)
                txn_clean.append(line)
            elif suffix_key_01.match(first_line) is not None:
                suffix_match = suffix_key_01.match(first_line)
                line = suffix_match.group(1)
                txn_clean.append(line)
            else:
                txn_clean.append(first_line)

    return txn_clean


def transaction_fetch(transaction_page, stmt):
    list1 = []
    list2 = []
    list3 = []
    list3_clean = []
    name_list = []
    with pdfplumber.open(stmt) as pdf:
        page_total = len(pdf.pages)
        for count, entry in enumerate(pdf.pages):
            if count + transaction_page > (page_total - 1):
                break
            page = pdf.pages[count + transaction_page]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')

            reg_key = re.compile('(\d{2}\/\d{2}\/\d{2}) (\d{2}\/\d{2}\/\d{2}) ([A-Z0-9]{17} )?(Deferred |Standard )?(.+)\s(-?\$.*)')

            name_key_multi = re.compile(
                r'(.*) (\d-\d+) (-?\$.*.\d+)')  # 'WINSTON W MCFARLANE 9-31001 $898.02 $0.00 $898.02'
            name_key_single = re.compile(
                r'(.*) (Closing Date \d+\/\d+\/\d+) (Account Ending \d-\d+)')  # 'WINSTON W MCFARLANE Closing Date 03/25/22 Account Ending 9-31001'

            fee_key = "Total Fees"
            int_key = "Total Interest for this Period"

            fee_section_check = 0

            current_transaction = []

            for a in pull_list:
                # Is transaction in the fee section
                if a == "Fees" and pull_list[pull_list.index(a) + 1] == "Amount":
                    fee_section_check = 1

                # Find list item that begins transaction
                if reg_key.match(a) is not None or "Tran Date" in a or "NOTICE:" in a or fee_key in a or int_key in a:
                    if len(current_transaction) > 0:
                        re_match = reg_key.match(current_transaction[0])
                        if re_match is None:  # remove instances where fees/interest ends right before page does
                            current_transaction = []
                        else:
                            trans_amt = re_match.group(6)
                            trans_amt = trans_amt.replace('$', '')  # format value into float
                            trans_amt = trans_amt.replace(',', '')
                            trans_amt = trans_amt.replace(' ', '')
                            trans_amt = float(trans_amt)
                            trans_amt = trans_amt * -1
                            list1.append(trans_amt)  # append txn amount

                            trans_date = re_match.group(2)
                            if trans_date is not None:
                                trans_date = datetime.strptime(trans_date, '%m/%d/%y')

                            list2.append(trans_date)  # append date value

                            txn_name = re_match.group(5)
                            txn_name = transaction_clean(current_transaction, txn_name, fee_section_check)
                            txn_name = ' '.join(txn_name)
                            list3.append(txn_name)

                            current_transaction = []

                    current_transaction.append(a)

                elif len(current_transaction) > 0:
                    current_transaction.append(a)

                if name_key_multi.match(a) is not None:
                    name_match = name_key_multi.match(a)
                    if name_match.group(1) not in name_list:
                        name_list.append(name_match.group(1))
                if name_key_single.match(a) is not None:
                    name_match = name_key_single.match(a)
                    if name_match.group(1) not in name_list:
                        name_list.append(name_match.group(1))

                # Find end of fee section
                #if fee_key in a:
                    #fee_section_check = 0

    for a in list3:
        for b in name_list:
            if b in a:
                a = a.replace(b + ' ', '')
        list3_clean.append(a)

    # For each transaction in list 3 replace value in name_list with ''
    return list1, list2, list3_clean


def transaction_finder(stmt):
    with pdfplumber.open(stmt) as pdf:
        for count, item in enumerate(pdf.pages):
            page = pdf.pages[count]
            text = page.extract_text(x_tolerance=1)
            pull_list = text.split('\n')
            transaction_page = -1
            if transaction_page == -1:
                for previous, entry in zip(pull_list, pull_list[1:]):
                    if (entry == 'PAYMENTS & CREDITS' or entry == 'PURCHASES & ADJUSTMENTS' or entry == 'FEES' ) and previous == 'CURRENT ACTIVITY':
                    #if entry == 'PAYMENTS & CREDITS' and previous == 'CURRENT ACTIVITY':
                        transaction_page = count
                        return transaction_page
                        break
        transaction_page = 1
        return transaction_page


def paypal_cc_parse(statement):
    with pdfplumber.open(statement) as pdf:
        page = pdf.pages[0]
        # PULL DATA FROM text paypal CC
        text = page.extract_text(x_tolerance=1)
        # Convert text to list separated by \n
        pull_list = text.split('\n')
        opening_date, opening_bal, closing_date, closing_bal = summary_pull(pull_list)

        # find first transaction page
        transaction_page = transaction_finder(statement)

        # parse through transaction page and pull out relevant information
        trans_amt, trans_date, trans_desc = transaction_fetch(transaction_page, statement)

        # repeat closing date entries to match number of transactions
        closing_date = [closing_date] * len(trans_desc)

    return opening_date, opening_bal, closing_date, closing_bal, trans_amt, trans_date, trans_desc
