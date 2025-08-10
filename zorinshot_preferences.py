#!/usr/bin/env python3
"""
ZorinShot Preferences Dialog

Provides a user-friendly interface for configuring ZorinShot settings.
"""

import os
import gi
from pathlib import Path

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from zorinshot_settings import settings_manager, get_settings, save_settings

class PreferencesDialog(Gtk.Dialog):
    """ZorinShot preferences dialog."""
    
    def __init__(self, parent=None):
        super().__init__(title="ZorinShot Preferences", transient_for=parent, flags=0)
        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.add_button(Gtk.STOCK_APPLY, Gtk.ResponseType.APPLY)
        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        
        self.set_default_size(500, 400)
        self.set_resizable(True)
        
        self.settings = get_settings()
        self._create_ui()
        self._load_current_settings()
    
    def _create_ui(self):
        """Create the preferences UI."""
        content_area = self.get_content_area()
        content_area.set_border_width(12)
        
        # Create notebook for tabbed interface
        notebook = Gtk.Notebook()
        content_area.pack_start(notebook, True, True, 0)
        
        # General tab
        self._create_general_tab(notebook)
        
        # Autosave tab
        self._create_autosave_tab(notebook)
        
        # Appearance tab
        self._create_appearance_tab(notebook)
        
        # Advanced tab
        self._create_advanced_tab(notebook)
    
    def _create_general_tab(self, notebook):
        """Create the general settings tab."""
        vbox = Gtk.VBox(spacing=12)
        vbox.set_border_width(12)
        
        # Window settings
        frame = Gtk.Frame(label="Window Settings")
        frame_vbox = Gtk.VBox(spacing=6)
        frame_vbox.set_border_width(12)
        frame.add(frame_vbox)
        
        # Window size
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Default window size:"), False, False, 0)
        
        self.width_spin = Gtk.SpinButton.new_with_range(400, 2000, 50)
        self.height_spin = Gtk.SpinButton.new_with_range(300, 1500, 50)
        
        hbox.pack_start(self.width_spin, False, False, 0)
        hbox.pack_start(Gtk.Label(label="×"), False, False, 0)
        hbox.pack_start(self.height_spin, False, False, 0)
        
        frame_vbox.pack_start(hbox, False, False, 0)
        
        # Toolbar style
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Toolbar style:"), False, False, 0)
        
        self.toolbar_combo = Gtk.ComboBoxText()
        self.toolbar_combo.append("icons", "Icons only")
        self.toolbar_combo.append("text", "Text only")
        self.toolbar_combo.append("both", "Icons and text")
        
        hbox.pack_start(self.toolbar_combo, False, False, 0)
        frame_vbox.pack_start(hbox, False, False, 0)
        
        vbox.pack_start(frame, False, False, 0)
        
        # Behavior settings
        frame = Gtk.Frame(label="Behavior")
        frame_vbox = Gtk.VBox(spacing=6)
        frame_vbox.set_border_width(12)
        frame.add(frame_vbox)
        
        self.copy_on_save_check = Gtk.CheckButton(label="Copy to clipboard when saving")
        self.show_confirmation_check = Gtk.CheckButton(label="Show save confirmation dialog")
        self.auto_close_check = Gtk.CheckButton(label="Auto-close editor after saving")
        self.remember_tool_check = Gtk.CheckButton(label="Remember last selected tool")
        
        frame_vbox.pack_start(self.copy_on_save_check, False, False, 0)
        frame_vbox.pack_start(self.show_confirmation_check, False, False, 0)
        frame_vbox.pack_start(self.auto_close_check, False, False, 0)
        frame_vbox.pack_start(self.remember_tool_check, False, False, 0)
        
        vbox.pack_start(frame, False, False, 0)
        
        notebook.append_page(vbox, Gtk.Label(label="General"))
    
    def _create_autosave_tab(self, notebook):
        """Create the autosave settings tab."""
        vbox = Gtk.VBox(spacing=12)
        vbox.set_border_width(12)
        
        # Autosave settings
        frame = Gtk.Frame(label="Autosave Configuration")
        frame_vbox = Gtk.VBox(spacing=6)
        frame_vbox.set_border_width(12)
        frame.add(frame_vbox)
        
        # Enable autosave
        self.autosave_check = Gtk.CheckButton(label="Enable autosave")
        self.autosave_check.connect("toggled", self._on_autosave_toggled)
        frame_vbox.pack_start(self.autosave_check, False, False, 0)
        
        # Default save location
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Default save location:"), False, False, 0)
        
        self.location_entry = Gtk.Entry()
        self.location_entry.set_editable(False)
        hbox.pack_start(self.location_entry, True, True, 0)
        
        self.browse_button = Gtk.Button(label="Browse...")
        self.browse_button.connect("clicked", self._on_browse_location)
        hbox.pack_start(self.browse_button, False, False, 0)
        
        frame_vbox.pack_start(hbox, False, False, 0)
        
        # Quick location buttons
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Quick locations:"), False, False, 0)
        
        desktop_btn = Gtk.Button(label="Desktop")
        desktop_btn.connect("clicked", lambda b: self._set_quick_location("Desktop"))
        hbox.pack_start(desktop_btn, False, False, 0)
        
        pictures_btn = Gtk.Button(label="Pictures")
        pictures_btn.connect("clicked", lambda b: self._set_quick_location("Pictures"))
        hbox.pack_start(pictures_btn, False, False, 0)
        
        documents_btn = Gtk.Button(label="Documents")
        documents_btn.connect("clicked", lambda b: self._set_quick_location("Documents"))
        hbox.pack_start(documents_btn, False, False, 0)
        
        frame_vbox.pack_start(hbox, False, False, 0)
        
        # Filename pattern
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Filename pattern:"), False, False, 0)
        
        self.filename_entry = Gtk.Entry()
        self.filename_entry.set_tooltip_text(
            "Use strftime format codes:\n"
            "%Y = Year (2023)\n"
            "%m = Month (01-12)\n"
            "%d = Day (01-31)\n"
            "%H = Hour (00-23)\n"
            "%M = Minute (00-59)\n"
            "%S = Second (00-59)"
        )
        hbox.pack_start(self.filename_entry, True, True, 0)
        
        frame_vbox.pack_start(hbox, False, False, 0)
        
        # Default format
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Default format:"), False, False, 0)
        
        self.format_combo = Gtk.ComboBoxText()
        self.format_combo.append("png", "PNG")
        self.format_combo.append("jpg", "JPEG")
        
        hbox.pack_start(self.format_combo, False, False, 0)
        
        frame_vbox.pack_start(hbox, False, False, 0)
        
        vbox.pack_start(frame, False, False, 0)
        
        # Preview
        frame = Gtk.Frame(label="Preview")
        frame_vbox = Gtk.VBox(spacing=6)
        frame_vbox.set_border_width(12)
        frame.add(frame_vbox)
        
        self.preview_label = Gtk.Label()
        self.preview_label.set_selectable(True)
        frame_vbox.pack_start(self.preview_label, False, False, 0)
        
        # Update preview button
        update_btn = Gtk.Button(label="Update Preview")
        update_btn.connect("clicked", self._update_preview)
        frame_vbox.pack_start(update_btn, False, False, 0)
        
        vbox.pack_start(frame, False, False, 0)
        
        notebook.append_page(vbox, Gtk.Label(label="Autosave"))
    
    def _create_appearance_tab(self, notebook):
        """Create the appearance settings tab."""
        vbox = Gtk.VBox(spacing=12)
        vbox.set_border_width(12)
        
        # Default annotation settings
        frame = Gtk.Frame(label="Default Annotation Settings")
        frame_vbox = Gtk.VBox(spacing=6)
        frame_vbox.set_border_width(12)
        frame.add(frame_vbox)
        
        # Pen width
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Pen width:"), False, False, 0)
        self.pen_width_spin = Gtk.SpinButton.new_with_range(1, 20, 0.5)
        hbox.pack_start(self.pen_width_spin, False, False, 0)
        frame_vbox.pack_start(hbox, False, False, 0)
        
        # Arrow width
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Arrow width:"), False, False, 0)
        self.arrow_width_spin = Gtk.SpinButton.new_with_range(1, 20, 0.5)
        hbox.pack_start(self.arrow_width_spin, False, False, 0)
        frame_vbox.pack_start(hbox, False, False, 0)
        
        # Rectangle width
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Rectangle width:"), False, False, 0)
        self.rect_width_spin = Gtk.SpinButton.new_with_range(1, 20, 0.5)
        hbox.pack_start(self.rect_width_spin, False, False, 0)
        frame_vbox.pack_start(hbox, False, False, 0)
        
        # Text size
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Text size:"), False, False, 0)
        self.text_size_spin = Gtk.SpinButton.new_with_range(8, 72, 1)
        hbox.pack_start(self.text_size_spin, False, False, 0)
        frame_vbox.pack_start(hbox, False, False, 0)
        
        # Default color
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Default color:"), False, False, 0)
        
        self.color_button = Gtk.ColorButton()
        self.color_button.set_use_alpha(True)
        hbox.pack_start(self.color_button, False, False, 0)
        
        frame_vbox.pack_start(hbox, False, False, 0)
        
        vbox.pack_start(frame, False, False, 0)
        
        notebook.append_page(vbox, Gtk.Label(label="Appearance"))
    
    def _create_advanced_tab(self, notebook):
        """Create the advanced settings tab."""
        vbox = Gtk.VBox(spacing=12)
        vbox.set_border_width(12)
        
        # Performance settings
        frame = Gtk.Frame(label="Performance")
        frame_vbox = Gtk.VBox(spacing=6)
        frame_vbox.set_border_width(12)
        frame.add(frame_vbox)
        
        # Max undo levels
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Maximum undo levels:"), False, False, 0)
        self.undo_spin = Gtk.SpinButton.new_with_range(5, 100, 5)
        hbox.pack_start(self.undo_spin, False, False, 0)
        frame_vbox.pack_start(hbox, False, False, 0)
        
        # JPEG quality
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="JPEG quality:"), False, False, 0)
        self.jpeg_quality_spin = Gtk.SpinButton.new_with_range(10, 100, 5)
        hbox.pack_start(self.jpeg_quality_spin, False, False, 0)
        frame_vbox.pack_start(hbox, False, False, 0)
        
        vbox.pack_start(frame, False, False, 0)
        
        # Temporary directory
        frame = Gtk.Frame(label="Temporary Files")
        frame_vbox = Gtk.VBox(spacing=6)
        frame_vbox.set_border_width(12)
        frame.add(frame_vbox)
        
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(Gtk.Label(label="Temporary directory:"), False, False, 0)
        
        self.temp_entry = Gtk.Entry()
        hbox.pack_start(self.temp_entry, True, True, 0)
        
        temp_browse_btn = Gtk.Button(label="Browse...")
        temp_browse_btn.connect("clicked", self._on_browse_temp)
        hbox.pack_start(temp_browse_btn, False, False, 0)
        
        frame_vbox.pack_start(hbox, False, False, 0)
        
        vbox.pack_start(frame, False, False, 0)
        
        # Reset settings
        frame = Gtk.Frame(label="Reset")
        frame_vbox = Gtk.VBox(spacing=6)
        frame_vbox.set_border_width(12)
        frame.add(frame_vbox)
        
        reset_btn = Gtk.Button(label="Reset to Defaults")
        reset_btn.connect("clicked", self._on_reset_settings)
        frame_vbox.pack_start(reset_btn, False, False, 0)
        
        vbox.pack_start(frame, False, False, 0)
        
        notebook.append_page(vbox, Gtk.Label(label="Advanced"))
    
    def _load_current_settings(self):
        """Load current settings into the UI."""
        # General settings
        self.width_spin.set_value(self.settings.window_width)
        self.height_spin.set_value(self.settings.window_height)
        self.toolbar_combo.set_active_id(self.settings.toolbar_style)
        
        self.copy_on_save_check.set_active(self.settings.copy_to_clipboard_on_save)
        self.show_confirmation_check.set_active(self.settings.show_save_confirmation)
        self.auto_close_check.set_active(self.settings.auto_close_after_save)
        self.remember_tool_check.set_active(self.settings.remember_tool_selection)
        
        # Autosave settings
        self.autosave_check.set_active(self.settings.autosave_enabled)
        self.location_entry.set_text(self.settings.default_save_location)
        self.filename_entry.set_text(self.settings.filename_pattern)
        self.format_combo.set_active_id(self.settings.default_format)
        
        # Appearance settings
        self.pen_width_spin.set_value(self.settings.default_pen_width)
        self.arrow_width_spin.set_value(self.settings.default_arrow_width)
        self.rect_width_spin.set_value(self.settings.default_rect_width)
        self.text_size_spin.set_value(self.settings.default_text_size)
        
        # Set color
        color = Gdk.RGBA()
        color.red = self.settings.default_color_r / 255.0
        color.green = self.settings.default_color_g / 255.0
        color.blue = self.settings.default_color_b / 255.0
        color.alpha = self.settings.default_color_a / 255.0
        self.color_button.set_rgba(color)
        
        # Advanced settings
        self.undo_spin.set_value(self.settings.max_undo_levels)
        self.jpeg_quality_spin.set_value(self.settings.image_quality_jpeg)
        self.temp_entry.set_text(self.settings.temp_dir)
        
        # Update autosave UI state
        self._on_autosave_toggled(self.autosave_check)
        
        # Update preview
        self._update_preview()
    
    def _save_settings(self):
        """Save settings from the UI."""
        # General settings
        self.settings.window_width = int(self.width_spin.get_value())
        self.settings.window_height = int(self.height_spin.get_value())
        self.settings.toolbar_style = self.toolbar_combo.get_active_id()
        
        self.settings.copy_to_clipboard_on_save = self.copy_on_save_check.get_active()
        self.settings.show_save_confirmation = self.show_confirmation_check.get_active()
        self.settings.auto_close_after_save = self.auto_close_check.get_active()
        self.settings.remember_tool_selection = self.remember_tool_check.get_active()
        
        # Autosave settings
        self.settings.autosave_enabled = self.autosave_check.get_active()
        self.settings.default_save_location = self.location_entry.get_text()
        self.settings.filename_pattern = self.filename_entry.get_text()
        self.settings.default_format = self.format_combo.get_active_id()
        
        # Appearance settings
        self.settings.default_pen_width = self.pen_width_spin.get_value()
        self.settings.default_arrow_width = self.arrow_width_spin.get_value()
        self.settings.default_rect_width = self.rect_width_spin.get_value()
        self.settings.default_text_size = int(self.text_size_spin.get_value())
        
        # Get color
        color = self.color_button.get_rgba()
        self.settings.default_color_r = int(color.red * 255)
        self.settings.default_color_g = int(color.green * 255)
        self.settings.default_color_b = int(color.blue * 255)
        self.settings.default_color_a = int(color.alpha * 255)
        
        # Advanced settings
        self.settings.max_undo_levels = int(self.undo_spin.get_value())
        self.settings.image_quality_jpeg = int(self.jpeg_quality_spin.get_value())
        self.settings.temp_dir = self.temp_entry.get_text()
        
        # Save to file
        save_settings()
    
    def _on_autosave_toggled(self, widget):
        """Handle autosave checkbox toggle."""
        enabled = widget.get_active()
        self.location_entry.set_sensitive(enabled)
        self.browse_button.set_sensitive(enabled)
        self.filename_entry.set_sensitive(enabled)
        self.format_combo.set_sensitive(enabled)
    
    def _on_browse_location(self, widget):
        """Handle browse location button."""
        dialog = Gtk.FileChooserDialog(
            title="Select Default Save Location",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Set current location
        current_location = self.location_entry.get_text()
        if current_location and os.path.exists(current_location):
            dialog.set_current_folder(current_location)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.location_entry.set_text(dialog.get_filename())
            self._update_preview()
        
        dialog.destroy()
    
    def _on_browse_temp(self, widget):
        """Handle browse temp directory button."""
        dialog = Gtk.FileChooserDialog(
            title="Select Temporary Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.temp_entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def _set_quick_location(self, location_name):
        """Set a quick location."""
        home = Path.home()
        locations = {
            "Desktop": home / "Desktop",
            "Pictures": home / "Pictures",
            "Documents": home / "Documents"
        }
        
        location_path = locations.get(location_name)
        if location_path and location_path.exists():
            self.location_entry.set_text(str(location_path))
        else:
            # Create the directory if it doesn't exist
            location_path.mkdir(exist_ok=True)
            self.location_entry.set_text(str(location_path))
        
        self._update_preview()
    
    def _update_preview(self, widget=None):
        """Update the filename preview."""
        try:
            import time
            location = self.location_entry.get_text()
            pattern = self.filename_entry.get_text()
            format_ext = self.format_combo.get_active_id()
            
            if location and pattern and format_ext:
                filename = time.strftime(pattern) + f".{format_ext}"
                full_path = str(Path(location) / filename)
                self.preview_label.set_text(f"Example: {full_path}")
            else:
                self.preview_label.set_text("Preview will appear here")
                
        except Exception as e:
            self.preview_label.set_text(f"Error in pattern: {e}")
    
    def _on_reset_settings(self, widget):
        """Handle reset settings button."""
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Reset all settings to defaults?"
        )
        dialog.format_secondary_text(
            "This will reset all preferences to their default values. "
            "This action cannot be undone."
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            settings_manager.reset_to_defaults()
            self.settings = get_settings()
            self._load_current_settings()
        
        dialog.destroy()
    
    def run_dialog(self):
        """Run the preferences dialog."""
        self.show_all()
        
        while True:
            response = self.run()
            
            if response == Gtk.ResponseType.OK:
                self._save_settings()
                break
            elif response == Gtk.ResponseType.APPLY:
                self._save_settings()
                continue
            else:
                break
        
        self.destroy()
        return response == Gtk.ResponseType.OK

