"""
Personal Finance Tracker (Beginner)
- Desktop GUI: tkinter
- Database: SQLite (finance.db, created automatically, starts with 0 transactions)
- Web view: runs automatically so your phone/laptop browser can use the same data
Run:  python finance_tracker.py
"""
import json, socket, sqlite3, threading, tkinter as tk
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from tkinter import ttk, messagebox

DB, PORT, CUR = "finance.db", 8000, "₹"
CATS = {
    "Expense": ["Food", "Rent", "Transport", "Shopping", "Bills", "Health",
                "Entertainment", "Education", "Other"],
    "Income": ["Salary", "Freelance", "Investment", "Gift", "Other"],
}

# ---------------------------------------------------------------- database
def db(sql, args=()):
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    try:
        cur = c.execute(sql, args)
        c.commit()
        return [dict(r) for r in cur.fetchall()]
    finally:
        c.close()

def init_db():
    db("""CREATE TABLE IF NOT EXISTS categories(
          id INTEGER PRIMARY KEY, kind TEXT, name TEXT, UNIQUE(kind, name))""")
    db("""CREATE TABLE IF NOT EXISTS transactions(
          id INTEGER PRIMARY KEY, kind TEXT, amount REAL,
          category TEXT, note TEXT, day TEXT)""")
    for kind, names in CATS.items():
        for n in names:
            db("INSERT OR IGNORE INTO categories(kind,name) VALUES(?,?)", (kind, n))

def categories():
    out = {"Expense": [], "Income": []}
    for r in db("SELECT kind,name FROM categories ORDER BY id"):
        out[r["kind"]].append(r["name"])
    return out

def add_tx(kind, amount, cat, note, day):
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number")
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")
    if cat not in categories().get(kind, []):
        raise ValueError("Please choose a category from the list")
    day = (day or str(date.today())).strip()
    try:
        date.fromisoformat(day)
    except ValueError:
        raise ValueError("Date must look like 2026-11-16")
    db("INSERT INTO transactions(kind,amount,category,note,day) VALUES(?,?,?,?,?)",
       (kind, amount, cat, (note or "").strip(), day))

def snapshot():
    tx = db("SELECT * FROM transactions ORDER BY day DESC, id DESC")
    inc = sum(t["amount"] for t in tx if t["kind"] == "Income")
    exp = sum(t["amount"] for t in tx if t["kind"] == "Expense")
    return {"cats": categories(), "tx": tx, "income": inc, "expense": exp,
            "balance": inc - exp, "cur": CUR}

# ---------------------------------------------------------------- web (phone / laptop browser)
PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Finance Tracker</title><style>
:root{--bg:#f4f6fb;--card:#fff;--ink:#1e2433;--mute:#6b7385;--pri:#4f46e5;--g:#16a34a;--r:#dc2626}
@media(prefers-color-scheme:dark){:root{--bg:#12141c;--card:#1c1f2b;--ink:#eef0f6;--mute:#9aa1b5}}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--ink)}
.w{max-width:760px;margin:auto;padding:16px}h1{font-size:22px;margin:8px 0 16px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.c{background:var(--card);border-radius:14px;padding:12px;box-shadow:0 1px 4px #0001}
.c small{color:var(--mute)}.c b{display:block;font-size:18px;margin-top:4px}
form,.list{background:var(--card);border-radius:14px;padding:14px;margin-top:14px;box-shadow:0 1px 4px #0001}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
input,select,button{width:100%;padding:11px;margin-top:8px;border-radius:10px;border:1px solid #8884;
background:transparent;color:var(--ink);font-size:16px}
button{background:var(--pri);color:#fff;border:0;font-weight:600}
.t{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #8882}
.t small{color:var(--mute)}.t button{width:auto;background:none;color:var(--r);padding:4px 8px;margin:0}
@media(max-width:480px){.cards{grid-template-columns:1fr}}
</style></head><body><div class="w"><h1>💰 Personal Finance Tracker</h1>
<div class="cards"><div class="c"><small>Balance</small><b id="b"></b></div>
<div class="c"><small>Income</small><b id="i" style="color:var(--g)"></b></div>
<div class="c"><small>Expenses</small><b id="e" style="color:var(--r)"></b></div></div>
<form id="f"><div class="row"><select id="k"><option>Expense</option><option>Income</option></select>
<input id="a" type="number" step="0.01" placeholder="Amount" required></div>
<select id="c"></select><div class="row"><input id="n" placeholder="Note (optional)">
<input id="d" type="date"></div><button>Add transaction</button></form>
<div class="list" id="l"></div></div><script>
let D;const $=i=>document.getElementById(i);
const m=n=>D.cur+n.toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2});
function cats(){$('c').innerHTML=D.cats[$('k').value].map(x=>`<option>${x}</option>`).join('')}
async function load(){D=await (await fetch('/api/data')).json();
$('b').textContent=m(D.balance);$('i').textContent=m(D.income);$('e').textContent=m(D.expense);
const cur=$('c').value;cats();if(cur)$('c').value=cur;
$('l').innerHTML=D.tx.length?D.tx.map(t=>`<div class="t"><div><b>${t.category}</b><br><small>${t.day} ${t.note?'· '+t.note:''}</small></div>
<div style="color:var(--${t.kind=='Income'?'g':'r'})">${t.kind=='Income'?'+':'-'}${m(t.amount)}
<button onclick="del(${t.id})">✕</button></div></div>`).join(''):'<small>No transactions yet. Add your first one above!</small>'}
async function post(u,b){return fetch(u,{method:'POST',body:JSON.stringify(b)})}
async function del(id){await post('/api/delete',{id});load()}
$('k').onchange=cats;$('d').valueAsDate=new Date();
$('f').onsubmit=async e=>{e.preventDefault();
const r=await post('/api/add',{kind:$('k').value,amount:$('a').value,category:$('c').value,note:$('n').value,day:$('d').value});
if(!r.ok){alert((await r.json()).error);return}$('a').value='';$('n').value='';load()};
load();setInterval(load,5000);</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, body, ctype="application/json", code=200):
        b = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        if self.path == "/api/data":
            self._send(json.dumps(snapshot()))
        else:
            self._send(PAGE, "text/html")
    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or "{}")
        try:
            if self.path == "/api/add":
                add_tx(data.get("kind"), data.get("amount"), data.get("category"),
                       data.get("note"), data.get("day"))
            elif self.path == "/api/delete":
                db("DELETE FROM transactions WHERE id=?", (data.get("id"),))
            self._send("{}")
        except ValueError as e:
            self._send(json.dumps({"error": str(e)}), code=400)

def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"

def start_web():
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

# ---------------------------------------------------------------- tkinter GUI
F = "Segoe UI"
BG, CARD, INK, MUTE = "#eef1f8", "#ffffff", "#1e2433", "#6b7385"
PRI, PRI2, GREEN, RED, LINE, CHIP = "#4f46e5", "#7c3aed", "#16a34a", "#dc2626", "#dde1ee", "#eceefa"
BARS = ["#4f46e5", "#7c3aed", "#0ea5e9", "#f59e0b", "#ec4899"]

def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * t) for x, y in zip(a, b))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FinTrack - Personal Finance Tracker")
        self.geometry("1120x720")
        self.minsize(980, 640)
        self.configure(bg=BG)
        self.kind, self.cat = tk.StringVar(value="Expense"), tk.StringVar()
        self.amount, self.note = tk.StringVar(), tk.StringVar()
        self.day = tk.StringVar(value=str(date.today()))
        self.data = None
        self.style()
        self.build()
        self.set_kind("Expense")
        self.refresh()
        self.after(3000, self.poll)

    def style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", rowheight=34, font=(F, 10), background=CARD,
                    fieldbackground=CARD, borderwidth=0, foreground=INK)
        s.configure("Treeview.Heading", font=(F, 10, "bold"), background="#f3f4fb",
                    foreground=MUTE, borderwidth=0, relief="flat", padding=8)
        s.map("Treeview.Heading", background=[("active", "#f3f4fb")])
        s.map("Treeview", background=[("selected", "#dfe3ff")], foreground=[("selected", INK)])
        s.configure("Vertical.TScrollbar", background=LINE, troughcolor=CARD, borderwidth=0)

    # ---- small helpers
    def card(self, parent, **kw):
        return tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground="#e3e7f3", **kw)

    def field(self, parent, label, var, prefix=""):
        tk.Label(parent, text=label, bg=CARD, fg=MUTE, font=(F, 9, "bold")).pack(anchor="w", pady=(12, 3))
        e = tk.Entry(parent, textvariable=var, font=(F, 12), relief="flat", bg="#f6f7fb", fg=INK,
                     insertbackground=INK, highlightthickness=1, highlightbackground=LINE, highlightcolor=PRI)
        e.pack(fill="x", ipady=8)
        return e

    def build(self):
        # gradient header
        self.hdr = tk.Canvas(self, height=96, highlightthickness=0, bd=0)
        self.hdr.pack(fill="x")
        self.hdr.bind("<Configure>", self.draw_header)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=18)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ---- left: add form
        left = self.card(body, width=320, padx=22, pady=20)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 18))
        left.pack_propagate(False)
        tk.Label(left, text="Add transaction", bg=CARD, fg=INK, font=(F, 15, "bold")).pack(anchor="w")
        tk.Label(left, text="Record income or an expense", bg=CARD, fg=MUTE, font=(F, 9)).pack(anchor="w", pady=(0, 12))

        tg = tk.Frame(left, bg=CHIP)
        tg.pack(fill="x")
        self.tog = {}
        for k in ("Expense", "Income"):
            b = tk.Label(tg, text=k, font=(F, 10, "bold"), pady=8, cursor="hand2")
            b.pack(side="left", fill="x", expand=True, padx=3, pady=3)
            b.bind("<Button-1>", lambda e, k=k: self.set_kind(k))
            self.tog[k] = b

        self.field(left, "AMOUNT (" + CUR + ")", self.amount)
        tk.Label(left, text="CATEGORY  (tap to choose)", bg=CARD, fg=MUTE, font=(F, 9, "bold")).pack(anchor="w", pady=(12, 4))
        self.chips = tk.Frame(left, bg=CARD)
        self.chips.pack(fill="x")
        self.field(left, "NOTE (optional)", self.note)
        self.field(left, "DATE  (YYYY-MM-DD)", self.day)
        add = tk.Label(left, text="＋  Add transaction", bg=PRI, fg="white", font=(F, 11, "bold"),
                       pady=11, cursor="hand2")
        add.pack(fill="x", pady=(20, 0))
        add.bind("<Button-1>", lambda e: self.add())
        add.bind("<Enter>", lambda e: add.config(bg=PRI2))
        add.bind("<Leave>", lambda e: add.config(bg=PRI))

        # ---- right: stats, chart, table
        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        stats = tk.Frame(right, bg=BG)
        stats.grid(row=0, column=0, sticky="ew")
        self.vals = {}
        for i, (key, title, color) in enumerate([("balance", "Balance", PRI),
                                                 ("income", "Income", GREEN), ("expense", "Expenses", RED)]):
            c = self.card(stats)
            c.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 14, 0))
            stats.columnconfigure(i, weight=1, uniform="s")
            tk.Frame(c, bg=color, height=4).pack(fill="x")
            tk.Label(c, text=title, bg=CARD, fg=MUTE, font=(F, 10)).pack(anchor="w", padx=16, pady=(10, 0))
            self.vals[key] = tk.Label(c, text="", bg=CARD, fg=INK, font=(F, 20, "bold"))
            self.vals[key].pack(anchor="w", padx=16, pady=(0, 12))

        cc = self.card(right, padx=18, pady=12)
        cc.grid(row=1, column=0, sticky="ew", pady=14)
        tk.Label(cc, text="Spending by category", bg=CARD, fg=INK, font=(F, 12, "bold")).pack(anchor="w")
        self.chart = tk.Canvas(cc, height=130, bg=CARD, highlightthickness=0)
        self.chart.pack(fill="x", pady=(6, 0))
        self.chart.bind("<Configure>", lambda e: self.draw_chart())

        tc = self.card(right, padx=18, pady=12)
        tc.grid(row=2, column=0, sticky="nsew")
        head = tk.Frame(tc, bg=CARD)
        head.pack(fill="x", pady=(0, 8))
        tk.Label(head, text="Recent transactions", bg=CARD, fg=INK, font=(F, 12, "bold")).pack(side="left")
        d = tk.Label(head, text="🗑  Delete selected", bg="#fee2e2", fg=RED, font=(F, 9, "bold"),
                     padx=12, pady=5, cursor="hand2")
        d.pack(side="right")
        d.bind("<Button-1>", lambda e: self.delete())

        box = tk.Frame(tc, bg=CARD)
        box.pack(fill="both", expand=True)
        cols = ("day", "kind", "category", "note", "amount")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", selectmode="browse")
        for c, w in zip(cols, (100, 80, 130, 220, 120)):
            self.tree.heading(c, text=c.upper(), anchor="e" if c == "amount" else "w")
            self.tree.column(c, width=w, anchor="e" if c == "amount" else "w")
        self.tree.tag_configure("odd", background="#fafbff")
        self.tree.tag_configure("Income", foreground=GREEN)
        self.tree.tag_configure("Expense", foreground=RED)
        sb = ttk.Scrollbar(box, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.empty = tk.Label(box, text="No transactions yet\nAdd your first one using the form on the left",
                              bg=CARD, fg=MUTE, font=(F, 11), justify="center")

    def draw_header(self, e=None):
        w = self.hdr.winfo_width()
        self.hdr.delete("all")
        for x in range(0, w, 4):
            self.hdr.create_rectangle(x, 0, x + 4, 96, fill=mix(PRI, PRI2, x / max(w, 1)), outline="")
        self.hdr.create_text(30, 38, text="💰  FinTrack", anchor="w", fill="white", font=(F, 24, "bold"))
        self.hdr.create_text(32, 70, text="Personal Finance Tracker  •  " + date.today().strftime("%A, %d %B %Y"),
                             anchor="w", fill="#e0e0ff", font=(F, 10))
        self.hdr.create_text(w - 30, 48, text=f"📱 Open on phone: http://{lan_ip()}:{PORT}",
                             anchor="e", fill="white", font=(F, 10))

    # ---- behaviour
    def set_kind(self, k):
        self.kind.set(k)
        for name, b in self.tog.items():
            on = name == k
            b.config(bg=(GREEN if k == "Income" else RED) if on else CHIP, fg="white" if on else MUTE)
        for w in self.chips.winfo_children():
            w.destroy()
        names = categories()[k]
        self.cat.set(names[0])
        self.chip_lbls = {}
        for i, n in enumerate(names):
            l = tk.Label(self.chips, text=n, font=(F, 9), padx=4, pady=5, cursor="hand2")
            l.grid(row=i // 3, column=i % 3, sticky="ew", padx=2, pady=2)
            l.bind("<Button-1>", lambda e, n=n: self.pick(n))
            self.chip_lbls[n] = l
        for c in range(3):
            self.chips.columnconfigure(c, weight=1, uniform="c")
        self.pick(names[0])

    def pick(self, n):
        self.cat.set(n)
        for name, l in self.chip_lbls.items():
            l.config(bg=PRI if name == n else CHIP, fg="white" if name == n else INK)

    def add(self):
        try:
            add_tx(self.kind.get(), self.amount.get(), self.cat.get(), self.note.get(), self.day.get())
        except ValueError as e:
            return messagebox.showerror("Oops", str(e))
        self.amount.set("")
        self.note.set("")
        self.refresh()

    def delete(self):
        sel = self.tree.selection()
        if sel:
            db("DELETE FROM transactions WHERE id=?", (sel[0],))
            self.refresh()

    def refresh(self):
        self.data = d = snapshot()
        sel = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for i, t in enumerate(d["tx"]):
            sign = "+" if t["kind"] == "Income" else "-"
            self.tree.insert("", "end", iid=str(t["id"]),
                             tags=(t["kind"], "odd" if i % 2 else ""),
                             values=(t["day"], t["kind"], t["category"], t["note"],
                                     f"{sign}{CUR}{t['amount']:,.2f}"))
        if sel and self.tree.exists(sel[0]):
            self.tree.selection_set(sel[0])
        if d["tx"]:
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.5, anchor="center")
        for k in ("balance", "income", "expense"):
            self.vals[k].config(text=f"{CUR}{d[k]:,.2f}", fg=RED if k == "balance" and d[k] < 0 else INK)
        self.draw_chart()

    def draw_chart(self):
        c = self.chart
        c.delete("all")
        if not self.data:
            return
        tot = {}
        for t in self.data["tx"]:
            if t["kind"] == "Expense":
                tot[t["category"]] = tot.get(t["category"], 0) + t["amount"]
        rows = sorted(tot.items(), key=lambda x: -x[1])[:5]
        if not rows:
            c.create_text(10, 60, anchor="w", fill=MUTE, font=(F, 10),
                          text="Add an expense to see where your money goes")
            return
        w, top = max(c.winfo_width(), 300), rows[0][1]
        for i, (name, amt) in enumerate(rows):
            y = 8 + i * 24
            c.create_text(0, y + 9, text=name, anchor="w", fill=INK, font=(F, 9))
            span = w - 110 - 110
            c.create_rectangle(100, y + 2, 100 + span, y + 16, fill="#f0f1f8", outline="")
            c.create_rectangle(100, y + 2, 100 + max(6, span * amt / top), y + 16,
                               fill=BARS[i % len(BARS)], outline="")
            c.create_text(w, y + 9, text=f"{CUR}{amt:,.0f}", anchor="e", fill=MUTE, font=(F, 9, "bold"))

    def poll(self):  # picks up entries added from the phone
        self.refresh()
        self.after(3000, self.poll)

if __name__ == "__main__":
    init_db()
    start_web()
    App().mainloop()
