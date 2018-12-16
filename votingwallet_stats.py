from WalletConnector import WalletConnector
from datetime import datetime, date
import time

import api_pb2
import api_pb2_grpc


class VotingWallet(WalletConnector):
    def __init__(self, cert=None, connection=None):
        super(VotingWallet, self).__init__(cert, connection)
    def get_block_after_date(self, timestamp):
        current_block = self.wallet.BestBlock(api_pb2.BestBlockRequest()).height
        current_time = time.time()
        # estimate block count for the difference
        elapsed = current_time - timestamp
        blocks = int(elapsed / 60 / 5) # blocks every 5 minutes
        estimated_block = current_block - blocks
        if estimated_block < 1:
            estimated_block = 1
        # get data on the estimated block
        response = self.wallet.BlockInfo(api_pb2.BlockInfoRequest(block_height=estimated_block))
        while estimated_block > 1 and response.timestamp > timestamp:
            estimated_block = estimated_block - 1
            response = self.wallet.BlockInfo(api_pb2.BlockInfoRequest(block_height=estimated_block))
        while estimated_block <= current_block and response.timestamp < timestamp:
            estimated_block = estimated_block + 1
            response = self.wallet.BlockInfo(api_pb2.BlockInfoRequest(block_height=estimated_block))
        return response

    def tickets_map(self):
        if not hasattr(self, '_tickets_map_cache'):
            self._tickets_map_cache = self.get_tickets_map()
        return self._tickets_map_cache

    def is_split(self, ticket):
        if not hasattr(self, '_is_split_cache'):
            self._is_split_cache = dict()
        if not ticket.ticket.hash in self._is_split_cache:
            decoded = self.decoder.DecodeRawTransaction(api_pb2.DecodeRawTransactionRequest(serialized_transaction=ticket.ticket.transaction)).transaction
            ret = len(decoded.outputs) > 5
            self._is_split_cache[ticket.ticket.hash] = ret
        return self._is_split_cache[ticket.ticket.hash]

    def get_tickets_by_interval(self, begin, end):
        bought = []
        bought_split = []
        voted = []
        voted_split = []
        revoked = []
        revoked_split = []
        sts = api_pb2.GetTicketsResponse.TicketDetails.TicketStatus
        tmap = self.tickets_map()
        for thash in tmap:
            ticket = tmap[thash]
            ts = ticket.ticket.timestamp
            if ts < end and ts >= begin:
                bought.append(ticket)
                split = self.is_split(ticket)
                if split:
                    bought_split.append(ticket)
            if ticket.ticket_status > sts.Value('LIVE'):
                ts = ticket.spender.timestamp
                if ts < end and ts >= begin:
                    if ticket.ticket_status == sts.Value('VOTED'):
                        voted.append(ticket)
                        split = self.is_split(ticket)
                        if split:
                            voted_split.append(ticket)
                    else:
                        revoked.append(ticket)
                        split = self.is_split(ticket)
                        if split:
                            revoked_split.append(ticket)
        return [bought, voted, revoked, bought_split, voted_split, revoked_split]

def next_month(now):
    if now[0] == 12:
        return [1, now[1] + 1]
    else:
        return [now[0] + 1, now[1]]

def cmp_dates(a, b):
    return a[0] == b[0] and a[1] == b[1]

def format_date(d):
    return '01/%02d/%04d' % (d[0], d[1])

def make_dates():
    now = [datetime.now().month, datetime.now().year]
    end = next_month(now)
    start = [1,2016]
    ret = []
    while not cmp_dates(start, end):
        ret.append( [format_date(start), format_date(next_month(start))] )
        start = next_month(start)
    return ret

def pretty_print(dates, stats_map):
    # header
    first_date = datetime.strptime(dates[0][0], "%d/%m/%Y")
    last_date = datetime.strptime(dates[-1][0], "%d/%m/%Y")

    years = range(first_date.year, last_date.year + 1)
    head = '+-------------+' + ('------------+' * len(years)) + '\n| month/year  |'
    for y in years:
        head += '    %04d    |' % y
    head += '\n+-------------+' + ('------------+' * len(years))
    print head

    for month in xrange(1, 13):
        lines = ['| %02d: Bought  |' % month,
                 '|     Voted   |',
                 '|     Revoked |',
                 '+-------------+']
        for y in years:
            key = '%02d/%04d' % (month, y)
            val = stats_map.get(key, [0,0,0,0,0,0])
            for i in xrange(3):
                lines[i] += ' %5d(%3d) |' % (val[i], val[i+3])
            lines[3] += '------------+'
        for line in lines:
            print line
    

if __name__ == '__main__':
    w = VotingWallet()
    dates = make_dates()
    stats = []
    for pair in dates:
        begin = time.mktime(datetime.strptime(pair[0], "%d/%m/%Y").timetuple())
        end = time.mktime(datetime.strptime(pair[1], "%d/%m/%Y").timetuple())
        stats.append( map(len, w.get_tickets_by_interval(begin, end)) )
    stats_map = dict()
    for i in xrange(len(dates)):
        d = datetime.strptime(dates[i][0], "%d/%m/%Y")
        month = '%02d/%04d' % (d.month, d.year)
        stats_map[month] = stats[i]
    pretty_print(dates, stats_map)

    