import pdfplumber
import xlwt
from xlwt import *
from Parse_AMEX_CC import *
from Parse_CAP1_CC import *
from Parse_TD_DB import *
from Parse_PNC_DB import *
from Parse_USBANK_DB import *
from Parse_PAYPAL_DB import *
from Parse_BANKOFAMERICA_DB import *
from Parse_PAYPAL_CC import *
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

    opening_date = []
    opening_bal = []
    closing_date = []
    closing_bal = []

    trans_desc = []
    trans_date = []
    trans_amt = []

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
        if amex_CC_ID in text:
            print("Amex CC")
            stmt_style = "PAR"
            StatementID = "amex_CC"
            for item in sorted(statementPDF):
                o_date, o_bal, c_date, c_bal, t_amt, t_date, t_desc = amex_cc_parse(parser_dir + '/' + item)
                opening_date.append(o_date)
                opening_bal.append(o_bal)
                closing_date.extend(c_date)
                closing_bal.append(c_bal)
                trans_desc.extend(t_desc)
                trans_date.extend(t_date)
                trans_amt.extend(t_amt)
                if (len(trans_amt)) != (len(trans_desc)) != (len(trans_date)):
                    print("Error: Transaction count disparity")

        # if cap1 cc key in text, identify statement as Cap1 CC
        elif cap1_CC_ID in text:
            print("Cap One CC")
            stmt_style = "ADB"
            StatementID = "cap1_CC"
            for item in sorted(statementPDF):
                o_date, o_bal, c_date, c_bal, t_amt, t_date, t_desc = cap1_cc_parse(parser_dir + '/' + item)
                opening_date.append(o_date)
                opening_bal.append(o_bal)
                closing_date.extend(c_date)
                closing_bal.append(c_bal)
                trans_desc.extend(t_desc)
                trans_date.extend(t_date)
                trans_amt.extend(t_amt)
                if (len(trans_amt)) != (len(trans_desc)) != (len(trans_date)):
                    print("Error: Transaction count disparity")

        # if TD db key in text, identify statement as TD DB
        elif td_DB_ID in text:
            print("TD DB")
            stmt_style = "ADB"
            StatementID = "td_DB"
            for item in sorted(statementPDF):
                o_date, o_bal, c_date, c_bal, t_amt, t_date, t_desc, chk_cnt = td_db_parse(parser_dir + '/' + item)
                check_count += chk_cnt
                opening_date.append(o_date)
                opening_bal.append(o_bal)
                closing_date.extend(c_date)
                closing_bal.append(c_bal)
                trans_desc.extend(t_desc)
                trans_date.extend(t_date)
                trans_amt.extend(t_amt)
                if (len(trans_amt)) != (len(trans_desc)) != (len(trans_date)):
                    print("Error: Transaction count disparity")

        # if PNC db key in text, identify statement as PNC DB
        elif pnc_DB_ID in text or pnc_DB_ID_2 in text:
            print("PNC DB")
            stmt_style = "ADB"
            StatementID = "pnc_DB"
            for item in sorted(statementPDF):
                o_date, o_bal, c_date, c_bal, t_amt, t_date, t_desc, chk_cnt = pnc_db_parse(parser_dir + '/' + item)
                check_count += chk_cnt
                opening_date.append(o_date)
                opening_bal.append(o_bal)
                closing_date.extend(c_date)
                closing_bal.append(c_bal)
                trans_desc.extend(t_desc)
                trans_date.extend(t_date)
                trans_amt.extend(t_amt)
                if (len(trans_amt)) != (len(trans_desc)) != (len(trans_date)):
                    print("Error: Transaction count disparity")

        # if US Bank db key in text, identify statement as US Bank DB
        elif usbank_DB_ID in text or usbank_DB_ID_2 in text or usbank_DB_ID_3 in text:
            print("US Bank DB")
            stmt_style = "ADB"
            StatementID = "usbank_DB"
            for item in sorted(statementPDF):
                o_date, o_bal, c_date, c_bal, t_amt, t_date, t_desc, chk_cnt = usbank_db_parse(parser_dir + '/' + item)
                check_count += chk_cnt
                opening_date.append(o_date)
                opening_bal.append(o_bal)
                closing_date.extend(c_date)
                closing_bal.append(c_bal)
                trans_desc.extend(t_desc)
                trans_date.extend(t_date)
                trans_amt.extend(t_amt)
                if (len(trans_amt)) != (len(trans_desc)) != (len(trans_date)):
                    print("Error: Transaction count disparity")

        # if Paypal db key in text, identify statement as Paypal DB
        elif paypal_DB_ID in text:
            print("Paypal DB")
            stmt_style = "ADB"
            StatementID = "paypal_DB"
            for item in sorted(statementPDF):
                o_date, o_bal, c_date, c_bal, t_amt, t_date, t_desc, chk_cnt = paypal_db_parse(parser_dir + '/' + item)
                # Test_num = paypal_db_parse(parser_dir + '/' + item)
                check_count += chk_cnt
                opening_date.append(o_date)
                opening_bal.append(o_bal)
                closing_date.extend(c_date)
                closing_bal.append(c_bal)
                trans_desc.extend(t_desc)
                trans_date.extend(t_date)
                trans_amt.extend(t_amt)
                if (len(trans_amt)) != (len(trans_desc)) != (len(trans_date)):
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
                o_date, o_bal, c_date, c_bal, t_amt, t_date, t_desc = paypal_cc_parse(parser_dir + '/' + item)
                # Test_num = paypal_db_parse(parser_dir + '/' + item)
                opening_date.append(o_date)
                opening_bal.append(o_bal)
                closing_date.extend(c_date)
                closing_bal.append(c_bal)
                trans_desc.extend(t_desc)
                trans_date.extend(t_date)
                trans_amt.extend(t_amt)
                if (len(trans_amt)) != (len(trans_desc)) != (len(trans_date)):
                    print("Error: Transaction count disparity")

    # check if statement has any transactions
    if len(trans_desc) == 0:
        print("Statement has no transactions.")
        exit()

    # print(trans_desc)
    # print(trans_date)
    # print(closing_date)
    # print(trans_amt)

    # if round(sum(trans_amt) + opening_bal, 2) == round(closing_bal, 2):
    #     print('TRUE')
    # add this check to each statement function

    # write transaction information to .xls file
    # if statementPDF in parserStatements:
    if check_count > 0:
        wbName = statement_name + '-PT_' + stmt_style + '_' + str(len(trans_desc)) + " " + str(check_count)
    else:
        wbName = statement_name + '-PT_' + stmt_style + '_' + str(len(trans_desc))
    wbNameErr = statement_name + '-failed_verification'
    # else:
    # wbName = statementPDF + '-PT_PAR_' + str(len(transFull))
    # set up DP Template
    workbook = xlwt.Workbook()
    transSheet = workbook.add_sheet("Transactions")
    balanceSheet = workbook.add_sheet("Ledger Balances")

    al = Alignment()
    al.horz = Alignment.HORZ_CENTER

    header_font = Font()
    header_font.name = 'Calibri (Body)'
    header_font.bold = True
    header_font.height = 240    # 12 * 20 for 12 pt

    desc_header_style = XFStyle()
    desc_header_style.font = header_font

    header_style = XFStyle()
    header_style.font = header_font
    header_style.alignment = al

    cell_font = Font()
    cell_font.name = 'Calibri'
    cell_font.height = 240  # 12 * 20 for 12 pt

    desc_cell_style = XFStyle()
    desc_cell_style.font = cell_font

    cell_style = XFStyle()
    cell_style.font = cell_font
    cell_style.alignment = al

    date_style = XFStyle()
    date_style.font = cell_font
    date_style.num_format_str = 'YYYY-MM-DD'
    date_style.alignment = al

    amt_style = XFStyle()
    amt_style.font = cell_font
    amt_style.num_format_str = "0.00"
    amt_style.alignment = al

    # write headers
    transSheet.write(0, 0, "Description", desc_header_style)
    transSheet.write(0, 1, "Date of transaction", header_style)
    transSheet.write(0, 2, "Amount", header_style)
    transSheet.write(0, 3, "Ledger", header_style)
    transSheet.write(0, 4, "Stmt Order", header_style)
    transSheet.write(0, 5, "Closing Date", header_style)
    transSheet.write(0, 6, opening_bal[0], amt_style)
    transSheet.write(0, 7, "Opening Date", header_style)
    transSheet.write(0, 8, "Days in Billing Period", header_style)

    # FILL SHEET COLUMNS
    row = 1
    if len(opening_date) > 0:
        if type(opening_date[0]) == str:
            transSheet.write(row, 8, int(opening_date[0]), cell_style)
        else:
            transSheet.write(row, 7, opening_date[0], date_style)
    while row <= len(trans_desc):
        transSheet.write(row, 0, trans_desc[(row - 1)], desc_cell_style)
        transSheet.write(row, 1, trans_date[(row - 1)], date_style)
        amt = float(trans_amt[(row - 1)])
        transSheet.write(row, 2, amt, amt_style)
        transSheet.write(row, 4, row, cell_style)
        transSheet.write(row, 5, closing_date[(row - 1)], date_style)
        transSheet.write(row, 6, xlwt.Formula(f"G{row}+C{row + 1}"), amt_style)
        row += 1

    # Set up Ledger Balance Sheet
    balanceSheet.write(0, 1, "Date", header_style)
    balanceSheet.write(0, 2, "Balance Amount", header_style)

    # Fill Ledger Balance # TODO: Add back in if fully automated. Causes issues with P/B otherwise
    # row = 1
    # while row <= len(closing_bal):
    #     balanceSheet.write(row, 1, closing_date[(row - 1)], date_style)
    #     print(closing_bal)
    #     if closing_bal[-1] is not None:
    #         amt = float(closing_bal[(row - 1)])
    #         amt = amt * (-1)
    #         balanceSheet.write(row, 2, amt, amt_style)
    #     row += 1


    # Format Column Width ((x)+0.915344)/0.00391534
    transSheet.col(0).width = 10450  # 40 column width
    transSheet.col(1).width = 4320  # 16 column width
    transSheet.col(2).width = 3597  # 13.17 column width
    transSheet.col(3).width = 0  # 0 column width
    transSheet.col(4).width = 2660  # 9.5 column width
    transSheet.col(5).width = 3214  # 11.67 column width
    transSheet.col(6).width = 3809  # 14 column width
    transSheet.col(7).width = 4021  # 14.83 column width
    transSheet.col(8).width = 4660  # 17.33 column width

    balanceSheet.col(0).width = 0  # 0 column width
    balanceSheet.col(1).width = 10195  # 39 column width
    balanceSheet.col(2).width = 10195  # 39 column width

    bal_check = round(opening_bal[0] + round((sum(trans_amt)), 2), 2)
    # print(bal_check)
    # print(closing_bal[-1])
    if bal_check != closing_bal[-1]:
        workbook.save(parser_dir + "/" + wbNameErr + ".xls")
    else:
        workbook.save(parser_dir + "/" + wbName + ".xls")

    end_time = perf_counter()
    print(f"Time Elapsed in Seconds: {end_time - start_time}")