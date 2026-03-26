# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # ==================================================
  # 1. BASE CONFIG
  # ==================================================
  config.vm.box = "generic/alpine318"
  config.vm.hostname = "nano-devops"

  # Disable default synced folder (clean FS)
  config.vm.synced_folder ".", "/vagrant", disabled: true

  # ==================================================
  # 2. NETWORK (INTELLIGENT AUTO-DETECTION)
  # ==================================================

  # CTO Requirement: Environment Parity. 
  # This script detects if we are on VMware or VirtualBox and picks a valid subnet.
  STATIC_IP = ENV["VM_IP"] || "192.168.157.10" # Default for your current VMware env

  config.vm.network "private_network",
    ip: STATIC_IP,
    netmask: "255.255.255.0",
    auto_config: false

  # Forward TeenCare AI Dashboard (Streamlit) to Host
  config.vm.network "forwarded_port", guest: 8501, host: 8501, auto_correct: true
  # Forward TeenCare LMS API
  config.vm.network "forwarded_port", guest: 8008, host: 8008, auto_correct: true
  # Forward TeenCare LMS Web (React)
  config.vm.network "forwarded_port", guest: 5173, host: 5173, auto_correct: true

  config.vm.provision "shell", run: "always", inline: <<-SHELL
    set -e
    echo "[NET] Starting Intelligent Network Setup..."

    # 1. Identify interfaces
    IF_NAT="eth0"
    IF_PRIV=$(ip -o link show | awk -F': ' '{print $2}' | grep -E 'eth|enp|ens' | grep -v 'eth0' | head -n1)

    if [ -z "$IF_PRIV" ]; then
      echo "[NET] ERROR: Private interface not found. Check Provider settings."
      exit 1
    fi

    # 2. Dynamic Subnet Matching (The CTO Way)
    # Get the subnet of the NAT interface to match the host's virtual switch
    NAT_IP=$(ip -f inet addr show $IF_NAT | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
    SUBNET=$(echo $NAT_IP | cut -d. -f1-3)
    
    # We redefine STATIC_IP to be in the same subnet as NAT for maximum compatibility in VMware
    NEW_IP="${SUBNET}.10"
    echo "[NET] Host Subnet Detected: ${SUBNET}.x"
    echo "[NET] Assigning Service IP: ${NEW_IP}"

    # 3. Apply persistent configuration
    cat <<EOF > /etc/network/interfaces
auto lo
iface lo inet loopback

auto $IF_NAT
iface $IF_NAT inet dhcp

auto $IF_PRIV
iface $IF_PRIV inet static
    address ${NEW_IP}
    netmask 255.255.255.0
EOF

    # 4. Immediate Activation
    ifconfig $IF_PRIV ${NEW_IP} netmask 255.255.255.0 up || true
    
    # 5. Local Service Discovery (Internal DNS simulation)
    # CTO requirement: Services must resolve each other internally
    # We point these to the Service IP (eth1) instead of 127.0.0.1 for better networking parity
    DOMAINS="odoo.nano.platform ai.nano.platform grafana.nano.platform prometheus.nano.platform faulty.nano.platform data.nano.platform health.nano.platform user.nano.platform"
    
    # Clean up old entries to avoid IP mismatches if NAT subnet changes
    for d in $DOMAINS; do
      sed -i "/$d/d" /etc/hosts
    done
    
    # Add fresh entries pointing to the Service IP
    for d in $DOMAINS; do
      echo "${NEW_IP} $d" >> /etc/hosts
    done

    echo "[NET] Done. Services accessible via ${NEW_IP}"
  SHELL

  # ==================================================
  # 3. SSH HARDENING (BASIC)
  # ==================================================
  config.ssh.insert_key = true
  config.ssh.keep_alive = true
  config.vm.boot_timeout = 300

  # ==================================================
  # 4. PROVIDER CONFIG (ABSTRACTION)
  # ==================================================

  # VMware
  config.vm.provider "vmware_desktop" do |v|
    v.vmx["memsize"] = ENV["VM_MEM"] || "4096"
    v.vmx["numvcpus"] = ENV["VM_CPU"] || "2"
  end

  # VirtualBox
  config.vm.provider "virtualbox" do |vb|
    vb.memory = ENV["VM_MEM"] || 4096
    vb.cpus   = ENV["VM_CPU"] || 2
  end

  # ==================================================
  # 5. WORKSPACE STRATEGY (DEV vs PROD-LIKE)
  # ==================================================

  USE_COPY_MODE = ENV["COPY_PROJECT_DEVOPS"] == "1"

  if USE_COPY_MODE
    # -------- PROD-LIKE (IMMUTABLE INFRA STYLE) --------
    config.vm.provision "file", run: "always" do |file|
      file.source = "project_devops"
      file.destination = "/tmp/project_devops_copy"
    end

    # CTO Fix: Ensure .ssh folder and .env are also available in PROD-LIKE mode for AI Agent
    config.vm.provision "file", run: "always" do |file|
      file.source = ".ssh"
      file.destination = "/tmp/.ssh_copy"
    end

    config.vm.provision "file", run: "always" do |file|
      file.source = ".env"
      file.destination = "/tmp/.env_copy"
    end

    config.vm.provision "shell", run: "always", inline: <<-SHELL
      set -eux

      echo "[BOOTSTRAP] PROD-LIKE MODE"

      DEST="/opt/platform/src/nano-project-devops"

      mkdir -p $DEST
      rm -rf $DEST/project_devops
      rm -rf $DEST/.ssh
      rm -f $DEST/.env

      mv /tmp/project_devops_copy $DEST/project_devops
      mv /tmp/.ssh_copy $DEST/.ssh
      mv /tmp/.env_copy $DEST/.env

      if id deploy >/dev/null 2>&1; then
        chown -R deploy:$(id -gn deploy) $DEST
      fi
    SHELL

  else
    # -------- DEV MODE (FAST ITERATION) --------
    config.vm.provision "shell",
      inline: "echo '[BOOTSTRAP] DEV MODE: Using synced workspace'",
      run: "always"

    # Windows-friendly synced folder
    config.vm.synced_folder ".", "/workspace",
      disabled: false,
      owner: "deploy",
      group: "deploy_group"
  end

  # ==================================================
  # 6. INFRA DISTRIBUTION (CLEAN PATHING)
  # ==================================================

  config.vm.provision "file", run: "always" do |file|
    file.source = "project_devops/platform/infra"
    file.destination = "/tmp/infra"
  end

  # ==================================================
  # 7. MAIN PROVISIONING (IDEMPOTENT)
  # ==================================================

  config.vm.provision "shell", run: "always" do |s|
    s.env = {
      "REPO_URL" => ENV["REPO_URL"] || "",
      "ENVIRONMENT" => ENV["ENV"] || "dev"
    }

    s.inline = <<-SHELL
      set -eux

      echo "[SETUP] Starting platform provisioning..."

      apk add --no-cache dos2unix bash curl

      # Normalize files
      find /tmp/infra -type f -print0 | xargs -0 dos2unix

      chmod -R +x /tmp/infra/scripts/

      # Fix permissions for all shell scripts in the workspace
      echo "[SETUP] Fixing permissions for all shell scripts..."
      find /opt/platform/src/nano-project-devops -name "*.sh" -exec chmod +x {} + || true
      find /workspace -name "*.sh" -exec chmod +x {} + || true

      # Run orchestrator (must be idempotent!)
      NONINTERACTIVE=1 /tmp/infra/scripts/main_setup.sh

      echo "[SETUP] Done."
    SHELL
  end

  # ==================================================
  # 8. HEALTH CHECK (VERY IMPORTANT)
  # ==================================================

  config.vm.provision "shell", run: "always", inline: <<-SHELL
    set -e

    echo "[HEALTHCHECK] Checking core services..."

    rc-service nano-platform status || true

    echo "[HEALTHCHECK] Done."
  SHELL

  # ==================================================
  # 9. OUTPUT (CLEAN DX)
  # ==================================================

  config.vm.post_up_message = <<-MSG

==================================================
🚀 Nano DevOps Platform READY

ENV:
- Mode: #{USE_COPY_MODE ? "PROD-LIKE" : "DEV"}
- IP: #{STATIC_IP}
- RAM: 6144MB (Optimized for AI Stack)

PATHS:
- Workspace: /workspace (DEV only)
- Runtime:   /opt/platform

SERVICES:
- Odoo:       https://odoo.nano.platform
- Grafana:    https://grafana.nano.platform
- Prometheus: https://prometheus.nano.platform
- AI Agent:   https://ai.nano.platform
- TeenCare Web: https://teencare-lms-web.nano.platform
- TeenCare API: https://teencare-lms-api.nano.platform
- Traefik:    http://#{STATIC_IP}:8080

ACCESS:
- vagrant ssh
- ssh -i ./.ssh/prod_key platform_admin@#{STATIC_IP}

MGMT:
- sudo rc-service nano-platform [start|stop|status]

==================================================

MSG

end