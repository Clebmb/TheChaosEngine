import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import shutil
import random
import string
import threading

class ChaosEngineApp:
    def __init__(self, root):
        self.root = root
        root.title("The Chaos Engine - Digital Ritual Chamber")
        
        BG_COLOR = '#2E2E2E'
        FG_COLOR = '#E0E0E0'
        ENTRY_BG = '#3C3F41'
        ENTRY_FG = 'white'
        BUTTON_BG_SECONDARY = '#4A4A4A'
        BUTTON_FG_SECONDARY = 'white'
        BUTTON_ACTIVE_SECONDARY = '#5A5A5A'
        ACCENT_COLOR = '#7B1FA2'
        ACCENT_ACTIVE = '#9C27B0'
        CHRONICLE_BG = '#252526'
        CHRONICLE_FG = '#D4D4D4'
        PROGRESS_TROUGH = '#3C3F41'
        CHECKBOX_FG = '#B0B0B0' # Lighter gray for checkbox text

        root.configure(bg=BG_COLOR)

        self.intent_source_path = tk.StringVar()
        self.ritual_space_path = tk.StringVar()
        self.archive_to_cache_var = tk.BooleanVar(value=False) # Variable for checkbox

        style = ttk.Style()
        style.theme_use('clam') 
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=('Georgia', 11))
        style.configure("TEntry", fieldbackground=ENTRY_BG, foreground=ENTRY_FG, insertbackground=ENTRY_FG, font=('Segoe UI', 10), borderwidth=1, relief=tk.FLAT)
        style.map("TEntry", bordercolor=[('focus', ACCENT_COLOR)], highlightcolor=[('focus', ACCENT_COLOR)])
        style.configure("Secondary.TButton", background=BUTTON_BG_SECONDARY, foreground=BUTTON_FG_SECONDARY, font=('Georgia', 10), padding=(8, 4))
        style.map("Secondary.TButton", background=[('active', BUTTON_ACTIVE_SECONDARY)], relief=[('pressed', tk.SUNKEN), ('!pressed', tk.RAISED)])
        style.configure("Accent.TButton", background=ACCENT_COLOR, foreground='white', font=('Georgia', 12, 'bold'), padding=(10, 6))
        style.map("Accent.TButton", background=[('active', ACCENT_ACTIVE)], relief=[('pressed', tk.SUNKEN), ('!pressed', tk.RAISED)])
        style.configure("TProgressbar", troughcolor=PROGRESS_TROUGH, background=ACCENT_COLOR, thickness=18)
        style.configure("TCheckbutton", background=BG_COLOR, foreground=CHECKBOX_FG, font=('Georgia', 10), indicatorcolor=ENTRY_BG)
        style.map("TCheckbutton",
                  indicatorcolor=[('selected', ACCENT_COLOR), ('!selected', ENTRY_BG)],
                  foreground=[('active', FG_COLOR)])


        main_frame = ttk.Frame(root, padding="15 15 15 15", style="TFrame")
        style.configure("TFrame", background=BG_COLOR)
        main_frame.grid(row=0, column=0, sticky="nsew")
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        ttk.Label(main_frame, text="Source of Intent (The Seed):").grid(row=0, column=0, padx=(0,10), pady=(0,5), sticky="w")
        self.intent_entry = ttk.Entry(main_frame, textvariable=self.intent_source_path, width=48)
        self.intent_entry.grid(row=0, column=1, padx=0, pady=(0,5), sticky="ew")
        ttk.Button(main_frame, text="Choose Intent...", command=self.browse_intent_source, style="Secondary.TButton").grid(row=0, column=2, padx=(8,0), pady=(0,5))

        ttk.Label(main_frame, text="The Ritual Space (The Crucible):").grid(row=1, column=0, padx=(0,10), pady=(5,5), sticky="w") # Reduced bottom pady
        self.ritual_entry = ttk.Entry(main_frame, textvariable=self.ritual_space_path, width=48)
        self.ritual_entry.grid(row=1, column=1, padx=0, pady=(5,5), sticky="ew")
        ttk.Button(main_frame, text="Designate Space...", command=self.browse_ritual_space, style="Secondary.TButton").grid(row=1, column=2, padx=(8,0), pady=(5,5))

        main_frame.grid_columnconfigure(1, weight=1)

        # Archive Checkbox
        self.archive_checkbox = ttk.Checkbutton(main_frame, text="Archive Transmuted Space to C:/ritualCache", variable=self.archive_to_cache_var)
        self.archive_checkbox.grid(row=2, column=0, columnspan=3, pady=(5,10), sticky="w")


        self.commence_button = ttk.Button(main_frame, text="Initiate the Working", command=self.start_working_thread, style="Accent.TButton")
        self.commence_button.grid(row=3, column=0, columnspan=3, pady=(5,15), sticky="ew") # Adjusted pady

        ttk.Label(main_frame, text="Chronicle of the Working:").grid(row=4, column=0, columnspan=3, pady=(5,2), sticky="w")
        self.chronicle_text = tk.Text(main_frame, height=7, width=68, state=tk.DISABLED, bg=CHRONICLE_BG, fg=CHRONICLE_FG, font=('Courier New', 10), relief=tk.SOLID, borderwidth=1, padx=5, pady=5, highlightthickness=1, highlightbackground=BUTTON_BG_SECONDARY, highlightcolor=ACCENT_COLOR)
        self.chronicle_text.grid(row=5, column=0, columnspan=3, pady=(0,10), sticky="ew")
        
        self.transmutation_bar = ttk.Progressbar(main_frame, orient="horizontal", length=500, mode="determinate")
        self.transmutation_bar.grid(row=6, column=0, columnspan=3, pady=(5,0), sticky="ew")

        # Adjust window height to accommodate the new checkbox
        root.geometry(f"620x480") # Increased height
        root.resizable(False, False)

    def chronicle_entry(self, message):
        self.chronicle_text.config(state=tk.NORMAL)
        self.chronicle_text.insert(tk.END, f">> {message}\n")
        self.chronicle_text.see(tk.END)
        self.chronicle_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def browse_intent_source(self):
        folder_selected = filedialog.askdirectory(title="Select the Source of Your Intent")
        if folder_selected:
            self.intent_source_path.set(folder_selected)
            self.chronicle_entry(f"Intent Source chosen: {folder_selected}")

    def browse_ritual_space(self):
        folder_selected = filedialog.askdirectory(title="Designate the Ritual Space for Transformation")
        if folder_selected:
            self.ritual_space_path.set(folder_selected)
            self.chronicle_entry(f"Ritual Space designated: {folder_selected}")

    def generate_glyph_of_obscurity(self, length=12):
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(characters) for i in range(length))

    def start_working_thread(self):
        source_intent = self.intent_source_path.get()
        ritual_space = self.ritual_space_path.get()

        if not source_intent or not ritual_space:
            messagebox.showerror("Incomplete Invocation", "Both the Source of Intent and the Ritual Space must be defined.")
            self.chronicle_entry("Error: Invocation incomplete. Define both Source and Space.")
            return
        if not os.path.isdir(source_intent):
            messagebox.showerror("Illusory Source", f"The Source of Intent does not manifest in this reality: {source_intent}")
            self.chronicle_entry(f"Error: Illusory Source at {source_intent}")
            return
        if not os.path.isdir(ritual_space):
            messagebox.showerror("Unformed Space", f"The Ritual Space is unformed or beyond reach: {ritual_space}")
            self.chronicle_entry(f"Error: Unformed Ritual Space at {ritual_space}")
            return
        if os.path.abspath(source_intent) == os.path.abspath(ritual_space):
            messagebox.showerror("Paradoxical Invocation", "The Source of Intent and Ritual Space cannot be one and the same. Choose distinct loci.")
            self.chronicle_entry("Error: Paradox! Source and Space are identical.")
            return

        self.commence_button.config(state=tk.DISABLED, text="The Working Unfolds...")
        self.transmutation_bar["value"] = 0
        self.transmutation_bar["maximum"] = 100

        working_thread = threading.Thread(target=self.perform_the_working, args=(source_intent, ritual_space))
        working_thread.start()

    def perform_the_working(self, source_folder_intent, ritual_space_original_path):
        source_basename = os.path.basename(source_folder_intent)
        target_basename_original = os.path.basename(ritual_space_original_path)
        final_location_message = "" # To store where the folder ended up

        try:
            self.chronicle_entry("The currents stir... The Working has begun.")
            self.transmutation_bar["value"] = 5
            self.root.update_idletasks()

            # Phase 1: Banishing (25% of progress) -> completes at 30%
            self.chronicle_entry(f"Phase 1: Banishing influences from '{target_basename_original}'")
            items_in_space = os.listdir(ritual_space_original_path)
            total_items = len(items_in_space) if items_in_space else 1
            for i, item_name in enumerate(items_in_space):
                item_path = os.path.join(ritual_space_original_path, item_name)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path): os.unlink(item_path)
                    elif os.path.isdir(item_path): shutil.rmtree(item_path)
                except Exception as e: self.chronicle_entry(f"   Obstruction banishing {item_name}: {e}")
                self.transmutation_bar["value"] = 5 + int(25 * (i + 1) / total_items)
                self.root.update_idletasks()
            self.chronicle_entry("Banishing complete. The Ritual Space is a Void.")
            self.transmutation_bar["value"] = 30
            self.root.update_idletasks()

            # Phase 2: Imbuing (40% of progress) -> completes at 70%
            self.chronicle_entry(f"Phase 2: Imbuing with Intent from '{source_basename}'")
            items_of_intent = os.listdir(source_folder_intent)
            total_intent_items = len(items_of_intent) if items_of_intent else 1
            for i, item_name in enumerate(items_of_intent):
                s_item = os.path.join(source_folder_intent, item_name)
                d_item = os.path.join(ritual_space_original_path, item_name)
                if os.path.isdir(s_item): shutil.copytree(s_item, d_item, dirs_exist_ok=True)
                else: shutil.copy2(s_item, d_item)
                self.transmutation_bar["value"] = 30 + int(40 * (i + 1) / total_intent_items)
                self.root.update_idletasks()
            self.chronicle_entry("Imbuing complete. The Intent has filled the Space.")
            self.transmutation_bar["value"] = 70
            self.root.update_idletasks()

            # Phase 3: Veiling, Sealing & Optional Archival (15% of progress) -> completes at 85%
            self.chronicle_entry(f"Phase 3: Veiling the Work on '{target_basename_original}'...")
            parent_locus = os.path.dirname(ritual_space_original_path)
            glyph_name = self.generate_glyph_of_obscurity()
            
            # Path of the renamed folder in its original parent directory
            path_after_rename_in_original_parent = os.path.join(parent_locus, glyph_name)
            
            while os.path.exists(path_after_rename_in_original_parent): # Ensure unique glyph in original parent
                glyph_name = self.generate_glyph_of_obscurity()
                path_after_rename_in_original_parent = os.path.join(parent_locus, glyph_name)
            
            os.rename(ritual_space_original_path, path_after_rename_in_original_parent)
            self.chronicle_entry(f"'{target_basename_original}' transmuted to '{glyph_name}' in its original locus.")
            
            final_path_of_glyph_folder = path_after_rename_in_original_parent # Default final path

            if self.archive_to_cache_var.get():
                self.chronicle_entry(f"Archival option selected. Preparing to move '{glyph_name}' to ritualCache.")
                ritual_cache_dir = "C:/ritualCache"
                try:
                    os.makedirs(ritual_cache_dir, exist_ok=True)
                    self.chronicle_entry(f"Ensured ritualCache exists at: {ritual_cache_dir}")
                    
                    destination_in_cache = os.path.join(ritual_cache_dir, glyph_name)
                    
                    # Handle potential name collision in cache
                    if os.path.exists(destination_in_cache):
                        self.chronicle_entry(f"Warning: '{glyph_name}' already exists in ritualCache. Appending suffix.")
                        original_glyph_name = glyph_name
                        suffix_num = 1
                        while os.path.exists(destination_in_cache):
                            glyph_name = f"{original_glyph_name}_{suffix_num}"
                            destination_in_cache = os.path.join(ritual_cache_dir, glyph_name)
                            suffix_num += 1
                        self.chronicle_entry(f"New glyph for cache: '{glyph_name}'")

                    shutil.move(path_after_rename_in_original_parent, destination_in_cache)
                    self.chronicle_entry(f"'{os.path.basename(path_after_rename_in_original_parent)}' archived to: {destination_in_cache}")
                    final_location_message = f"Archived to C:/ritualCache as: {glyph_name}"
                    final_path_of_glyph_folder = destination_in_cache # Update final path
                except Exception as e:
                    self.chronicle_entry(f"   Error during archival: {e}. '{glyph_name}' remains in original locus.")
                    final_location_message = f"Remains in original locus as: {glyph_name} (Archival failed)"
            else:
                final_location_message = f"Remains in original locus as: {glyph_name}"

            self.chronicle_entry(f"The Ritual Space is now sealed under glyph: {os.path.basename(final_path_of_glyph_folder)}")
            self.transmutation_bar["value"] = 85
            self.root.update_idletasks()

            # Phase 4: Dissolving the Source (15% of progress) -> completes at 100%
            self.chronicle_entry(f"Phase 4: Dissolving the original Intent Source '{source_basename}'")
            try:
                shutil.rmtree(source_folder_intent)
                self.chronicle_entry(f"Intent Source '{source_basename}' has been fully dissolved.")
            except Exception as e:
                self.chronicle_entry(f"   Warning: Could not fully dissolve Intent Source '{source_basename}': {e}")
            self.transmutation_bar["value"] = 100
            self.root.update_idletasks()
            
            messagebox.showinfo("The Working is Complete", 
                                f"The transformation is sealed.\n"
                                f"{final_location_message}.\n"
                                f"The original Intent Source '{source_basename}' has been dissolved.")
            # Modified final log message
            self.chronicle_entry(f"--- The Working is Concluded. ---")

        except Exception as e:
            self.chronicle_entry(f"A discordant resonance! The Working faltered: {e}")
            messagebox.showerror("A Disturbance in the Flow", f"An unexpected current disrupted the Working: {e}")
        finally:
            self.commence_button.config(state=tk.NORMAL, text="Initiate the Working")
            self.ritual_space_path.set("") 
            self.intent_source_path.set("") 
            self.chronicle_entry("The Chamber is quiescent. Await the next calling or close the Engine.")

if __name__ == "__main__":
    main_root_altar = tk.Tk()
    app_engine = ChaosEngineApp(main_root_altar)
    main_root_altar.mainloop()