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
    
    # Senior DevOps: Generate TLS certificates if they don't exist
    CERT_GEN_SCRIPT="/opt/platform/src/nano-project-devops/project_devops/platform/infra/scripts/system/generate_certs.sh"
    if [ -f "\$CERT_GEN_SCRIPT" ]; then
        einfo "Generating TLS certificates..."
        sh "\$CERT_GEN_SCRIPT"
    fi

    # Senior DevOps: Ensure .env is linked to the composition directory
    # This fixes the "variable is not set" WARN when running docker compose manually
    DOTENV_ROOT="/opt/platform/src/nano-project-devops/.env"
    ENV_FILE_ARG=""
    if [ -f "\$DOTENV_ROOT" ]; then
        einfo "Linking .env from root to composition directory"
        ln -sf "\$DOTENV_ROOT" "\$PLATFORM_PATH/.env"
        # Explicitly use it as an argument too for maximum robustness
        ENV_FILE_ARG="--env-file \$DOTENV_ROOT"
    fi

    # Start the platform as the deploy user with all modules
    # Added --build to ensure code changes are picked up during provision/restart
    COMPOSE_CMD="docker compose \$ENV_FILE_ARG -f docker-compose.yml -f docker-compose.observability.yml -f docker-compose.apps.yml"
    if [ -f "\$PLATFORM_PATH/docker-compose.override.yml" ]; then
        COMPOSE_CMD="\$COMPOSE_CMD -f docker-compose.override.yml"
    fi

    su - "$DEPLOY_USER" -c "cd '\$PLATFORM_PATH' && \$COMPOSE_CMD up -d --build"
    
    # Senior DevOps: Seed data for TeenCare LMS if it's new
    # This ensures "vagrant provision" gives a ready-to-use app
    einfo "Seeding TeenCare LMS data..."
    su - "$DEPLOY_USER" -c "cd '\$PLATFORM_PATH' && docker compose exec -T teencare-lms-api python scripts/seed.py" || true

    eend \$?
}

stop() {
    ebegin "Stopping Nano DevOps Platform"
    
    PLATFORM_PATH=\$(find_composition_path)
    if [ -n "\$PLATFORM_PATH" ]; then
        DOTENV_ROOT="/opt/platform/src/nano-project-devops/.env"
        ENV_FILE_ARG=""
        if [ -f "\$DOTENV_ROOT" ]; then
            ENV_FILE_ARG="--env-file \$DOTENV_ROOT"
        fi

        COMPOSE_CMD="docker compose \$ENV_FILE_ARG -f docker-compose.yml -f docker-compose.observability.yml -f docker-compose.apps.yml"
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
        DOTENV_ROOT="/opt/platform/src/nano-project-devops/.env"
        ENV_FILE_ARG=""
        if [ -f "\$DOTENV_ROOT" ]; then
            ENV_FILE_ARG="--env-file \$DOTENV_ROOT"
        fi

        COMPOSE_CMD="docker compose \$ENV_FILE_ARG -f docker-compose.yml -f docker-compose.observability.yml -f docker-compose.apps.yml"
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

# Start or restart the service to apply changes
if rc-service "$SERVICE_NAME" status >/dev/null 2>&1; then
    echo "Restarting service '$SERVICE_NAME'..."
    rc-service "$SERVICE_NAME" restart
else
    echo "Starting service '$SERVICE_NAME'..."
    rc-service "$SERVICE_NAME" start
fi

echo "Service '$SERVICE_NAME' has been created, enabled, and started."
echo "You can manage it with: rc-service $SERVICE_NAME [start|stop|restart|status]"
echo "=========================================="
