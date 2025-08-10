#!/usr/bin/env python3
"""
ZorinShot Enhanced: Wayland-Compatible Lightshot Alternative with Autosave

Enhanced version with autosave functionality, settings persistence, and improved UI.

Features:
- Wayland-native screenshot capture using multiple fallback methods
- Interactive region selection
- Basic annotation tools (pen, arrow, rectangle, text)
- Clipboard integration
- Autosave with customizable default location
- Quick save and Save As functionality
- Comprehensive settings system
- Settings persistence between sessions

Dependencies:
    sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0 python3-pil
    sudo apt install -y grim slurp wl-clipboard gnome-screenshot imagemagick xclip
"""

import os
import sys
import math
import time
import threading
import tempfile
from dataclasses import dataclass
from typing import List, Tuple, Optional
from pathlib import Path
import io

# Import our modules
from wayland_screenshot_simple import WaylandScreenshotCapture
from zorinshot_settings import get_settings, save_settings, settings_manager
from zorinshot_preferences import PreferencesDialog

import gi
from PIL import Image, ImageDraw, ImageFont

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, cairo, GLib

try:
    import requests
except ImportError:
    requests = None

########################
# Utility Functions    #
########################

def pixbuf_to_pil(pixbuf: GdkPixbuf.Pixbuf) -> Image.Image:
    """Convert GdkPixbuf -> PIL Image"""
    data = pixbuf.get_pixels()
    w = pixbuf.get_width()
    h = pixbuf.get_height()
    rowstride = pixbuf.get_rowstride()
    mode = "RGBA" if pixbuf.get_has_alpha() else "RGB"
    im = Image.frombuffer(mode, (w, h), bytes(data), 'raw', mode, rowstride, 1)
    return im.copy()

def pil_to_pixbuf(im: Image.Image) -> GdkPixbuf.Pixbuf:
    """Convert PIL Image -> GdkPixbuf"""
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA")
    data = im.tobytes()
    w, h = im.size
    has_alpha = im.mode == "RGBA"
    rowstride = (4 if has_alpha else 3) * w
    return GdkPixbuf.Pixbuf.new_from_data(data, GdkPixbuf.Colorspace.RGB,
                                          has_alpha, 8, w, h, rowstride, None, None)

########################
# Annotation Primitives #
########################

@dataclass
class PenStroke:
    points: List[Tuple[float, float]]
    width: float = 3.0
    color: Tuple[int, int, int, int] = (153, 51, 255, 242)  # RGBA 0-255

@dataclass
class RectShape:
    x: float
    y: float
    w: float
    h: float
    width: float = 3.0
    color: Tuple[int, int, int, int] = (153, 51, 255, 242)  # RGBA 0-255

@dataclass
class ArrowShape:
    x1: float
    y1: float
    x2: float
    y2: float
    width: float = 3.0
    color: Tuple[int, int, int, int] = (153, 51, 255, 242)  # RGBA 0-255

@dataclass
class TextLabel:
    x: float
    y: float
    text: str
    font_size: int = 16
    color: Tuple[int, int, int, int] = (153, 51, 255, 242)  # RGBA 0-255

########################
# Main Application     #
########################

class ZorinShotApp:
    """Main ZorinShot application class."""
    
    def __init__(self):
        self.screenshot_capture = WaylandScreenshotCapture()
        self.settings = get_settings()
        
        # Ensure temp directory exists
        temp_dir = Path(self.settings.temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Check available methods
        methods = self.screenshot_capture.get_available_methods()
        if not any(methods.values()):
            self._show_no_methods_dialog()
            return
        
        # Start with region selection
        self.start_region_selection()
    
    def _show_no_methods_dialog(self):
        """Show dialog when no screenshot methods are available."""
        dialog = Gtk.MessageDialog(
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="No screenshot methods available",
        )
        dialog.format_secondary_text(
            "ZorinShot requires at least one of the following:\n"
            "• grim + slurp (for Wayland)\n"
            "• gnome-screenshot (for GNOME)\n"
            "• ImageMagick import (for X11)\n\n"
            "Please install the required packages and try again."
        )
        dialog.run()
        dialog.destroy()
        sys.exit(1)
    
    def start_region_selection(self):
        """Start the region selection process."""
        self._capture_region_and_edit()
    
    def _capture_region_and_edit(self):
        """Capture a region and open the editor."""
        # Capture region using our screenshot module
        temp_file = str(Path(self.settings.temp_dir) / f"region_{os.getpid()}.png")
        result = self.screenshot_capture.capture_region(temp_file)
        
        if result:
            # Load the captured image and open editor
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(result)
                editor = EditorWindow(pixbuf, self.screenshot_capture)
                editor.show_all()
            except Exception as e:
                self._show_error_dialog(f"Failed to load captured image: {e}")
        else:
            self._show_error_dialog("Failed to capture region. Please check that screenshot tools are installed.")
    
    def _show_error_dialog(self, message: str):
        """Show an error dialog."""
        dialog = Gtk.MessageDialog(
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error",
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

########################
# Editor Window        #
########################

class EditorWindow(Gtk.Window):
    """Screenshot editor window with annotation tools and autosave."""
    
    TOOL_PEN = "pen"
    TOOL_RECT = "rect"
    TOOL_ARROW = "arrow"
    TOOL_TEXT = "text"

    def __init__(self, pixbuf: GdkPixbuf.Pixbuf, screenshot_capture: WaylandScreenshotCapture):
        super().__init__(title="ZorinShot Editor")
        
        self.settings = get_settings()
        self.set_default_size(self.settings.window_width, self.settings.window_height)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        self.screenshot_capture = screenshot_capture
        self.orig_pixbuf = pixbuf
        self.base_image = pixbuf_to_pil(pixbuf)
        
        # Set current tool from settings or default
        if self.settings.remember_tool_selection:
            self.current_tool = self.settings.last_selected_tool
        else:
            self.current_tool = self.TOOL_ARROW
            
        self.drawing = False
        self.temp_points: List[Tuple[float, float]] = []
        self.shapes: List[object] = []
        self.undo_stack: List[List[object]] = []
        
        # Track if image has been modified
        self.modified = False
        
        self._setup_ui()
        self._setup_events()
        self._update_title()
    
    def _setup_ui(self):
        """Set up the user interface."""
        vbox = Gtk.VBox(spacing=6)
        self.add(vbox)
        
        # Menu bar
        self._create_menu_bar(vbox)
        
        # Toolbar
        toolbar = Gtk.Toolbar()
        if self.settings.toolbar_style == "text":
            toolbar.set_style(Gtk.ToolbarStyle.TEXT)
        elif self.settings.toolbar_style == "both":
            toolbar.set_style(Gtk.ToolbarStyle.BOTH)
        else:
            toolbar.set_style(Gtk.ToolbarStyle.ICONS)
            
        vbox.pack_start(toolbar, False, False, 0)
        
        # Tool buttons
        self._add_tool_button(toolbar, Gtk.STOCK_EDIT, "Pen (P)", self.TOOL_PEN)
        self._add_tool_button(toolbar, Gtk.STOCK_SELECT_ALL, "Rectangle (R)", self.TOOL_RECT)
        self._add_tool_button(toolbar, Gtk.STOCK_GO_FORWARD, "Arrow (A)", self.TOOL_ARROW)
        self._add_tool_button(toolbar, Gtk.STOCK_ADD, "Text (T)", self.TOOL_TEXT)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Action buttons
        self._add_action_button(toolbar, Gtk.STOCK_UNDO, "Undo (Ctrl+Z)", self.undo)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Quick save button (new feature)
        if self.settings.autosave_enabled:
            self._add_action_button(toolbar, Gtk.STOCK_SAVE, "Quick Save (Ctrl+S)", self.quick_save)
            self._add_action_button(toolbar, Gtk.STOCK_SAVE_AS, "Save As (Ctrl+Shift+S)", self.save_dialog)
        else:
            self._add_action_button(toolbar, Gtk.STOCK_SAVE, "Save (Ctrl+S)", self.save_dialog)
        
        self._add_action_button(toolbar, Gtk.STOCK_COPY, "Copy (Enter/Ctrl+C)", self.copy_to_clipboard)
        self._add_action_button(toolbar, Gtk.STOCK_GO_UP, "Upload (U)", self.upload)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        self._add_action_button(toolbar, Gtk.STOCK_PREFERENCES, "Preferences", self.show_preferences)
        self._add_action_button(toolbar, Gtk.STOCK_QUIT, "Close (Esc)", lambda: self.close())
        
        # Drawing area in scrolled window
        scrolled = Gtk.ScrolledWindow()
        vbox.pack_start(scrolled, True, True, 0)
        
        self.darea = Gtk.DrawingArea()
        self.darea.set_can_focus(True)
        self.darea.grab_focus()
        
        img_w, img_h = self.base_image.size
        self.darea.set_size_request(img_w, img_h)
        
        scrolled.add(self.darea)
        
        # Status bar
        self.statusbar = Gtk.Statusbar()
        self.status_context = self.statusbar.get_context_id("main")
        vbox.pack_start(self.statusbar, False, False, 0)
        
        self._update_status("Ready")
    
    def _create_menu_bar(self, vbox):
        """Create the menu bar."""
        menubar = Gtk.MenuBar()
        
        # File menu
        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="File")
        file_item.set_submenu(file_menu)
        
        if self.settings.autosave_enabled:
            quick_save_item = Gtk.MenuItem(label="Quick Save")
            quick_save_item.connect("activate", lambda w: self.quick_save())
            file_menu.append(quick_save_item)
            
            save_as_item = Gtk.MenuItem(label="Save As...")
            save_as_item.connect("activate", lambda w: self.save_dialog())
            file_menu.append(save_as_item)
        else:
            save_item = Gtk.MenuItem(label="Save...")
            save_item.connect("activate", lambda w: self.save_dialog())
            file_menu.append(save_item)
        
        file_menu.append(Gtk.SeparatorMenuItem())
        
        copy_item = Gtk.MenuItem(label="Copy to Clipboard")
        copy_item.connect("activate", lambda w: self.copy_to_clipboard())
        file_menu.append(copy_item)
        
        file_menu.append(Gtk.SeparatorMenuItem())
        
        close_item = Gtk.MenuItem(label="Close")
        close_item.connect("activate", lambda w: self.close())
        file_menu.append(close_item)
        
        menubar.append(file_item)
        
        # Edit menu
        edit_menu = Gtk.Menu()
        edit_item = Gtk.MenuItem(label="Edit")
        edit_item.set_submenu(edit_menu)
        
        undo_item = Gtk.MenuItem(label="Undo")
        undo_item.connect("activate", lambda w: self.undo())
        edit_menu.append(undo_item)
        
        edit_menu.append(Gtk.SeparatorMenuItem())
        
        prefs_item = Gtk.MenuItem(label="Preferences")
        prefs_item.connect("activate", lambda w: self.show_preferences())
        edit_menu.append(prefs_item)
        
        menubar.append(edit_item)
        
        vbox.pack_start(menubar, False, False, 0)
    
    def _add_tool_button(self, toolbar, icon, tooltip, tool):
        """Add a tool button to the toolbar."""
        btn = Gtk.ToolButton.new_from_stock(icon)
        btn.set_tooltip_text(tooltip)
        btn.connect("clicked", lambda *_: self.set_tool(tool))
        toolbar.insert(btn, -1)
    
    def _add_action_button(self, toolbar, icon, tooltip, callback):
        """Add an action button to the toolbar."""
        btn = Gtk.ToolButton.new_from_stock(icon)
        btn.set_tooltip_text(tooltip)
        btn.connect("clicked", lambda *_: callback())
        toolbar.insert(btn, -1)
    
    def _setup_events(self):
        """Set up event handlers."""
        self.darea.set_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                              Gdk.EventMask.BUTTON_RELEASE_MASK |
                              Gdk.EventMask.POINTER_MOTION_MASK |
                              Gdk.EventMask.KEY_PRESS_MASK)
        
        self.darea.connect("draw", self.on_draw)
        self.darea.connect("button-press-event", self.on_button_press)
        self.darea.connect("button-release-event", self.on_button_release)
        self.darea.connect("motion-notify-event", self.on_motion)
        
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect("key-press-event", self.on_key)
        self.connect("delete-event", self.on_close)
    
    def set_tool(self, tool: str):
        """Set the current drawing tool."""
        self.current_tool = tool
        
        # Save tool selection if enabled
        if self.settings.remember_tool_selection:
            self.settings.last_selected_tool = tool
            save_settings()
        
        self._update_status(f"Tool: {tool.title()}")
    
    def on_key(self, _w, e: Gdk.EventKey):
        """Handle keyboard events."""
        key = e.keyval
        ctrl = (e.state & Gdk.ModifierType.CONTROL_MASK) != 0
        shift = (e.state & Gdk.ModifierType.SHIFT_MASK) != 0
        
        if key in (Gdk.KEY_P, Gdk.KEY_p):
            self.set_tool(self.TOOL_PEN)
        elif key in (Gdk.KEY_R, Gdk.KEY_r):
            self.set_tool(self.TOOL_RECT)
        elif key in (Gdk.KEY_A, Gdk.KEY_a):
            self.set_tool(self.TOOL_ARROW)
        elif key in (Gdk.KEY_T, Gdk.KEY_t):
            self.set_tool(self.TOOL_TEXT)
        elif ctrl and key == Gdk.KEY_z:
            self.undo()
        elif ctrl and shift and key == Gdk.KEY_s:
            self.save_dialog()
        elif ctrl and key == Gdk.KEY_s:
            if self.settings.autosave_enabled:
                self.quick_save()
            else:
                self.save_dialog()
        elif ctrl and key == Gdk.KEY_c:
            self.copy_to_clipboard()
        elif key == Gdk.KEY_Return:
            self.copy_to_clipboard()
        elif key == Gdk.KEY_Escape:
            self.close()
        elif key in (Gdk.KEY_U, Gdk.KEY_u):
            self.upload()
        
        return True
    
    def on_close(self, widget, event):
        """Handle window close event."""
        if self.modified and self.settings.show_save_confirmation:
            dialog = Gtk.MessageDialog(
                parent=self,
                flags=Gtk.DialogFlags.MODAL,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Save changes before closing?"
            )
            dialog.format_secondary_text("You have unsaved changes. Do you want to save them?")
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                if self.settings.autosave_enabled:
                    self.quick_save()
                else:
                    self.save_dialog()
        
        return False  # Allow window to close
    
    def on_button_press(self, _w, e: Gdk.EventButton):
        """Handle mouse button press."""
        if e.button != 1:
            return False
        
        x, y = e.x, e.y
        self.drawing = True
        self.temp_points = [(x, y)]
        
        if self.current_tool == self.TOOL_TEXT:
            self.create_text_at(x, y)
            self.drawing = False
        
        return True
    
    def on_motion(self, _w, e: Gdk.EventMotion):
        """Handle mouse motion."""
        if not self.drawing:
            return False
        
        x, y = e.x, e.y
        
        if self.current_tool == self.TOOL_PEN:
            self.temp_points.append((x, y))
        else:
            if len(self.temp_points) == 1:
                self.temp_points.append((x, y))
            else:
                self.temp_points[1] = (x, y)
        
        self.darea.queue_draw()
        return True
    
    def on_button_release(self, _w, e: Gdk.EventButton):
        """Handle mouse button release."""
        if e.button != 1 or not self.drawing:
            return False
        
        self.drawing = False
        
        if not self.temp_points:
            return True
        
        # Save current state for undo (limit undo stack size)
        self.undo_stack.append([shape for shape in self.shapes])
        if len(self.undo_stack) > self.settings.max_undo_levels:
            self.undo_stack.pop(0)
        
        # Get default color and widths from settings
        default_color = settings_manager.get_default_color()
        
        # Add the new shape
        if self.current_tool == self.TOOL_PEN and len(self.temp_points) >= 2:
            self.shapes.append(PenStroke(
                points=self.temp_points.copy(),
                width=self.settings.default_pen_width,
                color=default_color
            ))
        elif self.current_tool == self.TOOL_RECT and len(self.temp_points) >= 2:
            (x1, y1), (x2, y2) = self.temp_points[0], self.temp_points[-1]
            self.shapes.append(RectShape(
                x=min(x1, x2), y=min(y1, y2),
                w=abs(x2-x1), h=abs(y2-y1),
                width=self.settings.default_rect_width,
                color=default_color
            ))
        elif self.current_tool == self.TOOL_ARROW and len(self.temp_points) >= 2:
            (x1, y1), (x2, y2) = self.temp_points[0], self.temp_points[-1]
            self.shapes.append(ArrowShape(
                x1=x1, y1=y1, x2=x2, y2=y2,
                width=self.settings.default_arrow_width,
                color=default_color
            ))
        
        self.temp_points = []
        self.modified = True
        self._update_title()
        self.darea.queue_draw()
        return True
    
    def create_text_at(self, x, y):
        """Create a text annotation at the specified position."""
        dialog = Gtk.Dialog(title="Add Text", transient_for=self, flags=0)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        
        entry = Gtk.Entry()
        entry.set_activates_default(True)
        
        box = dialog.get_content_area()
        box.set_border_width(12)
        box.add(Gtk.Label(label="Enter text:"))
        box.add(entry)
        box.show_all()
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            text = entry.get_text().strip()
            if text:
                # Save current state for undo
                self.undo_stack.append([shape for shape in self.shapes])
                if len(self.undo_stack) > self.settings.max_undo_levels:
                    self.undo_stack.pop(0)
                
                default_color = settings_manager.get_default_color()
                self.shapes.append(TextLabel(
                    x=x, y=y, text=text,
                    font_size=self.settings.default_text_size,
                    color=default_color
                ))
                self.modified = True
                self._update_title()
                self.darea.queue_draw()
        
        dialog.destroy()
    
    def draw_arrow(self, cr: cairo.Context, x1, y1, x2, y2, width=3.0):
        """Draw an arrow on the cairo context."""
        cr.set_line_width(width)
        cr.move_to(x1, y1)
        cr.line_to(x2, y2)
        cr.stroke()
        
        # Draw arrowhead
        ang = math.atan2(y2 - y1, x2 - x1)
        head_len = 12 + width * 2
        head_ang = math.pi / 6
        
        xh1 = x2 - head_len * math.cos(ang - head_ang)
        yh1 = y2 - head_len * math.sin(ang - head_ang)
        xh2 = x2 - head_len * math.cos(ang + head_ang)
        yh2 = y2 - head_len * math.sin(ang + head_ang)
        
        cr.move_to(x2, y2)
        cr.line_to(xh1, yh1)
        cr.move_to(x2, y2)
        cr.line_to(xh2, yh2)
        cr.stroke()
    
    def on_draw(self, widget, cr: cairo.Context):
        """Handle drawing on the canvas."""
        # Draw the base image
        pb = pil_to_pixbuf(self.base_image)
        Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
        cr.paint()
        
        # Draw all shapes
        for shp in self.shapes:
            # Convert color from 0-255 to 0-1 range for Cairo
            r, g, b, a = [c/255.0 for c in shp.color]
            cr.set_source_rgba(r, g, b, a)
            
            if isinstance(shp, PenStroke):
                cr.set_line_width(shp.width)
                pts = shp.points
                if len(pts) >= 2:
                    cr.move_to(*pts[0])
                    for p in pts[1:]:
                        cr.line_to(*p)
                    cr.stroke()
            
            elif isinstance(shp, RectShape):
                cr.set_line_width(shp.width)
                cr.rectangle(shp.x + 0.5, shp.y + 0.5, shp.w, shp.h)
                cr.stroke()
            
            elif isinstance(shp, ArrowShape):
                self.draw_arrow(cr, shp.x1, shp.y1, shp.x2, shp.y2, shp.width)
            
            elif isinstance(shp, TextLabel):
                cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                cr.set_font_size(shp.font_size)
                cr.move_to(shp.x, shp.y)
                cr.show_text(shp.text)
        
        # Draw temporary shape being drawn
        if self.temp_points:
            cr.set_source_rgba(0.6, 0.2, 1.0, 0.7)
            
            if self.current_tool == self.TOOL_PEN and len(self.temp_points) >= 2:
                cr.set_line_width(3.0)
                cr.move_to(*self.temp_points[0])
                for p in self.temp_points[1:]:
                    cr.line_to(*p)
                cr.stroke()
            
            elif self.current_tool in (self.TOOL_RECT, self.TOOL_ARROW) and len(self.temp_points) >= 2:
                (x1, y1), (x2, y2) = self.temp_points[0], self.temp_points[-1]
                
                if self.current_tool == self.TOOL_RECT:
                    cr.set_line_width(3.0)
                    cr.rectangle(min(x1, x2) + 0.5, min(y1, y2) + 0.5, abs(x2-x1), abs(y2-y1))
                    cr.stroke()
                else:
                    self.draw_arrow(cr, x1, y1, x2, y2, width=3.0)
        
        return False
    
    def undo(self):
        """Undo the last action."""
        if self.undo_stack:
            self.shapes = self.undo_stack.pop()
            self.modified = True
            self._update_title()
            self.darea.queue_draw()
            self._update_status("Undone")
    
    def quick_save(self):
        """Quick save to the default location (NEW FEATURE)."""
        if not self.settings.autosave_enabled:
            self.save_dialog()
            return
        
        try:
            # Generate filename with timestamp
            filename = settings_manager.get_default_save_path()
            
            # Ensure the directory exists
            save_dir = Path(filename).parent
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the image
            self._save_current_image_pil(filename)
            
            # Copy to clipboard if enabled
            if self.settings.copy_to_clipboard_on_save:
                self.screenshot_capture.copy_to_clipboard(filename)
            
            # Show confirmation if enabled
            if self.settings.show_save_confirmation:
                self._show_info_dialog(f"Screenshot saved to {filename}")
            else:
                self._update_status(f"Saved: {Path(filename).name}")
            
            self.modified = False
            self._update_title()
            
            # Auto-close if enabled
            if self.settings.auto_close_after_save:
                self.close()
                
        except Exception as e:
            self._show_error_dialog(f"Failed to save: {e}")
    
    def copy_to_clipboard(self):
        """Copy the current image to clipboard."""
        try:
            # Create a temporary file with the current image
            temp_file = str(Path(self.settings.temp_dir) / f"clipboard_{os.getpid()}.png")
            self._save_current_image_pil(temp_file)
            
            # Use our screenshot capture module to copy to clipboard
            if self.screenshot_capture.copy_to_clipboard(temp_file):
                self._update_status("Copied to clipboard")
                if self.settings.show_save_confirmation:
                    self._show_info_dialog("Image copied to clipboard!")
            else:
                self._show_error_dialog("Failed to copy to clipboard")
            
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
                
        except Exception as e:
            self._show_error_dialog(f"Failed to copy to clipboard: {e}")
    
    def save_dialog(self):
        """Show save file dialog."""
        dialog = Gtk.FileChooserDialog(
            title="Save Screenshot",
            parent=self,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        # Set default location
        if self.settings.default_save_location and os.path.exists(self.settings.default_save_location):
            dialog.set_current_folder(self.settings.default_save_location)
        
        # Add file filters
        filter_png = Gtk.FileFilter()
        filter_png.set_name("PNG files")
        filter_png.add_mime_type("image/png")
        dialog.add_filter(filter_png)
        
        filter_jpg = Gtk.FileFilter()
        filter_jpg.set_name("JPEG files")
        filter_jpg.add_mime_type("image/jpeg")
        dialog.add_filter(filter_jpg)
        
        # Set default filename
        default_filename = time.strftime(self.settings.filename_pattern) + f".{self.settings.default_format}"
        dialog.set_current_name(default_filename)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self._save_current_image_pil(filename)
                
                # Copy to clipboard if enabled
                if self.settings.copy_to_clipboard_on_save:
                    self.screenshot_capture.copy_to_clipboard(filename)
                
                if self.settings.show_save_confirmation:
                    self._show_info_dialog(f"Screenshot saved to {filename}")
                else:
                    self._update_status(f"Saved: {Path(filename).name}")
                
                self.modified = False
                self._update_title()
                
                # Auto-close if enabled
                if self.settings.auto_close_after_save:
                    self.close()
                    
            except Exception as e:
                self._show_error_dialog(f"Failed to save: {e}")
        
        dialog.destroy()
    
    def upload(self):
        """Upload the screenshot to a service."""
        # This is a placeholder for upload functionality
        self._show_info_dialog("Upload functionality not implemented yet")
    
    def show_preferences(self):
        """Show the preferences dialog."""
        prefs = PreferencesDialog(parent=self)
        if prefs.run_dialog():
            # Reload settings
            self.settings = get_settings()
            self._update_status("Settings updated")
    
    def _save_current_image_pil(self, filename: str):
        """Save the current image with annotations using PIL."""
        try:
            # Start with a copy of the base image
            img_w, img_h = self.base_image.size
            result_image = self.base_image.copy().convert('RGBA')
            
            # Create a drawing context
            draw = ImageDraw.Draw(result_image)
            
            # Try to load a font, fall back to default if not available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            except:
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
            
            # Draw all annotations using PIL
            for shp in self.shapes:
                color = shp.color  # Already in RGBA 0-255 format
                
                if isinstance(shp, PenStroke):
                    # Draw pen strokes as connected lines
                    pts = shp.points
                    if len(pts) >= 2:
                        for i in range(len(pts) - 1):
                            x1, y1 = pts[i]
                            x2, y2 = pts[i + 1]
                            draw.line([(x1, y1), (x2, y2)], fill=color, width=int(shp.width))
                
                elif isinstance(shp, RectShape):
                    # Draw rectangle outline
                    x1, y1 = shp.x, shp.y
                    x2, y2 = shp.x + shp.w, shp.y + shp.h
                    draw.rectangle([(x1, y1), (x2, y2)], outline=color, width=int(shp.width))
                
                elif isinstance(shp, ArrowShape):
                    # Draw arrow line
                    draw.line([(shp.x1, shp.y1), (shp.x2, shp.y2)], fill=color, width=int(shp.width))
                    
                    # Draw arrowhead
                    ang = math.atan2(shp.y2 - shp.y1, shp.x2 - shp.x1)
                    head_len = 12 + shp.width * 2
                    head_ang = math.pi / 6
                    
                    xh1 = shp.x2 - head_len * math.cos(ang - head_ang)
                    yh1 = shp.y2 - head_len * math.sin(ang - head_ang)
                    xh2 = shp.x2 - head_len * math.cos(ang + head_ang)
                    yh2 = shp.y2 - head_len * math.sin(ang + head_ang)
                    
                    draw.line([(shp.x2, shp.y2), (xh1, yh1)], fill=color, width=int(shp.width))
                    draw.line([(shp.x2, shp.y2), (xh2, yh2)], fill=color, width=int(shp.width))
                
                elif isinstance(shp, TextLabel):
                    # Draw text
                    if font:
                        draw.text((shp.x, shp.y - shp.font_size), shp.text, fill=color, font=font)
                    else:
                        draw.text((shp.x, shp.y - shp.font_size), shp.text, fill=color)
            
            # Determine format based on file extension
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in ['.jpg', '.jpeg']:
                # Convert to RGB for JPEG
                result_image = result_image.convert('RGB')
                result_image.save(filename, 'JPEG', quality=self.settings.image_quality_jpeg)
            else:
                # Save as PNG (default)
                result_image.save(filename, 'PNG')
            
            print(f"Image saved successfully to {filename}")
            
        except Exception as e:
            print(f"Error saving image: {e}")
            raise
    
    def _update_title(self):
        """Update the window title."""
        title = "ZorinShot Editor"
        if self.modified:
            title += " *"
        self.set_title(title)
    
    def _update_status(self, message: str):
        """Update the status bar."""
        self.statusbar.pop(self.status_context)
        self.statusbar.push(self.status_context, message)
    
    def _show_info_dialog(self, message: str):
        """Show an info dialog."""
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()
    
    def _show_error_dialog(self, message: str):
        """Show an error dialog."""
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


def main():
    """Main entry point."""
    # Initialize GTK
    Gtk.init(sys.argv)
    
    # Create and run the application
    app = ZorinShotApp()
    
    # Start GTK main loop
    Gtk.main()


if __name__ == "__main__":
    main()

