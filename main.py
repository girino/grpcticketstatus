##
## Copyright 2018 by Girino Vey
##
## Licensed under Girino's Anarchist License
## http://www.girino.org/license
##



import grpc
import psutil
import os

#generate apis from proto
from grpc_tools import protoc
protoc.main(['-I.', '--python_out=.', '--grpc_python_out=.', 'api.proto'])

import api_pb2
import api_pb2_grpc


TransactionTypeEnum  = {
    'REGULAR' : 0,
    'COINBASE' : 4,
    'TICKET_PURCHASE' : 1,
    'VOTE' : 2,
    'REVOCATION' : 3
}

StatusTypeEnum = {
    'UNKNOWN' : 0,
    'IMMATURE' : 1,
    'LIVE' : 2,
    'VOTED' : 3
}

def reverse_status(status):
    for key in StatusTypeEnum.keys():
        if StatusTypeEnum[key] == status:
            return key
    raise Exception('Status not found.')

def find_all_files(path, filename):
    matches = []
    for root, dirnames, filenames in os.walk(path):
        for fn in filenames:
            if fn.lower() == filename.lower():
                matches.append(os.path.join(root, fn))
    return matches

def to_hex(bin):
    return bin[::-1].encode('hex')

class WalletConnector:
    def __init__(self):
        self.found_certs = self.find_cert()
        self.init_channels()

    def find_cert(self):
        # looks for cert in linux
        home = os.path.expanduser('~')
        paths = [
            home + "/.config/decrediton/wallets/mainnet",
            os.path.expandvars('%APPDATA%\\decrediton\\wallets\\mainnet'),
            os.path.expandvars('%LOCALAPPDATA%\\decrediton\\wallets\\mainnet'),
            home + "/Library/Application Support/decrediton/wallets/mainnet"
        ]
        ret = []
        for path in paths:
            if os.path.isdir(path):
                ret = ret + find_all_files(path, 'rpc.cert')
        return ret

    def init_channels(self):
        dcrwallet_pid = None
        for  p in psutil.process_iter():
            if (p.name().lower() == 'dcrwallet') or (p.name().lower() == 'dcrwallet.exe') :
                dcrwallet_pid = p.pid
                break
        if dcrwallet_pid == None:
            raise Exception('Process \'dcrwallet\' could not be found.')

        self.channel = None
        for conn in psutil.Process(pid=dcrwallet_pid).connections():
            if conn.status == 'LISTEN':
                for cert in self.found_certs:
                    self.creds = grpc.ssl_channel_credentials(open(cert).read())
                    try:
                        self.channel = grpc.secure_channel('%s:%d' % (conn.laddr.ip, conn.laddr.port), self.creds)
                        self.wallet = api_pb2_grpc.WalletServiceStub(self.channel)
                        self.decoder = api_pb2_grpc.DecodeMessageServiceStub(self.channel)
                        # ping to test
                        self.wallet.Ping(api_pb2.PingRequest())
                        break
                    except grpc._channel._Rendezvous:
                        # ignore errors
                        self.channel = None
        if self.channel == None:
            raise Exception('Could not open connection to wallet.')

    def getTicketPurchases(self, type):
        ret = []
        all_txs = self.wallet.GetTransactions(api_pb2.GetTransactionsRequest())
        for blockinfo in all_txs:
            if hasattr (blockinfo, 'mined_transactions') and hasattr (blockinfo.mined_transactions, 'transactions'):
                for tx in blockinfo.mined_transactions.transactions:
                    if hasattr(tx, 'transaction_type') and tx.transaction_type == type:
                        ret.append(tx)
        return ret

    def map_voted(self):
        self.voted = {}
        for tx in self.getTicketPurchases(TransactionTypeEnum['VOTE']):
            # decode
            decoded = self.decoder.DecodeRawTransaction(api_pb2.DecodeRawTransactionRequest(serialized_transaction=tx.transaction))
            for input_ in decoded.transaction.inputs:
                self.voted[input_.previous_transaction_hash] = tx
        return self.voted


    def get_status(self, hash):
        if not hasattr(self, 'voted'):
            self.voted = self.map_voted()
        if self.voted.has_key(hash):
            return StatusTypeEnum["VOTED"]
        tx_full = self.wallet.GetTransaction(api_pb2.GetTransactionRequest(transaction_hash=hash))
        if tx_full.confirmations < 256:
            return StatusTypeEnum["IMMATURE"]
        return StatusTypeEnum["LIVE"]

    def accumulate_ticket_data(self):
        ret = []
        for tx in self.getTicketPurchases(TransactionTypeEnum['TICKET_PURCHASE']):
            summary = {'txid' : to_hex(tx.hash), 
                        'status' : self.get_status(tx.hash),
                        'buy_date' : tx.timestamp}
            val = 0
            for inpt in tx.debits:
                val = val + inpt.previous_amount
            summary['spent'] = val
            if self.voted.has_key(tx.hash):
                val_credits = 0
                for oupt in self.voted[tx.hash].credits:
                    val_credits = val_credits + oupt.amount
                summary['received'] = val_credits
                summary['vote_date'] = self.voted[tx.hash].timestamp
            ret.append(summary)
        return ret


w = WalletConnector()

# TODO: design a pretty printer.
# TODO: calculate ROI/time
# TODO: add sorting and sorting cmd params
print(w.accumulate_ticket_data())