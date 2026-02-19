#!/bin/bash

# NeuroFlow Documentation Build and Deploy Script

set -e  # Exit on error

echo "🚀 NeuroFlow Documentation Build Script"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running in docs-site directory
if [ ! -f "mkdocs.yml" ]; then
    log_error "Please run this script from the docs-site directory"
    exit 1
fi

# Install dependencies
log_info "Installing dependencies..."
pip install mkdocs mkdocs-material mkdocs-minify-plugin mike

# Check for required files
log_info "Checking documentation files..."
required_files=(
    "docs/index.md"
    "docs/getting-started/installation.md"
    "docs/getting-started/quickstart.md"
    "docs/concepts/architecture.md"
    "docs/guides/building-agents.md"
    "docs/api-reference/python/index.md"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        log_warn "Missing file: $file"
    fi
done

# Build documentation
log_info "Building documentation..."
mkdocs build --verbose

# Check build output
if [ -d "site" ]; then
    log_info "Build successful! Site directory created."
    echo ""
    echo "📊 Build Statistics:"
    echo "   Files generated: $(find site -type f | wc -l)"
    echo "   Total size: $(du -sh site | cut -f1)"
    echo ""
else
    log_error "Build failed! Site directory not created."
    exit 1
fi

# Preview (optional)
if [ "$1" == "--serve" ]; then
    log_info "Starting local preview server..."
    echo "   Open http://localhost:8000 in your browser"
    echo "   Press Ctrl+C to stop"
    echo ""
    mkdocs serve
fi

echo "✅ Documentation build complete!"
echo ""
echo "Next steps:"
echo "  - Preview: ./deploy.sh --serve"
echo "  - Deploy:  mike deploy --push main"
echo ""
