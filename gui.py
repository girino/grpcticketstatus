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
        tv['columns'] = ('status', 'datebuy', 'spent')
        tv.heading('#0', text='Txid')
        tv.column('#0', anchor='w', width=600)
        tv.heading('status', text='Status')
        tv.column('status', anchor='w', width=100)
        tv.heading('datebuy', text='Buy Date')
        tv.column('datebuy', anchor='w', width=100)
        tv.heading('spent', text='Amount Spent')
        tv.column('spent', anchor='w', width=100)
        tv.grid(sticky = (N,S,W,E))
        self.treeview = tv
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        

    def LoadTable(self, data):
        df = "{:%Y-%m-%d}"
        for d in data:
            self.treeview.insert('', 'end', text=d['txid'], 
                values=(main.reverse_status(d['status']), 
                        df.format(datetime.datetime.fromtimestamp(d['buy_date'])), 
                        d['total_spent']/1e8))

if __name__ == "__main__":

    try:
        w = main.WalletConnector().accumulate_ticket_data()
    except Exception as e:
        w = [{'ERROR' : e.message}]

    root = Tk()
    App(root, w)
    root.mainloop()