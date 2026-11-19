<div align="center">

# 💰 FinTrack

**A simple personal finance tracker with a desktop app *and* a phone-friendly web view — in a single Python file.**

![Python](https://img.shields.io/badge/python-3.8%2B-4f46e5?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-16a34a)
![Database](https://img.shields.io/badge/database-SQLite-0ea5e9?logo=sqlite&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-tkinter-7c3aed)
![License](https://img.shields.io/badge/license-MIT-f59e0b)

<img src="docs/screenshots/desktop.png" alt="FinTrack desktop app" width="780">

</div>

---

## ✨ Features

- 🖥️ **Desktop app** built with `tkinter` — gradient header, summary cards, category chips and a clean transaction table
- 📱 **Built-in web view** — open the same data on your phone or another laptop over your Wi-Fi
- 🔄 **Live sync** — add an expense on your phone and it shows up on the desktop within seconds (and vice versa)
- 📊 **Spending by category** — a bar chart of your top 5 expense categories
- 💸 **Income & expense tracking** with a running balance
- 🌙 **Dark mode** support on the web view
- 🗄️ **SQLite storage** — one local `finance.db` file, created automatically, starts empty
- 📦 **Zero dependencies** — only the Python standard library
- 🇮🇳 Amounts shown in ₹ with Indian number formatting (easy to change)

## 📸 Screenshots

| Desktop | Phone / browser |
|:---:|:---:|
| <img src="docs/screenshots/desktop.png" width="480"> | <img src="docs/screenshots/mobile.png" width="200"> |

> 💡 Add your own screenshots to `docs/screenshots/` as `desktop.png` and `mobile.png`.

## 🚀 Quick start

**Requirements:** Python 3.8 or newer (tkinter is included with the standard Windows/macOS installers).

```bash
# 1. Clone the repository
git clone https://github.com/YOUR-USERNAME/fintrack.git
cd fintrack

# 2. Run it
python finance_tracker.py
```

That's it. The desktop window opens, `finance.db` is created on first launch, and the web server starts in the background.

> **Linux users:** if you get `No module named tkinter`, install it with
> `sudo apt install python3-tk` (Debian/Ubuntu) or `sudo dnf install python3-tkinter` (Fedora).

## 📱 Using it on your phone

1. Make sure your phone and computer are on the **same Wi-Fi network**.
2. Start the app — the header shows a link like `http://192.168.1.23:8000`.
3. Type that address into your phone's browser.
4. Tip: use **Add to Home Screen** to make it feel like a real app.

If it doesn't load, allow Python through your firewall (Windows Defender will usually prompt you the first time).

## 🧭 How to use

1. Pick **Expense** or **Income** at the top of the form.
2. Enter the **amount**, tap a **category**, add an optional **note**, and check the **date** (`YYYY-MM-DD`).
3. Click **＋ Add transaction**.
4. To remove an entry, select it in the table and click **🗑 Delete selected** (on the web view, tap ✕).

## 🏗️ How it works

```
┌────────────────────┐        ┌──────────────────┐        ┌─────────────────────┐
│  tkinter desktop   │ ─────▶ │                  │ ◀───── │  Web view (phone)   │
│  (main thread)     │        │  SQLite          │        │  ThreadingHTTPServer│
└────────────────────┘        │  finance.db      │        │  (background thread)│
                              └──────────────────┘        └─────────────────────┘
```

Both interfaces read and write the same SQLite file. The desktop app polls every 3 seconds and the web page every 5 seconds, so changes appear on both sides.

### REST endpoints

| Method | Path          | Description                                          |
|--------|---------------|------------------------------------------------------|
| GET    | `/`           | The web interface                                    |
| GET    | `/api/data`   | Balance, totals, categories, all transactions (JSON) |
| POST   | `/api/add`    | Add a transaction                                    |
| POST   | `/api/delete` | Delete a transaction by `id`                         |

### Project structure

```
fintrack/
├── finance_tracker.py   # the whole app: database, web server, GUI
├── requirements.txt     # (none needed)
├── docs/screenshots/    # images used in this README
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## ⚙️ Customising

All settings are at the top of `finance_tracker.py`:

```python
DB, PORT, CUR = "finance.db", 8000, "₹"   # database file, web port, currency symbol
CATS = {
    "Expense": ["Food", "Rent", "Transport", ...],
    "Income":  ["Salary", "Freelance", ...],
}
```

- Change `CUR` to `"$"`, `"€"`, `"£"`, etc. For the web view's number formatting, change `'en-IN'` in the page script too.
- Edit `CATS` to add your own categories (new ones are inserted into the database on next launch).
- Change `PORT` if `8000` is already in use.

## 🔒 Privacy & security notes

- Your data stays on **your machine** in `finance.db` — nothing is sent to the internet.
- `finance.db` is listed in `.gitignore` so you don't accidentally publish your finances.
- The web server listens on `0.0.0.0` and has **no password**, so anyone on your Wi-Fi network can view and edit your data while the app is running. Only run it on networks you trust. To make it desktop-only, change `"0.0.0.0"` to `"127.0.0.1"` in `start_web()`.

## 🗺️ Roadmap

- [ ] Edit existing transactions
- [ ] Monthly filter and summary
- [ ] Export to CSV
- [ ] Budget limits per category
- [ ] Optional password for the web view
- [ ] Custom categories from the UI

## 🤝 Contributing

Ideas and pull requests are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

Released under the [MIT License](LICENSE).

---

<div align="center">Made with ❤️ and Python</div>
