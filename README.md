# ZorinShot Flatpak Package

A complete Flatpak package for ZorinShot - a Wayland-compatible screenshot tool with autosave and annotation features.

## 🚀 Quick Start

### Build and Install
```bash
# Make build script executable
chmod +x build-flatpak.sh

# Build and install ZorinShot
./build-flatpak.sh
```

### Run the Application
```bash
# Run ZorinShot
flatpak run com.github.zorinshot.ZorinShot
```

## 📦 What's Included

- **Complete Flatpak manifest** (`com.github.zorinshot.ZorinShot.yml`)
- **AppStream metadata** for software centers
- **Desktop entry** for application menus
- **SVG icon** for consistent branding
- **Build script** for easy compilation
- **All source files** for ZorinShot Enhanced

## ✨ Features

- **Wayland-native screenshot capture** with X11 fallback
- **Interactive region selection** with visual feedback
- **Annotation tools**: pen, arrow, rectangle, text
- **Autosave functionality** with customizable default locations
- **Quick Save and Save As** options
- **Clipboard integration** for instant sharing
- **Persistent settings** and preferences
- **Keyboard shortcuts** for efficient workflow
- **Multiple format support** (PNG, JPEG)

## 🔧 Requirements

- **Flatpak** and **flatpak-builder** installed
- **GNOME runtime** (automatically installed)
- **Internet connection** for downloading dependencies

### Install Requirements (Ubuntu/Debian)
```bash
sudo apt install flatpak flatpak-builder
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

## 🏗️ Manual Build Process

If you prefer to build manually:

```bash
# Install GNOME runtime
flatpak install flathub org.gnome.Platform//46 org.gnome.Sdk//46

# Build the package
flatpak-builder --force-clean --sandbox --user --install-deps-from=flathub \
    --repo=repo build-dir com.github.zorinshot.ZorinShot.yml

# Install locally
flatpak --user remote-add --no-gpg-verify zorinshot-repo repo
flatpak --user install zorinshot-repo com.github.zorinshot.ZorinShot
```

## 📱 Usage

### Basic Workflow
1. **Launch**: `flatpak run com.github.zorinshot.ZorinShot`
2. **Select region**: Click and drag to select screenshot area
3. **Annotate**: Use tools to add arrows, text, shapes
4. **Save**: Use Quick Save (Ctrl+S) or Save As (Ctrl+Shift+S)

### Set Up Autosave
1. Go to **Edit → Preferences**
2. Click **Autosave** tab
3. Enable autosave and set default location
4. Configure filename pattern and format

### Keyboard Shortcuts
- **Ctrl+S**: Quick Save (to default location)
- **Ctrl+Shift+S**: Save As (choose location)
- **Ctrl+C** / **Enter**: Copy to clipboard
- **P**: Pen tool
- **A**: Arrow tool
- **R**: Rectangle tool
- **T**: Text tool
- **Ctrl+Z**: Undo
- **Esc**: Close

## 🗑️ Uninstall

```bash
# Remove the application
flatpak --user uninstall com.github.zorinshot.ZorinShot

# Remove the repository (optional)
flatpak --user remote-delete zorinshot-repo
```

## 🐛 Troubleshooting

### Build Issues
- Ensure you have internet connection for downloading dependencies
- Check that GNOME runtime is properly installed
- Try cleaning build directory: `rm -rf build-dir repo`

### Runtime Issues
- Make sure Wayland/X11 is properly configured
- Check that screenshot tools are available in the sandbox
- Verify file system permissions for saving screenshots

### Permission Issues
- The Flatpak has necessary permissions for screenshot capture
- Home directory access is granted for saving files
- Portal access is configured for Wayland screenshot functionality

## 📄 License

MIT License - see source repository for details.

## 🤝 Contributing

This is a Flatpak packaging of ZorinShot. For application issues or feature requests, please visit the main ZorinShot repository.

---

**Enjoy taking screenshots with ZorinShot!** 📸

