# AI Toolkit - Local LLM Chat Application (GPT4All Edition)

## 1. Project Overview

AI Toolkit is a self-hosted web application designed for efficiently running and managing local Large Language Models. Powered by the [GPT4All](https://gpt4all.io/) ecosystem, this application provides an intuitive interface to download and chat with a wide variety of open-source, quantized models directly on your own hardware.

This platform is perfect for developers, researchers, and AI enthusiasts who want a fast, private, and resource-efficient way to interact with LLMs without relying on third-party APIs.

## 2. Features

- **Efficient Local Inference:** All model processing is handled by the GPT4All library, which is optimized for running quantized GGUF models on consumer hardware (CPU and GPU).
- **Model Management:**
    - Download any model from the GPT4All model list directly through the UI.
    - View and manage your collection of locally stored models.
    - A simple and clean chat interface to interact with any of your downloaded models.
- **User & Access Management (RBAC):**
    - A full user authentication system (register/login).
    - The first user to register is automatically granted 'admin' privileges.
    - Admins can manage users (update roles, delete users) through a dedicated UI.
    - All data and actions are protected, ensuring users can only access what their role permits.
- **AI-Powered Error Diagnosis:**
    - A built-in agent automatically captures backend errors.
    - It uses an LLM to perform a root cause analysis and propose a code fix, which admins can view in the "Code Health" dashboard.
- **Customizable UI:**
    - A sleek, dark-themed interface with a Light mode toggle.
    - A dedicated settings page allows users to customize their experience.

## 3. Tech Stack

- **Backend:** Python 3, Flask
- **Frontend:** React.js
- **Database:** PostgreSQL (for production), SQLite (for development)
- **LLM Inference Engine:** GPT4All
- **Deployment:** Apache2 with `mod_wsgi` on Ubuntu Server

## 4. Deployment Guide (Ubuntu Server)

This guide walks you through deploying the AI Toolkit on a fresh Ubuntu Server using the automated installation script.

### 4.1. Automated Installation (Recommended)

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
    The script will prompt you for all necessary configuration details (database credentials, domain name, etc.).
    ```bash
    sudo ./install.sh
    ```
4.  **Access the Application:**
    Once the script finishes, you can access the application by navigating to `http://your_server_domain_or_ip` in your web browser. The first step will be to register your admin account.

### 4.2. Manual Installation

For users who prefer a manual setup, the steps are outlined in the `install.sh` script. You can use the script as a reference for the required commands and their order.
