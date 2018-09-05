from WalletConnector import WalletConnector, pretty_print

if __name__ == '__main__':
    w = WalletConnector()

    # TODO: calculate ROI/time
    # TODO: add sorting and sorting cmd params
    # TODO: create GUI
    out = w.accumulate_ticket_data()

    pretty_print(out)
    raw_input('Press ENTER to close.')