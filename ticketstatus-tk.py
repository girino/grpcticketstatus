try:
    from Tkinter import *
    from ttk import *
except ImportError:  # Python 3
    from tkinter import *
    from tkinter.ttk import *
import datetime
import webbrowser
import WalletConnector

# tooltip from https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, parent, tree, col, text='widget info'):
        self.waittime = 2000     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = tree
        self.text = text
        self.parent = parent
        self.col = col
        # self.widget.bind("<Enter>", self.enter)
        # self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.widget.bind("<Motion>", self.leave_enter)
        self.event = None
        self.id = None
        self.tw = None
        self.event = False

    def leave_enter(self, event=None):
        self.leave(event)
        self.enter(event)

    def enter(self, event=None):
        if self.widget.identify_column(event.x) == self.col:
            self.event = event
            self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.parent.bbox("insert")
        if self.event:
            x += self.event.x + 25
            y += self.event.y + 20
        else:
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 20

        # creates a toplevel window
        self.tw = Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

class App(Frame):

    def __init__(self, parent, data):
        Frame.__init__(self, parent, padding=(3,3,3,3))
        self.grid(column=0, row=0, sticky = (N,S,W,E))

        self.CreateUI()
        self.data = data
        self.LoadTable(data)
        parent.grid_rowconfigure(0, weight = 1)
        parent.grid_columnconfigure(0, weight = 1)

        self.tooltip = CreateToolTip(self, self.treeview, '#0', 'Control Click to open block explorer')

    def CreateUI(self):
        tv = Treeview(self, selectmode='browse')

        # scrollbars, thanks https://www.reddit.com/r/learnpython/comments/34wgxn/ttktreeview_ttkscrollbar_and_horizontal_scrolling/
        ysb = Scrollbar(self, orient=VERTICAL, command=tv.yview)
        xsb = Scrollbar(self, orient=HORIZONTAL, command=tv.xview)
        tv.configure(yscroll=ysb.set, xscroll=xsb.set)
        tv.column('#0', minwidth=150, stretch=False)
        tv.heading('#0', text='Folder')

        ysb.pack(anchor=E, fill=Y, side=RIGHT)
        xsb.pack(anchor=S, fill=X, side=BOTTOM)
        tv.pack(expand=True, fill=BOTH)

        self.treeview = tv
        # self.grid_rowconfigure(0, weight = 1)
        # self.grid_columnconfigure(0, weight = 1)
        # self.grid_columnconfigure(1, weight=9)
        self.vsb = ysb
        self.hsb = xsb
        
        tv['columns'] = ('status', 'buy_date', 'total_spent', 'profit')
        tv.heading('#0', text='Ticket/Vote Txid')
        tv.column('#0', anchor='w', width=600)
        tv.heading('status', text='Status', command=lambda: self.sort_data('status'))
        tv.column('status', anchor='center', width=100)
        tv.heading('buy_date', text='Buy/Vote Date', command=lambda: self.sort_data('buy_date'))
        tv.column('buy_date', anchor='center', width=100)
        tv.heading('total_spent', text='Amount Spent/Received')
        tv.column('total_spent', anchor='e', width=100)
        tv.heading('profit', text='Profit')
        tv.column('profit', anchor='e', width=100)

        tv.bind("<Control-Button-1>", self.link_tree)
        #tv.bind("<Command-Button-1>", self.link_tree)
        
    def LoadTable(self, data):
        self.treeview.delete(*self.treeview.get_children())
        df = "{:%Y-%m-%d}"
        nf = "{:14.8f}"
        nfp = "{:5.2f}%"
        last = 'gray'
        for d in data:
            profit = '-'
            profit_percent = '-'
            if d['status'] == WalletConnector.StatusTypeEnum['VOTED']:
                profit = d['received'] - d['total_spent']
                profit_percent = nfp.format(profit * 100.0 / d['total_spent'])
                profit = nf.format(profit/1e8)
                color = 'green'
            elif d['status'] == WalletConnector.StatusTypeEnum['REVOKED']:
                color = 'orange' if last != 'orange' else 'light-orange'
            else:
                color = 'white' if last != 'white' else 'gray'
            last = color
            id_parent = self.treeview.insert('', 'end', text=d['txid'], 
                            values=(WalletConnector.reverse_status(d['status']), 
                                    df.format(datetime.datetime.fromtimestamp(d['buy_date'])), 
                                    nf.format(d['total_spent']/1e8), profit), tag=color)
            if d['status'] == WalletConnector.StatusTypeEnum['VOTED']:
                self.treeview.insert(id_parent, 'end', text=d['vote_txid'], 
                            values=('-', 
                                    df.format(datetime.datetime.fromtimestamp(d['vote_date'])), 
                                    nf.format(d['received']/1e8), profit_percent), tag='light-green')
                self.treeview.item(id_parent, open=True)
        self.treeview.tag_configure('green', background='#B5EAAA')
        self.treeview.tag_configure('light-green', background='#C3FDB8')
        self.treeview.tag_configure('gray', background='#E5E4E2')
        self.treeview.tag_configure('orange', background='#D45B12')
        self.treeview.tag_configure('light-orange', background='#F3BC2E')
    
    def sort_data(self, col):
        if (hasattr(self, 'sorted_by')) and (self.sorted_by == col):
            self.sorted_by = 'reverse_' + col
            reverse = True
        else:
            self.sorted_by = col
            reverse = False

        self.data = sorted(self.data, key=lambda x: x[col], reverse=reverse)
        self.LoadTable(self.data)

    def link_tree(self,event):
        if (self.treeview.identify_column(event.x) == '#0'):
            input_id = self.treeview.identify_row(event.y)
            self.input_item = self.treeview.item(input_id, "text")
            webbrowser.open('https://explorer.dcrdata.org/tx/{}'.format(self.input_item))


if __name__ == "__main__":

    try:
        w = WalletConnector.WalletConnector().accumulate_ticket_data()
    except Exception as e:
        w = [{'txid' : e.message,
                'status' : 0,
                'buy_date' : 0,
                'total_spent' : 1,
                'vote_txid' : '-',
                'vote_date' : 0,
                'received' : 0}]

    root = Tk()
    root.style = Style()
    prefered_themes = ['alt', 'aqua', 'clam', 'classic', 'default']
    available_themes = root.style.theme_names()
    for theme in prefered_themes:
        if theme in available_themes:
            root.style.theme_use("alt")
            break

    app = App(root, w)
    root.mainloop()