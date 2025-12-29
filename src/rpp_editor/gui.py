"""
RPP Editor GUI - A GUI application for editing and comparing REAPER project files
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from .parser import RPPParser, TrackInfo, compare_tracks


class RPPEditorGUI:
    """Main GUI application for RPP file editing and comparison."""

    def __init__(self, root):
        self.root = root
        self.root.title("RPP Editor - REAPER Project File Editor")
        self.root.geometry("1200x800")

        # Parsers for the two files
        self.parser1: Optional[RPPParser] = None
        self.parser2: Optional[RPPParser] = None

        # Currently selected tracks
        self.selected_track1: Optional[TrackInfo] = None
        self.selected_track2: Optional[TrackInfo] = None

        self.create_widgets()
        self.setup_layout()

    def create_widgets(self):
        """Create all GUI widgets."""

        # Main frame
        self.main_frame = ttk.Frame(self.root)

        # Menu bar
        self.create_menu()

        # File selection frame
        self.file_frame = ttk.Frame(self.main_frame)
        self.create_file_selection_widgets()

        # Comparison frame
        self.comparison_frame = ttk.Frame(self.main_frame)
        self.create_comparison_widgets()

        # Control buttons frame
        self.control_frame = ttk.Frame(self.main_frame)
        self.create_control_widgets()

        # Status bar
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Load two RPP files to begin comparison")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var)

    def create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load File 1", command=self.load_file1)
        file_menu.add_command(label="Load File 2", command=self.load_file2)
        file_menu.add_separator()
        file_menu.add_command(label="Save File 1", command=self.save_file1)
        file_menu.add_command(label="Save File 1 As...", command=self.save_file1_as)
        file_menu.add_command(label="Save File 2", command=self.save_file2)
        file_menu.add_command(label="Save File 2 As...", command=self.save_file2_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_file_selection_widgets(self):
        """Create file selection widgets."""

        # File 1 section
        file1_frame = ttk.LabelFrame(self.file_frame, text="File 1", padding=10)

        self.file1_var = tk.StringVar()
        self.file1_entry = ttk.Entry(
            file1_frame, textvariable=self.file1_var, width=50, state="readonly"
        )
        self.file1_button = ttk.Button(file1_frame, text="Browse...", command=self.load_file1)

        self.file1_info_var = tk.StringVar()
        self.file1_info_label = ttk.Label(
            file1_frame, textvariable=self.file1_info_var, foreground="gray"
        )

        # File 2 section
        file2_frame = ttk.LabelFrame(self.file_frame, text="File 2", padding=10)

        self.file2_var = tk.StringVar()
        self.file2_entry = ttk.Entry(
            file2_frame, textvariable=self.file2_var, width=50, state="readonly"
        )
        self.file2_button = ttk.Button(file2_frame, text="Browse...", command=self.load_file2)

        self.file2_info_var = tk.StringVar()
        self.file2_info_label = ttk.Label(
            file2_frame, textvariable=self.file2_info_var, foreground="gray"
        )

        # Pack widgets
        file1_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.file1_entry.pack(side=tk.LEFT, padx=5)
        self.file1_button.pack(side=tk.RIGHT, padx=5)
        self.file1_info_label.pack(side=tk.BOTTOM, anchor=tk.W, padx=5)

        file2_frame.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.file2_entry.pack(side=tk.LEFT, padx=5)
        self.file2_button.pack(side=tk.RIGHT, padx=5)
        self.file2_info_label.pack(side=tk.BOTTOM, anchor=tk.W, padx=5)

    def create_comparison_widgets(self):
        """Create track comparison widgets."""

        # File 1 tracks
        tracks1_frame = ttk.LabelFrame(self.comparison_frame, text="File 1 Tracks", padding=10)

        self.tracks1_tree = ttk.Treeview(
            tracks1_frame,
            columns=("volume", "pan", "effects", "envelopes"),
            show="tree headings",
            height=15,
        )
        self.tracks1_tree.heading("#0", text="Track Name")
        self.tracks1_tree.heading("volume", text="Volume")
        self.tracks1_tree.heading("pan", text="Pan")
        self.tracks1_tree.heading("effects", text="Effects")
        self.tracks1_tree.heading("envelopes", text="Envelopes")

        # Initial column configuration (will be auto-resized when data is loaded)
        self.tracks1_tree.column("#0", width=200, stretch=False)  # Increased default width
        self.tracks1_tree.column("volume", width=100, stretch=False)
        self.tracks1_tree.column("pan", width=100, stretch=False)
        self.tracks1_tree.column("effects", width=400, stretch=False)  # Increased default width
        self.tracks1_tree.column("envelopes", width=200, stretch=False)

        tracks1_scrollbar = ttk.Scrollbar(
            tracks1_frame, orient=tk.VERTICAL, command=self.tracks1_tree.yview
        )
        self.tracks1_tree.configure(yscrollcommand=tracks1_scrollbar.set)

        tracks1_h_scrollbar = ttk.Scrollbar(
            tracks1_frame, orient=tk.HORIZONTAL, command=self.tracks1_tree.xview
        )
        self.tracks1_tree.configure(xscrollcommand=tracks1_h_scrollbar.set)

        # File 2 tracks
        tracks2_frame = ttk.LabelFrame(self.comparison_frame, text="File 2 Tracks", padding=10)

        self.tracks2_tree = ttk.Treeview(
            tracks2_frame,
            columns=("volume", "pan", "effects", "envelopes"),
            show="tree headings",
            height=15,
        )
        self.tracks2_tree.heading("#0", text="Track Name")
        self.tracks2_tree.heading("volume", text="Volume")
        self.tracks2_tree.heading("pan", text="Pan")
        self.tracks2_tree.heading("effects", text="Effects")
        self.tracks2_tree.heading("envelopes", text="Envelopes")

        # Initial column configuration (will be auto-resized when data is loaded)
        self.tracks2_tree.column("#0", width=200, stretch=False)  # Increased default width
        self.tracks2_tree.column("volume", width=100, stretch=False)
        self.tracks2_tree.column("pan", width=100, stretch=False)
        self.tracks2_tree.column("effects", width=400, stretch=False)  # Increased default width
        self.tracks2_tree.column("envelopes", width=200, stretch=False)

        tracks2_scrollbar = ttk.Scrollbar(
            tracks2_frame, orient=tk.VERTICAL, command=self.tracks2_tree.yview
        )
        self.tracks2_tree.configure(yscrollcommand=tracks2_scrollbar.set)

        tracks2_h_scrollbar = ttk.Scrollbar(
            tracks2_frame, orient=tk.HORIZONTAL, command=self.tracks2_tree.xview
        )
        self.tracks2_tree.configure(xscrollcommand=tracks2_h_scrollbar.set)

        # Pack the frames first
        tracks1_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        tracks2_frame.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        # Pack scrollbars first, then treeview to ensure proper layout
        # Tracks1 (left side)
        tracks1_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        tracks1_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tracks1_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tracks2 (right side)
        tracks2_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        tracks2_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tracks2_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind selection events
        self.tracks1_tree.bind("<<TreeviewSelect>>", self.on_track1_select)
        self.tracks2_tree.bind("<<TreeviewSelect>>", self.on_track2_select)

    def create_control_widgets(self):
        """Create control buttons."""

        # Copy buttons frame
        copy_frame = ttk.LabelFrame(self.control_frame, text="Copy Track Settings", padding=10)

        self.copy_left_button = ttk.Button(
            copy_frame,
            text="← Copy Selected to File 1",
            command=self.copy_track_to_file1,
            state="disabled",
        )
        self.copy_right_button = ttk.Button(
            copy_frame,
            text="Copy Selected to File 2 →",
            command=self.copy_track_to_file2,
            state="disabled",
        )

        # Copy options
        copy_options_frame = ttk.Frame(copy_frame)

        self.copy_volume_var = tk.BooleanVar(value=True)
        self.copy_pan_var = tk.BooleanVar(value=True)
        self.copy_effects_var = tk.BooleanVar(value=True)
        self.copy_envelopes_var = tk.BooleanVar(value=True)

        copy_volume_check = ttk.Checkbutton(
            copy_options_frame, text="Volume", variable=self.copy_volume_var
        )
        copy_pan_check = ttk.Checkbutton(copy_options_frame, text="Pan", variable=self.copy_pan_var)
        copy_effects_check = ttk.Checkbutton(
            copy_options_frame, text="Effects", variable=self.copy_effects_var
        )
        copy_envelopes_check = ttk.Checkbutton(
            copy_options_frame, text="Envelopes", variable=self.copy_envelopes_var
        )

        # Differences frame
        diff_frame = ttk.LabelFrame(self.control_frame, text="Track Differences", padding=10)

        self.diff_text = tk.Text(diff_frame, height=8, width=80, state="disabled")
        diff_scrollbar = ttk.Scrollbar(diff_frame, orient=tk.VERTICAL, command=self.diff_text.yview)
        self.diff_text.configure(yscrollcommand=diff_scrollbar.set)

        # Pack widgets
        copy_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)

        self.copy_left_button.pack(pady=5, fill=tk.X)
        self.copy_right_button.pack(pady=5, fill=tk.X)

        copy_options_frame.pack(pady=10)
        copy_volume_check.pack(side=tk.LEFT, padx=5)
        copy_pan_check.pack(side=tk.LEFT, padx=5)
        copy_effects_check.pack(side=tk.LEFT, padx=5)
        copy_envelopes_check.pack(side=tk.LEFT, padx=5)

        diff_frame.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.diff_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        diff_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_layout(self):
        """Setup the main layout."""
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.file_frame.pack(fill=tk.X, pady=(0, 10))
        self.comparison_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.control_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)

    def load_file1(self):
        """Load the first RPP file."""
        file_path = filedialog.askopenfilename(
            title="Load RPP File 1",
            filetypes=[("RPP files", "*.rpp"), ("All files", "*.*")],
            initialdir=os.path.dirname(os.path.abspath(__file__)),
        )

        if file_path:
            try:
                self.parser1 = RPPParser(file_path)
                self.file1_var.set(os.path.basename(file_path))

                # Update info
                info = self.parser1.get_project_info()
                master_fx = "Yes" if info["has_master_effects"] else "No"
                info_text = (
                    f"Version: {info['version']}, Tracks: {info['track_count']}, "
                    f"Master FX: {master_fx}, Tempo: {info['tempo']}"
                )
                self.file1_info_var.set(info_text)

                # Update tracks list
                self.update_tracks_display()

                self.status_var.set(f"Loaded file 1: {os.path.basename(file_path)}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")

    def load_file2(self):
        """Load the second RPP file."""
        file_path = filedialog.askopenfilename(
            title="Load RPP File 2",
            filetypes=[("RPP files", "*.rpp"), ("All files", "*.*")],
            initialdir=os.path.dirname(os.path.abspath(__file__)),
        )

        if file_path:
            try:
                self.parser2 = RPPParser(file_path)
                self.file2_var.set(os.path.basename(file_path))

                # Update info
                info = self.parser2.get_project_info()
                master_fx = "Yes" if info["has_master_effects"] else "No"
                info_text = (
                    f"Version: {info['version']}, Tracks: {info['track_count']}, "
                    f"Master FX: {master_fx}, Tempo: {info['tempo']}"
                )
                self.file2_info_var.set(info_text)

                # Update tracks list
                self.update_tracks_display()

                self.status_var.set(f"Loaded file 2: {os.path.basename(file_path)}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")

    def update_tracks_display(self):
        """Update the tracks display in both treeviews."""

        # Clear existing items
        for item in self.tracks1_tree.get_children():
            self.tracks1_tree.delete(item)

        for item in self.tracks2_tree.get_children():
            self.tracks2_tree.delete(item)

        # Populate tracks from file 1
        if self.parser1:
            for i, track in enumerate(self.parser1.tracks):
                effects_str = ", ".join([fx["name"] for fx in track.effects])
                envelopes_str = self._format_envelope_info(track)
                # Use different formatting for master track
                display_name = f"🎛️ {track.name}" if track.is_master else track.name
                self.tracks1_tree.insert(
                    "",
                    "end",
                    iid=str(i),
                    text=display_name,
                    values=(f"{track.volume:.3f}", f"{track.pan:.3f}", effects_str, envelopes_str),
                    tags=("master",) if track.is_master else (),
                )

        # Populate tracks from file 2
        if self.parser2:
            for i, track in enumerate(self.parser2.tracks):
                effects_str = ", ".join([fx["name"] for fx in track.effects])
                envelopes_str = self._format_envelope_info(track)
                # Use different formatting for master track
                display_name = f"🎛️ {track.name}" if track.is_master else track.name
                self.tracks2_tree.insert(
                    "",
                    "end",
                    iid=str(i),
                    text=display_name,
                    values=(f"{track.volume:.3f}", f"{track.pan:.3f}", effects_str, envelopes_str),
                    tags=("master",) if track.is_master else (),
                )

        # Highlight differences
        self.highlight_differences()

        # Auto-resize columns to fit content
        self.auto_resize_columns()

    def _format_envelope_info(self, track):
        """Format envelope information for display."""
        env_parts = []
        
        if track.volume_envelope and track.volume_envelope.active:
            env_parts.append(f"Vol({len(track.volume_envelope.points)}pts)")
        
        if track.pan_envelope and track.pan_envelope.active:
            env_parts.append(f"Pan({len(track.pan_envelope.points)}pts)")
        
        if track.parameter_envelopes:
            active_param_envs = [e for e in track.parameter_envelopes if e.active]
            if active_param_envs:
                env_parts.append(f"{len(active_param_envs)} Param Envs")
        
        return ", ".join(env_parts) if env_parts else "None"

    def auto_resize_columns(self):
        """Automatically resize columns to fit their content."""
        import tkinter.font as tkFont

        # Get the default font for the treeview
        try:
            font = tkFont.Font(font=self.tracks1_tree.cget("font"))
        except (tk.TclError, ValueError, TypeError):
            # Fallback to default font
            font = tkFont.Font(family="TkDefaultFont", size=9)

        def calculate_column_width(tree, column_id):
            """Calculate the optimal width for a column based on its content."""
            max_width = 100  # Starting minimum width

            # Check header width
            if column_id == "#0":
                header_text = "Track Name"
            else:
                header_text = tree.heading(column_id)["text"]
            header_width = font.measure(header_text) + 40  # Increased padding
            max_width = max(max_width, header_width)

            # Check all items in the tree
            for item in tree.get_children():
                if column_id == "#0":
                    text = tree.item(item, "text")
                else:
                    values = tree.item(item, "values")
                    col_index = {"volume": 0, "pan": 1, "effects": 2, "envelopes": 3}.get(column_id)
                    if col_index is not None and col_index < len(values):
                        text = values[col_index]
                    else:
                        text = ""

                if text:
                    # Increased padding to ensure text isn't cut off
                    text_width = font.measure(str(text)) + 50
                    max_width = max(max_width, text_width)

            # Set more generous limits based on column type
            if column_id == "#0":  # Track Name
                max_width = min(max_width, 500)  # Increased from 400px
                max_width = max(max_width, 250)  # Increased minimum - ensure track names show fully
            elif column_id in ["volume", "pan"]:  # Numeric columns
                max_width = min(max_width, 120)
                max_width = max(max_width, 100)  # Increased from 80px
            elif column_id == "effects":  # Effects column
                max_width = min(
                    max_width, 1200
                )  # Increased from 600px - more room for long effect lists
                max_width = max(max_width, 350)  # Increased minimum for effects
            elif column_id == "envelopes":  # Envelopes column
                max_width = min(max_width, 400)  # Reasonable maximum for envelope info
                max_width = max(max_width, 150)  # Minimum for envelope column

            return max_width

        # Auto-resize columns for both trees
        for tree in [self.tracks1_tree, self.tracks2_tree]:
            for col_id in ["#0", "volume", "pan", "effects", "envelopes"]:
                width = calculate_column_width(tree, col_id)
                tree.column(col_id, width=width, stretch=False)

    def highlight_differences(self):
        """Highlight tracks with differences between the two files."""
        if not (self.parser1 and self.parser2):
            return

        # Compare tracks by name
        for track1 in self.parser1.tracks:
            track2 = self.parser2.get_track_by_name(track1.name)
            if track2:
                differences = compare_tracks(track1, track2)
                if differences:
                    # Find and highlight the corresponding items
                    for item in self.tracks1_tree.get_children():
                        if self.tracks1_tree.item(item, "text") == track1.name:
                            self.tracks1_tree.item(item, tags=("different",))
                            break

                    for item in self.tracks2_tree.get_children():
                        if self.tracks2_tree.item(item, "text") == track2.name:
                            self.tracks2_tree.item(item, tags=("different",))
                            break

        # Configure tags
        self.tracks1_tree.tag_configure("different", background="#ffcccc")
        self.tracks2_tree.tag_configure("different", background="#ffcccc")
        self.tracks1_tree.tag_configure(
            "master", background="#e6f3ff", font=("TkDefaultFont", 9, "bold")
        )
        self.tracks2_tree.tag_configure(
            "master", background="#e6f3ff", font=("TkDefaultFont", 9, "bold")
        )

    def on_track1_select(self, event):
        """Handle track selection in file 1."""
        selection = self.tracks1_tree.selection()
        if selection and self.parser1:
            track_index = int(selection[0])
            self.selected_track1 = self.parser1.tracks[track_index]
            self.update_copy_buttons()
            self.update_differences_display()

    def on_track2_select(self, event):
        """Handle track selection in file 2."""
        selection = self.tracks2_tree.selection()
        if selection and self.parser2:
            track_index = int(selection[0])
            self.selected_track2 = self.parser2.tracks[track_index]
            self.update_copy_buttons()
            self.update_differences_display()

    def update_copy_buttons(self):
        """Update the state of copy buttons based on selections."""
        if self.selected_track1 and self.selected_track2:
            self.copy_left_button.config(state="normal")
            self.copy_right_button.config(state="normal")
        else:
            self.copy_left_button.config(state="disabled")
            self.copy_right_button.config(state="disabled")

    def update_differences_display(self):
        """Update the differences display."""
        self.diff_text.config(state="normal")
        self.diff_text.delete(1.0, tk.END)

        if self.selected_track1 and self.selected_track2:
            differences = compare_tracks(self.selected_track1, self.selected_track2)

            self.diff_text.insert(tk.END, "Comparing:\n")
            self.diff_text.insert(tk.END, f"  File 1: {self.selected_track1.name}\n")
            self.diff_text.insert(tk.END, f"  File 2: {self.selected_track2.name}\n\n")

            if differences:
                self.diff_text.insert(tk.END, "Differences found:\n")
                for key, values in differences.items():
                    self.diff_text.insert(tk.END, f"  {key.capitalize()}:\n")
                    self.diff_text.insert(tk.END, f"    File 1: {values['track1']}\n")
                    self.diff_text.insert(tk.END, f"    File 2: {values['track2']}\n\n")
            else:
                self.diff_text.insert(tk.END, "No differences found.\n")

        self.diff_text.config(state="disabled")

    def copy_track_to_file1(self):
        """Copy selected track settings from file 2 to file 1."""
        if not (self.selected_track1 and self.selected_track2 and self.parser1):
            return

        try:
            self.parser1.copy_track_settings(
                self.selected_track2,
                self.selected_track1,
                copy_volume=self.copy_volume_var.get(),
                copy_pan=self.copy_pan_var.get(),
                copy_effects=self.copy_effects_var.get(),
                copy_envelopes=self.copy_envelopes_var.get(),
            )

            self.update_tracks_display()
            self.update_differences_display()
            self.status_var.set(
                f"Copied settings from {self.selected_track2.name} to {self.selected_track1.name}"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy track settings:\n{str(e)}")

    def copy_track_to_file2(self):
        """Copy selected track settings from file 1 to file 2."""
        if not (self.selected_track1 and self.selected_track2 and self.parser2):
            return

        try:
            self.parser2.copy_track_settings(
                self.selected_track1,
                self.selected_track2,
                copy_volume=self.copy_volume_var.get(),
                copy_pan=self.copy_pan_var.get(),
                copy_effects=self.copy_effects_var.get(),
                copy_envelopes=self.copy_envelopes_var.get(),
            )

            self.update_tracks_display()
            self.update_differences_display()
            self.status_var.set(
                f"Copied settings from {self.selected_track1.name} to {self.selected_track2.name}"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy track settings:\n{str(e)}")

    def save_file1(self):
        """Save file 1."""
        if self.parser1:
            try:
                self.parser1.save_file()
                self.status_var.set("File 1 saved successfully")
                messagebox.showinfo("Success", "File 1 saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file 1:\n{str(e)}")

    def save_file1_as(self):
        """Save file 1 with a new name."""
        if self.parser1:
            file_path = filedialog.asksaveasfilename(
                title="Save RPP File 1 As",
                filetypes=[("RPP files", "*.rpp"), ("All files", "*.*")],
                defaultextension=".rpp",
            )

            if file_path:
                try:
                    self.parser1.save_file(file_path)
                    self.status_var.set(f"File 1 saved as {os.path.basename(file_path)}")
                    messagebox.showinfo("Success", f"File saved as {os.path.basename(file_path)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

    def save_file2(self):
        """Save file 2."""
        if self.parser2:
            try:
                self.parser2.save_file()
                self.status_var.set("File 2 saved successfully")
                messagebox.showinfo("Success", "File 2 saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file 2:\n{str(e)}")

    def save_file2_as(self):
        """Save file 2 with a new name."""
        if self.parser2:
            file_path = filedialog.asksaveasfilename(
                title="Save RPP File 2 As",
                filetypes=[("RPP files", "*.rpp"), ("All files", "*.*")],
                defaultextension=".rpp",
            )

            if file_path:
                try:
                    self.parser2.save_file(file_path)
                    self.status_var.set(f"File 2 saved as {os.path.basename(file_path)}")
                    messagebox.showinfo("Success", f"File saved as {os.path.basename(file_path)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About RPP Editor",
            "RPP Editor v1.0\n\n"
            "A GUI application for editing and comparing REAPER project files.\n\n"
            "Features:\n"
            "• Load and compare two RPP files\n"
            "• View track differences\n"
            "• Copy track settings between files\n"
            "• Save modified files\n\n"
            "Built with Python and tkinter",
        )


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = RPPEditorGUI(root)

    # Try to load the example files if they exist
    if os.path.exists("test1.rpp"):
        try:
            app.parser1 = RPPParser("test1.rpp")
            app.file1_var.set("test1.rpp")
            info = app.parser1.get_project_info()
            master_fx = "Yes" if info["has_master_effects"] else "No"
            info_text = (
                f"Version: {info['version']}, Tracks: {info['track_count']}, "
                f"Master FX: {master_fx}, Tempo: {info['tempo']}"
            )
            app.file1_info_var.set(info_text)
        except Exception:
            pass

    if os.path.exists("test2.rpp"):
        try:
            app.parser2 = RPPParser("test2.rpp")
            app.file2_var.set("test2.rpp")
            info = app.parser2.get_project_info()
            master_fx = "Yes" if info["has_master_effects"] else "No"
            info_text = (
                f"Version: {info['version']}, Tracks: {info['track_count']}, "
                f"Master FX: {master_fx}, Tempo: {info['tempo']}"
            )
            app.file2_info_var.set(info_text)
        except Exception:
            pass

    # Update display if files were loaded
    if app.parser1 or app.parser2:
        app.update_tracks_display()

    root.mainloop()


if __name__ == "__main__":
    main()
