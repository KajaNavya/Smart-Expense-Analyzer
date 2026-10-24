import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from tkcalendar import DateEntry
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import datetime

# ---------------- DATABASE SETUP ----------------

conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, salary REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, category TEXT, amount REAL, description TEXT)")
conn.commit()

# ---------------- CONFIGURATION ----------------

EXPANDED_CATEGORIES = [
    "Rent", "EMI", "Groceries", "Food Delivery", "Dining Out",
    "Transport", "Fuel", "Electricity", "Water Bill", "Internet",
    "Mobile Recharge", "Subscriptions", "Shopping", "Clothes", 
    "Health", "Medicines", "Insurance", "Education", "Books",
    "Entertainment", "Travel", "Gifts", "Charity", "Maintenance", 
    "Repairs", "Savings", "Investment", "Tax", "Bills", "Other"
]

# ---------------- MAIN APPLICATION ----------------

class ExpenseAnalyzer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Smart Expense Analyzer")
        self.geometry("800x650")
        self.active_user = None
        self.switch_login()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def switch_login(self):
        self.clear()
        LoginPage(self)

    def switch_signup(self):
        self.clear()
        SignupPage(self)

    def switch_home(self):
        self.clear()
        HomePage(self)

# ---------------- AUTHENTICATION ----------------

class LoginPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.pack(pady=50)
        tk.Label(self, text="User Login", font=("Arial", 22, "bold")).pack(pady=20)
        tk.Label(self, text="Username").pack()
        self.user = tk.Entry(self, font=("Arial", 12)); self.user.pack(pady=5)
        tk.Label(self, text="Password").pack()
        
        self.pw = tk.Entry(self, show="*", font=("Arial", 12))
        self.pw.pack(pady=5)

        self.var = tk.IntVar()
        self.cb = tk.Checkbutton(self, text="Show Password", variable=self.var, command=self.toggle_pw)
        self.cb.pack()

        tk.Button(self, text="Login", width=15, bg="#4CAF50", fg="white", command=self.login).pack(pady=15)
        tk.Button(self, text="New User? Signup", command=self.parent.switch_signup, relief="flat").pack()

    def toggle_pw(self):
        self.pw.config(show="" if self.var.get() == 1 else "*")

    def login(self):
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (self.user.get(), self.pw.get()))
        user = cursor.fetchone()
        if user:
            self.parent.active_user = user[0]
            self.parent.switch_home()
        else:
            messagebox.showerror("Error", "Invalid Credentials")

class SignupPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.pack(pady=50)
        tk.Label(self, text="Create Account", font=("Arial", 22, "bold")).pack(pady=20)
        tk.Label(self, text="Username").pack()
        self.u = tk.Entry(self); self.u.pack(pady=2)
        tk.Label(self, text="Password").pack()
        self.p = tk.Entry(self, show="*"); self.p.pack(pady=2)
        tk.Label(self, text="Monthly Salary").pack()
        self.s = tk.Entry(self); self.s.pack(pady=2)
        tk.Button(self, text="Register", bg="#2196F3", fg="white", command=self.signup).pack(pady=15)
        tk.Button(self, text="Back to Login", command=self.parent.switch_login).pack()

    def signup(self):
        try:
            cursor.execute("INSERT INTO users(username,password,salary) VALUES(?,?,?)", 
                           (self.u.get(), self.p.get(), float(self.s.get())))
            conn.commit()
            messagebox.showinfo("Success", "Account created!")
            self.parent.switch_login()
        except: messagebox.showerror("Error", "Registration failed.")

# ---------------- HOME DASHBOARD ----------------

class HomePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.pack(pady=20, fill="both", expand=True)
        tk.Label(self, text="Expense Dashboard", font=("Arial", 24, "bold")).pack(pady=10)
        self.summary = tk.Label(self, font=("Arial", 14), fg="#333"); self.summary.pack(pady=5)
        
        tk.Button(self, text="Edit Salary", font=("Arial", 9), command=self.edit_salary_window, relief="flat", fg="blue").pack()
        
        self.topcat = tk.Label(self, font=("Arial", 11, "italic"), fg="blue"); self.topcat.pack(pady=5)
        self.update_summary()
        self.check_budget_alerts()

        btn_grid = tk.Frame(self)
        btn_grid.pack(pady=20)
        
        menu_items = [
            ("Add New Expense", self.add),
            ("View & Edit Expenses", self.view),
            ("Visual Statistics", self.stats),
            ("Monthly Report", self.report),
            ("Predict Next Month", self.predict),
            ("AI Smart Advisor", self.smart_advisor), 
            ("Export to Excel", self.export)
        ]
        for text, cmd in menu_items:
            color = "#673AB7" if "AI" in text else "SystemButtonFace"
            fg_color = "white" if "AI" in text else "black"
            tk.Button(btn_grid, text=text, width=25, bg=color, fg=fg_color, font=("Arial", 10), command=cmd).pack(pady=5)
        
        tk.Button(self, text="Logout", fg="red", command=self.parent.switch_login, relief="flat").pack(pady=20)

    def update_summary(self):
        uid = self.parent.active_user
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id=?", (uid,))
        total = cursor.fetchone()[0] or 0
        cursor.execute("SELECT salary FROM users WHERE id=?", (uid,))
        salary = cursor.fetchone()[0]
        self.summary.config(text=f"Total: ₹{total} | Salary: ₹{salary} | Balance: ₹{max(0, salary-total)}")
        cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id=? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1", (uid,))
        top = cursor.fetchone()
        if top: self.topcat.config(text=f"Highest Spend: {top[0]} (₹{top[1]})")

    def check_budget_alerts(self):
        uid = self.parent.active_user
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id=?", (uid,))
        total = cursor.fetchone()[0] or 0
        cursor.execute("SELECT salary FROM users WHERE id=?", (uid,))
        salary = cursor.fetchone()[0]
        if total > (0.7 * salary):
            messagebox.showwarning("Budget Alert", f"Warning: Spent ₹{total} ({round((total/salary)*100)}% of salary)!")

    def add(self): AddExpense(self)
    def view(self): ViewExpenses(self)
    def stats(self): Statistics(self)
    def report(self): MonthlyReport(self)
    def edit_salary_window(self): EditSalary(self)
    
    def export(self):
        uid = self.parent.active_user
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="My_Expenses.xlsx")
        if file_path:
            try:
                df = pd.read_sql_query(f"SELECT date, category, amount, description FROM expenses WHERE user_id={uid}", conn)
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", f"Saved to: {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed: {e}")

    def predict(self):
        uid = self.parent.active_user
        cursor.execute("SELECT strftime('%m',date), SUM(amount) FROM expenses WHERE user_id=? GROUP BY strftime('%m',date)", (uid,))
        data = cursor.fetchall()
        if len(data) < 2:
            messagebox.showinfo("AI", "Need more data to predict.")
            return
        months = np.array([int(d[0]) for d in data]).reshape(-1, 1)
        values = np.array([d[1] for d in data])
        model = LinearRegression().fit(months, values)
        pred = model.predict([[max(months)[0] + 1]])
        messagebox.showinfo("AI Prediction", f"Estimated next month: ₹{round(pred[0], 2)}")

    def smart_advisor(self):
        uid = self.parent.active_user
        cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id=? GROUP BY category", (uid,))
        data = cursor.fetchall()
        if not data:
            messagebox.showinfo("AI Advisor", "No data to analyze yet.")
            return

        total_spent = sum([d[1] for d in data])
        advice = []
        
        for cat, amt in data:
            percent = (amt / total_spent) * 100
            if percent > 15 and cat not in ["Rent", "EMI"]:
                reduce_amt = round(amt * 0.4) 
                advice.append(f"• You're spending too much on '{cat}' (₹{amt}).\n  You MUST reduce this by ₹{reduce_amt} to improve your savings!")

        if not advice:
            final_msg = "Your spending is currently under control, but keep an eye on those 'Other' expenses!"
            messagebox.showinfo("AI Smart Advisor", f"--- Savings Intervention ---\n\n{final_msg}")
        else:
            final_msg = "\n\n".join(advice)
            messagebox.showwarning("AI Smart Advisor", f"--- Savings Intervention ---\n\n{final_msg}")

# ---------------- SUPPORTING CLASSES ----------------

class EditSalary(tk.Toplevel):
    def __init__(self, home_page):
        super().__init__(home_page)
        self.home = home_page
        self.title("Update Salary")
        self.geometry("250x150")
        tk.Label(self, text="New Salary:").pack(pady=10)
        self.salary_entry = tk.Entry(self); self.salary_entry.pack(pady=5)
        tk.Button(self, text="Update", bg="#4CAF50", fg="white", command=self.update).pack(pady=10)

    def update(self):
        try:
            new_salary = float(self.salary_entry.get())
            cursor.execute("UPDATE users SET salary=? WHERE id=?", (new_salary, self.home.parent.active_user))
            conn.commit(); self.home.update_summary(); self.destroy()
        except: messagebox.showerror("Error", "Enter a valid number.")

class MonthlyReport(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent; self.title("Monthly Report"); self.geometry("350x450")
        f = tk.Frame(self); f.pack(pady=10)
        self.m = ttk.Combobox(f, width=5, values=[f"{i:02d}" for i in range(1,13)])
        self.m.set(datetime.now().strftime("%m")); self.m.pack(side="left", padx=5)
        self.y = ttk.Combobox(f, width=8, values=[str(i) for i in range(2023, 2031)])
        self.y.set(datetime.now().strftime("%Y")); self.y.pack(side="left", padx=5)
        tk.Button(self, text="Show Report", bg="#2196F3", fg="white", command=self.show).pack(pady=10)
        self.res = tk.Label(self, text="", justify="left", font=("Arial", 10)); self.res.pack(pady=10)

    def show(self):
        uid = self.parent.parent.active_user
        cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id=? AND strftime('%m', date)=? AND strftime('%Y', date)=? GROUP BY category", (uid, self.m.get(), self.y.get()))
        data = cursor.fetchall()
        if not data:
            self.res.config(text="No expenses found.")
            return
        txt = f"Summary for {self.m.get()}/{self.y.get()}:\n" + "-"*30 + "\n"
        for c, a in data: txt += f"• {c}: ₹{a}\n"
        txt += f"\nTotal: ₹{sum(d[1] for d in data)}"
        self.res.config(text=txt)

class ViewExpenses(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent); self.parent = parent; self.title("Manage Expenses"); self.geometry("850x500")
        cols = ("ID", "Date", "Category", "Amount", "Description")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c); self.tree.column(c, width=120)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Edit Selected", bg="#FFC107", width=15, command=self.edit_selected).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Delete Selected", bg="#F44336", fg="white", width=15, command=self.delete_selected).pack(side="left", padx=10)
        
        self.load()

    def load(self):
        self.tree.delete(*self.tree.get_children())
        cursor.execute("SELECT id, date, category, amount, description FROM expenses WHERE user_id=?", (self.parent.parent.active_user,))
        for r in cursor.fetchall(): self.tree.insert("", tk.END, values=r)

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to delete.")
            return
        if messagebox.askyesno("Confirm", "Delete this expense?"):
            item_id = self.tree.item(selected[0])['values'][0]
            cursor.execute("DELETE FROM expenses WHERE id=?", (item_id,))
            conn.commit()
            self.load()
            self.parent.update_summary()

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to edit.")
            return
        data = self.tree.item(selected[0])['values']
        EditExpenseWindow(self, data)

class EditExpenseWindow(tk.Toplevel):
    def __init__(self, parent_view, data):
        super().__init__(parent_view); self.parent_view = parent_view; self.exp_id = data[0]
        self.title("Edit Expense"); self.geometry("300x400")
        
        tk.Label(self, text="Date").pack(pady=5)
        self.dt = DateEntry(self); self.dt.set_date(datetime.strptime(data[1], "%Y-%m-%d")); self.dt.pack()
        
        tk.Label(self, text="Category").pack(pady=5)
        self.cat = ttk.Combobox(self, values=EXPANDED_CATEGORIES); self.cat.set(data[2]); self.cat.pack()
        
        tk.Label(self, text="Amount").pack(pady=5)
        self.amt = tk.Entry(self); self.amt.insert(0, data[3]); self.amt.pack()
        
        tk.Label(self, text="Description").pack(pady=5)
        self.ds = tk.Entry(self); self.ds.insert(0, data[4]); self.ds.pack()
        
        tk.Button(self, text="Update Expense", bg="#4CAF50", fg="white", command=self.update).pack(pady=20)

    def update(self):
        try:
            cursor.execute("UPDATE expenses SET date=?, category=?, amount=?, description=? WHERE id=?",
                           (self.dt.get_date().strftime("%Y-%m-%d"), self.cat.get(), float(self.amt.get()), self.ds.get(), self.exp_id))
            conn.commit()
            self.parent_view.load()
            self.parent_view.parent.update_summary()
            self.destroy()
            messagebox.showinfo("Success", "Expense updated!")
        except:
            messagebox.showerror("Error", "Invalid inputs. Check amount.")

class AddExpense(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent); self.parent = parent; self.title("Add Expense"); self.geometry("300x350")
        tk.Label(self, text="Date").pack()
        self.dt = DateEntry(self); self.dt.pack()
        tk.Label(self, text="Category").pack()
        self.cat = ttk.Combobox(self, values=EXPANDED_CATEGORIES); self.cat.pack()
        tk.Label(self, text="Amount").pack()
        self.amt = tk.Entry(self); self.amt.pack()
        tk.Label(self, text="Description").pack()
        self.ds = tk.Entry(self); self.ds.pack()
        tk.Button(self, text="Save", bg="#4CAF50", fg="white", command=self.save).pack(pady=15)

    def save(self):
        try:
            uid = self.parent.parent.active_user
            cursor.execute("INSERT INTO expenses(user_id,date,category,amount,description) VALUES(?,?,?,?,?)", (uid, self.dt.get_date().strftime("%Y-%m-%d"), self.cat.get(), float(self.amt.get()), self.ds.get()))
            conn.commit(); self.parent.update_summary(); self.destroy()
        except: messagebox.showerror("Error", "Check inputs.")

class Statistics(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent); self.parent = parent; self.title("Analytics")
        tk.Button(self, text="Pie Chart Breakdown", width=25, bg="#2196F3", fg="white", command=self.pie).pack(pady=10, padx=20)
        tk.Button(self, text="Bar Chart Comparison", width=25, bg="#4CAF50", fg="white", command=self.bar).pack(pady=10, padx=20)

    def pie(self):
        cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id=? GROUP BY category", (self.parent.parent.active_user,))
        d = cursor.fetchall()
        if d:
            plt.figure("Category Breakdown")
            plt.pie([x[1] for x in d], labels=[x[0] for x in d], autopct="%1.1f%%")
            plt.show()

    def bar(self):
        cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id=? GROUP BY category", (self.parent.parent.active_user,))
        d = cursor.fetchall()
        if d:
            plt.figure("Spending Comparison")
            categories = [x[0] for x in d]
            amounts = [x[1] for x in d]
            plt.bar(categories, amounts, color='skyblue')
            plt.xticks(rotation=45)
            plt.ylabel("Amount (₹)")
            plt.tight_layout()
            plt.show()

if __name__ == "__main__":
    app = ExpenseAnalyzer()
    app.mainloop()