from WalletConnector import WalletConnector
from datetime import datetime, date
import time

import api_pb2
import api_pb2_grpc

def compare_times(begin, end, ts):
    return ts < end and ts >= begin

class VotingWallet(WalletConnector):
    def __init__(self, cert=None, connection=None):
        super(VotingWallet, self).__init__(cert, connection)

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
        bought = [tmap[thash] for thash in tmap if compare_times(begin, end, tmap[thash].ticket.timestamp)]
        spent = [tmap[thash] for thash in tmap if tmap[thash].ticket_status > sts.Value('LIVE')]
        spent_period = [ticket for ticket in spent if compare_times(begin, end, ticket.spender.timestamp)]
        voted = [ticket for ticket in spent_period if ticket.ticket_status == sts.Value('VOTED')]
        revoked = [ticket for ticket in spent_period if ticket.ticket_status != sts.Value('VOTED')]
        bought_split = [ticket for ticket in bought if self.is_split(ticket)]
        voted_split = [ticket for ticket in voted if self.is_split(ticket)]
        revoked_split = [ticket for ticket in revoked if self.is_split(ticket)]
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

def make_dates(start=[1,2016]):
    now = [datetime.now().month, datetime.now().year]
    end = next_month(now)
    ret = []
    while not cmp_dates(start, end):
        ret.append( [format_date(start), format_date(next_month(start))] )
        start = next_month(start)
    return ret

def pretty_print_monthly(dates, stats_map):
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

def pretty_print_global_stats(raw_stats):
    all_voted = reduce(lambda a, x: a + x[1], raw_stats, [])
    all_voted_split = reduce(lambda a, x: a + x[1+3], raw_stats, [])
    all_bought = reduce(lambda a, x: a + x[0], raw_stats, [])
    all_bought_split = reduce(lambda a, x: a + x[0+3], raw_stats, [])
    all_revoke = reduce(lambda a, x: a + x[2], raw_stats, [])
    all_revoke_split = reduce(lambda a, x: a + x[2+3], raw_stats, [])
    vote_time = reduce(lambda a, x: a + (x.spender.timestamp - x.ticket.timestamp), all_voted, 0)
    vote_time_split = reduce(lambda a, x: a + (x.spender.timestamp - x.ticket.timestamp), all_voted_split, 0)
    max_vote_time = reduce(lambda a, x: max(a, (x.spender.timestamp - x.ticket.timestamp)), all_voted, -1)
    max_vote_time_split = reduce(lambda a, x: max(a, (x.spender.timestamp - x.ticket.timestamp)), all_voted_split, -1)
    min_vote_time = reduce(lambda a, x: min(a, (x.spender.timestamp - x.ticket.timestamp)), all_voted, 3600*24*365)
    min_vote_time_split = reduce(lambda a, x: min(a, (x.spender.timestamp - x.ticket.timestamp)), all_voted_split, 3600*24*365)
    print "Vote time:", "min: % 3.2f, avg: % 3.2f, max: % 3.2f" % (1.0*min_vote_time/3600/24, 1.0*vote_time/len(all_voted)/3600/24, 1.0*max_vote_time/3600/24)
    print "  (split):", "min: % 3.2f, avg: % 3.2f, max: % 3.2f" % (1.0*min_vote_time_split/3600/24, 1.0*vote_time_split/len(all_voted_split)/3600/24, 1.0*max_vote_time_split/3600/24)
    print "All Tickets:", "bought: %5d, voted: %5d, revoked: %5d" % (len(all_bought), len(all_voted), len(all_revoke))
    print "    (split):", "bought: %5d, voted: %5d, revoked: %5d" % (len(all_bought_split), len(all_voted_split), len(all_revoke_split))

if __name__ == '__main__':
    w = VotingWallet()
    dates = make_dates([1, 2016])
    stats = []
    raw_stats = []
    for pair in dates:
        begin = time.mktime(datetime.strptime(pair[0], "%d/%m/%Y").timetuple())
        end = time.mktime(datetime.strptime(pair[1], "%d/%m/%Y").timetuple())
        tickets = w.get_tickets_by_interval(begin, end)
        stats.append( map(len, tickets) )
        raw_stats.append( tickets )
    stats_map = dict()
    for i in xrange(len(dates)):
        d = datetime.strptime(dates[i][0], "%d/%m/%Y")
        month = '%02d/%04d' % (d.month, d.year)
        stats_map[month] = stats[i]
    pretty_print_monthly(dates, stats_map)
    pretty_print_global_stats(raw_stats)

