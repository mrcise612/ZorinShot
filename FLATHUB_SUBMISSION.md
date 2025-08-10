# ZorinShot - Flathub Submission Package

This package contains everything needed to submit ZorinShot to Flathub.

## 📋 Submission Checklist

### ✅ Requirements Met
- [x] **Open Source**: MIT License
- [x] **Desktop Application**: GTK-based GUI application
- [x] **Flatpak Manifest**: Complete YAML manifest file
- [x] **AppStream Metadata**: Proper metainfo.xml file
- [x] **Desktop Entry**: Valid .desktop file
- [x] **Icon**: SVG icon provided
- [x] **Build System**: Uses flatpak-builder
- [x] **Sandboxing**: Proper finish-args permissions
- [x] **Dependencies**: All dependencies declared

### 📦 Package Contents

```
zorinshot-flatpak/
├── com.github.zorinshot.ZorinShot.yml          # Main Flatpak manifest
├── com.github.zorinshot.ZorinShot.desktop      # Desktop entry
├── com.github.zorinshot.ZorinShot.metainfo.xml # AppStream metadata
├── com.github.zorinshot.ZorinShot.svg          # Application icon
├── zorinshot                                   # Launcher script
├── wayland_screenshot_simple.py               # Screenshot engine
├── zorinshot_enhanced.py                      # Main application
├── zorinshot_settings.py                      # Settings system
├── zorinshot_preferences.py                   # Preferences dialog
├── build-flatpak.sh                          # Build script
└── FLATHUB_SUBMISSION.md                      # This file
```

## 🚀 How to Submit to Flathub

### Step 1: Create GitHub Repository
1. Create a new repository: `https://github.com/YOUR_USERNAME/com.github.zorinshot.ZorinShot`
2. Upload all files from this package
3. Ensure the repository is public

### Step 2: Test the Build
```bash
# Build and test locally
./build-flatpak.sh

# Test the application
flatpak run com.github.zorinshot.ZorinShot
```

### Step 3: Submit to Flathub
1. Fork the Flathub repository: `https://github.com/flathub/flathub`
2. Create a new branch: `git checkout -b add-zorinshot`
3. Add your manifest file to the flathub repository
4. Create a pull request with:
   - Title: "Add ZorinShot"
   - Description: Include app description and features
   - Link to your source repository

### Step 4: Review Process
- Flathub maintainers will review your submission
- They may request changes or improvements
- Address any feedback promptly
- Once approved, your app will be published

## 📝 Application Information

**App ID**: `com.github.zorinshot.ZorinShot`
**Name**: ZorinShot
**Category**: Graphics, Photography, Utility
**License**: MIT
**Runtime**: GNOME 46

**Description**: 
Wayland-compatible screenshot tool with autosave and annotation features. Perfect for content creators, developers, and anyone who needs to capture and annotate screenshots regularly.

**Key Features**:
- Wayland-native screenshot capture with X11 fallback
- Interactive region selection
- Annotation tools (pen, arrow, rectangle, text)
- Autosave with customizable default locations
- Quick Save and Save As functionality
- Clipboard integration
- Persistent settings and preferences
- Keyboard shortcuts for efficient workflow

## 🔧 Technical Details

### Permissions (finish-args)
- `--socket=wayland` - Wayland display access
- `--socket=x11` - X11 fallback support
- `--share=ipc` - Inter-process communication
- `--filesystem=home` - Access to user's home directory
- `--filesystem=xdg-desktop` - Desktop folder access
- `--filesystem=xdg-pictures` - Pictures folder access
- `--filesystem=xdg-documents` - Documents folder access
- `--talk-name=org.freedesktop.portal.Screenshot` - Screenshot portal
- `--talk-name=org.freedesktop.portal.Clipboard` - Clipboard access

### Dependencies
- **Runtime**: org.gnome.Platform 46
- **Python Packages**: Pillow (PIL), requests
- **System Tools**: grim, slurp (for Wayland), gnome-screenshot (fallback)

### Build Process
1. Install Python dependencies (Pillow, requests)
2. Install ZorinShot Python modules
3. Install launcher script
4. Install desktop entry and icon
5. Install AppStream metadata

## 🧪 Testing Instructions

### Local Testing
```bash
# Build the Flatpak
./build-flatpak.sh

# Run the application
flatpak run com.github.zorinshot.ZorinShot

# Test features:
# 1. Take a screenshot
# 2. Use annotation tools
# 3. Save to different locations
# 4. Test autosave functionality
# 5. Check preferences dialog
```

### Validation
```bash
# Validate manifest
flatpak-builder --show-manifest com.github.zorinshot.ZorinShot.yml

# Validate desktop file
desktop-file-validate com.github.zorinshot.ZorinShot.desktop

# Validate AppStream metadata
appstream-util validate com.github.zorinshot.ZorinShot.metainfo.xml
```

## 📞 Support Information

**Homepage**: https://github.com/zorinshot/zorinshot
**Bug Reports**: https://github.com/zorinshot/zorinshot/issues
**Documentation**: https://github.com/zorinshot/zorinshot/wiki

## 📄 License

This application is licensed under the MIT License. See the LICENSE file in the source repository for details.

---

**Ready for Flathub submission!** 🎉

