import tkinter as tk
from tkinter import messagebox
import datetime
import winsound
import os

class SoundHeatmapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yearly Sound Heatmap")
        
        self.cols = 24
        self.rows = 52
        self.cell_width = 30
        self.cell_height = 15
        
        self.margin_x = 50 
        self.margin_y = 30 
        
        self.audio_folder = "audio_files"
        self.sound_db = self.build_database_from_folder()

        self.setup_ui()
        self.draw_grid()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(self.main_frame, text="Yearly Sound Heatmap (2026)", font=("Arial", 14, "bold"))
        title.pack(side=tk.TOP, pady=(0, 10))

        # --- NEW: Control Panel for Search ---
        # Placing it on the right side of the canvas to utilize the empty space
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=40, pady=50)
        
        search_label = tk.Label(self.control_frame, text="Search for a Time Slot", font=("Arial", 12, "bold"))
        search_label.pack(pady=(0, 15))
        
        tk.Label(self.control_frame, text="Week (1-52):").pack()
        self.search_week = tk.Spinbox(self.control_frame, from_=1, to=52, width=10)
        self.search_week.pack(pady=5)
        
        tk.Label(self.control_frame, text="Hour (0-23):").pack()
        self.search_hour = tk.Spinbox(self.control_frame, from_=0, to=23, width=10)
        self.search_hour.pack(pady=5)
        
        search_btn = tk.Button(self.control_frame, text="Search & Play", command=self.execute_search, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        search_btn.pack(pady=20)
        # ------------------------------------

        canvas_width = (self.cols * self.cell_width) + self.margin_x
        canvas_height = (self.rows * self.cell_height) + self.margin_y
        
        self.canvas = tk.Canvas(self.main_frame, width=canvas_width, height=canvas_height, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def draw_grid(self):
        self.rectangles = {}
        
        # X-Axis Labels
        for hour in range(self.cols):
            x = self.margin_x + (hour * self.cell_width) + (self.cell_width / 2)
            self.canvas.create_text(x, self.margin_y / 2, text=f"{hour}h", font=("Arial", 8))

        # Y-Axis Labels
        for week in range(1, self.rows + 1):
            y = self.margin_y + ((week - 1) * self.cell_height) + (self.cell_height / 2)
            self.canvas.create_text(self.margin_x / 2, y, text=f"W{week}", font=("Arial", 8))

        # Grid Rectangles
        for week in range(1, self.rows + 1):
            for hour in range(self.cols):
                x1 = self.margin_x + (hour * self.cell_width)
                y1 = self.margin_y + ((week - 1) * self.cell_height)
                x2 = x1 + self.cell_width
                y2 = y1 + self.cell_height
                
                if (week, hour) in self.sound_db:
                    color = "#4CAF50"  # Green
                else:
                    color = "#E0E0E0"  # Light Gray
                
                rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="white")
                self.rectangles[(week, hour)] = rect_id

    def on_canvas_click(self, event):
        adjusted_x = event.x - self.margin_x
        adjusted_y = event.y - self.margin_y

        if adjusted_x < 0 or adjusted_y < 0:
            return

        hour = adjusted_x // self.cell_width
        week = (adjusted_y // self.cell_height) + 1
        
        if 0 <= hour < self.cols and 1 <= week <= self.rows:
            self.play_sound(week, hour)

    def execute_search(self):
        """Fetches values from the Spinboxes and triggers the sound."""
        try:
            week = int(self.search_week.get())
            hour = int(self.search_hour.get())
            
            if 1 <= week <= self.rows and 0 <= hour < self.cols:
                self.play_sound(week, hour)
            else:
                messagebox.showerror("Invalid Input", "Please enter a valid week (1-52) and hour (0-23).")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter numbers only.")

    def play_sound(self, week, hour):
        if (week, hour) in self.sound_db:
            file_path = self.sound_db[(week, hour)]
            print(f"Triggering: {file_path} (Week {week}, Hour {hour})")
            
            try:
                winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass 
                
            messagebox.showinfo("Sound Found", f"Time Slot: Week {week}, {hour}:00\nFile: {file_path}")
        else:
            messagebox.showwarning("Empty Slot", f"No sound recorded for Week {week}, {hour}:00.")

    def build_database_from_folder(self):
        db = {}
        if not os.path.exists(self.audio_folder):
            return db

        for filename in os.listdir(self.audio_folder):
            if filename.startswith("audio_") and filename.endswith(".wav"):
                try:
                    clean_name = filename.replace("audio_", "").replace(".wav", "")
                    parts = clean_name.split("_")
                    
                    if len(parts) == 3:
                        date_str, hour_str = parts[0], parts[1]
                        day, month, hour = int(date_str[0:2]), int(date_str[2:4]), int(hour_str)
                        
                        date_obj = datetime.date(2026, month, day)
                        week = date_obj.isocalendar()[1]
                        
                        db[(week, hour)] = os.path.join(self.audio_folder, filename)
                except Exception:
                    continue
        return db

if __name__ == "__main__":
    root = tk.Tk()
    app = SoundHeatmapApp(root)
    root.mainloop()