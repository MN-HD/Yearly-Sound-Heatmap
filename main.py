import tkinter as tk
from tkinter import messagebox
import datetime
import os
import platform
import subprocess
import json
import numpy as np
import soundfile as sf

class SoundHeatmapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yearly Sound Heatmap (Data-Driven)") 
        self.root.geometry("1100x750") 
        
        self.cols = 24
        self.rows = 52
        
        self.base_width = 32
        self.base_height = 20
        self.zoom = 1.0 
        
        self.margin_x = 50 
        self.margin_y = 30 
        
        self.audio_folder = "audio_files"
        self.cache_file = "sound_data_cache.json"
        
        # We now calculate min and max frequencies to scale the colors dynamically
        self.min_freq = float('inf')
        self.max_freq = float('-inf')
        
        self.sound_db = self.build_database()

        self.setup_ui()
        self.draw_grid()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(self.main_frame, text="Yearly Sound Heatmap (2026)", font=("Arial", 14, "bold"))
        title.pack(side=tk.TOP, pady=(0, 10))

        # --- Control Panel ---
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

        # --- Scrollable Canvas Container ---
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", 
                                xscrollcommand=self.h_scrollbar.set, 
                                yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scrollbar.config(command=self.canvas.yview)
        self.h_scrollbar.config(command=self.canvas.xview)
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel_vertical)
        self.canvas.bind("<Shift-MouseWheel>", self.on_mousewheel_horizontal)
        self.root.bind("<Control-MouseWheel>", self.on_zoom)
        self.root.bind("<Up>", self.pan_up)
        self.root.bind("<Down>", self.pan_down)
        self.root.bind("<Left>", self.pan_left)
        self.root.bind("<Right>", self.pan_right)

    def on_mousewheel_vertical(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_mousewheel_horizontal(self, event):
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")

    def on_zoom(self, event):
        if event.delta > 0:
            self.zoom *= 1.1 
        elif event.delta < 0:
            self.zoom /= 1.1 
            
        self.zoom = max(0.5, min(self.zoom, 3.0))
        self.canvas.delete("all")
        self.draw_grid()

    def pan_up(self, event): self.canvas.yview_scroll(-1, "units")
    def pan_down(self, event): self.canvas.yview_scroll(1, "units")
    def pan_left(self, event): self.canvas.xview_scroll(-1, "units")
    def pan_right(self, event): self.canvas.xview_scroll(1, "units")

    def get_data_driven_color(self, freq):
        """Generates color strictly based on the calculated audio frequency."""
        if self.max_freq == self.min_freq:
            return "#4CAF50" # Fallback green if all frequencies are identical
            
        # Create a strict scale from 0.0 (Lowest recorded freq) to 1.0 (Highest recorded freq)
        data_ratio = (freq - self.min_freq) / (self.max_freq - self.min_freq)
        
        r = int(data_ratio * 255)
        g = 0
        b = int((1.0 - data_ratio) * 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def draw_grid(self):
        self.rectangles = {}
        cw = self.base_width * self.zoom
        ch = self.base_height * self.zoom
        font_size = max(6, int(8 * self.zoom))
        
        for hour in range(self.cols):
            x = self.margin_x + (hour * cw) + (cw / 2)
            self.canvas.create_text(x, self.margin_y / 2, text=f"{hour}h", font=("Arial", font_size))

        for week in range(1, self.rows + 1):
            y = self.margin_y + ((week - 1) * ch) + (ch / 2)
            self.canvas.create_text(self.margin_x / 2, y, text=f"W{week}", font=("Arial", font_size))

        for week in range(1, self.rows + 1):
            for hour in range(self.cols):
                x1 = self.margin_x + (hour * cw)
                y1 = self.margin_y + ((week - 1) * ch)
                x2 = x1 + cw
                y2 = y1 + ch
                
                # Retrieve data and calculate color
                if (week, hour) in self.sound_db:
                    freq = self.sound_db[(week, hour)]['freq']
                    color = self.get_data_driven_color(freq)
                else:
                    color = "#F0F0F0" 
                
                rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#E0E0E0")
                self.rectangles[(week, hour)] = rect_id

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def on_canvas_click(self, event):
        cw = self.base_width * self.zoom
        ch = self.base_height * self.zoom
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        adjusted_x = canvas_x - self.margin_x
        adjusted_y = canvas_y - self.margin_y

        if adjusted_x < 0 or adjusted_y < 0:
            return

        hour = int(adjusted_x // cw)
        week = int(adjusted_y // ch) + 1
        
        if 0 <= hour < self.cols and 1 <= week <= self.rows:
            self.play_sound(week, hour)

    def execute_search(self):
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
            file_path = self.sound_db[(week, hour)]['path']
            freq = self.sound_db[(week, hour)]['freq']
            print(f"Triggering: {file_path} (Week {week}, Hour {hour}, {freq:.2f} Hz)")
            
            current_os = platform.system()
            audio_process = None
            
            try:
                if current_os == "Windows":
                    import winsound
                    winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                elif current_os == "Darwin":  
                    audio_process = subprocess.Popen(["afplay", file_path])
                elif current_os == "Linux":
                    audio_process = subprocess.Popen(["aplay", file_path])
            except Exception as e:
                print(f"Audio playback error: {e}")
                
            messagebox.showinfo("Sound Found", f"Time Slot: Week {week}, {hour}:00\nFrequency: {freq:.2f} Hz\nFile: {file_path}")
            
            try:
                if current_os == "Windows":
                    import winsound
                    winsound.PlaySound(None, winsound.SND_PURGE)
                else:
                    if audio_process is not None:
                        audio_process.terminate()
            except Exception as e:
                print(f"Could not stop audio: {e}")
                
        else:
            messagebox.showwarning("Empty Slot", f"No sound recorded for Week {week}, {hour}:00.")

    def analyze_audio_frequency(self, filepath):
        """Mathematically extracts the frequency from the physical soundwave."""
        try:
            data, samplerate = sf.read(filepath)
            # Ensure the audio is mono
            if len(data.shape) > 1:
                data = data[:, 0]
            
            # Count the zero-crossings to determine the pitch
            zero_crossings = np.where(np.diff(np.sign(data)))[0]
            if len(zero_crossings) < 2:
                return 0.0
                
            cycles = len(zero_crossings) / 2.0
            duration = len(data) / samplerate
            return cycles / duration
        except Exception:
            return 0.0

    def build_database(self):
        """Loads from cache if available, otherwise builds by analyzing audio files."""
        # 1. Try to load the fast cache first
        if os.path.exists(self.cache_file):
            print("Loading sound data from cache...")
            with open(self.cache_file, "r") as f:
                raw_cache = json.load(f)
                
            db = {}
            for key_str, data in raw_cache.items():
                week, hour = eval(key_str) # Convert string "(week, hour)" back to tuple
                db[(week, hour)] = data
                
                # Update global min/max for coloring
                freq = data['freq']
                if freq > 0:
                    self.min_freq = min(self.min_freq, freq)
                    self.max_freq = max(self.max_freq, freq)
            return db

        # 2. If no cache exists, do the heavy mathematical lifting
        db = {}
        if not os.path.exists(self.audio_folder):
            return db

        print("Analyzing acoustic data... This will take a moment, but only happens once!")
        files = os.listdir(self.audio_folder)
        
        for filename in files:
            if filename.startswith("audio_") and (filename.endswith(".wav") or filename.endswith(".mp3")):
                try:
                    clean_name = filename.replace("audio_", "").replace(".wav", "").replace(".mp3", "")
                    parts = clean_name.split("_")
                    
                    if len(parts) == 5:
                        year, month, day, hour = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                        date_obj = datetime.date(year, month, day)
                        week = date_obj.isocalendar()[1]
                        
                        filepath = os.path.join(self.audio_folder, filename)
                        
                        # Extract physical frequency data
                        freq = self.analyze_audio_frequency(filepath)
                        
                        db[(week, hour)] = {
                            'path': filepath,
                            'freq': freq
                        }
                        
                        if freq > 0:
                            self.min_freq = min(self.min_freq, freq)
                            self.max_freq = max(self.max_freq, freq)
                            
                except Exception:
                    continue

        # Save the heavy lifting to the cache file
        with open(self.cache_file, "w") as f:
            # JSON requires string keys, so we convert the tuple to a string
            json_friendly_db = {str(k): v for k, v in db.items()}
            json.dump(json_friendly_db, f)

        print("Acoustic analysis complete and cached!")
        return db

if __name__ == "__main__":
    root = tk.Tk()
    app = SoundHeatmapApp(root)
    root.mainloop()