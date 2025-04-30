import json, requests, time, os, threading, re, webbrowser, keyboard, pyautogui, autoit, psutil, locale
import traceback
import pygetwindow as gw
from recorder_main import BGSI_Recorder
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from datetime import datetime
import ttkbootstrap as ttk
     
class SnippingWidget:
    def __init__(self, root, config_key=None, callback=None):
        self.root = root
        self.config_key = config_key
        self.callback = callback
        self.snipping_window = None
        self.begin_x = None
        self.begin_y = None
        self.end_x = None
        self.end_y = None

    def start(self):
        self.snipping_window = ttk.Toplevel(self.root)
        self.snipping_window.attributes('-fullscreen', True)
        self.snipping_window.attributes('-alpha', 0.3)
        self.snipping_window.configure(bg="lightblue")
        
        self.snipping_window.bind("<Button-1>", self.on_mouse_press)
        self.snipping_window.bind("<B1-Motion>", self.on_mouse_drag)
        self.snipping_window.bind("<ButtonRelease-1>", self.on_mouse_release)

        self.canvas = ttk.Canvas(self.snipping_window, bg="lightblue", highlightthickness=0)
        self.canvas.pack(fill=ttk.BOTH, expand=True)
        
    # hi im tea (ffffffffff)
    
    def on_mouse_press(self, event):
        self.begin_x = event.x
        self.begin_y = event.y
        self.canvas.delete("selection_rect")

    def on_mouse_drag(self, event):
        self.end_x, self.end_y = event.x, event.y
        self.canvas.delete("selection_rect")
        self.canvas.create_rectangle(self.begin_x, self.begin_y, self.end_x, self.end_y,
                                      outline="white", width=2, tag="selection_rect")

    def on_mouse_release(self, event):
        self.end_x = event.x
        self.end_y = event.y

        x1, y1 = min(self.begin_x, self.end_x), min(self.begin_y, self.end_y)
        x2, y2 = max(self.begin_x, self.end_x), max(self.begin_y, self.end_y)

        self.capture_region(x1, y1, x2, y2)
        self.snipping_window.destroy()

    def capture_region(self, x1, y1, x2, y2):
        if self.config_key:
            region = [x1, y1, x2 - x1, y2 - y1]
            print(f"Region for '{self.config_key}' set to {region}")
            
            if self.callback:
                self.callback(region)
                
class BGSI_Main():
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            locale.setlocale(locale.LC_ALL, '')
            
        self.logs_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Roblox', 'logs')
        self.macro_paths_directory = os.path.join(os.getcwd(), "macro_paths")
        os.makedirs(self.macro_paths_directory, exist_ok=True)
        
        self.config = self.load_config()
        self.recorder = BGSI_Recorder()
        
        self.start_time = None
        self.last_position = 0
        self.detection_running = False
        self.lock = threading.Lock()
        
        self.last_bubble_sell_time = time.time()
        self.last_alien_shop_buy_time = time.time()
        self.last_chest_collect_time = time.time()
        self.last_daily_quest_time = time.time()
        
        self.last_anti_afk_time = time.time()
        self.anti_afk_interval = 180
        
        self.last_royal_rift_log = None
        self.last_aura_egg_log = None
        self.last_silly_rift_log = None
        self.last_egg_hatch_log = None
        self.init_gui()
        
       
    def error_logging(self, exception, custom_message=None, max_log_size=2 * 1024 * 1024):
        log_file = "error_logs.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = traceback.format_exc()

        if not os.path.exists(log_file):
            with open(log_file, "w") as log:
                log.write("Error Log File Created\n")
                log.write("-" * 40 + "\n")

        if os.path.exists(log_file) and os.path.getsize(log_file) > max_log_size:
            with open(log_file, "r") as log:
                lines = log.readlines()
            with open(log_file, "w") as log:
                log.writelines(lines[-1000:])

        with open(log_file, "a") as log:
            log.write(f"\n[{timestamp}] ERROR LOG\n")
            log.write(f"Error Type: {error_type}\n")
            log.write(f"Error Message: {error_message}\n")
            if custom_message:
                log.write(f"Custom Message: {custom_message}\n")
            log.write(f"Traceback:\n{stack_trace}\n")
            log.write("-" * 40 + "\n")

        print(f"Error logged to {log_file}.")
                
    def save_config(self):
        try:
            with open("config.json", "r") as file:
                config = json.load(file)
        except FileNotFoundError:
            config = {}

        config.update({
            "dont_ask_for_update": self.config.get("dont_ask_for_update", False),
            "webhook_url": self.webhook_url_entry.get(),
            "private_server_link": self.private_server_link_entry.get(),
            "ps_link_type": self.ps_type_var.get(),
            "discord_user_id": self.discord_user_id_entry.get(),
            "farming_world": self.farming_world_var.get(), 
            "enable_farming": self.enable_farming_var.get(),
            "auto_bubble_sell": self.auto_bubble_sell_var.get(),  
            "auto_bubble_sell_minutes": self.auto_sell_minutes_var.get(),  
            "royal_chest_alert": self.royal_chest_alert_var.get(),
            "royal_chest_alert_value": self.royal_chest_alert_value_var.get(),
            "egg_hatching_detection": self.egg_hatching_detection_var.get(),  
            "aura_egg_alert": self.aura_egg_alert_var.get(),
            "silly_egg_alert": self.silly_egg_alert_var.get(), 
            "roblox_username": self.roblox_username_var.get(),  
            "world_mapicon": self.config.get("world_mapicon", [0, 0]),
            "zen_mapicon": self.config.get("zen_mapicon", [0, 0]),
            "overworld_mapicon": self.config.get("overworld_mapicon", [0, 0]),
            "world_teleport_button": self.config.get("world_teleport_button", [0, 0]),
            "anti_afk": self.anti_afk_var.get(),
            "ignore_cam_align": self.ignore_cam_align_var.get(),
            "auto_buy_alien_stock":  self.auto_buy_alien_stock_var.get(),
            "auto_buy_alien_stock_minutes": self.auto_alien_buy_minutes_var.get(),
            "auto_claim_chest": self.auto_claim_chest_var.get(),
            "auto_claim_chest_minutes": self.auto_claim_chest_minutes_var.get(),
            "auto_daily_quest": self.auto_daily_quest_var.get(),
            "auto_daily_quest_minutes": self.auto_daily_quest_minutes_var.get(),
            "dailyquest_mapicon": self.config.get("dailyquest_mapicon", [51, 429]),
            "alien_gembutton1": self.config.get("alien_gembutton1", [772, 649]),
            "alien_gembutton2": self.config.get("alien_gembutton2", [957, 651]),
            "alien_gembutton3": self.config.get("alien_gembutton3", [1134, 649]),
            "float_chest_collect_button": self.config.get("float_chest_collect_button", [1082, 214]),
            "void_chest_collect_button": self.config.get("void_chest_collect_button", [830, 878]),
            "daily_gift_skip_button": self.config.get("daily_gift_skip_button", [962, 616]),
            "daily_gift_box_1": self.config.get("daily_gift_box_1", [663, 427]),
            "daily_gift_box_2": self.config.get("daily_gift_box_2", [788, 431]),
            "daily_gift_box_3": self.config.get("daily_gift_box_3", [904, 436]),
            "daily_gift_box_4": self.config.get("daily_gift_box_4", [1018, 437]),
            "daily_gift_box_5": self.config.get("daily_gift_box_5", [716, 554]),
            "daily_gift_box_6": self.config.get("daily_gift_box_6", [844, 565]),
            "daily_gift_box_7": self.config.get("daily_gift_box_7", [975, 564]),
            "daily_gift_box_8": self.config.get("daily_gift_box_8", [747, 704]),
            "daily_gift_box_9": self.config.get("daily_gift_box_9", [997, 725])
        })


        with open("config.json", "w") as file:
            json.dump(config, file, indent=4)

        self.config = config

    def load_config(self):
        try:
            config_paths = [
                "config.json",
                "source_code/config.json",
                os.path.join(os.path.dirname(__file__), "config.json"),
                os.path.join(os.path.dirname(__file__), "source_code/config.json")
            ]
            
            for path in config_paths:
                if os.path.exists(path):
                    with open(path, "r") as file:
                        config = json.load(file)
                        return config
        
        except Exception as e:
                self.error_logging(e, "Error at loading config.json. Try adding empty: '{}' into config.json to fix this error!")
    
    def import_config(self):
        try:
            file_path = filedialog.askopenfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                title="Select CONFIG.JSON please!"
            )
            
            if not file_path: return
            with open(file_path, "r") as file:
                config = json.load(file)
            
            self.config = config
            
            # Update GUI elements with imported config values
            self.webhook_url_entry.delete(0, 'end')
            self.webhook_url_entry.insert(0, config.get("webhook_url", ""))
            self.private_server_link_entry.delete(0, 'end')
            self.private_server_link_entry.insert(0, config.get("private_server_link", ""))
            self.ps_type_var.set(config.get("ps_link_type", "Public"))
            self.discord_user_id_entry.delete(0, 'end')
            self.discord_user_id_entry.insert(0, config.get("discord_user_id", ""))
            
            self.farming_world_var.set(config.get("farming_world", "Zen"))
            self.enable_farming_var.set(config.get("enable_farming", False))
            self.auto_bubble_sell_var.set(config.get("auto_bubble_sell", False))
            self.auto_sell_minutes_var.set(config.get("auto_bubble_sell_minutes", "10"))
            
            # Pet tab settings
            self.egg_hatching_detection_var.set(config.get("egg_hatching_detection", False))
            self.aura_egg_alert_var.set(config.get("aura_egg_alert", False))
            self.silly_egg_alert_var.set(config.get("silly_egg_alert", False))
            self.royal_chest_alert_var.set(config.get("royal_chest_alert", False))
            self.royal_chest_alert_value_var.set(config.get("royal_chest_alert_value", ""))
            self.roblox_username_var.set(config.get("roblox_username", ""))
            
            self.save_config()
            messagebox.askokcancel("Ok imported!!", "Your selected config.json imported and saved successfully!")
            
        except Exception as e:
            self.error_logging(e, "Error at importing config.json")
     
            
    def init_gui(self):
        selected_theme = self.config.get("selected_theme", "solar")
        abslt_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(abslt_path, "Noteab_BGSI.ico")
        
        self.root = ttk.Window(themename=selected_theme)
        self.root.title("Noteab's BGSI Macro (v1.0-alpha) (Idle)")
        self.root.geometry("635x355")
        
        try:
            self.root.iconbitmap(icon_path)
        except Exception as e: pass
        
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        webhook_frame = ttk.Frame(notebook)
        farming_frame = ttk.Frame(notebook)
        misc_frame = ttk.Frame(notebook)
        pet_frame = ttk.Frame(notebook)
        credits_frame = ttk.Frame(notebook)
        #stats_frame = ttk.Frame(notebook)

        notebook.add(webhook_frame, text='Webhook')
        notebook.add(farming_frame, text='Farming')
        notebook.add(misc_frame, text='Misc')
        notebook.add(pet_frame, text='Pets & Chests Alert')
        #notebook.add(stats_frame, text='Session Report')
        notebook.add(credits_frame, text='Credits')
   

        self.create_webhook_tab(webhook_frame)
        self.create_farming_tab(farming_frame)
        self.create_pet_tab(pet_frame)
        self.create_misc_tab(misc_frame)
        #self.create_stats_tab(stats_frame)
        self.create_credit_tab(credits_frame)
        
        button_frame = ttk.Frame(self.root)
        button_frame.pack(side='top', pady=10) 
        start_button = ttk.Button(button_frame, text="Start (F1)", command=self.start_detection)
        stop_button = ttk.Button(button_frame, text="Stop (F2)", command=self.stop_detection)
        start_button.pack(side='left', padx=5)
        stop_button.pack(side='left', padx=5)

        # Theme
        theme_label = ttk.Label(button_frame, text="Macro Theme:")
        theme_label.pack(side='left', padx=15)
        theme_combobox = ttk.Combobox(button_frame, values=ttk.Style().theme_names(), state="readonly")
        theme_combobox.set(selected_theme)
        theme_combobox.pack(side='left', padx=5)
        theme_combobox.bind("<<ComboboxSelected>>", lambda event: self.update_theme(theme_combobox.get()))

        keyboard.add_hotkey('F1', self.start_detection_listener)
        keyboard.add_hotkey('F2', self.stop_detection_listener)
        
        self.check_for_updates()
        self.root.mainloop()
        

    def update_theme(self, theme_name):
        self.root.style.theme_use(theme_name)
        self.config["selected_theme"] = theme_name
        self.save_config()
        
    def start_detection_listener(self):
        self.root.after(0, self.start_detection)

    def stop_detection_listener(self):
        self.root.after(0, self.stop_detection)

    def check_for_updates(self):
        current_version = "v1.5.5-patch1.1"
        dont_ask_again = self.config.get("dont_ask_for_update", False)
        
        if dont_ask_again: return
        
        try:
            response = requests.get("https://api.github.com/repos/noteab/Noteab-Macro/releases/latest")
            response.raise_for_status()
            latest_release = response.json()
            latest_version = latest_release['tag_name']
            
            if latest_version != current_version:
                message = f"New update of this macro {latest_version} is available. Do you want to download the newest version?"
                if messagebox.askyesno("Update Available!!", message):
                    download_url = latest_release['assets'][0]['browser_download_url']
                    self.download_update(download_url)
                else:
                    if messagebox.askyesno("Don't Ask Again", "Would you like to stop receiving update notifications?"):
                        self.config["dont_ask_for_update"] = True
                        self.save_config()
                            
        except requests.RequestException as e:
            print(f"Failed to fetch the latest version from GitHub: {e}")
    
    def download_update(self, download_url):
        try:
            zip_filename = os.path.basename(download_url)
            save_path = filedialog.asksaveasfilename(defaultextension=".zip", initialfile=zip_filename, title="Save As")
            
            if not save_path: return
            
            response = requests.get(download_url)
            response.raise_for_status()
        
            with open(save_path, 'wb') as file:
                file.write(response.content)
            
            messagebox.showinfo("Download Complete", f"The latest version has been downloaded as {save_path}. Make sure to turn off antivirus and extract it manually.")
        except requests.RequestException as e:
            print(f"Failed to download the update: {e}")
    
    def create_webhook_tab(self, frame):
        ttk.Label(frame, text="Discord Webhook URL:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.webhook_url_entry = ttk.Entry(frame, width=50, show="*")
        self.webhook_url_entry.grid(row=0, column=1, columnspan=2, pady=5)
        self.webhook_url_entry.insert(0, self.config.get("webhook_url", ""))
        self.webhook_url_entry.bind("<FocusOut>", lambda event: self.save_config())

        ttk.Label(frame, text="Private Server Link: (optional)").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.private_server_link_entry = ttk.Entry(frame, width=50)
        self.private_server_link_entry.grid(row=2, column=1, columnspan=2, pady=5)
        self.private_server_link_entry.insert(0, self.config.get("private_server_link", ""))
        self.private_server_link_entry.bind("<FocusOut>", lambda event: self.save_config())

        ttk.Label(frame, text="Private server link type:").grid(row=3, column=0, sticky="e", padx=5, pady=0)
        self.ps_type_var = ttk.StringVar(value=self.config.get("ps_link_type", "Public"))
        public_radio = ttk.Radiobutton(frame, text="Public (too broke for 99 robux ps)", variable=self.ps_type_var, value="Public", command=self.save_config)
        private_radio = ttk.Radiobutton(frame, text="Private", variable=self.ps_type_var, value="Private", command=self.save_config)
        public_radio.grid(row=3, column=1, sticky="w")
        private_radio.grid(row=3, column=2, sticky="w")
        
        ttk.Label(frame, text="Discord User ID:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.discord_user_id_entry = ttk.Entry(frame, width=50)
        self.discord_user_id_entry.grid(row=4, column=1, columnspan=2, pady=5)
        self.discord_user_id_entry.insert(0, self.config.get("discord_user_id", ""))
        self.discord_user_id_entry.bind("<FocusOut>", lambda event: self.save_config())

        ttk.Button(frame, text="Import Config", command=self.import_config).grid(row=5, column=0, pady=0)
        
    def create_farming_tab(self, frame):
        farming_frame = ttk.Frame(frame)
        farming_frame.pack(pady=10)

        # Farming World Label and Dropdown
        ttk.Label(farming_frame, text="Farming World:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.farming_world_var = ttk.StringVar(value=self.config.get("farming_world", "Zen"))
        farming_dropdown = ttk.Combobox(
            farming_frame,
            textvariable=self.farming_world_var,
            values=["Zen"],
            state="readonly"
        )
        farming_dropdown.grid(row=0, column=1, padx=1, pady=2)
        farming_dropdown.bind("<<ComboboxSelected>>", lambda e: self.save_config())

        # Calibrate World Teleport Button
        calibrate_button = ttk.Button(farming_frame, text="Calibrate World Teleport", command=self.world_tp_assign_window)
        calibrate_button.grid(row=0, column=2, padx=5, pady=5)

        # Auto Sell Bubbles Checkbox
        self.auto_bubble_sell_var = ttk.BooleanVar(value=self.config.get("auto_bubble_sell", False))
        auto_bubble_check = ttk.Checkbutton(
            farming_frame, 
            text="Auto sell bubbles in every (minutes):", 
            variable=self.auto_bubble_sell_var,
            command=self.save_config
        )
        auto_bubble_check.grid(row=1, column=0, padx=5, sticky="w")

        # Auto sell minutes
        self.auto_sell_minutes_var = ttk.StringVar(value=self.config.get("auto_bubble_sell_minutes", "10"))
        auto_sell_minutes_entry = ttk.Entry(farming_frame, textvariable=self.auto_sell_minutes_var, width=7)
        auto_sell_minutes_entry.grid(row=1, column=1, pady=5)
        auto_sell_minutes_entry.bind("<FocusOut>", lambda event: self.save_config())

        # Enable farming in Selected World Checkbox
        self.enable_farming_var = ttk.BooleanVar(value=self.config.get("enable_farming", False))
        enable_farming_check = ttk.Checkbutton(
            farming_frame, 
            text="Enable farming in selected World?", 
            variable=self.enable_farming_var,
            command=self.save_config
        )
        enable_farming_check.grid(row=2, column=0, padx=5, sticky="w")
        
        # Anti AFK
        self.anti_afk_var = ttk.BooleanVar(value=self.config.get("anti_afk", False))
        anti_afk_check = ttk.Checkbutton(
            farming_frame,
            text="Anti AFK (only works if auto farm are disabled)",
            variable=self.anti_afk_var,
            command=self.save_config
        )
        anti_afk_check.grid(row=3, column=0, padx=5, pady=10, sticky="w")
        
        # Ignore cam align
        self.ignore_cam_align_var = ttk.BooleanVar(value=self.config.get("ignore_cam_align", False))
        ignore_cam_check = ttk.Checkbutton(
            farming_frame,
            text="Ignore cam aligning when macroing?\n(if you already aligned the cam manually)",
            variable=self.ignore_cam_align_var,
            command=self.save_config
        )
        ignore_cam_check.grid(row=4, column=0, padx=5, pady=0, sticky="w")

        # Collect Paths
        collection_path_button = ttk.Button(farming_frame, text="Macro Paths", command=self.collection_path_window)
        collection_path_button.grid(row=7, column=0, padx=0, pady=8)
        
    def create_misc_tab(self, frame):
        misc_frame = ttk.Frame(frame)
        misc_frame.pack(pady=10)

        # Calibrate world clicks
        calibrate_button = ttk.Button(misc_frame, text="Calibrate Mouse Clicks", command=self.misc_assign_window)
        calibrate_button.grid(row=0, column=2, padx=5, pady=5)

        # Auto Sell Bubbles Checkbox
        self.auto_buy_alien_stock_var = ttk.BooleanVar(value=self.config.get("auto_buy_alien_stock", False))
        auto_buy_alien_var = ttk.Checkbutton(
            misc_frame, 
            text="Auto buy alien stock every (minutes):", 
            variable=self.auto_buy_alien_stock_var,
            command=self.save_config
        )
        auto_buy_alien_var.grid(row=0, column=0, padx=5, sticky="w")

        # Auto sell minutes
        self.auto_alien_buy_minutes_var = ttk.StringVar(value=self.config.get("auto_buy_alien_stock_minutes", "20"))
        auto_alien_buy_entry = ttk.Entry(misc_frame, textvariable=self.auto_alien_buy_minutes_var, width=7)
        auto_alien_buy_entry.grid(row=0, column=1, pady=5)
        auto_alien_buy_entry.bind("<FocusOut>", lambda event: self.save_config())
        
        self.auto_claim_chest_var = ttk.BooleanVar(value=self.config.get("auto_claim_chest", False))
        auto_claim_chest_check = ttk.Checkbutton(
            misc_frame, 
            text="Claim Void/Floating Chest every (minutes)\n(Requires level 15 'Buffs Mastery')", 
            variable=self.auto_claim_chest_var,
            command=self.save_config
        )
        auto_claim_chest_check.grid(row=1, column=0, padx=5, sticky="w")
        
        self.auto_claim_chest_minutes_var = ttk.StringVar(value=self.config.get("auto_claim_chest_minutes", "35"))
        auto_claim_chest_entry = ttk.Entry(misc_frame, textvariable=self.auto_claim_chest_minutes_var, width=7)
        auto_claim_chest_entry.grid(row=1, column=1, pady=5)
        auto_claim_chest_entry.bind("<FocusOut>", lambda event: self.save_config())
        
        # auto daily quest
        self.auto_daily_quest_var = ttk.BooleanVar(value=self.config.get("auto_daily_quest", False))
        auto_daily_quest_check = ttk.Checkbutton(
            misc_frame, 
            text="Auto claim Daily Quest every (minutes):", 
            variable=self.auto_daily_quest_var,
            command=self.save_config
        )
        auto_daily_quest_check.grid(row=2, column=0, padx=5, sticky="w")
        
        self.auto_daily_quest_minutes_var = ttk.StringVar(value=self.config.get("auto_daily_quest_minutes", "70"))
        auto_daily_quest_entry = ttk.Entry(misc_frame, textvariable=self.auto_daily_quest_minutes_var, width=7)
        auto_daily_quest_entry.grid(row=2, column=1, pady=5)
        auto_daily_quest_entry.bind("<FocusOut>", lambda event: self.save_config())
    
    def create_pet_tab(self, frame):
        pet_frame = ttk.Frame(frame)
        pet_frame.pack(pady=10)

        # Egg Hatching Detection Checkbox
        self.egg_hatching_detection_var = ttk.BooleanVar(value=self.config.get("egg_hatching_detection", False))
        egg_hatching_check = ttk.Checkbutton(
            pet_frame, 
            text="Egg hatching detection (Require Bloxstrap ExpChat FFlag)",
            variable=self.egg_hatching_detection_var,
            command=self.save_config
        )
        egg_hatching_check.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 2))

        # Aura Egg Alert Checkbox
        self.aura_egg_alert_var = ttk.BooleanVar(value=self.config.get("aura_egg_alert", False))
        aura_egg_alert_check = ttk.Checkbutton(
            pet_frame,
            text="Aura egg alert (rare egg rift - forced @everyone ping)",
            variable=self.aura_egg_alert_var,
            command=self.save_config
        )
        aura_egg_alert_check.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        # Silly Egg Alert Checkbox
        self.silly_egg_alert_var = ttk.BooleanVar(value=self.config.get("silly_egg_alert", False))
        silly_egg_alert_check = ttk.Checkbutton(
            pet_frame,
            text="Silly egg alert (rare egg rift - forced @everyone ping)",
            variable=self.silly_egg_alert_var,
            command=self.save_config
        )
        silly_egg_alert_check.grid(row=2, column=0, sticky="w", padx=5, pady=5)

        # Royal Chest Alert Checkbox
        self.royal_chest_alert_var = ttk.BooleanVar(value=self.config.get("royal_chest_alert", False))
        royal_chest_alert_check = ttk.Checkbutton(
            pet_frame, 
            text="Enable Royal Chest Alert\n(Discord User ID/Role ID to ping)", 
            variable=self.royal_chest_alert_var,
            command=self.save_config
        )
        royal_chest_alert_check.grid(row=3, column=0, columnspan=2, padx=5, sticky="w")
        
        self.royal_chest_alert_value_var = ttk.StringVar(value=self.config.get("royal_chest_alert_value", ""))
        royal_chest_alert_entry = ttk.Entry(pet_frame, textvariable=self.royal_chest_alert_value_var, width=25)
        royal_chest_alert_entry.grid(row=3, column=1, padx=5, pady=5)
        royal_chest_alert_entry.bind("<FocusOut>", lambda event: self.save_config())

        # Username Entry
        ttk.Label(pet_frame, text="Your Roblox username (not display name):").grid(row=4, column=0, sticky="w", padx=0, pady=5)
        self.roblox_username_var = ttk.StringVar(value=self.config.get("roblox_username", ""))
        roblox_username_entry = ttk.Entry(pet_frame, textvariable=self.roblox_username_var, width=25)
        roblox_username_entry.grid(row=4, column=1, padx=0, pady=5, sticky="w")
        roblox_username_entry.bind("<FocusOut>", lambda e: self.save_config())

        # --- Bloxstrap FFlag Functions ---
        def open_bloxstrap_fflag_folder():
            folder = os.path.join(os.getenv('LOCALAPPDATA'), 'Bloxstrap', 'Modifications', 'ClientSettings')
            if os.path.exists(folder):
                os.startfile(folder)
            else:
                messagebox.showerror("Error", f"File not found:\n{folder}\n\nHave you tried install Bloxstrap yet? Or install it in correct default directory as Bloxstrap recommended to you?")

        def copy_fflag_value():
            fflag_text = (
                '"FStringDebugLuaLogLevel": "debug",\n'
                '"FStringDebugLuaLogPattern": "ExpChat/mountClientApp"'
            )
            self.root.clipboard_clear()
            self.root.clipboard_append(fflag_text)
            messagebox.showinfo(
                "Copied!",
                "Required FFlag for Royal Chest/Aura egg copied to clipboard!\n\n"
                "Paste these into your ClientAppSettings JSON file and save it.\n"
                "Make sure to close any active Roblox window before editing/applying, "
                "then restart Roblox for the FFlag to take effect!"
            )

        # Bloxstrap FFlag Buttons
        open_fflag_button = ttk.Button(pet_frame, text="Open Bloxstrap FFlag folder", command=open_bloxstrap_fflag_folder)
        open_fflag_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

        copy_fflag_button = ttk.Button(pet_frame, text="Copy the fflag value to clipboard (for royal/aura egg detection)", command=copy_fflag_value)
        copy_fflag_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5)
        
    def world_tp_assign_window(self):
        assign_window = ttk.Toplevel(self.root)
        assign_window.title("World Teleport Coordinate")
        assign_window.geometry("550x340")
        assign_window.attributes("-topmost", True)

        positions = [
            ("Map Icon (the one has keybind of M)", "world_mapicon"),
            ("Zen Map Icon", "zen_mapicon"),
            ("World 1 The Overworld Icon", "overworld_mapicon"),
            ("Teleport Button", "world_teleport_button")
        ]

        coord_vars = {}

        for i, (label_text, config_key) in enumerate(positions):
            label = ttk.Label(assign_window, text=f"{label_text} (X, Y):")
            label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

            x_var = ttk.IntVar(value=self.config.get(config_key, [0, 0])[0])
            y_var = ttk.IntVar(value=self.config.get(config_key, [0, 0])[1])
            coord_vars[config_key] = (x_var, y_var)

            x_entry = ttk.Entry(assign_window, textvariable=x_var, width=6, state="readonly")
            x_entry.grid(row=i, column=1, padx=5, pady=5)

            y_entry = ttk.Entry(assign_window, textvariable=y_var, width=6, state="readonly")
            y_entry.grid(row=i, column=2, padx=5, pady=5)

            select_button = ttk.Button(
                assign_window, text="Assign Click",
                command=lambda key=config_key: self.start_capture_thread(key, coord_vars)
            )
            select_button.grid(row=i, column=3, padx=5, pady=5)

        save_button = ttk.Button(assign_window, text="Save", command=lambda: self.save_world_map_coordinates(assign_window, coord_vars))
        save_button.grid(row=len(positions), column=0, columnspan=4, pady=10)
    
    def misc_assign_window(self):
        assign_window = ttk.Toplevel(self.root)
        assign_window.title("Misc clicks assign window")
        assign_window.geometry("550x500")
        assign_window.attributes("-topmost", True)

        # tabs
        notebook = ttk.Notebook(assign_window)
        notebook.pack(fill='both', expand=True)
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Main Assignments")

        main_positions = [
            ("Playtime icon", "dailyquest_mapicon"),
            ("Alien Stock Buy button #1", "alien_gembutton1"),
            ("Alien Stock Buy button #2", "alien_gembutton2"),
            ("Alien Stock Buy button #3", "alien_gembutton3"),
            ("Void chest 'Collect' Button", "void_chest_collect_button"),
            ("Floating chest 'Collect' Button", "float_chest_collect_button"),
        ]

        coord_vars = {}

        for i, (label_text, config_key) in enumerate(main_positions):
            label = ttk.Label(main_frame, text=f"{label_text} (X, Y):")
            label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

            x_var = ttk.IntVar(value=self.config.get(config_key, [0, 0])[0])
            y_var = ttk.IntVar(value=self.config.get(config_key, [0, 0])[1])
            coord_vars[config_key] = (x_var, y_var)

            x_entry = ttk.Entry(main_frame, textvariable=x_var, width=6, state="readonly")
            x_entry.grid(row=i, column=1, padx=5, pady=5)

            y_entry = ttk.Entry(main_frame, textvariable=y_var, width=6, state="readonly")
            y_entry.grid(row=i, column=2, padx=5, pady=5)

            select_button = ttk.Button(
                main_frame, text="Assign Click",
                command=lambda key=config_key: self.start_capture_thread(key, coord_vars)
            )
            select_button.grid(row=i, column=3, padx=5, pady=5)

        # Daily Gift Boxes Tab
        gift_frame = ttk.Frame(notebook)
        notebook.add(gift_frame, text="Daily Gift Boxes")
        gift_positions = [
            ("Daily gift Skip button", "daily_gift_skip_button"),
            ("Daily Gift Box #1", "daily_gift_box_1"),
            ("Daily Gift Box #2", "daily_gift_box_2"),
            ("Daily Gift Box #3", "daily_gift_box_3"),
            ("Daily Gift Box #4", "daily_gift_box_4"),
            ("Daily Gift Box #5", "daily_gift_box_5"),
            ("Daily Gift Box #6", "daily_gift_box_6"),
            ("Daily Gift Box #7", "daily_gift_box_7"),
            ("Daily Gift Box #8", "daily_gift_box_8"),
            ("Daily Gift Box #9", "daily_gift_box_9"),
        ]

        for i, (label_text, config_key) in enumerate(gift_positions):
            label = ttk.Label(gift_frame, text=f"{label_text} (X, Y):")
            label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

            x_var = ttk.IntVar(value=self.config.get(config_key, [0, 0])[0])
            y_var = ttk.IntVar(value=self.config.get(config_key, [0, 0])[1])
            coord_vars[config_key] = (x_var, y_var)

            x_entry = ttk.Entry(gift_frame, textvariable=x_var, width=6, state="readonly")
            x_entry.grid(row=i, column=1, padx=5, pady=5)

            y_entry = ttk.Entry(gift_frame, textvariable=y_var, width=6, state="readonly")
            y_entry.grid(row=i, column=2, padx=5, pady=5)

            select_button = ttk.Button(
                gift_frame, text="Assign Click",
                command=lambda key=config_key: self.start_capture_thread(key, coord_vars)
            )
            select_button.grid(row=i, column=3, padx=5, pady=5)

        # Save Button
        misc_save_button = ttk.Button(assign_window, text="Save", command=lambda: self.save_world_map_coordinates(assign_window, coord_vars))
        misc_save_button.pack(pady=10)

           
    def collection_path_window(self):
        collect_window = ttk.Toplevel(self.root)
        collect_window.title("General Macro Paths")
        collect_window.geometry("550x340")

        # Align camera button at the top (yeah why not)
        top_frame = ttk.Frame(collect_window)
        top_frame.pack(pady=10)
        align_camera_button = ttk.Button(top_frame, text="Click to align the camera!", command=self.camera_align)
        align_camera_button.pack()

        # paths attri (label, internal_name)
        path_list = [
            ("Zen path", "zen_map"),
            ("Bubble sell path", "bubble_sell"),
            ("Alien shop path", "alien_shop")
        ]

        for label_text, internal_name in path_list:
            row_frame = ttk.Frame(collect_window)
            row_frame.pack(pady=10)

            label = ttk.Label(row_frame, text=label_text)
            label.pack(side="left", padx=(0, 15))

            countdown_var = ttk.StringVar(value="")
            countdown_label_value = ttk.Label(row_frame, textvariable=countdown_var)
            countdown_label_value.pack(side="left", padx=(0, 10))

            countdown_active = False

            def make_update_countdown(countdown_var, countdown_active_ref, internal_name):
                def update_countdown(count, action_type):
                    if count > 0 and countdown_active_ref[0]:
                        countdown_var.set(f"Ready to {action_type} in: {count}")
                        threading.Timer(1, update_countdown, args=(count - 1, action_type)).start()
                    elif countdown_active_ref[0]:
                        countdown_var.set(f"{action_type}...")
                        if action_type == "Record":
                            threading.Thread(target=lambda: self.recorder.record()).start()
                        elif action_type == "Replay":
                            threading.Thread(target=lambda: self.recorder.play(
                                speed_factor=1.0, only_essential_moves=False, macro_path=os.path.join(self.macro_paths_directory, f"{internal_name}.json")
                            )).start()
                            countdown_var.set("")
                return update_countdown

            countdown_active_ref = [False]  # mutable in closures
            update_countdown = make_update_countdown(countdown_var, countdown_active_ref, internal_name)

            def make_update_countdown(countdown_var, countdown_active_ref, internal_name):
                def update_countdown(count, action_type):
                    if count > 0 and countdown_active_ref[0]:
                        countdown_var.set(f"Ready to {action_type} in: {count}")
                        threading.Timer(1, update_countdown, args=(count - 1, action_type)).start()
                    elif countdown_active_ref[0]:
                        countdown_var.set(f"{action_type}...")
                        if action_type == "Record":
                            threading.Thread(target=lambda: self.recorder.record()).start()
                        elif action_type == "Replay":
                            threading.Thread(target=lambda: self.recorder.play(
                                speed_factor=1.0, only_essential_moves=False, macro_path=f"{internal_name}.json"
                            )).start()
                            countdown_var.set("")
                return update_countdown

            countdown_active_ref = [False]  # mutable in closures
            update_countdown = make_update_countdown(countdown_var, countdown_active_ref, internal_name)

            def make_start_recording(update_countdown, countdown_active_ref):
                def start_recording():
                    countdown_active_ref[0] = True
                    update_countdown(4, "Record")
                return start_recording

            def make_stop_recording(countdown_var, countdown_active_ref, internal_name):
                def stop_recording():
                    countdown_active_ref[0] = False
                    countdown_var.set("")
                    threading.Thread(target=lambda: self.recorder.stop_recording(os.path.join(self.macro_paths_directory, internal_name))).start()
                return stop_recording

            def make_play_macro(update_countdown, countdown_active_ref):
                def play_macro():
                    countdown_active_ref[0] = True
                    update_countdown(5, "Replay")
                return play_macro

            record_button = ttk.Button(row_frame, text="Start Recording", command=make_start_recording(update_countdown, countdown_active_ref))
            record_button.pack(side="left", padx=5)

            stop_button = ttk.Button(row_frame, text="Stop Recording", command=make_stop_recording(countdown_var, countdown_active_ref, internal_name))
            stop_button.pack(side="left", padx=5)

            play_button = ttk.Button(row_frame, text="Play Macro", command=make_play_macro(update_countdown, countdown_active_ref))
            play_button.pack(side="left", padx=5)
        
    # def check_tesseract_ocr(self):
    #     tesseract_env_path = os.getenv('TESSERACT_PATH')
    #     if tesseract_env_path and os.path.exists(tesseract_env_path):
    #         pytesseract.pytesseract.tesseract_cmd = tesseract_env_path
    #         return True

    #     possible_paths = [
    #         r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    #         r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    #         os.path.join(os.getenv('LOCALAPPDATA'), 'Programs', 'Tesseract-OCR', 'tesseract.exe'),
    #         os.path.join(os.getenv('LOCALAPPDATA'), 'Tesseract-OCR', 'tesseract.exe')
    #     ]

    #     for path in possible_paths:
    #         if os.path.exists(path):
    #             pytesseract.pytesseract.tesseract_cmd = path
    #             return True
                
    #     return False
    
    # def download_tesseract(self):
    #     download_url = "https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe"
    #     try:
    #         exe_filename = os.path.basename(download_url)
    #         save_path = filedialog.asksaveasfilename(defaultextension=".exe", initialfile=exe_filename, title="Save As")
            
    #         if not save_path:
    #             messagebox.showwarning("Download Cancelled", "No file path selected. Download cancelled.")
    #             return
            
    #         response = requests.get(download_url)
    #         response.raise_for_status()
        
    #         with open(save_path, 'wb') as file:
    #             file.write(response.content)
            
    #         messagebox.showinfo("Download Complete", f"Tesseract installer has been downloaded as {save_path}. Please run the installer to complete the setup. \n \n After installed tesseract, restart the macro to let it check if your ocr module is ready!")
    #     except requests.RequestException as e:
    #         messagebox.showerror("Download Failed", f"Failed to download Tesseract: {e}")
    #     except IOError as e:
    #         messagebox.showerror("File Error", f"Failed to save the file: {e}")

        
    def create_stats_tab(self, frame):
        pass
        
    def create_credit_tab(self, credits_frame):
        current_dir = os.getcwd()
        images_dir = os.path.join(current_dir, "images")
        credit_paths = [
            os.path.join(images_dir, "tea.png"),
            os.path.join(images_dir, "maxstellar.png")
        ]

        def load_image(filename, size):
            for path in credit_paths:
                if os.path.basename(path) == filename and os.path.exists(path):
                    try:
                        img = Image.open(path)
                        img = img.resize(size, Image.LANCZOS)
                        return ImageTk.PhotoImage(img)
                    except Exception as e:
                        print(f"Failed to load image: {path}, Error: {e}")
                        return None
            return None

        credits_frame_content = ttk.Frame(credits_frame)
        credits_frame_content.pack(pady=20)
        noteab_image = load_image("tea.png", (85, 85))
        noteab_frame = ttk.Frame(credits_frame_content, borderwidth=2, relief="solid")
        noteab_frame.grid(row=0, column=0, padx=10, pady=2)
        
        if noteab_image: ttk.Label(noteab_frame, image=noteab_image).pack(pady=5)
        ttk.Label(noteab_frame, text="BGSI Developer: Noteab").pack()

        discord_label = ttk.Label(noteab_frame, text="Join my Community Server!!", foreground="#03cafc", cursor="hand2")
        discord_label.pack()
        discord_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://discord.gg/noteab"))

        github_label = ttk.Label(noteab_frame, text="GitHub: Noteab BGSI Macro!", foreground="#03cafc", cursor="hand2")
        github_label.pack()
        github_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/noteab/Sol-Biome-Tracker"))
        self.noteab_image = noteab_image
    
        
    def save_world_map_coordinates(self, window, coord_vars):
        for key, (x_var, y_var) in coord_vars.items():
            self.config[key] = [x_var.get(), y_var.get()]
        self.save_config()
        window.destroy()
        
    def start_capture_thread(self, config_key, coord_vars):
        snipping_tool = SnippingWidget(self.root, config_key=config_key, callback=lambda region: self.update_coordinates(config_key, region, coord_vars))
        snipping_tool.start()

    def update_coordinates(self, config_key, region, coord_vars):
        x, y = region[0], region[1]
        coord_vars[config_key][0].set(x) 
        coord_vars[config_key][1].set(y)
        self.save_config() 
            
    ## SNIPPING ^^ ##

    def start_detection(self):
        if not self.detection_running:
            self.detection_running = True
            self.root.title("Noteab's BGSI Macro (v1.0-alpha) (Running)")
            self.send_webhook_status("Macro started!", color=0x64ff5e)
            
            if not hasattr(self, 'collect_thread') or not (self.collect_thread and self.collect_thread.is_alive()):
                self.collect_thread = threading.Thread(target=self.collect_coins_and_gems_loop, name="BGSI Collect Loop", daemon=True)
                self.collect_thread.start()

            if not hasattr(self, 'rift_thread') or not (self.rift_thread and self.rift_thread.is_alive()):
                self.rift_thread = threading.Thread(target=self.check_rift_loop, name="Rift Check Loop", daemon=True)
                self.rift_thread.start()

            if not hasattr(self, 'check_roblox_processes_thread') or not (self.check_roblox_processes_thread and self.check_roblox_processes_thread.is_alive()):
                self.check_roblox_processes_thread = threading.Thread(target=self.check_roblox_processes_loop, name="check roblox Loop", daemon=True)
                self.check_roblox_processes_thread.start()
                
            self.start_anti_afk_timer()
                
            # print("Active threads before starting new ones:")
            # for thread in threading.enumerate():
            #     print(f"Thread name: {thread.name}, is alive: {thread.is_alive()}")

    def stop_detection(self):
        if self.detection_running:
            self.detection_running = False
            if hasattr(self, "recorder") and self.recorder: self.recorder.is_playing = False
            self.start_time = None
            self.root.title("Noteab's BGSI Macro (v1.0-alpha) (Stopped)")
            self.send_webhook_status("Macro stopped!", color=0xff0000)
            self.save_config()
    
    def get_latest_log_file(self):
        files = [os.path.join(self.logs_dir, f) for f in os.listdir(self.logs_dir) if f.endswith('.log')]
        latest_file = max(files, key=os.path.getmtime)
        return latest_file

    def read_log_file(self, log_file_path):
        if not os.path.exists(log_file_path):
            print(f"Log file not found: {log_file_path}")
            return []

        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            file.seek(self.last_position)
            lines = file.readlines()
            self.last_position = file.tell()
            return lines
        
    def read_full_log_file(self, log_file_path):
        if not os.path.exists(log_file_path):
            print(f"Log file not found: {log_file_path}")
            return []

        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.readlines()
        
    def collect_coins_and_gems_loop(self):
        try:
            for _ in range(4):
                if not self.detection_running or not self.config.get("enable_farming"): return
                self.activate_roblox_window()
                time.sleep(0.5)

            if self.detection_running and self.config.get("enable_farming"):
                time.sleep(1.32)
                autoit.send("{ESC}")
                time.sleep(0.7)
                autoit.send("r")
                time.sleep(0.7)
                autoit.send("{ENTER}")
                time.sleep(5.5)

            if self.detection_running and self.config.get("enable_farming") and not self.config.get("ignore_cam_align"):
                self.camera_align()
                time.sleep(2)

            if self.detection_running and self.config.get("enable_farming"):
                self.teleport_to_farm_world(target="zen")
                time.sleep(2.3)

            # Intervals (im the horse?)
            bubble_sell_interval = int(self.config.get("auto_bubble_sell_minutes", 10)) * 60
            alien_shop_interval = int(self.config.get("auto_buy_alien_stock_minutes", 10)) * 60
            chest_collect_interval = int(self.config.get("auto_claim_chest_minutes", 35)) * 60
            daily_quest_interval = int(self.config.get("auto_daily_quest_minutes", 15)) * 60

            while self.detection_running:
                if not self.enable_farming_var.get(): return
                now = time.time()

                # --- Daily Quest Auto Logic ---
                if self.config.get("auto_daily_quest", False) and (now - self.last_daily_quest_time) >= daily_quest_interval:
                    print("auto daily quest running")
                    dailyquest_mapicon = self.config.get("dailyquest_mapicon", [51, 429])
                    daily_gift_skip_button = self.config.get("daily_gift_skip_button", [962, 616])
                    
                    self.Global_MouseClick(dailyquest_mapicon[0], dailyquest_mapicon[1])
                    time.sleep(1.85)

                    # Loop for aaaaaaaaaaaaaaaaaaaaaaaadaily gift buttons
                    for i in range(1, 10):  # daily_gift_box_1 to daily_gift_box_9
                        if not self.detection_running: break
                        daily_gift_button = self.config.get(f"daily_gift_box_{i}", [0, 0])
                        if daily_gift_button != [0, 0]:
                            self.Global_MouseClick(daily_gift_button[0], daily_gift_button[1])
                            time.sleep(1.55)
                            self.Global_MouseClick(daily_gift_skip_button[0], daily_gift_skip_button[1])
                            time.sleep(1.5)
                              
                    self.Global_MouseClick(dailyquest_mapicon[0], dailyquest_mapicon[1])
                    self.last_daily_quest_time = now
                    time.sleep(1.55)
                    print("auto daily quest ended")
                    
                # --- Bubble Sell ---
                if self.config.get("auto_bubble_sell", False) and (now - self.last_bubble_sell_time) >= bubble_sell_interval:
                    print("auto bubble sell running")
                    if not self.detection_running: return
                    self.teleport_to_farm_world(target="overworld", world_scroll="down")
                    if not self.detection_running: return
                    self.replay_macro_path(path_type="Bubble Sell")
                    if not self.detection_running: return
                    self.teleport_to_farm_world(target="zen")
                    self.last_bubble_sell_time = now
                    print("auto bubble sell ended")

                # --- Alien Shop Auto Buy Logic ---
                if self.config.get("auto_buy_alien_stock", False) and (now - self.last_alien_shop_buy_time) >= alien_shop_interval:
                    print("autobuy alien shop running")
                    if not self.detection_running: return
                    self.teleport_to_farm_world(target="zen")
                    if not self.detection_running: return
                    self.replay_macro_path(path_type="Alien Shop")

                    alien_gem_buttons = [
                        ("alien_gembutton1", 5),
                        ("alien_gembutton2", 10),
                        ("alien_gembutton3", 10),
                    ]

                    for key, max_clicks in alien_gem_buttons:
                        if not self.detection_running: break
                        coords = self.config.get(key, [0, 0])
                        if coords != [0, 0]:
                            for _ in range(max_clicks):
                                if not self.detection_running: break
                                self.Global_MouseClick(coords[0], coords[1])
                                time.sleep(0.15)

                    self.teleport_to_farm_world(target="zen")
                    self.last_alien_shop_buy_time = now
                    print("autobuy alien shop ended")

                # --- Auto claim chest ---
                if self.auto_claim_chest_var.get() and (now - self.last_chest_collect_time) >= chest_collect_interval:
                    world_mapicon = self.config.get("world_mapicon", [737, 314])
                    float_chest_button = self.config.get("float_chest_collect_button", [1093, 219])
                    void_chest_button = self.config.get("void_chest_collect_button", [829, 880])
                    if not self.detection_running: return
                    # Open world map
                    self.Global_MouseClick(world_mapicon[0], world_mapicon[1])
                    time.sleep(1.5)
                    autoit.mouse_move(1152, 381, speed=-1)
                    # float chest
                    autoit.mouse_wheel("down", 30)
                    time.sleep(1.5)
                    self.Global_MouseClick(float_chest_button[0], float_chest_button[1])
                    time.sleep(1.3)
                    # void chest
                    autoit.mouse_wheel("up", 30)
                    time.sleep(1.5)
                    self.Global_MouseClick(void_chest_button[0], void_chest_button[1])
                    time.sleep(1.5)
                    self.Global_MouseClick(world_mapicon[0], world_mapicon[1])
                    self.last_chest_collect_time = now
                    time.sleep(1.3)
                    self.teleport_to_farm_world(target="zen")
                    print("auto collect chests ended")
                
                # --- Farming replay ---
                if not self.detection_running: return
                macro_thread = threading.Thread(target=self.replay_macro_path, kwargs={"path_type": "Zen"}, name="MacroReplay", daemon=True)
                macro_thread.start()
                while macro_thread.is_alive():
                    if not self.detection_running:
                        self.recorder.is_playing = False
                        break
                    time.sleep(0.1)  # Check frequently

                if not self.detection_running:
                    self.recorder.is_playing = False
                    break
                if self.detection_running and self.enable_farming_var.get():
                    self.teleport_to_farm_world(target="zen")
                    time.sleep(1.2)

                time.sleep(0.1)

        except Exception as e:
            self.error_logging(e, "Error in main collect_coins_and_gems_loop function")

    def replay_macro_path(self, path_type=None):
        try:
            if path_type is None:
                path_type = self.config.get("farming_world", "Zen")
            
            farming_path_map = {
                "Zen": "zen_map.json",
                "Bubble Sell": "bubble_sell.json",
                "Alien Shop": "alien_shop.json"
            }
            
            macro_file_name = farming_path_map.get(path_type)
            
            if not macro_file_name: return
            
            macro_path = os.path.join(self.macro_paths_directory, macro_file_name)
            
            if self.detection_running:
                self.recorder.play(
                    speed_factor=1.0,
                    only_essential_moves=False,
                    macro_path=macro_path
                )
        except Exception as e:
            self.error_logging(e, "Error in replay_macro_path function")
    
    def screenshot_chat_area(self, name="ok"):
        try:
            left = 0
            top = 79
            w = 300
            h = 320
            
            self.Global_MouseClick(150, 150)
        
            os.makedirs("images", exist_ok=True)
            filename = f"images/{name}.png"
            screenshot = pyautogui.screenshot(region=(left, top, w, h))
            screenshot.save(filename)
            return filename
        except Exception as e:
            self.error_logging(e, "Error taking chat screenshot")
            return None
    
    def check_rift_and_egg_hatch_in_logs(self, log_file_path):
        try:
            log_lines = self.read_log_file(log_file_path)
            full_logs_lines = self.read_full_log_file(log_file_path)
            ps_link_type = self.config.get("ps_link_type", "Public")
            ps_link = self.config.get("private_server_link", "")
            public_ps_link = ""
            game_instance_id = None
            
            # Check for game instance ID
            for line in reversed(full_logs_lines):
                match = re.search(r"Joining game '([a-f0-9\-]+)'\s+place", line)
                if match:
                    game_instance_id = match.group(1)
                    break
            if game_instance_id:
                public_ps_link = f"roblox://experiences/start?placeId=85896571713843&gameInstanceId={game_instance_id}"

            # Alert toggles
            royal_chest_alert = self.config.get("royal_chest_alert", True)
            aura_egg_alert = self.config.get("aura_egg_alert", True)
            silly_egg_alert = self.config.get("silly_egg_alert", True)
            egg_hatching_detection = self.config.get("egg_hatching_detection", True)
            roblox_username = self.config.get("roblox_username", "")
            self.last_royal_rift_log = None
            self.last_aura_egg_log = None
            self.last_silly_rift_log = None
            self.last_egg_hatch_log = None

            for line in reversed(log_lines):
                if '[ExpChat/mountClientApp (Debug)]' in line:
                    # Royal Chest detection
                    if royal_chest_alert and '🔮 You hear Royalty in the distance...' in line and '<font color="#cb77ff">' in line:
                        if self.last_royal_rift_log != line: 
                            self.send_rare_rift_webhook("Royal", public_ps_link, ps_link, ps_link_type == "Public")
                            self.last_royal_rift_log = line
                        return

                    # Aura Egg detection
                    if aura_egg_alert and re.search(r"\.\.\.\s*aura\s*\.\.\.", line, re.IGNORECASE):
                        if self.last_aura_egg_log != line:
                            self.send_rare_rift_webhook("Aura Egg", public_ps_link, ps_link, ps_link_type == "Public")
                            self.last_aura_egg_log = line
                        return

                    # Silly egg detection
                    if silly_egg_alert and "so silly and fun" in line:
                        if self.last_silly_rift_log != line:
                            self.send_rare_rift_webhook("Silly Egg", public_ps_link, ps_link, ps_link_type == "Public")
                            self.last_silly_rift_log = line
                        return

                    # Egg hatch detection
                    if egg_hatching_detection and "just hatched a" in line:
                        match = re.search(
                            r'<font color="(?P<user_color>#[0-9a-fA-F]+)">(?P<username>[^<]+)</font> just hatched a <font color="(?P<pet_color>#[0-9a-fA-F]+)">(?P<pet_name>.+?) \((?P<chance>[\d\.]+%)\)</font>',
                            line
                        )
                        if match:
                            username = match.group("username")
                            pet_name = match.group("pet_name")
                            chance = match.group("chance")
                            pet_color = match.group("pet_color")
                            if username == roblox_username:
                                if self.last_egg_hatch_log != line:
                                    self.send_egg_hatch_webhook(username, pet_name, chance, pet_color)
                                    self.last_egg_hatch_log = line
                                    return

        except Exception as e:
            self.error_logging(e, "Error in check_rift_and_egg_hatch_in_logs function")
            
    def check_rift_loop(self):
        last_log_file = None
        while self.detection_running:
            try:
                current_log_file = self.get_latest_log_file()
                if current_log_file != last_log_file:
                    self.last_position = 0
                    last_log_file = current_log_file
                    
                self.check_rift_and_egg_hatch_in_logs(current_log_file)
                time.sleep(1)
                    
            except Exception as e:
                self.error_logging(e, "Error in check_rift_loop function.")
        
    def check_roblox_procs(self):
        try:
            current_user = psutil.Process().username()
            running_processes = psutil.process_iter(['pid', 'name', 'username'])
            roblox_processes = []

            for proc in running_processes:
                if proc.info['name'] in ['RobloxPlayerBeta.exe', 'Windows10Universal.exe'] and proc.info['username'] == current_user:
                    roblox_processes.append(proc.info)

            if roblox_processes: return True

        except Exception as e:
            self.error_logging(e, "Error in check_roblox_procs function.")
        
        return False
    
    def check_roblox_processes_loop(self):
        while self.detection_running:
            try:
                if not self.check_roblox_procs():
                    self.detection_running = False
                    self.send_webhook_status("Macro stopped - Roblox instance closed!", color=0xff0000)
                    self.root.title("Noteab's BGSI Macro (v1.0-alpha) (Stopped)")
                    break
                time.sleep(1.5)
            except Exception as e:
                 self.error_logging(e, "Error in check_roblox_processes_loop function.")
    
    def terminate_roblox_processes(self):
        try:
            current_user = psutil.Process().username()
            running_processes = psutil.process_iter(['pid', 'name', 'username'])

            for proc in running_processes:
                if proc.info['name'] in ['RobloxPlayerBeta.exe', 'Windows10Universal.exe'] and proc.info['username'] == current_user:
                    print(f"Terminating process: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.terminate()
                    proc.wait()

        except Exception as e:
            self.error_logging(e, "Error in terminate_roblox_processes function.")
    
    def Global_MouseClick(self, x, y, click=1):
        time.sleep(0.335)
        autoit.mouse_click("left", x, y, click, speed=2)
        
    
    def send_rare_rift_webhook(self, rift_name, public_ps_link, ps_link, is_public):
        webhook_url = self.config.get("webhook_url")
        richie_kid_ps_link = self.config.get("private_server_link", "empty")
        
        if not webhook_url:
            print("Webhook URL is missing/not included in the config.json")
            return

        rift_thumbnails = {
            "Royal": "https://i.postimg.cc/ydcCgyVb/royal.png",
            "Aura Egg": "https://static.wikia.nocookie.net/bgs-infinity/images/2/2e/Aura_Egg.png/revision/latest?cb=20250420102104",
            "Silly Egg": "https://i.postimg.cc/vTdZ1jMk/tspmoicl.png"
        }

        # --- PING LOGIC ---
        if rift_name == "Royal":
            discord_user_id = self.config.get("discord_user_id", "")
            royal_chest_alert_value = self.config.get("royal_chest_alert_value", "")
            pings = []
            if discord_user_id:
                pings.append(f"<@{discord_user_id}>")
            if royal_chest_alert_value:
                pings.append(f"<@{royal_chest_alert_value}>")
            content = " ".join(pings)
        elif rift_name == "Aura Egg" or rift_name == "Silly Egg":
            content = "@everyone"
        else:
            content = ""
        
        deep_link = f"roblox://experiences/start?{public_ps_link.split('?')[1]}"
        clickable_link = richie_kid_ps_link

        if is_public:
            description = (
                f"## The macroer is in a PUBLIC server!\n\n"
                f"Public server link (JOIN THIS ONE ⚠️ --> copy & paste the link to join):\n\n`{deep_link}`\n\n"
                f"Private server link:\n{clickable_link}"
            )
        else:
            description = (
                f"## The macroer is in their PRIVATE server!\n\n"
                f"Public server link (copy and paste):\n`{deep_link}`\n\n"
                f"Private server link (JOIN THIS ONE ⚠️):\n{clickable_link}"
            )

        embed_color = 10767045 if rift_name == "Royal" else 15591950 if rift_name == "Silly Egg" else 16761600
        embeds = [{
            "title": f"🌟 {rift_name} has been FOUND! 🌟",
            "description": description,
            "color": embed_color,
            "thumbnail": {"url": rift_thumbnails.get(rift_name, "")},
            "footer": {
                "text": "Noteab's BGSI Macro (v1.0-alpha)",
                "icon_url": "https://i.postimg.cc/sDmwGxM3/icon.png"
            }
        }]

        response = requests.post(
            webhook_url,
            json={
            "content": content,
                "embeds": embeds
        }
        )
        response.raise_for_status()
        print(f"Webhook sent successfully for {rift_name}: {response.status_code}")
            
    def send_egg_hatch_webhook(self, username, pet_name, chance, pet_color):
        webhook_url = self.config.get("webhook_url")
        if not webhook_url: return
        
        try:
            if 'E' in chance or 'e' in chance:
                chance_value = float(chance.strip('%')) / 100 if '%' in chance else float(chance)
            else:
                chance_value = float(chance.strip('%')) / 100

            if chance_value > 0:
                one_in_x = round(1 / chance_value)
                formatted_chance = f"{chance} (1 in {one_in_x})"
            else:
                formatted_chance = chance
                
        except ValueError:
            formatted_chance = chance

        color_decimal = int(pet_color.lstrip("#"), 16)

        embeds = [{
            "title": f"🥚 Egg Hatching Detection 🥚",
            "fields": [
                {"name": "Username", "value": username, "inline": True},
                {"name": "Hatched", "value": pet_name, "inline": True},
                {"name": "Rarity of", "value": formatted_chance, "inline": True},
                {"name": "Hatched date", "value": datetime.now().strftime("%A, %B %d, %Y %I:%M %p"), "inline": False}
            ],
            "color": color_decimal,
            "footer": {
                "text": "Noteab's BGSI Macro (v1.0-alpha)",
                "icon_url": "https://i.postimg.cc/sDmwGxM3/icon.png"
            }
        }]

        response = requests.post(
                webhook_url,
                json={
                    "content": "",
                            "embeds": embeds
                }
            )
        response.raise_for_status()
        print(f"Egg hatch webhook sent successfully: {response.status_code}")
                   
    def send_webhook_status(self, status, color=None):
        try:
            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                print("Webhook URL is missing/not included in the config.json")
                return
            
            default_color = 3066993 if "started" in status.lower() else 15158332
            embed_color = color if color is not None else default_color
            icon_url = "https://i.postimg.cc/sDmwGxM3/icon.png"

            embeds = [{
                "title": "🌟 Macro Status 🌟",
                "description": f"## [{time.strftime('%H:%M:%S')}] \n ## > {status}",
                "color": embed_color,
                "footer": {
                    "text": "Noteab's BGSI Macro (v1.0-alpha)",
                    "icon_url": icon_url
                }
            }]
            response = requests.post(
                webhook_url,
                data={"payload_json": json.dumps({"embeds": embeds})}
            )
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f"Failed to send webhook: {e}")
        except Exception as e:
            print(f"An error occurred in webhook_status: {e}")
        
    def activate_roblox_window(self):
        windows = gw.getAllTitles()
        roblox_window = None
        
        for window in windows:
            if "Roblox" in window:
                roblox_window = gw.getWindowsWithTitle(window)[0]
                break

        if roblox_window:
            try:
                roblox_window.activate()
            except Exception as e:
                print(f"Failed to activate window: {e}")
        else:
            print("Roblox window not found.")
    
    def autoit_hold_left_click(self, posX, posY, holdTime=3300):
        autoit.mouse_click("left", posX, posY, 5, speed=2)
        time.sleep(0.13)
        autoit.mouse_click("left", posX, posY, 3, speed=2)
        autoit.mouse_down("left")
        time.sleep(holdTime / 1000)
        autoit.mouse_up("left")

    def camera_align(self):
        autoit.mouse_click("left", 1152, 381)
        time.sleep(0.5)
        autoit.mouse_click("left", 1152, 381)
        time.sleep(1.75)
        autoit.mouse_click_drag(1152, 381, 1152, 381 + 50, "right")
    
    def start_anti_afk_timer(self):
        if self.detection_running:
            current_time = time.time()
            #print(current_time - self.last_anti_afk_time)
            if current_time - self.last_anti_afk_time >= self.anti_afk_interval:
                self.anti_afk_action()
                self.last_anti_afk_time = current_time
            threading.Timer(5, self.start_anti_afk_timer).start()

    def anti_afk_action(self):
        try:
            if self.config.get("anti_afk") and not self.enable_farming_var.get():
                for _ in range(4):
                    if not self.detection_running: return
                    self.activate_roblox_window()
                    time.sleep(0.1)

                self.Global_MouseClick(1253, 400)
                time.sleep(0.5)
                self.Global_MouseClick(1253, 400)
                time.sleep(0.5)

        except Exception as e:
            self.error_logging(e, "Error in anti_afk_action function.")
    
    def teleport_to_farm_world(self, target="zen", world_scroll="up", world_scroll_amount=15):
        for _ in range(4):
            if not self.detection_running: return
            self.activate_roblox_window()
            time.sleep(0.35)
        
        world_mapicon = self.config.get("world_mapicon", [737, 314])
        overworld_mapicon = self.config.get("overworld_mapicon", [937, 560])
        zen_mapicon = self.config.get("zen_mapicon", [769, 280])
        world_teleport_button = self.config.get("world_teleport_button", [1045, 673])
        
        self.Global_MouseClick(world_mapicon[0], world_mapicon[1])
        time.sleep(1.95)
        
        autoit.mouse_move(1152, 381, speed=-1)
        autoit.mouse_wheel(world_scroll, world_scroll_amount)
        time.sleep(1.5)
        
        # map to click
        if target == "zen":
            self.Global_MouseClick(zen_mapicon[0], zen_mapicon[1])
        elif target == "overworld":
            self.Global_MouseClick(overworld_mapicon[0], overworld_mapicon[1])
        else:
            raise ValueError(f"Unknown teleport target: {target}")
        time.sleep(1.2)
        self.Global_MouseClick(world_teleport_button[0], world_teleport_button[1])
        self.Global_MouseClick(world_teleport_button[0], world_teleport_button[1])
        time.sleep(3.5)
        
        # zoom in and out for cam view
        autoit.mouse_wheel("up", 20)
        time.sleep(2.3)
        autoit.mouse_wheel("down", 12)
        time.sleep(1.6)

if __name__ == "__main__":
    try:
        app_ok_bro = BGSI_Main()
    except KeyboardInterrupt:
        print("Exited (Keyboard Interrupted)")
    finally:
        keyboard.unhook_all()