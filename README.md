# AI Toolkit - Local LLM Management & Training Platform

## 1. Project Overview

AI Toolkit is a comprehensive, self-hosted web application designed to give you full control over your local Large Language Models (LLMs). It provides a powerful and intuitive interface to download, manage, chat with, and fine-tune open-source models on your own hardware.

This platform is perfect for developers, researchers, and AI enthusiasts who want to experiment with and develop on top of LLMs without relying on third-party APIs, ensuring privacy, security, and full control over the entire pipeline.

## 2. Features

- **Local-First Processing:** All model processing, inference, and training leverages your local machine's hardware (including GPU acceleration via PyTorch).
- **LLM Management:**
    - Download any open-source model from the Hugging Face Hub directly through the UI.
    - View and manage your collection of locally stored models.
    - Chat interface to interact with any of your downloaded models.
- **Model Fine-Tuning:**
    - Upload your own datasets (in `.txt`, `.csv`, or `.jsonl` format).
    - Launch fine-tuning jobs for any of your models using your datasets.
    - Monitor the status and progress of training jobs in real-time.
- **Performance Analytics:**
    - Automatically captures and stores key training metrics like 'loss'.
    - Visualizes training performance with charts to help you evaluate your fine-tuned models.
- **Role-Based Access Control (RBAC):**
    - A full user authentication system (register/login).
    - The first user to register is automatically granted 'admin' privileges.
    - Admins can manage all users (update roles, delete users) through a dedicated UI.
    - All data and actions are protected, ensuring users can only access what their role permits.
- **Dark-Themed UI:** A sleek, modern, and user-friendly interface built with React.

## 3. Tech Stack

- **Backend:** Python 3, Flask
- **Frontend:** React.js
- **Database:** PostgreSQL (for production), SQLite (for development)
- **LLM Interaction:** PyTorch, Hugging Face `transformers` & `huggingface_hub`
- **Database ORM:** Flask-SQLAlchemy
- **Database Migrations:** Flask-Migrate
- **Server:** Apache2 with `mod_wsgi`

## 4. Deployment Guide (Ubuntu Server)

### 4.1. Automated Installation (Recommended)

For a fast and easy setup, you can use the interactive installation script. This is the recommended method for most users.

1.  **Clone the Repository:**
    ```bash
    # Replace with your repository URL
    git clone https://github.com/your-repo/ai-toolkit.git
    cd ai-toolkit
    ```
2.  **Make the Script Executable:**
    ```bash
    chmod +x install.sh
    ```
3.  **Run the Script:**
    Run the script with `sudo`. It will prompt you for all the necessary configuration details.
    ```bash
    sudo ./install.sh
    ```
    Follow the on-screen prompts, and the script will handle the rest of the setup process automatically.

### 4.2. Manual Installation Guide

For users who prefer to set up the application step-by-step, or for troubleshooting, follow this detailed guide.

#### 4.2.1. Prerequisites

- An Ubuntu Server (20.04 or later recommended).
- A user with `sudo` privileges.
- Python 3.8+ and `pip` installed.
- Apache2 and PostgreSQL installed.

```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y python3-pip python3-venv apache2 postgresql postgresql-contrib libapache2-mod-wsgi-py3
```

### 4.2. Database Setup (PostgreSQL)

1.  **Log in to PostgreSQL:**
    ```bash
    sudo -u postgres psql
    ```
2.  **Create a database and user for the application:**
    (Replace `your_password` with a strong password)
    ```sql
    CREATE DATABASE aitoolkit_db;
    CREATE USER aitoolkit_user WITH PASSWORD 'your_password';
    ALTER ROLE aitoolkit_user SET client_encoding TO 'utf8';
    ALTER ROLE aitoolkit_user SET default_transaction_isolation TO 'read committed';
    ALTER ROLE aitoolkit_user SET timezone TO 'UTC';
    GRANT ALL PRIVILEGES ON DATABASE aitoolkit_db TO aitoolkit_user;
    \q
    ```

### 4.3. Application Setup

1.  **Clone the Repository:**
    Clone the project into a directory of your choice, for example `/var/www`.
    ```bash
    sudo git clone https://github.com/your-repo/ai-toolkit.git /var/www/aitoolkit
    cd /var/www/aitoolkit
    ```

2.  **Set up Python Virtual Environment:**
    ```bash
    sudo python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    ```

4.  **Set Environment Variables:**
    Create a `.env` file in the `backend` directory to store your database URL.
    ```bash
    # backend/.env
    DATABASE_URL='postgresql://aitoolkit_user:your_password@localhost/aitoolkit_db'
    FLASK_APP=wsgi.py
    ```
    The application will automatically load these variables.

5.  **Initialize the Database Schema:**
    Use Flask-Migrate to set up the database tables.
    ```bash
    # From the /var/www/aitoolkit/backend directory
    flask db init  # Only run this the very first time
    flask db migrate -m "Initial migration."
    flask db upgrade
    ```

6.  **Build the React Frontend:**
    ```bash
    # From the /var/www/aitoolkit/frontend directory
    npm install
    npm run build
    ```

### 4.4. Apache2 Configuration

1.  **Create an Apache Config File:**
    Use the provided `apache.conf` as a template. Copy it to the Apache sites-available directory.
    ```bash
    sudo cp /var/www/aitoolkit/apache.conf /etc/apache2/sites-available/aitoolkit.conf
    ```

2.  **Edit the Config File:**
    You **must** edit the file to match your project's paths and server name.
    ```bash
    sudo nano /etc/apache2/sites-available/aitoolkit.conf
    ```
    - Replace `your_server_domain_or_ip` with your server's public IP address or domain.
    - Replace all instances of `/path/to/your/project` with `/var/www/aitoolkit`.

3.  **Enable the Site and Necessary Modules:**
    ```bash
    sudo a2ensite aitoolkit.conf
    sudo a2enmod wsgi rewrite
    sudo systemctl restart apache2
    ```

### 4.5. Accessing the Application

You should now be able to access the AI Toolkit by navigating to `http://your_server_domain_or_ip` in your web browser.

## 5. Future Enhancements

- Support for distributed training across multiple machines.
- Integration with cloud services for hybrid processing.
- Advanced analytics and visualization tools for model evaluation.
- Role-based access control for users.
- More detailed training parameter configuration in the UI.
