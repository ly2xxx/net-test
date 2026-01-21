#!/bin/bash

# fix-claude-version.sh - Fix Claude Code version mismatches
# This script detects and resolves conflicts between multiple Claude Code installations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Extract version from package path
get_version_from_npm() {
    local path="$1"
    npm list -g @anthropic-ai/claude-code --prefix "$path" 2>/dev/null | grep '@anthropic-ai/claude-code@' | sed 's/.*@anthropic-ai\/claude-code@//' | head -1
}

# Get version from executable
get_running_version() {
    local exec_path="$1"
    if [ -f "$exec_path" ]; then
        grep -oP '(?<=// Version: )[0-9.]+' "$exec_path" 2>/dev/null | head -1
    fi
}

# Main detection logic
detect_version_mismatch() {
    log_info "Detecting Claude Code installations..."
    echo ""

    # Find where claude is currently running from
    CLAUDE_PATH=$(which claude 2>/dev/null || echo "")

    if [ -z "$CLAUDE_PATH" ]; then
        log_error "Claude Code is not found in PATH"
        exit 1
    fi

    log_info "Running executable: $CLAUDE_PATH"

    # Get running version from the executable
    RUNNING_VERSION=$(get_running_version "$CLAUDE_PATH")
    if [ -n "$RUNNING_VERSION" ]; then
        log_info "Running version: $RUNNING_VERSION"
    else
        log_warning "Could not detect running version from executable"
    fi

    # Find all npm installations
    declare -A installations

    # Check common npm global locations
    NPM_GLOBAL_DIRS=(
        "$HOME/.npm-global"
        "$HOME/.nvm/versions/node/$(node -v 2>/dev/null)/lib"
        "/usr/local"
    )

    for dir in "${NPM_GLOBAL_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            VERSION=$(get_version_from_npm "$dir")
            if [ -n "$VERSION" ]; then
                installations["$dir"]="$VERSION"
                log_info "Found installation at $dir: v$VERSION"
            fi
        fi
    done

    # Check if there's a mismatch
    if [ ${#installations[@]} -eq 0 ]; then
        log_warning "No npm installations found, but executable exists at $CLAUDE_PATH"
        return 1
    fi

    if [ ${#installations[@]} -eq 1 ]; then
        log_success "Only one installation found - no conflicts detected"
        return 0
    fi

    log_warning "Multiple installations detected!"
    return 2
}

# Remove old installations
fix_version_mismatch() {
    local keep_path=""
    local latest_version="0.0.0"

    log_info "Analyzing installations to determine which to keep..."
    echo ""

    # Find the latest version
    for path in "${!installations[@]}"; do
        version="${installations[$path]}"
        if [ "$(printf '%s\n' "$latest_version" "$version" | sort -V | tail -n1)" = "$version" ]; then
            latest_version="$version"
            keep_path="$path"
        fi
    done

    log_info "Latest version found: v$latest_version at $keep_path"
    log_info "This installation will be kept."
    echo ""

    # List installations to remove
    declare -a remove_paths=()
    for path in "${!installations[@]}"; do
        if [ "$path" != "$keep_path" ]; then
            remove_paths+=("$path")
            log_warning "Will remove: $path (v${installations[$path]})"
        fi
    done

    if [ ${#remove_paths[@]} -eq 0 ]; then
        log_success "No old installations to remove"
        return 0
    fi

    echo ""
    read -p "Do you want to proceed with removing old installations? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operation cancelled by user"
        return 1
    fi

    # Remove old installations
    for path in "${remove_paths[@]}"; do
        log_info "Removing installation at $path..."
        if npm uninstall -g @anthropic-ai/claude-code --prefix "$path" 2>/dev/null; then
            log_success "Removed installation from $path"
        else
            log_error "Failed to remove installation from $path"
        fi
    done

    return 0
}

# Verify the fix
verify_fix() {
    log_info "Verifying fix..."
    echo ""

    NEW_CLAUDE_PATH=$(which claude 2>/dev/null || echo "")
    if [ -z "$NEW_CLAUDE_PATH" ]; then
        log_error "Claude Code is no longer in PATH after cleanup!"
        return 1
    fi

    NEW_VERSION=$(get_running_version "$NEW_CLAUDE_PATH")

    log_success "Claude Code is now at: $NEW_CLAUDE_PATH"
    if [ -n "$NEW_VERSION" ]; then
        log_success "Version: $NEW_VERSION"
    fi

    return 0
}

# Main execution
main() {
    echo "========================================="
    echo "  Claude Code Version Mismatch Fixer"
    echo "========================================="
    echo ""

    detect_version_mismatch
    result=$?

    if [ $result -eq 1 ]; then
        log_error "Could not properly detect installations"
        exit 1
    elif [ $result -eq 0 ]; then
        log_success "No version mismatch detected!"
        exit 0
    fi

    echo ""
    echo "========================================="
    echo "  Fixing Version Mismatch"
    echo "========================================="
    echo ""

    fix_version_mismatch

    echo ""
    echo "========================================="
    echo "  Verification"
    echo "========================================="
    echo ""

    verify_fix

    echo ""
    log_success "All done! Please restart your terminal or run 'hash -r' to refresh the PATH cache"
}

# Run main function
main
