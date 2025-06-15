#!/bin/sh
# User SSH & Sudo Setup Script
# This script is responsible for setting up passwordless SSH access and sudo policies.

set -eu

# Source common utilities for logging
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../common/utils.sh" ]; then
    . "$SCRIPT_DIR/../common/utils.sh"
else
    log_info() { echo "INFO: $1"; }
    log_error() { echo "ERROR: $1"; exit 1; }
fi

log_info "=========================================="
log_info "User SSH & Sudo Setup"
log_info "=========================================="

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

# Directory where Vagrant copies the infra files
INFRA_SRC_DIR="/tmp/infra" # Base directory for all infra files

# 1. Install sudo if not present
if ! command -v sudo > /dev/null; then
    echo "Installing sudo..."
    apk add --no-cache sudo
fi

# 2. Deploy sudoers policy
SUDOERS_POLICY_SRC="$INFRA_SRC_DIR/sudoers.d/nano_devops_policy"
SUDOERS_POLICY_DEST="/etc/sudoers.d/nano_devops_policy"
if [ -f "$SUDOERS_POLICY_SRC" ]; then
    echo "Deploying sudoers policy to $SUDOERS_POLICY_DEST..."
    cp "$SUDOERS_POLICY_SRC" "$SUDOERS_POLICY_DEST"
    # Set strict permissions for the sudoers file
    chmod 440 "$SUDOERS_POLICY_DEST"
    echo "Sudoers policy deployed."
else
    echo "Warning: Sudoers policy file not found at $SUDOERS_POLICY_SRC."
fi

# 3. Deploy SSH authorized keys for defined users
AUTHORIZED_KEYS_SRC_DIR="$INFRA_SRC_DIR/authorized_keys"

if [ ! -d "$AUTHORIZED_KEYS_SRC_DIR" ]; then
    echo "Warning: authorized_keys source directory not found. Skipping SSH key setup."
    exit 0
fi

for user_dir in "$AUTHORIZED_KEYS_SRC_DIR"/*; do
    if [ -d "$user_dir" ]; then
        username=$(basename "$user_dir")
        
        # Check if the user exists
        if ! id "$username" > /dev/null 2>&1; then
            echo "User '$username' does not exist. Skipping SSH key setup for this user."
            continue
        fi

        log_info "Setting up SSH access for user '$username'..."
        
        # Get home directory
        home_dir=$(grep "^${username}:" /etc/passwd | cut -d: -f6)
        
        # Fallback if home directory is empty, root, or missing
        if [ -z "$home_dir" ] || [ "$home_dir" = "/" ]; then
            log_info "Warning: Home directory for $username is '$home_dir'. Forcing to /home/$username"
            home_dir="/home/$username"
        fi

        # --- FIX SECTION: Unlocking account ---
        log_info "Unlocking account for '$username'..."
        # Standard Alpine/BusyBox unlock
        passwd -u "$username" > /dev/null 2>&1 || true
        passwd -d "$username" > /dev/null 2>&1 || true
        
        # Force removal of '!' from shadow using a more robust regex.
        # This matches the username and removes a '!' if it's the first character of the password field.
        if grep -q "^${username}:!" /etc/shadow; then
            log_info "Force removing '!' lock from /etc/shadow for $username"
            sed -i "s/^\(${username}:\)!/\1/" /etc/shadow
        fi
        # --------------------------------------

        # Ensure home directory ownership and strict permissions
        if [ ! -d "$home_dir" ]; then
            log_info "Creating home directory for $username at $home_dir"
            mkdir -p "$home_dir"
        fi
        
        primary_group="$(id -gn "$username")"
        chown "$username:$primary_group" "$home_dir"
        chmod 700 "$home_dir"
        
        # Ensure parent directory of home is secure (not group-writable for SSH)
        parent_dir=$(dirname "$home_dir")
        if [ "$parent_dir" != "/" ] && [ "$parent_dir" != "." ]; then
            chmod g-w,o-w "$parent_dir"
        fi
        
        ssh_dir="$home_dir/.ssh"
        auth_keys_file="$ssh_dir/authorized_keys"

        # Create .ssh directory with correct permissions
        mkdir -p "$ssh_dir"
        chmod 700 "$ssh_dir"
        
        # Idempotent key addition
        tmp_keys=$(mktemp)
        key_count=0
        for key_file in "$user_dir"/*.pub; do
            if [ -f "$key_file" ] && [ -s "$key_file" ]; then
                log_info "Adding key from $key_file to user $username"
                cat "$key_file" >> "$tmp_keys"
                echo "" >> "$tmp_keys"
                key_count=$((key_count + 1))
            fi
        done

        if [ $key_count -gt 0 ]; then
            # Merge with existing keys and remove duplicates
            if [ -f "$auth_keys_file" ]; then
                cat "$auth_keys_file" >> "$tmp_keys"
            fi
            sort -u "$tmp_keys" > "$auth_keys_file"
            rm "$tmp_keys"
            log_info "Processed $key_count public key(s) for user '$username' (idempotent)."
        else
            rm "$tmp_keys"
            if [ "$username" != "vagrant" ]; then
                log_info "No keys found in source for '$username'. Clearing authorized_keys."
                > "$auth_keys_file"
            else
                log_info "Preserving existing vagrant keys."
            fi
        fi

        # Set correct ownership and permissions
        chown -R "$username:$primary_group" "$ssh_dir"
        chmod 600 "$auth_keys_file"
        
        # Final verification
        if [ -s "$auth_keys_file" ]; then
            log_info "Verification: $auth_keys_file updated for $username."
        fi
    fi
done

# Hardening SSHD configuration
SSHD_CONFIG="/etc/ssh/sshd_config"
if [ -f "$SSHD_CONFIG" ]; then
    log_info "Hardening SSHD configuration..."
    sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' "$SSHD_CONFIG"
    sed -i 's/^#\?AuthorizedKeysFile.*/AuthorizedKeysFile .ssh\/authorized_keys/' "$SSHD_CONFIG"
    sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' "$SSHD_CONFIG"
    sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' "$SSHD_CONFIG"
    
    # Validate and Restart
    if sshd -t; then
        log_info "SSHD configuration valid. Restarting service..."
        if command -v rc-service > /dev/null; then
            rc-service sshd restart
        else
            # Fallback for systems without OpenRC (like basic Docker)
            /usr/sbin/sshd -t && pkill -HUP sshd || true
        fi
    else
        log_error "SSHD configuration invalid! Please check $SSHD_CONFIG"
    fi
else
    log_error "SSHD configuration file not found at $SSHD_CONFIG"
fi

echo ""
echo "=========================================="
echo "User SSH and Sudo setup completed successfully!"
echo "=========================================="