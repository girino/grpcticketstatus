import sys
from WalletConnector import WalletConnector, pretty_print, StatusTypeEnum
import mysql.connector
import datetime
import argparse

# create table balances (wallet text, date text, immature double, locked double, spendable double, total double);

def consolidate(wconn):
    data = wconn.accumulate_ticket_data()
    balance = wconn.get_balance()
    nf = "{:14.8f}"
    nfp = "{:5.2f}%"
    nf2 = "{:5.2f}"
    live_immature = [StatusTypeEnum['LIVE'], StatusTypeEnum['IMMATURE']]
    immature = [StatusTypeEnum['IMMATURE']]
    live = [StatusTypeEnum['LIVE']]
    voted = [StatusTypeEnum['VOTED'], StatusTypeEnum['WAITING CONFIRMATION']]
    revoked = [StatusTypeEnum['REVOKED']]

    locked = sum([d['ticket_spent'] for d in data if d['status'] in live_immature])
    immature = balance.immature_reward + balance.immature_stake_generation
    spendable = balance.spendable
    total = balance.total + locked
    return {
        'locked': locked/1e8,
        'immature': immature/1e8,
        'spendable': spendable/1e8,
        'total': total/1e8,
    }

def insert_data(conn, data):
    cursor = conn.cursor()
    insert = """
    insert into balances (wallet, date, immature, locked, spendable, total) 
        values (%(wallet)s, %(date)s, %(immature)s, %(locked)s, %(spendable)s, %(total)s);
    """
    data['date'] = datetime.datetime.now().strftime('%Y%m%d%H%M')

    cursor.execute(insert, data)

    cursor.close()
    conn.commit()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--dbpassword", default="balances123", help="Database password (mandatory)")
    parser.add_argument("-g", "--dbhost", default="localhost", help="Database Host (defaults to localhost)")
    parser.add_argument("-d", "--dbname", default="balances", help="Database Name (default to 'balances')")
    parser.add_argument("-u", "--dbuser", default="balances", help="Database user (default to 'balances')")
    parser.add_argument("-c", "--wcert", default=None, help="wallet certificate (defaults to auto find)")
    parser.add_argument("-q", "--wport", default=None, help="wallet port (defaults to autofind)")
    parser.add_argument("-w", "--wname", default="default", help="wallet identifier on the DB (defaults to \"default\")")
    args = parser.parse_args()
    if args.dbpassword == None:
        parser.print_help()
        exit(-1)
    return args

def main(args):
    cert = args.wcert
    conn = None
    if args.wport:
        conn = "localhost:" + args.wport
    w = WalletConnector(cert, conn)
    data = consolidate(w)
    mydb = mysql.connector.connect(
        host=args.dbhost,
        user=args.dbuser,
        passwd=args.dbpassword,
        database=args.dbname
    )
    data['wallet'] = args.wname
    insert_data(mydb, data)
    mydb.close()


if __name__ == '__main__':
    args = parse_args()
    main(args)
    exit(0)


