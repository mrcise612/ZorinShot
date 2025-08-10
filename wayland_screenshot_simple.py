#!/usr/bin/env python3
"""
Simplified Wayland Screenshot Capture Module
Focuses on working methods without complex D-Bus dependencies:
1. GNOME Screenshot (works in most environments)
2. grim/slurp (for pure Wayland environments)
3. ImageMagick import (X11 fallback)
"""

import os
import sys
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WaylandScreenshotCapture:
    """Simplified Wayland screenshot capture with reliable fallback methods."""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "zorinshot"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Check available methods
        self.grim_available = self._check_grim_available()
        self.gnome_screenshot_available = self._check_gnome_screenshot_available()
        self.imagemagick_available = self._check_imagemagick_available()
        
        logger.info(f"Available methods: Grim={self.grim_available}, "
                   f"GNOME={self.gnome_screenshot_available}, "
                   f"ImageMagick={self.imagemagick_available}")
    
    def _check_grim_available(self) -> bool:
        """Check if grim and slurp are available."""
        try:
            subprocess.run(['grim', '--version'], capture_output=True, check=True)
            subprocess.run(['slurp', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_gnome_screenshot_available(self) -> bool:
        """Check if gnome-screenshot is available."""
        try:
            subprocess.run(['gnome-screenshot', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_imagemagick_available(self) -> bool:
        """Check if ImageMagick import is available."""
        try:
            subprocess.run(['import', '-version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def capture_fullscreen(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Capture fullscreen screenshot using the best available method.
        
        Args:
            output_path: Optional path to save the screenshot
            
        Returns:
            Path to the captured screenshot file, or None if failed
        """
        if not output_path:
            output_path = str(self.temp_dir / f"screenshot_{os.getpid()}.png")
        
        # Try methods in order of preference
        methods = [
            ("Grim", self._capture_fullscreen_grim),
            ("GNOME Screenshot", self._capture_fullscreen_gnome),
            ("ImageMagick", self._capture_fullscreen_imagemagick)
        ]
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Trying {method_name} for fullscreen capture")
                result = method_func(output_path)
                if result:
                    logger.info(f"Successfully captured using {method_name}")
                    return result
            except Exception as e:
                logger.warning(f"{method_name} failed: {e}")
                continue
        
        logger.error("All screenshot methods failed")
        return None
    
    def capture_region(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Capture region screenshot with interactive selection.
        
        Args:
            output_path: Optional path to save the screenshot
            
        Returns:
            Path to the captured screenshot file, or None if failed
        """
        if not output_path:
            output_path = str(self.temp_dir / f"screenshot_region_{os.getpid()}.png")
        
        # Try methods in order of preference
        methods = [
            ("Grim+Slurp", self._capture_region_grim_slurp),
            ("GNOME Screenshot", self._capture_region_gnome),
            ("ImageMagick", self._capture_region_imagemagick)
        ]
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Trying {method_name} for region capture")
                result = method_func(output_path)
                if result:
                    logger.info(f"Successfully captured using {method_name}")
                    return result
            except Exception as e:
                logger.warning(f"{method_name} failed: {e}")
                continue
        
        logger.error("All region capture methods failed")
        return None
    
    def _capture_fullscreen_grim(self, output_path: str) -> Optional[str]:
        """Capture fullscreen using grim."""
        if not self.grim_available:
            return None
        
        try:
            result = subprocess.run([
                'grim', output_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                logger.error(f"Grim failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Grim screenshot failed: {e}")
            return None
    
    def _capture_fullscreen_gnome(self, output_path: str) -> Optional[str]:
        """Capture fullscreen using gnome-screenshot."""
        if not self.gnome_screenshot_available:
            return None
        
        try:
            result = subprocess.run([
                'gnome-screenshot', '--file', output_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                logger.error(f"GNOME screenshot failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"GNOME screenshot failed: {e}")
            return None
    
    def _capture_fullscreen_imagemagick(self, output_path: str) -> Optional[str]:
        """Capture fullscreen using ImageMagick import."""
        if not self.imagemagick_available:
            return None
        
        try:
            result = subprocess.run([
                'import', '-window', 'root', output_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                logger.error(f"ImageMagick failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"ImageMagick screenshot failed: {e}")
            return None
    
    def _capture_region_grim_slurp(self, output_path: str) -> Optional[str]:
        """Capture region using grim and slurp."""
        if not self.grim_available:
            return None
        
        try:
            # First run slurp to get the region selection
            slurp_result = subprocess.run([
                'slurp'
            ], capture_output=True, text=True, timeout=30)
            
            if slurp_result.returncode != 0:
                logger.error(f"Slurp failed: {slurp_result.stderr}")
                return None
            
            region = slurp_result.stdout.strip()
            if not region:
                logger.info("No region selected")
                return None
            
            # Now use grim to capture the selected region
            grim_result = subprocess.run([
                'grim', '-g', region, output_path
            ], capture_output=True, text=True, timeout=10)
            
            if grim_result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                logger.error(f"Grim region capture failed: {grim_result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Grim+Slurp region capture failed: {e}")
            return None
    
    def _capture_region_gnome(self, output_path: str) -> Optional[str]:
        """Capture region using gnome-screenshot."""
        if not self.gnome_screenshot_available:
            return None
        
        try:
            result = subprocess.run([
                'gnome-screenshot', '--area', '--file', output_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                logger.error(f"GNOME region screenshot failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"GNOME region screenshot failed: {e}")
            return None
    
    def _capture_region_imagemagick(self, output_path: str) -> Optional[str]:
        """Capture region using ImageMagick import."""
        if not self.imagemagick_available:
            return None
        
        try:
            result = subprocess.run([
                'import', output_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                logger.error(f"ImageMagick region capture failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"ImageMagick region capture failed: {e}")
            return None
    
    def copy_to_clipboard(self, image_path: str) -> bool:
        """Copy image to clipboard using wl-clipboard or xclip."""
        try:
            # Try wl-clipboard first (Wayland)
            if shutil.which('wl-copy'):
                with open(image_path, 'rb') as f:
                    result = subprocess.run([
                        'wl-copy', '--type', 'image/png'
                    ], input=f.read(), timeout=10)
                    return result.returncode == 0
            
            # Fall back to xclip (X11)
            elif shutil.which('xclip'):
                result = subprocess.run([
                    'xclip', '-selection', 'clipboard', '-t', 'image/png', '-i', image_path
                ], capture_output=True, timeout=10)
                return result.returncode == 0
            
            else:
                logger.error("No clipboard utility available (wl-copy or xclip)")
                return False
                
        except Exception as e:
            logger.error(f"Clipboard copy failed: {e}")
            return False
    
    def get_available_methods(self) -> dict:
        """Get information about available screenshot methods."""
        return {
            'grim': self.grim_available,
            'gnome': self.gnome_screenshot_available,
            'imagemagick': self.imagemagick_available
        }
    
    def install_dependencies(self) -> bool:
        """Install required dependencies for Wayland screenshot capture."""
        try:
            # Check if we're on a Debian/Ubuntu system
            if shutil.which('apt'):
                packages = [
                    'grim',           # Wayland screenshot utility
                    'slurp',          # Wayland region selector
                    'wl-clipboard',   # Wayland clipboard utilities
                    'gnome-screenshot', # GNOME screenshot tool
                    'imagemagick',    # ImageMagick for X11 fallback
                    'xclip',          # X11 clipboard utility
                ]
                
                print("Installing dependencies...")
                result = subprocess.run([
                    'sudo', 'apt', 'update', '&&',
                    'sudo', 'apt', 'install', '-y'
                ] + packages, shell=True, text=True)
                
                return result.returncode == 0
            else:
                print("Automatic dependency installation not supported on this system")
                print("Please install: grim, slurp, wl-clipboard, gnome-screenshot, imagemagick, xclip")
                return False
                
        except Exception as e:
            logger.error(f"Dependency installation failed: {e}")
            return False


def main():
    """Test the screenshot capture functionality."""
    capture = WaylandScreenshotCapture()
    
    print("Available methods:", capture.get_available_methods())
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'fullscreen':
            result = capture.capture_fullscreen()
            if result:
                print(f"Fullscreen screenshot saved to: {result}")
                # Try to copy to clipboard
                if capture.copy_to_clipboard(result):
                    print("Screenshot copied to clipboard")
            else:
                print("Fullscreen screenshot failed")
        elif sys.argv[1] == 'region':
            result = capture.capture_region()
            if result:
                print(f"Region screenshot saved to: {result}")
                # Try to copy to clipboard
                if capture.copy_to_clipboard(result):
                    print("Screenshot copied to clipboard")
            else:
                print("Region screenshot failed")
        elif sys.argv[1] == 'install':
            success = capture.install_dependencies()
            if success:
                print("Dependencies installed successfully")
            else:
                print("Dependency installation failed")
    else:
        print("Usage: python3 wayland_screenshot_simple.py [fullscreen|region|install]")


if __name__ == "__main__":
    main()

