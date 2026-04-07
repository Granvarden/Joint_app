import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime, date, timedelta
from tkcalendar import Calendar

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard joint robot")
        
        try:
            self.root.state('zoomed')
        except:
            self.root.attributes('-zoomed', True)
            
        style = ttk.Style()
        style.theme_use('clam') 
        style.configure('TLabel', font=('Arial', 16))
        style.configure('TButton', font=('Arial', 18), padding=10) # ขยายปุ่มให้ใหญ่ขึ้น
        style.configure('TNotebook.Tab', font=('Arial', 16), padding=[15, 5])
        
        self.tab_data = {i: {'x': [], 'y': [], 'limit': None} for i in range(6)}
        self.current_date_var = tk.StringVar(value=date.today().strftime('%Y-%m-%d'))
        
        # --- สร้าง Frame หลัก ---
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # --- เพิ่ม Header ---
        header_label = tk.Label(self.main_frame, text="Sucking Voltage", font=('Arial', 24, 'bold'), fg='darkblue')
        header_label.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        # --- สร้าง Frame ย่อยสำหรับกราฟและฟอร์ม ---
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(expand=True, fill=tk.BOTH)

        # --- ส่วนแท็บกราฟ (ด้านซ้าย) ---
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 10))
        self.notebook.bind("<<NotebookTabChanged>>", self.check_existing_data)
        
        # --- ส่วนฟอร์มรับข้อมูล (ด้านขวา เรียงแนวตั้ง) ---
        self.form_frame = ttk.Frame(self.content_frame, width=300)
        self.form_frame.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        ttk.Label(self.form_frame, text="-- Management --", font=('Arial', 18, 'bold')).pack(anchor=tk.N, pady=(0, 10))
        
        self.cal_btn = ttk.Button(self.form_frame, text="📅 Open Calendar", command=self.open_calendar)
        self.cal_btn.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # ใช้ tk.Entry เพื่อให้ควบคุมขนาดฟอนต์และช่องให้ใหญ่ได้ง่ายขึ้น
        self.x_input = tk.Entry(self.form_frame, textvariable=self.current_date_var, state="readonly", justify='center', font=('Arial', 18))
        self.x_input.pack(fill=tk.X, padx=5, pady=(0, 15), ipady=5)
        
        ttk.Label(self.form_frame, text="Measurement:").pack(anchor=tk.W, padx=5)
        self.y_input = tk.Entry(self.form_frame, font=('Arial', 18), justify='center')
        self.y_input.pack(fill=tk.X, padx=5, pady=(0, 15), ipady=5)
        
        self.add_btn = ttk.Button(self.form_frame, text="Add measurement points", command=self.add_point)
        self.add_btn.pack(fill=tk.X, padx=5, pady=5)
        
        self.del_btn = ttk.Button(self.form_frame, text="Delete today's measurement points.", command=self.delete_point)
        self.del_btn.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Separator(self.form_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=20)
        
        ttk.Label(self.form_frame, text="-- Limit Line --", font=('Arial', 18, 'bold')).pack(anchor=tk.N, pady=(0, 10))
        
        ttk.Label(self.form_frame, text="Limit value (Y):").pack(anchor=tk.W, padx=5)
        self.limit_input = tk.Entry(self.form_frame, font=('Arial', 18), justify='center')
        self.limit_input.pack(fill=tk.X, padx=5, pady=(0, 10), ipady=5)
        
        self.limit_btn = ttk.Button(self.form_frame, text="Set limit", command=self.set_limit)
        self.limit_btn.pack(fill=tk.X, padx=5, pady=5)

        ttk.Separator(self.form_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=20)

        self.clear_btn = ttk.Button(self.form_frame, text="Clear graph on this page", command=self.clear_graph)
        self.clear_btn.pack(fill=tk.X, padx=5, pady=5)

        # --- สร้างกราฟ 6 แท็บ ---
        self.figures_list = []
        self.axes_list = []
        self.canvas_list = []
        
        for i in range(6):
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=f"JT.{i+1}")
            
            fig = Figure(figsize=(8, 6), dpi=100)
            fig.subplots_adjust(bottom=0.2, left=0.1) 
            ax = fig.add_subplot(111)
            
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            
            canvas.mpl_connect('pick_event', self.on_pick)
            
            self.figures_list.append(fig)
            self.axes_list.append(ax)
            self.canvas_list.append(canvas)
            
            self.update_graph(i)

    def get_selected_date(self):
        date_str = self.current_date_var.get()
        return datetime.strptime(date_str, '%Y-%m-%d').date()

    def open_calendar(self):
        top = tk.Toplevel(self.root)
        top.title("Select Date")
        
        window_width, window_height = 400, 350
        screen_width = top.winfo_screenwidth()
        screen_height = top.winfo_screenheight()
        x_cordinate = int((screen_width/2) - (window_width/2))
        y_cordinate = int((screen_height/2) - (window_height/2))
        top.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
        top.transient(self.root)
        top.grab_set()

        # ปิดการแสดงเลขสัปดาห์ด้วย showweeknumbers=False
        cal = Calendar(top, font="Arial 14", selectmode='day', 
                       date_pattern='yyyy-mm-dd', firstweekday='sunday',
                       showweeknumbers=False)
        cal.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        def confirm_date():
            self.current_date_var.set(cal.get_date())
            self.check_existing_data()
            top.destroy()
            
        ttk.Button(top, text="Confirm", command=confirm_date).pack(pady=(0, 20))

    def check_existing_data(self, event=None):
        try:
            current_tab = self.notebook.index(self.notebook.select())
        except:
            return 
            
        # ล้างและอัปเดตฟอร์มแกน Y ให้ตรงกับวันที่
        x_val = self.get_selected_date()
        tab_x = self.tab_data[current_tab]['x']
        tab_y = self.tab_data[current_tab]['y']
        
        self.y_input.delete(0, tk.END)
        if x_val in tab_x:
            idx = tab_x.index(x_val)
            self.y_input.insert(0, str(tab_y[idx]))

        # ล้างและอัปเดตฟอร์มเส้น Limit ให้ตรงกับแท็บปัจจุบัน
        self.limit_input.delete(0, tk.END)
        current_limit = self.tab_data[current_tab]['limit']
        if current_limit is not None:
            self.limit_input.insert(0, str(current_limit))

    def on_pick(self, event):
        current_tab = self.notebook.index(self.notebook.select())
        if event.mouseevent.inaxes != self.axes_list[current_tab]:
            return
            
        ind = event.ind[0]
        x_date = self.tab_data[current_tab]['x'][ind]
        y_old = self.tab_data[current_tab]['y'][ind]
        
        date_str = x_date.strftime('%d/%m/%Y')
        confirm = messagebox.askyesno("Confirm", 
                                      f"Do you want to modify the date value of {date_str}\n(the current value is: {y_old})?")
        
        if confirm:
            new_y = simpledialog.askfloat("Edit value.", 
                                          f"Fill new value for the date. {date_str}:", 
                                          initialvalue=y_old, 
                                          parent=self.root)
            if new_y is not None:
                self.tab_data[current_tab]['y'][ind] = new_y
                self.update_graph(current_tab)

    def add_point(self):
        x_val = self.get_selected_date()
        y_str = self.y_input.get().strip()
        
        try:
            y_val = float(y_str)
        except ValueError:
            messagebox.showerror("Data incorrect.", "value must be number.")
            return
            
        current_tab = self.notebook.index(self.notebook.select())
        tab_x = self.tab_data[current_tab]['x']
        tab_y = self.tab_data[current_tab]['y']
        
        if x_val in tab_x:
            messagebox.showwarning("Duplicate", "Data is available today. To edit, please click on a point on the graph.")
            return
        
        tab_x.append(x_val)
        tab_y.append(y_val)
        
        sorted_data = sorted(zip(tab_x, tab_y))
        if sorted_data:
            self.tab_data[current_tab]['x'] = [item[0] for item in sorted_data]
            self.tab_data[current_tab]['y'] = [item[1] for item in sorted_data]
        
        self.update_graph(current_tab)
        self.y_input.delete(0, tk.END)

    def delete_point(self):
        x_val = self.get_selected_date()
        current_tab = self.notebook.index(self.notebook.select())
        tab_x = self.tab_data[current_tab]['x']
        tab_y = self.tab_data[current_tab]['y']
        
        if x_val in tab_x:
            idx = tab_x.index(x_val)
            tab_x.pop(idx)
            tab_y.pop(idx)
            self.update_graph(current_tab)
            self.y_input.delete(0, tk.END)
            messagebox.showinfo("Successful", "Data has been successfully deleted.")
        else:
            messagebox.showinfo("Alert", "No data available for the selected date.")

    def set_limit(self):
        limit_str = self.limit_input.get().strip()
        current_tab = self.notebook.index(self.notebook.select())
        
        if not limit_str:
            self.tab_data[current_tab]['limit'] = None
        else:
            try:
                limit_val = float(limit_str)
                self.tab_data[current_tab]['limit'] = limit_val
            except ValueError:
                messagebox.showerror("Data incorrect.", "Limit value must be number.")
                return
                
        self.update_graph(current_tab)

    def clear_graph(self):
        current_tab = self.notebook.index(self.notebook.select())
        self.tab_data[current_tab]['x'] = []
        self.tab_data[current_tab]['y'] = []
        self.tab_data[current_tab]['limit'] = None
        self.limit_input.delete(0, tk.END)
        self.y_input.delete(0, tk.END)
        self.update_graph(current_tab)

    def update_graph(self, tab_index):
        ax = self.axes_list[tab_index]
        ax.clear()
        
        x_data = self.tab_data[tab_index]['x']
        y_data = self.tab_data[tab_index]['y']
        limit_val = self.tab_data[tab_index]['limit']
        
        # ถอดการกำหนดสเกลออก เพื่อให้แกน Y ยืดหยุ่นตามข้อมูลอัตโนมัติ
        # ax.set_ylim(5, 25) 
        
        if tab_index < 4:
            ax.set_ylabel("Voltage (V)", fontsize=20)
        else:
            ax.set_ylabel("Temperature (°C)", fontsize=20)
        
        if not x_data:
            today = date.today()
            ax.set_xlim(today - timedelta(days=1), today + timedelta(days=1))
        else:
            ax.plot(x_data, y_data, marker='o', markersize=8, linestyle='-', color='blue', 
                    linewidth=2, label="Measurement data", picker=5)
            
            ax.set_xticks(x_data)
            
            for i, txt in enumerate(y_data):
                ax.annotate(f"{txt:g}", (mdates.date2num(x_data[i]), y_data[i]), 
                            textcoords="offset points", xytext=(0, 10), ha='center', 
                            fontsize=14, fontweight='bold', color='black')
        
        if limit_val is not None:
            ax.axhline(y=limit_val, color='red', linestyle='--', linewidth=2, label=f"Limit line = {limit_val})")
            if x_data: 
                ax.legend(fontsize=14)
            
        ax.set_title(f"Record on page {tab_index+1}", fontsize=20)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.tick_params(axis='both', labelsize=14)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        for label in ax.get_xticklabels():
            label.set_rotation(45)
            
        self.figures_list[tab_index].autofmt_xdate()
        self.canvas_list[tab_index].draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()