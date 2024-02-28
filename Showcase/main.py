# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

import pdfplumber
import xlwt

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    import xlwt
    import datetime
    import os

    parser_dir = r'/Users/philteigne/PycharmProjects/PDFParse/DP APP Mockup'

    for item in os.listdir(parser_dir):
        if item[:7] != 'Ticket_':
            continue
        parser_dir = parser_dir + '/' + item
    for item in os.listdir(parser_dir):
        if item.endswith('.pdf'):
            print(item)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
