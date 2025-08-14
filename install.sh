#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration Variables ---
# Hardcoding these for simplicity and robustness with Peer Authentication
DB_NAME="aitoolkit_db"
DB_USER="www-data" # Use the Apache user for Peer Authentication

# --- Helper Functions ---
print_header() {
    echo "================================================================="
    echo "$1"
    echo "================================================================="
}

# --- Installation Functions ---

get_user_input() {
    print_header "Gathering Configuration Details"

    read -p "Enter the desired installation directory [/var/www/aitoolkit]: " APP_DIR
    APP_DIR=${APP_DIR:-/var/www/aitoolkit}

    read -p "Enter your server's domain name or IP address: " SERVER_NAME
    while [ -z "$SERVER_NAME" ]; do
        echo "Server name/IP cannot be empty." >&2
        read -p "Enter your server's domain name or IP address: " SERVER_NAME
    done

    echo "---"
    echo "Configuration:"
    echo "Installation Directory: $APP_DIR"
    echo "Server Name/IP: $SERVER_NAME"
    echo "Database Name: $DB_NAME (hardcoded)"
    echo "Database User: $DB_USER (hardcoded)"
    echo "---"
    read -p "Is this correct? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
}

install_system_deps() {
    print_header "Installing System Dependencies"
    apt-get update
    apt-get install -y python3-pip python3-venv apache2 postgresql postgresql-contrib libapache2-mod-wsgi-py3 npm
    echo "System dependencies installed."
}

configure_postgres() {
    print_header "Configuring PostgreSQL Authentication"
    # Find the pg_hba.conf file
    PG_HBA_CONF=$(sudo -u postgres psql -t -P format=unaligned -c 'show hba_file;')

    echo "Found pg_hba.conf at: $PG_HBA_CONF"

    # Check if the peer auth rule already exists
    if grep -q "local *$DB_NAME *$DB_USER *peer" "$PG_HBA_CONF"; then
        echo "PostgreSQL peer authentication rule already exists. Skipping."
    else
        echo "Adding peer authentication rule to pg_hba.conf..."
        # Add a rule to allow the 'www-data' user to connect to the specific db via peer auth
        echo "local    $DB_NAME    $DB_USER    peer" >> "$PG_HBA_CONF"
    fi

    echo "Restarting PostgreSQL service to apply changes..."
    systemctl restart postgresql
}

setup_database() {
    print_header "Setting Up PostgreSQL Database"
    # Create user and database. The user does not need a password for peer auth.
    # The username must be double-quoted because it contains a hyphen.
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" || echo "Database $DB_NAME already exists. Skipping."
    sudo -u postgres psql -c "CREATE USER \"$DB_USER\";" || echo "User $DB_USER already exists. Skipping."
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO \"$DB_USER\";"
    echo "PostgreSQL database and user configured."
}

setup_application() {
    print_header "Setting Up Application Files"

    echo "Creating installation directory at $APP_DIR..."
    mkdir -p $APP_DIR

    echo "Copying application files..."
    rsync -av --progress . $APP_DIR --exclude ".git"

    echo "Setting up Python virtual environment..."
    python3 -m venv $APP_DIR/backend/venv

    echo "Installing Python dependencies..."
    $APP_DIR/backend/venv/bin/pip install -r $APP_DIR/backend/requirements.txt

    echo "Installing frontend dependencies..."
    (cd $APP_DIR/frontend && npm install)

    echo "Building React application..."
    (cd $APP_DIR/frontend && npm run build)

    echo "Creating project .env file in the root directory..."
    # Use a passwordless connection string for Peer Authentication
    cat <<EOF > $APP_DIR/.env
DATABASE_URL="postgresql:///$DB_NAME"
FLASK_APP=backend.wsgi
EOF
    echo "Application setup complete."
}

configure_apache() {
    print_header "Configuring Apache2"
    TEMPLATE_CONF="apache.conf"
    APACHE_CONF_PATH="/etc/apache2/sites-available/aitoolkit.conf"
    echo "Creating Apache configuration file at $APACHE_CONF_PATH..."
    sed -e "s|your_server_domain_or_ip|$SERVER_NAME|g" \
        -e "s|/path/to/your/project|$APP_DIR|g" \
        "$TEMPLATE_CONF" > "$APACHE_CONF_PATH"
    echo "Apache configuration file created."
}

finalize_setup() {
    print_header "Finalizing Setup"
    echo "Initializing database schema..."
    (
        cd $APP_DIR &&
        echo "Initializing database migrations repository (if needed)..." &&
        backend/venv/bin/flask db init || true &&
        echo "Generating database migration..." &&
        backend/venv/bin/flask db migrate -m "Update database schema" &&
        echo "Applying database migration..." &&
        backend/venv/bin/flask db upgrade
    )
    echo "Enabling Apache site and modules..."
    a2ensite aitoolkit.conf
    a2enmod rewrite
    a2enmod wsgi
    echo "Restarting Apache2 service..."
    systemctl restart apache2
    echo "Setup finalized."
}

set_final_permissions() {
    print_header "Setting Final Ownership and Permissions"
    chown -R www-data:www-data $APP_DIR
    echo "Setting directory permissions to 755 and file permissions to 644..."
    find $APP_DIR -type d -exec chmod 755 {} \;
    find $APP_DIR -type f -exec chmod 644 {} \;
    echo "Setting execute permissions for venv and install scripts..."
    chmod +x $APP_DIR/backend/venv/bin/*
    chmod +x $APP_DIR/install.sh
    echo "Permissions set."
}

# --- Main Execution ---
main() {
    print_header "AI Toolkit Interactive Installer"
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use 'sudo ./install.sh'" >&2
        exit 1
    fi

    get_user_input
    install_system_deps
    configure_postgres
    setup_database
    setup_application
    finalize_setup
    set_final_permissions

    print_header "Installation Complete!"
    echo "You should now be able to access the application at your specified domain/IP."
}

# Run the main function
main
