try:
    from Tkinter import *
    from ttk import *
except ImportError:  # Python 3
    from tkinter import *
    from tkinter.ttk import *
import datetime
import main

class App(Frame):

    def __init__(self, parent, data):
        Frame.__init__(self, parent)
        self.CreateUI()
        self.LoadTable(data)
        self.grid(sticky = (N,S,W,E))
        parent.grid_rowconfigure(0, weight = 1)
        parent.grid_columnconfigure(0, weight = 1)

    def CreateUI(self):
        tv = Treeview(self)
        tv['columns'] = ('status', 'datebuy', 'spent', 'profit')
        tv.heading('#0', text='Ticket/Vote Txid')
        tv.column('#0', anchor='w', width=600)
        tv.heading('status', text='Status')
        tv.column('status', anchor='center', width=100)
        tv.heading('datebuy', text='Buy/Vote Date')
        tv.column('datebuy', anchor='center', width=100)
        tv.heading('spent', text='Amount Spent/Received')
        tv.column('spent', anchor='e', width=100)
        tv.heading('profit', text='Profit')
        tv.column('profit', anchor='e', width=100)
        tv.grid(sticky = (N,S,W,E))
        self.treeview = tv
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        

    def LoadTable(self, data):
        df = "{:%Y-%m-%d}"
        nf = "{:14.8f}"
        for d in data:
            profit = '-'
            profit_percent = '-'
            if d['status'] == main.StatusTypeEnum['VOTED']:
                profit = d['received'] - d['total_spent']
                profit_percent = nf.format(profit * 100.0 / d['total_spent'])
                profit = (nf+'%').format(profit)
            id_parent = self.treeview.insert('', 'end', text=d['txid'], 
                            values=(main.reverse_status(d['status']), 
                                    df.format(datetime.datetime.fromtimestamp(d['buy_date'])), 
                                    nf.format(d['total_spent']/1e8), profit))
            if d['status'] == main.StatusTypeEnum['VOTED']:
                self.treeview.insert(id_parent, 'end', text=d['vote_txid'], 
                            values=('-', 
                                    df.format(datetime.datetime.fromtimestamp(d['vote_date'])), 
                                    nf.format(d['received']/1e8), profit_percent))
                self.treeview.item(id_parent, open=True)

if __name__ == "__main__":

    try:
        w = main.WalletConnector().accumulate_ticket_data()
    except Exception as e:
        w = [{'txid' : e.message,
                'status' : 0,
                'buy_date' : 0,
                'total_spent' : 1,
                'vote_txid' : '-',
                'vote_date' : 0,
                'received' : 0}]

    root = Tk()
    App(root, w)
    root.mainloop()