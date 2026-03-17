import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import threading
import time
import json
import os
import sys
from pathlib import Path
import pystray
from PIL import Image, ImageDraw
import atexit
import winreg
from json import JSONDecodeError

class LooprAudio:
    def __init__(self):
        time.sleep(3)  # Brief delay for Windows startup stability

        self.root = tk.Tk()
        self.root.title("Loopr Audio")
        self.root.geometry("480x360")
        self.root.resizable(False, False)
        
        # Indigo color scheme - improved contrast
        self.colors = {
            'primary': '#4F46E5',      # Indigo-600
            'primary_dark': '#3730A3',  # Indigo-700
            'primary_light': '#6366F1', # Indigo-500
            'background': '#1E1B4B',    # Indigo-900
            'surface': '#312E81',       # Indigo-800
            'surface_light': '#4338CA', # Indigo-600 
            'text': '#F1F5F9',         # Slate-100 - better contrast
            'text_secondary': '#CBD5E1', # Slate-300 - better contrast
            'accent': '#8B5CF6',       # Violet-500
            'success': '#10B981',      # Emerald-500
            'warning': '#F59E0B'       # Amber-500
        }
        
        # Set window background
        self.root.configure(bg=self.colors['background'])
        
        # Load and set window icon
        self.set_window_icon()
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Audio state
        self.current_file = None
        self.is_playing = False
        self.is_looping = True
        self.volume = 0.7
        self.music_thread = None
        self.should_stop = False
        
        # Startup setting
        self.run_on_startup = False
        
        # Config file path - make it relative to the application location, not working directory
        if getattr(sys, 'frozen', False):
            # Running as compiled executable - config next to the exe
            config_dir = Path(sys.executable).parent
        else:
            # Running as Python script - config next to the script
            config_dir = Path(__file__).parent
        
        self.config_file = config_dir / "config.json"
        
        # System tray
        self.tray_icon = None

        # Load saved settings
        self.load_config()
        
        # Configure styles
        self.setup_styles()
        
        # Setup GUI
        self.setup_gui()
        
        # Setup system tray
        self.setup_tray()

        # Restore playback state from last run (simple play/stop flag)
        if self.is_playing:
            if isinstance(self.current_file, (str, os.PathLike)) and self.current_file and os.path.exists(self.current_file):
                self.start_playback()
            else:
                # Invalid or missing path; reset playback state to avoid startup crash
                self.is_playing = False
                self.current_file = None
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
    
    def get_display_filename(self, max_chars=40):
        """Get a truncated filename for display"""
        if not self.current_file:
            return "No file selected"
        
        filename = os.path.basename(self.current_file)
        if len(filename) <= max_chars:
            return filename
        
        # Truncate and add ellipsis
        # Try to preserve the file extension
        name, ext = os.path.splitext(filename)
        available_chars = max_chars - len(ext) - 3  # 3 for "..."
        
        if available_chars > 0:
            return name[:available_chars] + "..." + ext
        else:
            # If even the extension is too long, just truncate the whole thing
            return filename[:max_chars-3] + "..."
    
    def get_full_filename_tooltip(self):
        """Get the full filename for tooltip"""
        if not self.current_file:
            return "No file selected"
        return os.path.basename(self.current_file)
    
    def create_tooltip(self, widget, text_func):
        """Create a tooltip for a widget"""
        def on_enter(event):
            tooltip_text = text_func()
            if hasattr(self, 'tooltip_window'):
                self.tooltip_window.destroy()
            
            self.tooltip_window = tk.Toplevel()
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.configure(bg=self.colors['surface_light'])
            
            label = tk.Label(self.tooltip_window, 
                           text=tooltip_text,
                           bg=self.colors['surface_light'],
                           fg=self.colors['text'],
                           font=('Segoe UI', 8),
                           padx=5, pady=2)
            label.pack()
            
            # Position tooltip
            x = widget.winfo_rootx() + 10
            y = widget.winfo_rooty() + widget.winfo_height() + 5
            self.tooltip_window.geometry(f"+{x}+{y}")
        
        def on_leave(event):
            if hasattr(self, 'tooltip_window'):
                self.tooltip_window.destroy()
                delattr(self, 'tooltip_window')
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def get_resource_path(self, relative_path):
        """Get the absolute path to a resource, works for both development and PyInstaller builds"""
        if getattr(sys, 'frozen', False):
            # PyInstaller bundle - resources are in the _internal directory created by PyInstaller
            base_path = Path(sys.executable).parent / "_internal"
        else:
            # Running in development mode - resources are in our _internal folder relative to the script
            base_path = Path(__file__).parent / "_internal"
        
        return base_path / relative_path
    
    def set_window_icon(self):
        """Set the window icon using the project icon file"""
        try:
            # Try to load the icon file using the resource path
            icon_path = self.get_resource_path("loopr_icon.ico")
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
                print(f"Using window icon: {icon_path}")
                return
            
            # Fallback to PNG if ICO doesn't exist
            png_path = self.get_resource_path("loopr_icon.png")
            if png_path.exists():
                # Convert PNG to ICO format for tkinter
                try:
                    from PIL import Image
                    img = Image.open(png_path)
                    # Save as temporary ICO file in the same directory
                    temp_ico = png_path.parent / "temp_icon.ico"
                    img.save(temp_ico, format='ICO')
                    self.root.iconbitmap(str(temp_ico))
                    print(f"Using converted PNG icon: {png_path}")
                    return
                except Exception as e:
                    print(f"Could not convert PNG to ICO: {e}")
            
            print("No icon files found, using default tkinter icon")
            
        except Exception as e:
            print(f"Could not set window icon: {e}")
            # Use default tkinter icon on error
    
    def setup_styles(self):
        """Configure ttk styles for indigo theme"""
        style = ttk.Style()
        
        # Set theme to avoid conflicts
        style.theme_use('clam')
        
        # Configure button style
        style.configure('Indigo.TButton',
                       background=self.colors['primary'],
                       foreground='white',
                       borderwidth=1,
                       focuscolor='none',
                       relief='flat',
                       font=('Segoe UI', 10, 'bold'))
        
        style.map('Indigo.TButton',
                 background=[('active', self.colors['primary_light']),
                            ('pressed', self.colors['primary_dark'])],
                 foreground=[('active', 'white'),
                            ('pressed', 'white'),
                            ('focus', 'white')])
        
        # Configure play button style
        style.configure('Play.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       borderwidth=1,
                       focuscolor='none',
                       relief='flat',
                       font=('Segoe UI', 11, 'bold'))
        
        style.map('Play.TButton',
                 background=[('active', '#059669'),  # Emerald-600
                            ('pressed', '#047857')],  # Emerald-700
                 foreground=[('active', 'white'),
                            ('pressed', 'white'),
                            ('focus', 'white')])
        
        # Configure stop button style
        style.configure('Stop.TButton',
                       background=self.colors['warning'],
                       foreground='white',
                       borderwidth=1,
                       focuscolor='none',
                       relief='flat',
                       font=('Segoe UI', 11, 'bold'))
        
        style.map('Stop.TButton',
                 background=[('active', '#D97706'),  # Amber-600
                            ('pressed', '#B45309')],  # Amber-700
                 foreground=[('active', 'white'),
                            ('pressed', 'white'),
                            ('focus', 'white')])
        
        # Configure label styles
        style.configure('Title.TLabel',
                       background=self.colors['background'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 12, 'bold'),
                       relief='flat')
        
        style.configure('Info.TLabel',
                       background=self.colors['surface'],
                       foreground=self.colors['text_secondary'],
                       font=('Segoe UI', 9),
                       relief='flat')
        
        # Special style for volume control labels
        style.configure('Volume.TLabel',
                       background=self.colors['surface'],
                       foreground=self.colors['text_secondary'],
                       font=('Segoe UI', 9),
                       relief='flat')
        
        style.configure('File.TLabel',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 9),
                       relief='flat',
                       padding=(10, 5))
        
        # Configure checkbutton style
        style.configure('Indigo.TCheckbutton',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10),
                       focuscolor='none',
                       relief='flat')
        
        style.map('Indigo.TCheckbutton',
                 background=[('active', self.colors['surface']),
                            ('pressed', self.colors['surface'])],
                 foreground=[('active', self.colors['text']),
                            ('pressed', self.colors['text'])])
        
        # Configure scale style
        style.configure('Indigo.Horizontal.TScale',
                       background=self.colors['surface'],
                       troughcolor=self.colors['surface_light'],
                       borderwidth=0,
                       lightcolor=self.colors['primary'],
                       darkcolor=self.colors['primary'],
                       relief='flat')
        
        # Configure frame styles to fix background issues
        style.configure('Card.TFrame',
                       background=self.colors['surface'],
                       relief='flat',
                       borderwidth=1)
    
    def setup_gui(self):
        """Setup the main GUI elements with indigo theme"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['background'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎵 Loopr Audio", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # File selection section
        file_section = tk.Frame(main_frame, bg=self.colors['surface'], relief='flat', bd=1)
        file_section.pack(fill='x', pady=(0, 15))
        
        file_title = ttk.Label(file_section, text="Audio File", style='Info.TLabel')
        file_title.pack(anchor='w', padx=15, pady=(10, 5))
        
        file_content = tk.Frame(file_section, bg=self.colors['surface'])
        file_content.pack(fill='x', padx=15, pady=(0, 15))
        
        self.file_label = ttk.Label(file_content, 
                                   text=self.get_display_filename(),
                                   style='File.TLabel')
        self.file_label.pack(side='left', fill='x', expand=True)
        
        # Add tooltip for full filename
        self.create_tooltip(self.file_label, self.get_full_filename_tooltip)
        
        browse_btn = ttk.Button(file_content, text="Browse", style='Indigo.TButton', command=self.browse_file)
        browse_btn.pack(side='right', padx=(10, 0))
        
        # Controls section
        controls_section = tk.Frame(main_frame, bg=self.colors['surface'], relief='flat', bd=1)
        controls_section.pack(fill='x', pady=(0, 15))
        
        controls_title = ttk.Label(controls_section, text="Playback Controls", style='Info.TLabel')
        controls_title.pack(anchor='w', padx=15, pady=(10, 5))
        
        controls_content = tk.Frame(controls_section, bg=self.colors['surface'])
        controls_content.pack(fill='x', padx=15, pady=(0, 15))
        
        # Play/Stop button
        self.play_button = ttk.Button(controls_content, text="▶ Play", style='Play.TButton', command=self.toggle_play)
        self.play_button.pack(side='left', padx=(0, 15))
        
        # Loop checkbox
        self.loop_var = tk.BooleanVar(value=self.is_looping)
        self.loop_checkbox = ttk.Checkbutton(controls_content, text="🔁 Loop", 
                                           variable=self.loop_var, command=self.toggle_loop,
                                           style='Indigo.TCheckbutton')
        self.loop_checkbox.pack(side='left', padx=(0, 15))
        
        # Startup checkbox
        self.startup_var = tk.BooleanVar(value=self.run_on_startup)
        self.startup_checkbox = ttk.Checkbutton(controls_content, text="🚀 Start with Windows", 
                                              variable=self.startup_var, command=self.toggle_startup,
                                              style='Indigo.TCheckbutton')
        self.startup_checkbox.pack(side='left')
        
        # Volume section
        volume_section = tk.Frame(main_frame, bg=self.colors['surface'], relief='flat', bd=1)
        volume_section.pack(fill='x')
        
        volume_title = ttk.Label(volume_section, text="Volume Control", style='Info.TLabel')
        volume_title.pack(anchor='w', padx=15, pady=(10, 5))
        
        volume_content = tk.Frame(volume_section, bg=self.colors['surface'])
        volume_content.pack(fill='x', padx=15, pady=(0, 15))
        
        volume_icon = ttk.Label(volume_content, text="🔊", style='Volume.TLabel')
        volume_icon.pack(side='left', padx=(0, 10))
        
        self.volume_var = tk.DoubleVar(value=self.volume)
        self.volume_scale = ttk.Scale(volume_content, from_=0, to=1, orient=tk.HORIZONTAL,
                                    variable=self.volume_var, command=self.on_volume_change,
                                    style='Indigo.Horizontal.TScale')
        self.volume_scale.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Volume percentage entry (fixed width)
        volume_entry_frame = tk.Frame(volume_content, bg=self.colors['surface'])
        volume_entry_frame.pack(side='right')
        
        # Create entry widget for volume percentage
        self.volume_entry_var = tk.StringVar(value=str(int(self.volume * 100)))
        self.volume_entry = tk.Entry(volume_entry_frame, 
                                   textvariable=self.volume_entry_var,
                                   width=4,
                                   justify='center',
                                   bg=self.colors['surface_light'],
                                   fg=self.colors['text'],
                                   font=('Segoe UI', 9),
                                   relief='flat',
                                   bd=1)
        self.volume_entry.pack(side='left')
        
        # Bind entry events
        self.volume_entry.bind('<Return>', self.on_volume_entry_change)
        self.volume_entry.bind('<FocusOut>', self.on_volume_entry_change)
        
        # Static width label for '%' symbol
        percent_label = ttk.Label(volume_entry_frame, text="%", style='Volume.TLabel')
        percent_label.pack(side='left', padx=(2, 0))
        
        # Update file label and volume entry if we have saved settings
        if self.current_file:
            self.file_label.config(text=self.get_display_filename())
        
        # Initialize volume entry with current volume
        self.volume_entry_var.set(str(int(self.volume * 100)))
    
    def setup_tray(self):
        """Setup system tray icon using the same icon as the window"""
        try:
            # Try to load the same icon file used for the window
            icon_path = self.get_resource_path("loopr_icon.ico")
            
            if icon_path.exists():
                # Load the ICO file and convert to PIL Image
                image = Image.open(icon_path)
                # Convert to RGB if it's not already
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                # Resize to appropriate size for system tray
                image = image.resize((64, 64), Image.Resampling.LANCZOS)
                print(f"Using tray icon from ICO: {icon_path}")
            else:
                # Try PNG fallback
                png_path = self.get_resource_path("loopr_icon.png")
                if png_path.exists():
                    image = Image.open(png_path)
                    # Convert to RGB if it's not already
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    # Resize to appropriate size for system tray
                    image = image.resize((64, 64), Image.Resampling.LANCZOS)
                    print(f"Using tray icon from PNG: {png_path}")
                else:
                    # No custom icons found - create simple default
                    print("No custom icon files found, using simple default tray icon")
                    image = Image.new('RGB', (64, 64), color=(128, 128, 128))  # Simple gray icon
            
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Play/Pause", self.toggle_play),
                pystray.MenuItem("Exit", self.quit_app)
            )
            
            self.tray_icon = pystray.Icon("LooprAudio", image, "Loopr Audio", menu)
            
        except Exception as e:
            print(f"Could not set up tray icon: {e}")
            # Create a simple fallback icon
            image = Image.new('RGB', (64, 64), color=(128, 128, 128))  # Simple gray fallback
            menu = pystray.Menu(
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Play/Pause", self.toggle_play),
                pystray.MenuItem("Exit", self.quit_app)
            )
            self.tray_icon = pystray.Icon("LooprAudio", image, "Loopr Audio", menu)
    
    def browse_file(self):
        """Open file dialog to select audio file"""
        filetypes = [
            ("Audio files", "*.mp3 *.wav *.ogg *.m4a"),
            ("MP3 files", "*.mp3"),
            ("WAV files", "*.wav"),
            ("OGG files", "*.ogg"),
            ("M4A files", "*.m4a"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=filetypes
        )
        
        if filename:
            self.current_file = filename
            self.file_label.config(text=self.get_display_filename())
            self.save_config()
            
            # Stop current playback if any
            if self.is_playing:
                self.stop_playback()
    
    def toggle_play(self):
        """Toggle play/pause"""
        if not self.current_file:
            messagebox.showwarning("No File", "Please select an audio file first.")
            return
        
        if not os.path.exists(self.current_file):
            messagebox.showerror("File Not Found", "The selected audio file no longer exists.")
            return
        
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()
    
    def start_playback(self):
        """Start playing the audio file"""
        try:
            self.should_stop = False
            self.is_playing = True
            self.play_button.config(text="⏹ Stop", style='Stop.TButton')
            
            # Start playback in a separate thread
            self.music_thread = threading.Thread(target=self.play_music, daemon=True)
            self.music_thread.start()
            
        except Exception as e:
            messagebox.showerror("Playback Error", f"Error starting playback: {str(e)}")
            self.is_playing = False
            self.play_button.config(text="▶ Play", style='Play.TButton')
    
    def stop_playback(self):
        """Stop playing the audio file"""
        self.should_stop = True
        self.is_playing = False
        self.play_button.config(text="▶ Play", style='Play.TButton')
        
        try:
            pygame.mixer.music.stop()
        except:
            pass
    
    def play_music(self):
        """Music playback loop (runs in separate thread)"""
        try:
            pygame.mixer.music.load(self.current_file)
            pygame.mixer.music.set_volume(self.volume)
            
            # Use pygame's built-in looping for seamless playback
            # -1 means loop infinitely, 0 means play once
            loops = -1 if self.is_looping else 0
            pygame.mixer.music.play(loops=loops)
            
            # Wait for music to finish or stop signal
            while pygame.mixer.music.get_busy() and not self.should_stop:
                time.sleep(0.1)

        except (pygame.error, RuntimeError, FileNotFoundError, OSError) as e:
            print(f"Playback error: {e}")
        finally:
            if not self.should_stop:
                # Music ended naturally (not stopped by user)
                self.root.after(0, self.on_music_ended)
    
    def on_music_ended(self):
        """Called when music ends naturally"""
        self.is_playing = False
        self.play_button.config(text="▶ Play", style='Play.TButton')
    
    def toggle_loop(self):
        """Toggle loop mode"""
        self.is_looping = self.loop_var.get()
        self.save_config()
        
        # If music is currently playing, restart it with new loop setting
        if self.is_playing and self.current_file:
            # Get current position (not available in pygame.mixer.music, so we restart from beginning)
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.current_file)
            pygame.mixer.music.set_volume(self.volume)
            
            # Apply new loop setting
            loops = -1 if self.is_looping else 0
            pygame.mixer.music.play(loops=loops)
    
    def on_volume_change(self, value):
        """Handle volume slider change"""
        self.volume = float(value)
        
        # Update the entry widget (avoid triggering its event)
        self.volume_entry_var.set(str(int(self.volume * 100)))
        
        # Update pygame volume if playing
        try:
            pygame.mixer.music.set_volume(self.volume)
        except:
            pass
        
        self.save_config()
    
    def on_volume_entry_change(self, event=None):
        """Handle volume entry field change"""
        try:
            # Get the value from the entry
            entry_value = self.volume_entry_var.get().strip()
            
            # Parse the percentage
            if entry_value.endswith('%'):
                entry_value = entry_value[:-1]  # Remove % symbol if present
            
            volume_percent = int(entry_value)
            
            # Clamp between 0 and 100
            volume_percent = max(0, min(100, volume_percent))
            
            # Convert to 0-1 range
            self.volume = volume_percent / 100.0
            
            # Update the slider without triggering its callback
            self.volume_var.set(self.volume)
            
            # Update the entry to show the clamped value
            self.volume_entry_var.set(str(volume_percent))
            
            # Update pygame volume if playing
            try:
                pygame.mixer.music.set_volume(self.volume)
            except:
                pass
            
            self.save_config()
            
        except ValueError:
            # If invalid input, reset to current volume
            self.volume_entry_var.set(str(int(self.volume * 100)))
    
    def load_config(self):
        """Load saved configuration"""
        self.current_file = None
        self.volume = 0.7
        self.is_looping = True
        self.run_on_startup = False
        self.is_playing = False

        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            self.current_file = config.get('current_file')
            self.volume = config.get('volume', 0.7)
            self.is_looping = config.get('is_looping', True)
            self.run_on_startup = config.get('run_on_startup', False)
            self.is_playing = config.get('is_playing', False)

            # Reconcile run_on_startup with actual registry state.
            # If the registry was changed outside the app, this ensures
            # the in-memory flag (and UI) matches the real startup status.
            try:
                registry_startup = self.check_startup_status()
                if isinstance(registry_startup, bool):
                    self.run_on_startup = registry_startup
            except Exception as registry_error:
                # If we cannot read the registry, fall back to the config value.
                print(f"Error checking startup status from registry: {registry_error}")

        except (JSONDecodeError, OSError, TypeError, ValueError) as e:
            print(f"Error loading config, using defaults: {e}")
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save current configuration"""
        try:
            config = {
                'current_file': self.current_file,
                'volume': self.volume,
                'is_looping': self.is_looping,
                'run_on_startup': self.run_on_startup,
                'is_playing': self.is_playing
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"Error saving config: {e}")
    
    @property
    def is_playing(self):
        """Current playback state, persisted to config.json."""
        # Use a backing attribute so we can hook assignment via the setter.
        return getattr(self, '_is_playing', False)
    
    @is_playing.setter
    def is_playing(self, value):
        """Update playback state and persist to config when available."""
        new_value = bool(value)
        # Get the previous value, defaulting to False if unset.
        old_value = getattr(self, '_is_playing', False)
        # Always update the backing field, but only persist on real changes.
        self._is_playing = new_value
        if new_value == old_value:
            return
        # During very early initialization, config_file may not yet exist.
        if not hasattr(self, 'config_file'):
            return
        try:
            self.save_config()
        except Exception as e:
            # Avoid breaking playback control if saving fails.
            print(f"Error saving config after is_playing change: {e}")
    
    def on_window_close(self):
        """Handle window close event - minimize to tray"""
        self.hide_window()
    
    def hide_window(self):
        """Hide the main window and show tray icon"""
        self.root.withdraw()
        if self.tray_icon and not self.tray_icon.visible:
            # Start tray icon in a separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def add_to_startup(self):
        """Add Loopr Audio to Windows startup"""
        try:
            # Get the path to the executable
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                exe_path = sys.executable
            else:
                # Running as Python script - use python.exe + script path
                script_path = Path(__file__).resolve()
                exe_path = f'"{sys.executable}" "{script_path}"'
            
            # Registry key for startup programs
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            
            # Open the registry key
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            # Set the registry value
            winreg.SetValueEx(key, "LooprAudio", 0, winreg.REG_SZ, exe_path)
            
            # Close the key
            winreg.CloseKey(key)
            
            self.run_on_startup = True
            self.save_config()
            messagebox.showinfo("Success", "Loopr Audio has been added to Windows startup!")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add to startup: {e}")
            return False
    
    def remove_from_startup(self):
        """Remove Loopr Audio from Windows startup"""
        try:
            # Registry key for startup programs
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            
            # Open the registry key
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            # Delete the registry value
            winreg.DeleteValue(key, "LooprAudio")
            
            # Close the key
            winreg.CloseKey(key)
            
            self.run_on_startup = False
            self.save_config()
            messagebox.showinfo("Success", "Loopr Audio has been removed from Windows startup!")
            return True
            
        except FileNotFoundError:
            # Already not in startup
            self.run_on_startup = False
            self.save_config()
            messagebox.showinfo("Info", "Loopr Audio was not found in startup programs.")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove from startup: {e}")
            return False
    
    def check_startup_status(self):
        """Check if Loopr Audio is in Windows startup"""
        try:
            # Registry key for startup programs
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            
            # Open the registry key
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            
            # Try to read the value
            value, _ = winreg.QueryValueEx(key, "LooprAudio")
            
            # Close the key
            winreg.CloseKey(key)
            
            return True
            
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error checking startup status: {e}")
            return False
    
    def toggle_startup(self):
        """Toggle startup setting based on checkbox"""
        if self.startup_var.get():
            self.add_to_startup()
        else:
            self.remove_from_startup()
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        self.cleanup()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
    
    def cleanup(self):
        """Cleanup resources"""
        self.should_stop = True
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except:
            pass
        self.save_config()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    app = LooprAudio()
    app.run()

if __name__ == "__main__":
    main()
