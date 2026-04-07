import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import csv
import os
import sys
import sqlite3
import ctypes
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from datetime import datetime, date, timedelta
from tkcalendar import Calendar

def resource_path(relative_path):
    """ จัดการ Path สำหรับไฟล์ Resource เมื่อถูก Bundle เป็น EXE """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ตั้งค่า AppUserModelID สำหรับ Windows Taskbar Icon
try:
    myappid = 'mycompany.robotdashboard.monitor.v1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jointcore Tracker")
        
        # --- ตั้งค่าไอคอนหลัก ---
        self.icon_file = resource_path('logo.ico')
        if os.path.exists(self.icon_file):
            try:
                self.root.iconbitmap(self.icon_file)
            except:
                pass
            
        try:
            self.root.state('zoomed')
        except:
            try: self.root.attributes('-zoomed', True)
            except: pass
            
        style = ttk.Style()
        style.theme_use('clam') 
        style.configure('TLabel', font=('Arial', 16))
        style.configure('TButton', font=('Arial', 16), padding=8)
        style.configure('TNotebook.Tab', font=('Arial', 16), padding=[15, 5])
        
        self.setup_database()
        self.current_date_var = tk.StringVar(value=date.today().strftime('%d/%m/%Y'))
        
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        header_label = tk.Label(self.main_frame, text="Sucking Voltage", font=('Arial', 24, 'bold'), fg='darkblue')
        header_label.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(expand=True, fill=tk.BOTH)

        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 10))
        self.notebook.bind("<<NotebookTabChanged>>", self.check_existing_data)
        
        self.form_frame = ttk.Frame(self.content_frame, width=350)
        self.form_frame.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        ttk.Label(self.form_frame, text="-- Management --", font=('Arial', 18, 'bold')).pack(anchor=tk.N, pady=(0, 5))
        
        self.cal_btn = ttk.Button(self.form_frame, text="📅 Calendar", command=self.open_calendar)
        self.cal_btn.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.x_input = tk.Entry(self.form_frame, textvariable=self.current_date_var, state="readonly", justify='center', font=('Arial', 18))
        self.x_input.pack(fill=tk.X, padx=5, pady=(0, 10), ipady=3)
        
        ttk.Label(self.form_frame, text="Measurement (Y):").pack(anchor=tk.W, padx=5)
        self.y_input = tk.Entry(self.form_frame, font=('Arial', 18), justify='center')
        self.y_input.pack(fill=tk.X, padx=5, pady=(0, 10), ipady=3)
        
        btn_frame1 = ttk.Frame(self.form_frame)
        btn_frame1.pack(fill=tk.X, padx=5, pady=5)
        self.add_btn = ttk.Button(btn_frame1, text="Add", command=self.add_point)
        self.add_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        self.del_btn = ttk.Button(btn_frame1, text="Delete", command=self.delete_point)
        self.del_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))
        
        ttk.Separator(self.form_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(self.form_frame, text="-- Limit Line --", font=('Arial', 18, 'bold')).pack(anchor=tk.N, pady=(0, 5))
        
        ttk.Label(self.form_frame, text="Limit value:").pack(anchor=tk.W, padx=5)
        self.limit_input = tk.Entry(self.form_frame, font=('Arial', 18), justify='center')
        self.limit_input.pack(fill=tk.X, padx=5, pady=(0, 10), ipady=3)
        
        self.limit_btn = ttk.Button(self.form_frame, text="Set Limit", command=self.set_limit)
        self.limit_btn.pack(fill=tk.X, padx=5, pady=5)

        ttk.Separator(self.form_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=10)

        ttk.Label(self.form_frame, text="-- Actions --", font=('Arial', 18, 'bold')).pack(anchor=tk.N, pady=(0, 5))
        
        self.export_btn = ttk.Button(self.form_frame, text="Export CSV", command=self.export_csv)
        self.export_btn.pack(fill=tk.X, padx=5, pady=5)

        self.clear_btn = ttk.Button(self.form_frame, text="Clear Graph", command=self.clear_graph)
        self.clear_btn.pack(fill=tk.X, padx=5, pady=(50, 5))

        self.figures_list = []
        self.axes_list = []
        self.canvas_list = []
        
        for i in range(6):
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=f"JT.{i+1}")
            fig = Figure(figsize=(8, 6), dpi=100)
            fig.subplots_adjust(bottom=0.2, left=0.1, right=0.95, top=0.82) 
            ax = fig.add_subplot(111)
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            canvas.mpl_connect('pick_event', self.on_pick)
            self.figures_list.append(fig)
            self.axes_list.append(ax)
            self.canvas_list.append(canvas)
            self.update_graph(i)

    def setup_database(self):
        appdata_dir = os.getenv('APPDATA')
        self.db_dir = os.path.join(appdata_dir, 'DashboardJointRobot') if appdata_dir else os.path.join(os.path.expanduser('~'), '.DashboardJointRobot')
        if not os.path.exists(self.db_dir): os.makedirs(self.db_dir)
        self.db_path = os.path.join(self.db_dir, 'robot_data.db')
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS measurements (tab_index INTEGER, record_date TEXT, value REAL, UNIQUE(tab_index, record_date))''')
            c.execute('''CREATE TABLE IF NOT EXISTS limits (tab_index INTEGER PRIMARY KEY, limit_value REAL)''')
            conn.commit()
        self.tab_data = {i: {'x': [], 'y': [], 'limit': None} for i in range(6)}
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            for i in range(6):
                c.execute('SELECT limit_value FROM limits WHERE tab_index=?', (i,))
                limit_row = c.fetchone()
                if limit_row: self.tab_data[i]['limit'] = limit_row[0]
                c.execute('SELECT record_date, value FROM measurements WHERE tab_index=? ORDER BY record_date ASC', (i,))
                for row in c.fetchall():
                    self.tab_data[i]['x'].append(datetime.strptime(row[0], '%Y-%m-%d').date())
                    self.tab_data[i]['y'].append(row[1])

    def center_window(self, win):
        win.update_idletasks()
        width, height = win.winfo_reqwidth(), win.winfo_reqheight()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        win.geometry(f"+{x}+{y}")
        win.deiconify()

    def open_calendar(self):
        top = tk.Toplevel(self.root)
        top.withdraw() 
        
        if os.path.exists(self.icon_file):
            try: top.iconbitmap(self.icon_file)
            except: pass
            
        top.title("Select Date")
        
        cal = Calendar(top, font="Arial 16", selectmode='day', 
                       date_pattern='dd/mm/yyyy', firstweekday='sunday', 
                       showweeknumbers=False)
        cal.pack(padx=20, pady=(20, 10))
        
        def confirm_date():
            self.current_date_var.set(cal.get_date())
            self.check_existing_data()
            top.destroy()
            
        ttk.Button(top, text="Confirm", command=confirm_date).pack(pady=(0, 20))
        
        self.center_window(top)
        top.transient(self.root)
        top.grab_set() 
        top.focus_set()

    def check_existing_data(self, event=None):
        try: current_tab = self.notebook.index(self.notebook.select())
        except: return 
        try:
            x_val = datetime.strptime(self.current_date_var.get(), '%d/%m/%Y').date()
            tab_x, tab_y = self.tab_data[current_tab]['x'], self.tab_data[current_tab]['y']
            self.y_input.delete(0, tk.END)
            if x_val in tab_x: self.y_input.insert(0, str(tab_y[tab_x.index(x_val)]))
            self.limit_input.delete(0, tk.END)
            if self.tab_data[current_tab]['limit'] is not None: self.limit_input.insert(0, str(self.tab_data[current_tab]['limit']))
        except: pass

    def add_point(self):
        try:
            x_val = datetime.strptime(self.current_date_var.get(), '%d/%m/%Y').date()
            y_val = float(self.y_input.get().strip())
        except: return
        current_tab = self.notebook.index(self.notebook.select())
        if x_val in self.tab_data[current_tab]['x']: return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('INSERT OR REPLACE INTO measurements VALUES (?, ?, ?)', (current_tab, x_val.strftime('%Y-%m-%d'), y_val))
        self.tab_data[current_tab]['x'].append(x_val)
        self.tab_data[current_tab]['y'].append(y_val)
        sorted_data = sorted(zip(self.tab_data[current_tab]['x'], self.tab_data[current_tab]['y']))
        self.tab_data[current_tab]['x'], self.tab_data[current_tab]['y'] = [i[0] for i in sorted_data], [i[1] for i in sorted_data]
        self.update_graph(current_tab)
        self.y_input.delete(0, tk.END)

    def delete_point(self):
        try: x_val = datetime.strptime(self.current_date_var.get(), '%d/%m/%Y').date()
        except: return
        current_tab = self.notebook.index(self.notebook.select())
        if x_val in self.tab_data[current_tab]['x']:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM measurements WHERE tab_index=? AND record_date=?', (current_tab, x_val.strftime('%Y-%m-%d')))
            idx = self.tab_data[current_tab]['x'].index(x_val)
            self.tab_data[current_tab]['x'].pop(idx)
            self.tab_data[current_tab]['y'].pop(idx)
            self.update_graph(current_tab)
            self.y_input.delete(0, tk.END)

    def set_limit(self):
        try:
            val = float(self.limit_input.get().strip())
            current_tab = self.notebook.index(self.notebook.select())
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('INSERT OR REPLACE INTO limits VALUES (?, ?)', (current_tab, val))
            self.tab_data[current_tab]['limit'] = val
            self.update_graph(current_tab)
        except: pass

    def clear_graph(self):
        current_tab = self.notebook.index(self.notebook.select())
        dlg = tk.Toplevel(self.root)
        dlg.withdraw()
        if os.path.exists(self.icon_file):
            try: dlg.iconbitmap(self.icon_file)
            except: pass
        dlg.title("Confirm Clear Graph")
        bg_color = dlg.cget('bg')
        main_frame = tk.Frame(dlg, bg=bg_color)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)
        txt_frame = tk.Frame(main_frame, bg=bg_color)
        txt_frame.pack(pady=(0, 20))
        tk.Label(txt_frame, text="Are you sure you want to clear all data on ", font=('Arial', 16), bg=bg_color).pack(side=tk.LEFT)
        tk.Label(txt_frame, text=f"JT.{current_tab + 1}", font=('Arial', 16, 'bold'), fg='red', bg=bg_color).pack(side=tk.LEFT)
        tk.Label(txt_frame, text="?", font=('Arial', 16), bg=bg_color).pack(side=tk.LEFT)
        
        def on_yes():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM measurements WHERE tab_index=?', (current_tab,))
                conn.execute('DELETE FROM limits WHERE tab_index=?', (current_tab,))
            self.tab_data[current_tab] = {'x': [], 'y': [], 'limit': None}
            self.update_graph(current_tab)
            dlg.destroy()
        
        ttk.Button(main_frame, text="Yes", command=on_yes).pack(side=tk.LEFT, padx=10)
        ttk.Button(main_frame, text="No", command=dlg.destroy).pack(side=tk.LEFT, padx=10)
        self.center_window(dlg)
        dlg.transient(self.root)
        dlg.grab_set()

    def export_csv(self):
        current_tab = self.notebook.index(self.notebook.select())
        x_data, y_data = self.tab_data[current_tab]['x'], self.tab_data[current_tab]['y']
        limit_val = self.tab_data[current_tab]['limit']
        if not x_data: return
        
        # --- ตั้งชื่อไฟล์รอแบบ Export_JT.1_20260407.csv ---
        today_str = datetime.now().strftime('%Y%m%d')
        default_name = f"Export_JT.{current_tab + 1}_{today_str}.csv"
        
        file_path = filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=".csv", 
            filetypes=[("CSV", "*.csv")]
        )
        
        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Value", "Limit"])
                for i in range(len(x_data)):
                    writer.writerow([x_data[i].strftime('%d/%m/%Y'), y_data[i], limit_val if i == 0 else ""])

    def on_pick(self, event):
        """ แก้ไข Popup Edit ให้มีหน้าตาเหมือน Popup อื่นๆ """
        current_tab = self.notebook.index(self.notebook.select())
        ind = event.ind[0]
        x_date = self.tab_data[current_tab]['x'][ind]
        y_old = self.tab_data[current_tab]['y'][ind]

        # 1. สร้างหน้าต่าง Toplevel และตั้งค่า (เหมือน Popup อื่น)
        top = tk.Toplevel(self.root)
        top.withdraw() 
        if os.path.exists(self.icon_file):
            try: top.iconbitmap(self.icon_file)
            except: pass
        top.title("Edit Value")

        # 2. ส่วน Content (ใช้ Frame, Label, Entry)
        main_frame = ttk.Frame(top, padding=20)
        main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(main_frame, text=f"Edit for Date: {x_date.strftime('%d/%m/%Y')}", 
                  font=('Arial', 16, 'bold')).pack(pady=(0, 15))

        edit_label = ttk.Label(main_frame, text="Enter new value:")
        edit_label.pack(anchor=tk.W)

        edit_entry = tk.Entry(main_frame, font=('Arial', 18), justify='center')
        edit_entry.pack(fill=tk.X, pady=(5, 15), ipady=3)
        edit_entry.insert(0, str(y_old))
        edit_entry.focus_set()
        edit_entry.select_range(0, tk.END) # คลุมดำข้อความเดิมไว้ให้

        # 3. ส่วนปุ่มกด
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        def confirm_edit():
            try:
                new_y = float(edit_entry.get().strip())
                
                # อัปเดต Database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('UPDATE measurements SET value=? WHERE tab_index=? AND record_date=?', 
                                (new_y, current_tab, x_date.strftime('%Y-%m-%d')))
                
                # อัปเดต Local Data
                self.tab_data[current_tab]['y'][ind] = new_y
                
                # อัปเดต Graph
                self.update_graph(current_tab)
                
                # ปิด Popup
                top.destroy()
            except ValueError:
                # กรณีผู้ใช้กรอกข้อมูลไม่ใช่ตัวเลข
                messagebox.showerror("Error", "Invalid input. Please enter a number.", parent=top)

        ttk.Button(btn_frame, text="Save", command=confirm_edit).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        ttk.Button(btn_frame, text="Cancel", command=top.destroy).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

        # กด Enter เพื่อยืนยันได้เลย
        edit_entry.bind('<Return>', lambda e: confirm_edit())

        # 4. จัดตำแหน่ง modal (เหมือน Popup อื่น)
        self.center_window(top)
        top.transient(self.root)
        top.grab_set() 

    def update_graph(self, tab_index):
        ax = self.axes_list[tab_index]
        ax.clear()
        x_data, y_data, limit_val = self.tab_data[tab_index]['x'], self.tab_data[tab_index]['y'], self.tab_data[tab_index]['limit']
        ax.set_ylabel("Voltage (V)" if tab_index < 4 else "Temperature (°C)", fontsize=20)
        if not x_data:
            ax.set_xlim(date.today() - timedelta(days=1), date.today() + timedelta(days=1))
        else:
            ax.plot(x_data, y_data, marker='o', color='blue', linewidth=2, picker=5)
            ax.set_xticks(x_data)
            for i, txt in enumerate(y_data):
                ax.annotate(f"{txt:g}", (mdates.date2num(x_data[i]), y_data[i]), xytext=(0, 10), textcoords="offset points", ha='center', fontsize=12, fontweight='bold')
        
        limit_label = f"Limit = {limit_val}" if limit_val else "Limit"
        if limit_val is not None: ax.axhline(y=limit_val, color='red', linestyle='--', linewidth=2)
        
        ax.set_title(f"Record on JT.{tab_index+1}", fontsize=20, loc='left', pad=15)
        custom_lines = [Line2D([0], [0], color='blue', marker='o', label="Measurement data"), 
                        Line2D([0], [0], color='red', linestyle='--', label=limit_label)]
        ax.legend(handles=custom_lines, fontsize=14, loc='lower right', bbox_to_anchor=(1.0, 1.02))
        
        ax.grid(True, linestyle='--')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        for label in ax.get_xticklabels(): label.set_rotation(45)
        self.canvas_list[tab_index].draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()