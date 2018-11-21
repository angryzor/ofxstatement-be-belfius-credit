from ofxstatement.plugin import Plugin
from ofxstatement.parser import StatementParser
from ofxstatement.statement import Statement, StatementLine, BankAccount
from ofxstatement.exceptions import ParseError
import csv
import re
import datetime

start_date_line_exp = re.compile('Transacties van +(\d\d)/(\d\d)/(\d\d\d\d) +tot +(\d\d)/(\d\d)/(\d\d\d\d)')
record_line_exp = re.compile('(\d\d/\d\d)  +(\d\d/\d\d)  +(.+?)  +.+?  +')#(\d+,\d+)  +([A-Z]+)     -')
record_line_end_exp = re.compile('(\d+,\d+) +([A-Z]+)  +(\+|-)$')

class BelfiusBeCreditPlugin(Plugin):
    """Belgian Belfius Bank plugin for ofxstatement
    """

    def get_parser(self, filename):
        f = open(filename, 'r')
        parser = BelfiusBeCreditParser(f)
        return parser


class BelfiusBeCreditParser(StatementParser):

    next_year_line = False

    def __init__(self, fin):
        self.statement = Statement()
        self.fin = fin

    def parse_float(self, value):
        """Return a float from a string with ',' as decimal mark.
        """
        return float(value.replace(',','.'))

    def parse_datetime(self, value):
        [day, month] = map(int, value.split('/'))

        return datetime.date(self.statement.start_date.year + (1 if self.next_year_line else 0), month, day)

    def split_records(self):
        """Return iterable object consisting of a line per transaction
        """
        return self.fin

    def parse_record(self, line):
        """Parse given transaction line and return StatementLine object
        """
        stmt_ln = StatementLine()
        line_match = record_line_exp.match(line)

        if not line_match:
            date_match = start_date_line_exp.search(line)

            if date_match:
                self.statement.start_date = datetime.date(int(date_match[3]), int(date_match[2]), int(date_match[1]))
                self.statement.end_date = datetime.date(int(date_match[6]), int(date_match[5]), int(date_match[4]))

            return None

        line_match_2 = record_line_end_exp.search(line)
        # print(line_match)
        # print(line_match[3])
        # raise 'matched'

        [proc_day, proc_month] = map(int, line_match[2].split('/'))
        proc_date = datetime.date(self.statement.start_date.year, proc_month, proc_day)
        self.next_year_line = proc_date < self.statement.start_date

        self.statement.currency = 'EUR'#line_match[4]
        stmt_ln.date = self.parse_value(line_match[1], 'date')
        stmt_ln.payee = self.parse_value(line_match[3], 'payee')
        amt = self.parse_value(line_match_2[1], 'amount')
        stmt_ln.amount = amt if line_match_2[3] == '+' else -amt
        stmt_ln.trntype = self.parse_value('CREDIT', 'trntype')

        return stmt_ln

