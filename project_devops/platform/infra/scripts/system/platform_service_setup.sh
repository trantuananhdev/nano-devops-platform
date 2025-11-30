#!/bin/sh
# Alpine Linux OpenRC Service for Nano DevOps Platform
# This script creates a system service to start/stop the platform on boot.

set -e

echo "=========================================="
echo "Nano DevOps Platform - Service Setup"
echo "=========================================="

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

SERVICE_NAME="nano-platform"
SERVICE_PATH="/etc/init.d/$SERVICE_NAME"
DEPLOY_USER="deploy"

# Create the OpenRC service file
cat <<EOF > "$SERVICE_PATH"
#!/sbin/openrc-run

# Nano DevOps Platform Service
# This service starts the Docker Compose platform on boot.

description="Nano DevOps Platform (Docker Compose)"
depend() {
    need docker
    # Wait for shared folders if they are used (e.g. /workspace)
    # This is a bit tricky in Alpine/Vagrant, so we'll handle it in start()
}

# Candidate paths for the platform composition
CANDIDATE_PATHS="
/workspace/project_devops/platform/composition
/opt/platform/src/nano-project-devops/project_devops/platform/composition
"

find_composition_path() {
    for path in \$CANDIDATE_PATHS; do
        if [ -f "\$path/docker-compose.yml" ]; then
            echo "\$path"
            return 0
        fi
    done
    return 1
}

start() {
    ebegin "Starting Nano DevOps Platform"
    
    # Wait for shared folders/source to be ready (up to 30 seconds)
    MAX_WAIT=30
    WAIT_COUNT=0
    PLATFORM_PATH=""
    
    until PLATFORM_PATH=\$(find_composition_path) || [ \$WAIT_COUNT -ge \$MAX_WAIT ]; do
        echo "Waiting for platform source... (\$WAIT_COUNT/\$MAX_WAIT)"
        sleep 1
        WAIT_COUNT=\$((WAIT_COUNT + 1))
    done
    
    if [ -z "\$PLATFORM_PATH" ]; then
        eerror "Could not find platform composition path. Check if repo is mounted or cloned."
        eend 1
        return 1
    fi
    
    einfo "Starting platform at: \$PLATFORM_PATH"
    
    # Start the platform as the deploy user with all modules
    COMPOSE_CMD="docker compose -f docker-compose.yml -f docker-compose.observability.yml -f docker-compose.apps.yml"
    if [ -f "\$PLATFORM_PATH/docker-compose.override.yml" ]; then
        COMPOSE_CMD="\$COMPOSE_CMD -f docker-compose.override.yml"
    fi

    su - "$DEPLOY_USER" -c "cd '\$PLATFORM_PATH' && \$COMPOSE_CMD up -d"
    
    eend \$?
}

stop() {
    ebegin "Stopping Nano DevOps Platform"
    
    PLATFORM_PATH=\$(find_composition_path)
    if [ -n "\$PLATFORM_PATH" ]; then
        COMPOSE_CMD="docker compose -f docker-compose.yml -f docker-compose.observability.yml -f docker-compose.apps.yml"
        if [ -f "\$PLATFORM_PATH/docker-compose.override.yml" ]; then
            COMPOSE_CMD="\$COMPOSE_CMD -f docker-compose.override.yml"
        fi
        su - "$DEPLOY_USER" -c "cd '\$PLATFORM_PATH' && \$COMPOSE_CMD down"
    else
        # If we can't find the path (e.g. unmounted), we can't do a clean down
        # But we could stop all containers if needed. For now, just warn.
        ewarn "Could not find platform path to stop cleanly."
    fi
    
    eend \$?
}

status() {
    PLATFORM_PATH=\$(find_composition_path)
    if [ -n "\$PLATFORM_PATH" ]; then
        COMPOSE_CMD="docker compose -f docker-compose.yml -f docker-compose.observability.yml -f docker-compose.apps.yml"
        if [ -f "\$PLATFORM_PATH/docker-compose.override.yml" ]; then
            COMPOSE_CMD="\$COMPOSE_CMD -f docker-compose.override.yml"
        fi
        su - "$DEPLOY_USER" -c "cd '\$PLATFORM_PATH' && \$COMPOSE_CMD ps"
    else
        eerror "Platform source not found."
        return 1
    fi
}
EOF

# Set permissions for the service file
chmod +x "$SERVICE_PATH"

# Add the service to the default runlevel
rc-update add "$SERVICE_NAME" default

echo "Service '$SERVICE_NAME' has been created and enabled."
echo "You can manage it with: rc-service $SERVICE_NAME [start|stop|restart|status]"
echo "=========================================="
