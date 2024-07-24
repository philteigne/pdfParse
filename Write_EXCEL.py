import xlwt
from xlwt import *


def write_excel_file(statement_name, stmt_style, parser_dir, statements_obj):
    opening_date = statements_obj['opening_date']
    closing_date = statements_obj['closing_date']
    opening_bal = statements_obj['opening_bal']
    closing_bal = statements_obj['closing_bal']

    trans_desc = statements_obj['txn_desc']
    trans_date = statements_obj['txn_date']
    trans_amt = statements_obj['txn_amt']

    if statements_obj['check_count'] > 0:
        check_count = " " + str(statements_obj['check_count'])
    else:
        check_count = ''

    # if "acct_id" is in statements obj statement is part of a multi pdf
    if "acct_id" in statements_obj:
        acct_id = statements_obj['acct_id'] + "_" + str(closing_bal[-1]) + "-"
    else:
        acct_id = ''

    if len(trans_desc) == 0:
        print("Statement has no transactions.")
        exit()

    # write transaction information to .xls file
    wbName = acct_id + statement_name + '-PT_' + stmt_style + '_' + str(len(trans_desc)) + check_count

    wbNameErr = acct_id + statement_name + '-failed_verification'

    # set up DP Template
    workbook = xlwt.Workbook()
    transSheet = workbook.add_sheet("Transactions")
    balanceSheet = workbook.add_sheet("Ledger Balances")

    al = Alignment()
    al.horz = Alignment.HORZ_CENTER

    header_font = Font()
    header_font.name = 'Calibri (Body)'
    header_font.bold = True
    header_font.height = 240  # 12 * 20 for 12 pt

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