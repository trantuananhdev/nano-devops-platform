# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# ONE COMMAND (repo root):  vagrant up
# COPY_PROJECT_DEVOPS=1 is default (copy .env + project_devops into VM).
# Windows: Vagrant auto-runs host setup after up (one UAC for hosts + HTTPS).
# VM: Odoo crm_real_estate + CRM DB via post_up_automation.sh (background).

require "fileutils"

repo_root = File.expand_path(File.dirname(__FILE__))
env_path = File.join(repo_root, ".env")

unless File.file?(env_path)
  example = File.join(repo_root, ".env.example")
  if File.file?(example)
    FileUtils.cp(example, env_path)
    puts "[Vagrant] Created .env from .env.example — add GEMINI keys + GITHUB_TOKEN before demo"
  else
    abort "[Vagrant] FATAL: missing .env at repo root (required for Gemini, GitHub, Telegram)"
  end
end

PLATFORM_DOMAINS = %w[
  odoo.nano.platform ai.nano.platform grafana.nano.platform
  prometheus.nano.platform aggregator.nano.platform faulty.nano.platform
  data.nano.platform health.nano.platform user.nano.platform
  crm-ingest.nano.platform crm-demo.nano.platform goclaw.nano.platform
  shopee-search.nano.platform shopee-api.nano.platform
].freeze

STATIC_IP_DEFAULT = "192.168.157.10"

Vagrant.configure("2") do |config|

  config.vm.box = "generic/alpine318"
  config.vm.hostname = "nano-devops"
  config.vm.synced_folder ".", "/vagrant", disabled: true

  static_ip = (ENV["VM_IP"] || "").to_s.strip
  static_ip = STATIC_IP_DEFAULT if static_ip.empty?

  config.vm.network "private_network",
    ip: static_ip,
    netmask: "255.255.255.0",
    auto_config: false

  domains_shell = PLATFORM_DOMAINS.join(" ")

  config.vm.provision "shell", run: "always", inline: <<-SHELL
    set -e
    echo "[NET] Intelligent network setup..."
    IF_NAT="eth0"
    IF_PRIV=$(ip -o link show | awk -F': ' '{print $2}' | grep -E 'eth|enp|ens' | grep -v 'eth0' | head -n1)
    if [ -z "$IF_PRIV" ]; then echo "[NET] ERROR: no private NIC"; exit 1; fi
    NEW_IP="#{static_ip}"
    if [ -z "$NEW_IP" ] || [ "$NEW_IP" = "#{STATIC_IP_DEFAULT}" ]; then
      NAT_IP=$(ip -f inet addr show $IF_NAT | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
      SUBNET=$(echo $NAT_IP | cut -d. -f1-3)
      NEW_IP="${SUBNET}.10"
    fi
    mkdir -p /opt/platform
    echo "$NEW_IP" > /opt/platform/vm-service-ip
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
    ifconfig $IF_PRIV ${NEW_IP} netmask 255.255.255.0 up || true
    for d in #{domains_shell}; do sed -i "/$d/d" /etc/hosts; done
    for d in #{domains_shell}; do echo "${NEW_IP} $d" >> /etc/hosts; done
    echo "[NET] Service IP ${NEW_IP}"
  SHELL

  config.ssh.insert_key = true
  config.ssh.keep_alive = true
  config.vm.boot_timeout = 600

  config.vm.provider "vmware_desktop" do |v|
    v.vmx["memsize"] = ENV["VM_MEM"] || "4096"
    v.vmx["numvcpus"] = ENV["VM_CPU"] || "2"
  end

  config.vm.provider "virtualbox" do |vb|
    vb.memory = ENV["VM_MEM"] || 4096
    vb.cpus   = ENV["VM_CPU"] || 2
  end

  # COPY_PROJECT_DEVOPS=1 (default) → copy project_devops + .env into VM
  # COPY_PROJECT_DEVOPS=0 → DEV sync /workspace
  use_copy_mode = ENV.fetch("COPY_PROJECT_DEVOPS", "1").to_s.strip != "0"

  if use_copy_mode
    config.vm.provision "file", run: "always" do |file|
      file.source = "project_devops"
      file.destination = "/tmp/project_devops_copy"
    end

    if File.directory?(File.join(repo_root, ".ssh"))
      config.vm.provision "file", run: "always" do |file|
        file.source = ".ssh"
        file.destination = "/tmp/.ssh_copy"
      end
    end

    config.vm.provision "file", run: "always" do |file|
      file.source = ".env"
      file.destination = "/tmp/.env_copy"
    end

    config.vm.provision "shell", run: "always", inline: <<-SHELL
      set -eux
      DEST="/opt/platform/src/nano-project-devops"
      mkdir -p $DEST
      rm -rf $DEST/project_devops $DEST/.env
      mv /tmp/project_devops_copy $DEST/project_devops
      mv /tmp/.env_copy $DEST/.env
      if [ -d /tmp/.ssh_copy ]; then rm -rf $DEST/.ssh; mv /tmp/.ssh_copy $DEST/.ssh; fi
      apk add --no-cache dos2unix > /dev/null 2>&1 || true
      find $DEST/project_devops -type f -name "*.sh" -print0 | xargs -0 dos2unix
      if id deploy > /dev/null 2>&1; then chown -R deploy:platform_group $DEST; chmod -R 775 $DEST; fi
      echo "[BOOTSTRAP] PROD-LIKE copy OK"
    SHELL
  else
    config.vm.provision "shell", inline: "echo '[BOOTSTRAP] DEV /workspace'", run: "always"
    config.vm.synced_folder ".", "/workspace", disabled: false, owner: "deploy", group: "deploy_group"
  end

  config.vm.provision "file", run: "always" do |file|
    file.source = "project_devops/platform/infra"
    file.destination = "/tmp/infra"
  end

  config.vm.provision "shell", run: "always" do |s|
    s.env = { "REPO_URL" => ENV["REPO_URL"] || "", "ENVIRONMENT" => ENV["ENV"] || "dev" }
    s.inline = <<-SHELL
      set -eux
      apk add --no-cache dos2unix bash curl
      find /tmp/infra -type f -print0 | xargs -0 dos2unix
      chmod -R +x /tmp/infra/scripts/
      NONINTERACTIVE=1 /tmp/infra/scripts/main_setup.sh
    SHELL
  end

  config.vm.provision "shell", run: "always", inline: <<-SHELL
    set -e
    rm -f /opt/platform/.platform-ready
    if [ -x /tmp/infra/scripts/vagrant/post_up_automation.sh ]; then
      chmod +x /tmp/infra/scripts/vagrant/post_up_automation.sh
      nohup /tmp/infra/scripts/vagrant/post_up_automation.sh >> /var/log/nano-post-up.log 2>&1 &
      echo "[POST-UP] Background: Odoo module + CRM DB (log: /var/log/nano-post-up.log)"
    fi
  SHELL

  config.vm.provision "shell", run: "always", inline: <<-SHELL
    rc-service nano-platform status || true
  SHELL

  # Windows host setup — Vagrant 2.4 trigger.ruby (no powershell:/run_on_host: keys)
  if RUBY_PLATFORM =~ /mswin|mingw|cygwin/
    win_script = File.join(
      repo_root,
      "project_devops/platform/infra/scripts/vagrant/windows_host_setup.ps1"
    )

    config.trigger.after :up do |trigger|
      trigger.name = "windows-host-auto"
      trigger.info = "Windows: UAC once → hosts + HTTPS CA + browser"
      trigger.only_on = [:up]
      trigger.ruby do |env, machine|
        next unless File.file?(win_script)
        puts "[Vagrant] Starting Windows host setup..."
        system(
          "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
          "-File", win_script,
          "-RepoRoot", repo_root
        )
      end
    end
  end

  config.vm.post_up_message = <<-MSG

==================================================
Nano DevOps Platform

ONE COMMAND (repo root):
  vagrant up

Windows: approve UAC once (hosts + HTTPS — automatic).

URLs (after ~5–15 min first boot):
  CRM:    https://crm-demo.nano.platform
  Odoo:   https://odoo.nano.platform  (admin / admin)
  Grafana: https://grafana.nano.platform

Log: vagrant ssh -c "tail -f /var/log/nano-post-up.log"
DEV sync: set COPY_PROJECT_DEVOPS=0
==================================================

MSG

end
