#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Helper Functions ---
print_header() {
    echo "================================================================="
    echo "$1"
    echo "================================================================="
}

# --- Installation Functions ---

get_user_input() {
    print_header "Gathering Configuration Details"

    # Prompt for user-defined variables with defaults
    read -p "Enter the desired installation directory [/var/www/aitoolkit]: " APP_DIR
    APP_DIR=${APP_DIR:-/var/www/aitoolkit}

    read -p "Enter your server's domain name or IP address: " SERVER_NAME
    while [ -z "$SERVER_NAME" ]; do
        echo "Server name/IP cannot be empty." >&2
        read -p "Enter your server's domain name or IP address: " SERVER_NAME
    done

    read -p "Enter the name for the PostgreSQL database [aitoolkit_db]: " DB_NAME
    DB_NAME=${DB_NAME:-aitoolkit_db}

    read -p "Enter the username for the PostgreSQL user [aitoolkit_user]: " DB_USER
    DB_USER=${DB_USER:-aitoolkit_user}

    # Prompt for password without echoing to the terminal
    read -s -p "Enter the password for the PostgreSQL user: " DB_PASS
    echo
    while [ -z "$DB_PASS" ]; do
        echo "Password cannot be empty." >&2
        read -s -p "Enter the password for the PostgreSQL user: " DB_PASS
        echo
    done

    echo "---"
    echo "Configuration:"
    echo "Installation Directory: $APP_DIR"
    echo "Server Name/IP: $SERVER_NAME"
    echo "Database Name: $DB_NAME"
    echo "Database User: $DB_USER"
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
    # Use -y flag to automatically confirm installation
    apt-get install -y python3-pip python3-venv apache2 postgresql postgresql-contrib libapache2-mod-wsgi-py3 npm
    echo "System dependencies installed."
}

setup_database() {
    print_header "Setting Up PostgreSQL Database"
    # Execute SQL commands as the postgres user
    sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
    echo "PostgreSQL database and user created."
}

setup_application() {
    print_header "Setting Up Application Files"

    echo "Creating installation directory at $APP_DIR..."
    mkdir -p $APP_DIR

    # Copy the application files to the installation directory
    # Using rsync is a good way to copy files, excluding .git
    echo "Copying application files..."
    rsync -av --progress . $APP_DIR --exclude ".git"

    # --- Backend Setup ---
    echo "Setting up Python virtual environment..."
    python3 -m venv $APP_DIR/backend/venv

    echo "Ensuring virtual environment scripts are executable..."
    chmod +x $APP_DIR/backend/venv/bin/*

    echo "Installing Python dependencies..."
    $APP_DIR/backend/venv/bin/pip install -r $APP_DIR/backend/requirements.txt

    # --- Frontend Setup ---
    echo "Installing frontend dependencies..."
    # We need to change directory to run npm commands
    (cd $APP_DIR/frontend && npm install)

    echo "Building React application..."
    (cd $APP_DIR/frontend && npm run build)

    # --- Create .env file ---
    echo "Creating project .env file in the root directory..."
    cat <<EOF > $APP_DIR/.env
DATABASE_URL='postgresql://$DB_USER:$DB_PASS@localhost/$DB_NAME'
FLASK_APP=backend.wsgi
# Add any other environment variables here in the future
EOF

    echo "Application setup complete."
}

configure_apache() {
    print_header "Configuring Apache2"

    # Path to the template and the final config file
    TEMPLATE_CONF="apache.conf"
    APACHE_CONF_PATH="/etc/apache2/sites-available/aitoolkit.conf"

    echo "Creating Apache configuration file at $APACHE_CONF_PATH..."

    # Use sed to replace placeholders. Using a different delimiter for sed
    # because the path contains slashes.
    sed -e "s|your_server_domain_or_ip|$SERVER_NAME|g" \
        -e "s|/path/to/your/project|$APP_DIR|g" \
        "$TEMPLATE_CONF" > "$APACHE_CONF_PATH"

    echo "Apache configuration file created."
}

finalize_setup() {
    print_header "Finalizing Setup"

    echo "Initializing database schema..."
    # Run flask commands from the project root
    (
        cd $APP_DIR &&
        # Use the full path to the flask executable in the venv
        backend/venv/bin/flask db init &&
        backend/venv/bin/flask db migrate -m "Initial setup" &&
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

    # Check for root privileges
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use 'sudo ./install.sh'" >&2
        exit 1
    fi

    get_user_input
    install_system_deps
    setup_database
    setup_application
    finalize_setup
    configure_apache
    set_final_permissions

    print_header "Installation Complete!"
    echo "You should now be able to access the application at your specified domain/IP."
}

# Run the main function
main
