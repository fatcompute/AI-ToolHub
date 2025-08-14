# AI Toolkit - Local LLM Management & Training Platform

## 1. Project Overview

AI Toolkit is a comprehensive, self-hosted web application designed to give you full control over your local Large Language Models (LLMs). It provides a powerful and intuitive interface to download, manage, chat with, and fine-tune open-source models on your own hardware.

This version is configured to be self-contained, using a local SQLite database by default, which removes the need for an external database server and simplifies installation.

## 2. Features

- **Local-First Processing:** All model processing, inference, and training leverages your local machine's hardware (including GPU acceleration via PyTorch).
- **Model Management & Chat:**
    - Download any open-source model from the Hugging Face Hub directly through the UI.
    - View and manage your collection of locally stored models.
    - A clean chat interface to interact with any model, featuring persistent, user-specific conversation history.
- **Model Fine-Tuning & Evaluation:**
    - Upload your own training and evaluation datasets.
    - Launch fine-tuning jobs and track performance against an evaluation set.
    - Monitor the status and progress of training jobs in real-time.
- **Performance Analytics & Visualization:**
    - Automatically captures and stores key training and evaluation metrics (e.g., loss, accuracy, perplexity).
    - Visualizes performance with charts comparing Training vs. Evaluation Loss.
- **Role-Based Access Control (RBAC):**
    - A full user authentication system (register/login).
    - The first user to register is automatically granted 'admin' privileges.
    - Admins can manage all users through a dedicated UI.
- **AI Diagnosis Agent:** Automatically captures backend errors and uses an LLM to propose a fix, which admins can view in the "Code Health" dashboard.
- **Configuration & Settings:** A dedicated settings page for user preferences (like themes) and system configuration viewing.

## 3. Tech Stack

- **Backend:** Python 3, Flask
- **Frontend:** React.js
- **Database:** SQLite
- **LLM Interaction:** PyTorch, Hugging Face `transformers`
- **Deployment:** Apache2 with `mod_wsgi` on Ubuntu Server

## 4. Deployment Guide (Ubuntu Server)

This guide walks you through deploying the AI Toolkit on a fresh Ubuntu Server using the automated installation script.

### 4.1. Prerequisites

- An Ubuntu Server (20.04 or later recommended).
- A user with `sudo` privileges.
- An active internet connection to download dependencies.

### 4.2. Automated Installation (Recommended)

The installation script will handle installing all necessary packages (like Python, Apache, etc.), configuring the application, and starting the web server.

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
3.  **Run the Script as Root:**
    The script will ask for the installation directory and your server's domain name.
    ```bash
    sudo ./install.sh
    ```
4.  **Access the Application:**
    Once the script finishes, you can access the application by navigating to `http://your_server_domain_or_ip` in your web browser. The first step will be to register your admin account.
