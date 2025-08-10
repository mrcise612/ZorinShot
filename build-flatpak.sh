#!/bin/bash
# ZorinShot Flatpak Build Script

set -e

echo "🔨 Building ZorinShot Flatpak Package"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if flatpak-builder is available
if ! command -v flatpak-builder &> /dev/null; then
    print_error "flatpak-builder not found. Please install it first:"
    echo "sudo apt install flatpak flatpak-builder"
    exit 1
fi

# Check if GNOME runtime is available
print_status "Checking for GNOME runtime..."
if ! flatpak list | grep -q "org.gnome.Platform.*46"; then
    print_warning "GNOME 46 runtime not found. Installing..."
    flatpak install -y flathub org.gnome.Platform//46 org.gnome.Sdk//46 || {
        print_warning "Failed to install GNOME 46, trying GNOME 45..."
        flatpak install -y flathub org.gnome.Platform//45 org.gnome.Sdk//45 || {
            print_error "Failed to install GNOME runtime"
            exit 1
        }
    }
fi

# Create build directory
BUILD_DIR="build-dir"
REPO_DIR="repo"

print_status "Creating build directories..."
rm -rf "$BUILD_DIR" "$REPO_DIR"
mkdir -p "$BUILD_DIR" "$REPO_DIR"

# Build the Flatpak
print_status "Building ZorinShot Flatpak..."
flatpak-builder --force-clean --sandbox --user --install-deps-from=flathub \
    --repo="$REPO_DIR" "$BUILD_DIR" com.github.zorinshot.ZorinShot.yml

if [ $? -eq 0 ]; then
    print_success "Flatpak build completed successfully!"
    
    # Install the built package
    print_status "Installing ZorinShot Flatpak..."
    flatpak --user remote-add --no-gpg-verify zorinshot-repo "$REPO_DIR"
    flatpak --user install -y zorinshot-repo com.github.zorinshot.ZorinShot
    
    print_success "ZorinShot Flatpak installed successfully!"
    echo ""
    echo "🚀 You can now run ZorinShot with:"
    echo "   flatpak run com.github.zorinshot.ZorinShot"
    echo ""
    echo "📦 To create a bundle for distribution:"
    echo "   flatpak build-bundle $REPO_DIR zorinshot.flatpak com.github.zorinshot.ZorinShot"
    echo ""
    echo "🗑️  To uninstall:"
    echo "   flatpak --user uninstall com.github.zorinshot.ZorinShot"
    
else
    print_error "Flatpak build failed!"
    exit 1
fi

