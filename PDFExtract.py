import pdfplumber
from Parse_AMEX_CC import *
from Parse_CAP1_CC import *
from Parse_TD_DB import *
from Parse_PNC_DB import *
from Parse_USBANK_DB import *
from Parse_PAYPAL_DB import *
from Parse_BANKOFAMERICA_DB import *
from Parse_PAYPAL_CC import *
from Parse_SQUARE_DB import *
from Write_EXCEL import *
import os
from time import perf_counter

if __name__ == '__main__':
    # Time for efficiency measure
    start_time = perf_counter()

    #   find name of file
    statementPDF = []
    parser_dir = r'/Users/philteigne/Documents/DP APP'

    for item in os.listdir(parser_dir):
        if item[:7] != 'Ticket_':
            continue
        parser_dir = parser_dir + '/' + item
    for item in os.listdir(parser_dir):
        if item.endswith('.pdf') or item.endswith('.PDF'):
            statementPDF.append(item)
    statementPDF = sorted(statementPDF)

    acct_type = "Single" # Single or Multi

    opening_date = []
    opening_bal = []
    closing_date = []
    closing_bal = []

    trans_desc = []
    trans_date = []
    trans_amt = []

    statements_obj = {}

    check_count = 0

    # open pdf and create string object from first page
    with pdfplumber.open(parser_dir + '/' + statementPDF[0]) as pdf:
        statement_name = statementPDF[0]
        statement_name = statement_name[:-4]
        page = pdf.pages[0]
        text = page.extract_text()
        statement_count = len(statementPDF)
        check_count = 0

        # if amex CC key in text, identify statement as Amex CC
        if amex_CC_ID in text or amex_CC_ID_2 in text:
            print("Amex CC")
            stmt_style = "PAR"
            StatementID = "amex_CC"
            for item in sorted(statementPDF):
                return_obj = amex_cc_parse(parser_dir + '/' + item)
                key = '1'
                if key in statements_obj:
                    statements_obj[key]["opening_date"].append(return_obj[key]["opening_date"])
                    statements_obj[key]["opening_bal"].append(return_obj[key]["opening_bal"])
                    statements_obj[key]["closing_date"].extend(return_obj[key]["closing_date"])
                    statements_obj[key]["closing_bal"].append(return_obj[key]["closing_bal"])
                    statements_obj[key]["txn_desc"].extend(return_obj[key]["txn_desc"])
                    statements_obj[key]["txn_date"].extend(return_obj[key]["txn_date"])
                    statements_obj[key]["txn_amt"].extend(return_obj[key]["txn_amt"])
                else:
                    statements_obj[key] = return_obj[key]
                print("statements_obj", statements_obj)
                if (len(statements_obj[key]["txn_amt"])) != (len(statements_obj[key]["txn_desc"])) != (
                        len(statements_obj[key]["txn_date"])):
                    print("Error: Transaction count disparity")

        # if cap1 cc key in text, identify statement as Cap1 CC
        elif cap1_CC_ID in text:
            print("Cap One CC")
            stmt_style = "ADB"
            StatementID = "cap1_CC"
            for item in sorted(statementPDF):
                return_obj = cap1_cc_parse(parser_dir + '/' + item)
                key = '1'
                if key in statements_obj:
                    statements_obj[key]["opening_date"].append(return_obj[key]["opening_date"])
                    statements_obj[key]["opening_bal"].append(return_obj[key]["opening_bal"])
                    statements_obj[key]["closing_date"].extend(return_obj[key]["closing_date"])
                    statements_obj[key]["closing_bal"].append(return_obj[key]["closing_bal"])
                    statements_obj[key]["txn_desc"].extend(return_obj[key]["txn_desc"])
                    statements_obj[key]["txn_date"].extend(return_obj[key]["txn_date"])
                    statements_obj[key]["txn_amt"].extend(return_obj[key]["txn_amt"])
                else:
                    statements_obj[key] = return_obj[key]

                if (len(statements_obj[key]["txn_amt"])) != (len(statements_obj[key]["txn_desc"])) != (
                        len(statements_obj[key]["txn_date"])):
                    print("Error: Transaction count disparity")

        # if TD db key in text, identify statement as TD DB
        elif td_DB_ID in text:
            print("TD DB")
            stmt_style = "ADB"
            StatementID = "td_DB"
            for item in sorted(statementPDF):
                return_obj = td_db_parse(parser_dir + '/' + item)
                key = '1'
                if key in statements_obj:
                    statements_obj[key]["opening_date"].append(return_obj[key]["opening_date"])
                    statements_obj[key]["opening_bal"].append(return_obj[key]["opening_bal"])
                    statements_obj[key]["closing_date"].extend(return_obj[key]["closing_date"])
                    statements_obj[key]["closing_bal"].append(return_obj[key]["closing_bal"])
                    statements_obj[key]["txn_desc"].extend(return_obj[key]["txn_desc"])
                    statements_obj[key]["txn_date"].extend(return_obj[key]["txn_date"])
                    statements_obj[key]["txn_amt"].extend(return_obj[key]["txn_amt"])
                else:
                    statements_obj[key] = return_obj[key]

                if (len(statements_obj[key]["txn_amt"])) != (len(statements_obj[key]["txn_desc"])) != (
                        len(statements_obj[key]["txn_date"])):
                    print("Error: Transaction count disparity")

        # if PNC db key in text, identify statement as PNC DB
        elif pnc_DB_ID in text or pnc_DB_ID_2 in text:
            print("PNC DB")
            stmt_style = "ADB"
            StatementID = "pnc_DB"
            for item in sorted(statementPDF):
                return_obj = pnc_db_parse(parser_dir + '/' + item)
                key = '1'
                if key in statements_obj:
                    statements_obj[key]["opening_date"].append(return_obj[key]["opening_date"])
                    statements_obj[key]["opening_bal"].append(return_obj[key]["opening_bal"])
                    statements_obj[key]["closing_date"].extend(return_obj[key]["closing_date"])
                    statements_obj[key]["closing_bal"].append(return_obj[key]["closing_bal"])
                    statements_obj[key]["txn_desc"].extend(return_obj[key]["txn_desc"])
                    statements_obj[key]["txn_date"].extend(return_obj[key]["txn_date"])
                    statements_obj[key]["txn_amt"].extend(return_obj[key]["txn_amt"])
                else:
                    statements_obj[key] = return_obj[key]

                if (len(statements_obj[key]["txn_amt"])) != (len(statements_obj[key]["txn_desc"])) != (
                        len(statements_obj[key]["txn_date"])):
                    print("Error: Transaction count disparity")

        # if US Bank db key in text, identify statement as US Bank DB
        elif usbank_DB_ID in text or usbank_DB_ID_2 in text or usbank_DB_ID_3 in text:
            print("US Bank DB")
            stmt_style = "ADB"
            StatementID = "usbank_DB"
            for item in sorted(statementPDF):
                return_obj = usbank_db_parse(parser_dir + '/' + item)
                key = '1'
                if key in statements_obj:
                    statements_obj[key]["opening_date"].append(return_obj[key]["opening_date"])
                    statements_obj[key]["opening_bal"].append(return_obj[key]["opening_bal"])
                    statements_obj[key]["closing_date"].extend(return_obj[key]["closing_date"])
                    statements_obj[key]["closing_bal"].append(return_obj[key]["closing_bal"])
                    statements_obj[key]["txn_desc"].extend(return_obj[key]["txn_desc"])
                    statements_obj[key]["txn_date"].extend(return_obj[key]["txn_date"])
                    statements_obj[key]["txn_amt"].extend(return_obj[key]["txn_amt"])
                else:
                    statements_obj[key] = return_obj[key]

                if (len(statements_obj[key]["txn_amt"])) != (len(statements_obj[key]["txn_desc"])) != (
                        len(statements_obj[key]["txn_date"])):
                    print("Error: Transaction count disparity")

        # if Paypal db key in text, identify statement as Paypal DB
        elif paypal_DB_ID in text:
            print("Paypal DB")
            stmt_style = "ADB"
            StatementID = "paypal_DB"
            for item in sorted(statementPDF):
                return_obj = paypal_db_parse(parser_dir + '/' + item)
                key = '1'
                if key in statements_obj:
                    statements_obj[key]["opening_date"].append(return_obj[key]["opening_date"])
                    statements_obj[key]["opening_bal"].append(return_obj[key]["opening_bal"])
                    statements_obj[key]["closing_date"].extend(return_obj[key]["closing_date"])
                    statements_obj[key]["closing_bal"].append(return_obj[key]["closing_bal"])
                    statements_obj[key]["txn_desc"].extend(return_obj[key]["txn_desc"])
                    statements_obj[key]["txn_date"].extend(return_obj[key]["txn_date"])
                    statements_obj[key]["txn_amt"].extend(return_obj[key]["txn_amt"])
                else:
                    statements_obj[key] = return_obj[key]

                if (len(statements_obj[key]["txn_amt"])) != (len(statements_obj[key]["txn_desc"])) != (
                        len(statements_obj[key]["txn_date"])):
                    print("Error: Transaction count disparity")

        # if Bank of America db key in text, identify statement as Bank of America DB
        elif bankofamerica_DB_ID in text:
            print("Bank of America DB")
            stmt_style = "ADB"
            StatementID = "bankofamerica_DB"
            for item in sorted(statementPDF):
                # o_date, o_bal, c_date, c_bal, t_amt, t_date, t_desc, chk_cnt = bankofamerica_db_parse(parser_dir + '/' + item)
                Test_num = bankofamerica_db_parse(parser_dir + '/' + item)
                # check_count += chk_cnt
                # opening_date.append(o_date)
                # opening_bal.append(o_bal)
                # closing_date.extend(c_date)
                # closing_bal.append(c_bal)
                # trans_desc.extend(t_desc)
                # trans_date.extend(t_date)
                # trans_amt.extend(t_amt)
                if (len(trans_amt)) != (len(trans_desc)) != (len(trans_date)):
                    print("Error: Transaction count disparity")

        # if Bank of America db key in text, identify statement as Bank of America DB
        elif paypal_CC_ID in text:
            print("Paypal CC")
            stmt_style = "PAR"
            StatementID = "paypal_CC"
            for item in sorted(statementPDF):
                return_obj = paypal_cc_parse(parser_dir + '/' + item)
                key = '1'
                if key in statements_obj:
                    statements_obj[key]["opening_date"].append(return_obj[key]["opening_date"])
                    statements_obj[key]["opening_bal"].append(return_obj[key]["opening_bal"])
                    statements_obj[key]["closing_date"].extend(return_obj[key]["closing_date"])
                    statements_obj[key]["closing_bal"].append(return_obj[key]["closing_bal"])
                    statements_obj[key]["txn_desc"].extend(return_obj[key]["txn_desc"])
                    statements_obj[key]["txn_date"].extend(return_obj[key]["txn_date"])
                    statements_obj[key]["txn_amt"].extend(return_obj[key]["txn_amt"])
                else:
                    statements_obj[key] = return_obj[key]

                if (len(statements_obj[key]["txn_amt"])) != (len(statements_obj[key]["txn_desc"])) != (
                len(statements_obj[key]["txn_date"])):
                    print("Error: Transaction count disparity")

        elif square_DB_ID in text:
            print("Square DB")
            stmt_style = "PAR"
            StatementID = "square_DB"
            acct_type = "Multi"
            for item in sorted(statementPDF):
                return_obj = square_db_parse(parser_dir + '/' + item)
                for key in return_obj:
                    if key in statements_obj:
                        statements_obj[key]["opening_date"].append(return_obj[key]["opening_date"])
                        statements_obj[key]["opening_bal"].append(return_obj[key]["opening_bal"])
                        statements_obj[key]["closing_date"].extend(return_obj[key]["closing_date"])
                        statements_obj[key]["closing_bal"].append(return_obj[key]["closing_bal"])
                        statements_obj[key]["txn_desc"].extend(return_obj[key]["txn_desc"])
                        statements_obj[key]["txn_date"].extend(return_obj[key]["txn_date"])
                        statements_obj[key]["txn_amt"].extend(return_obj[key]["txn_amt"])
                    else:
                        statements_obj[key] = return_obj[key]

                if (len(statements_obj[key]["txn_amt"])) != (len(statements_obj[key]["txn_desc"])) != (len(statements_obj[key]["txn_date"])):
                    print("Error: Transaction count disparity")

    print(statements_obj)

    for key in statements_obj:
        write_excel_file(statement_name, stmt_style, parser_dir, statements_obj[key])

    end_time = perf_counter()
    print(f"Time Elapsed in Seconds: {end_time - start_time}")