# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # ----------------------------
  # Base Box
  # ----------------------------
  config.vm.box = "generic/alpine318"
  config.vm.hostname = "nano-devops"

  # ----------------------------
  # Network
  # ----------------------------
  config.vm.network "private_network", ip: "192.168.56.10"

  # ----------------------------
  # SSH
  # ----------------------------
  config.ssh.insert_key = true

  # ----------------------------
  # Provider Configuration
  # ----------------------------
  config.vm.provider "vmware_desktop" do |v|
    v.vmx["memsize"] = "4096"
    v.vmx["numvcpus"] = "2"
  end

  # ===================================================================
  # BOOTSTRAP STRATEGY
  #
  # 1. DEFAULT (DEV): Mounts host repo to /workspace for live development.
  # 2. OPTIONAL (PROD-LIKE): If COPY_PROJECT_DEVOPS=1, performs a
  #    one-shot copy to /opt/platform/src, simulating a deployment.
  # ===================================================================

  # --- STRATEGY 2: OPTIONAL PROD-LIKE COPY ---
  if ENV["COPY_PROJECT_DEVOPS"] == "1"
    config.vm.provision "file", run: "always" do |file|
      file.source = "project_devops"
      file.destination = "/tmp/project_devops_copy"
    end

    config.vm.provision "shell", inline: <<-SHELL
      set -eux
      echo "Executing PROD-LIKE bootstrap: Copying source to /opt/platform/src..."
      mkdir -p /opt/platform/src/nano-project-devops
      rm -rf /opt/platform/src/nano-project-devops/project_devops
      mv /tmp/project_devops_copy /opt/platform/src/nano-project-devops/project_devops
      if id deploy >/dev/null 2>&1; then
        chown -R deploy:$(id -gn deploy) /opt/platform/src/nano-project-devops
      fi
    SHELL
  # --- STRATEGY 1: DEFAULT DEV MOUNT ---
  else
    config.vm.provision "shell", inline: "echo 'Executing DEV bootstrap: Mounting repo to /workspace...'", run: "always"
    # Provider-aware synced folders for the workspace
    config.vm.provider "vmware_desktop" do |v, override|
      override.vm.synced_folder ".", "/workspace", disabled: false
    end
    config.vm.provider "virtualbox" do |vb, override|
      override.vm.synced_folder ".", "/workspace", type: "virtualbox", disabled: false
    end
  end

  # Always disable the default /vagrant mount to avoid confusion
  config.vm.synced_folder ".", "/vagrant", disabled: true

  # ----------------------------
  # Provisioning Scripts
  # ----------------------------

  # Fix: Ensure the infra directory structure is correctly placed at /tmp/infra
  config.vm.provision "file", run: "always" do |file|
    file.source = "project_devops/platform/infra"
    file.destination = "/tmp/infra"
  end

  # Run the main setup orchestrator
  config.vm.provision "shell", run: "always" do |s|
    # Pass REPO_URL for the rare case of cloning on a bare server (not default)
    s.env = { "REPO_URL" => ENV["REPO_URL"] || "" }
    s.inline = <<-SHELL
      set -eux
      echo "Running main setup orchestrator..."
      apk add --no-cache dos2unix
      
      # Ensure all infra files have Unix line endings and scripts are executable
      find /tmp/infra -type f -print0 | xargs -0 dos2unix
      chmod -R +x /tmp/infra/scripts/
      
      NONINTERACTIVE=1 /tmp/infra/scripts/main_setup.sh
    SHELL
  end

  # ----------------------------
  # Post-Boot Message
  # ----------------------------
  config.vm.post_up_message = <<-MSG
--------------------------------------------------
Nano DevOps Platform VM is ready.

- Workspace: /workspace (if not in COPY mode)
- Runtime: /opt/platform
- Composition: /opt/platform/src/nano-project-devops/project_devops/platform/composition

Access services (ensure hosts are mapped if not using localhost):
- Odoo:       https://odoo.localhost
- Grafana:    https://grafana.localhost
- Prometheus: https://prometheus.localhost
- Traefik:    http://localhost:8080

Management:
- SSH: vagrant ssh
- Service: sudo rc-service nano-platform [status|start|stop|restart]
--------------------------------------------------
MSG

end
