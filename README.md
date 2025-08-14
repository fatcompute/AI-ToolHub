# AI Toolkit - Local LLM Management & Training Platform

## 1. Project Overview

AI Toolkit is a comprehensive, self-hosted web application designed to give you full control over your local Large Language Models (LLMs). It provides a powerful and intuitive interface to download, manage, chat with, and fine-tune open-source models on your own hardware.

This platform is perfect for developers, researchers, and AI enthusiasts who want to experiment with and develop on top of LLMs without relying on third-party APIs, ensuring privacy, security, and full control over the entire pipeline.

## 2. Features

- **Local-First Processing:** All model processing, inference, and training leverages your local machine's hardware (including GPU acceleration via PyTorch).
- **Model Management & Chat:**
    - Download any open-source model from the Hugging Face Hub directly through the UI.
    - View and manage your collection of locally stored models.
    - A clean chat interface to interact with any model, featuring persistent, user-specific conversation history.
- **Model Fine-Tuning & Evaluation:**
    - Upload your own training and evaluation datasets.
    - Launch fine-tuning jobs, optionally providing an evaluation set to track performance against a separate dataset.
    - Monitor the status and progress of training jobs in real-time.
- **Performance Analytics & Visualization:**
    - Automatically captures and stores key training and evaluation metrics (e.g., loss, accuracy, perplexity).
    - Visualizes performance with charts comparing Training vs. Evaluation Loss to diagnose overfitting.
    - Displays final evaluation scores in a summary scorecard for at-a-glance model assessment.
- **Role-Based Access Control (RBAC):**
    - A full user authentication system (register/login).
    - The first user to register is automatically granted 'admin' privileges.
    - Admins can manage all users (update roles, delete users) through a dedicated UI.
- **AI Diagnosis Agent:** The application includes a built-in agent that automatically captures unhandled backend errors and proposes a code fix, which administrators can view in a dedicated "Code Health" dashboard.
- **Configuration & Settings:**
    - A dedicated settings page allows users to customize their experience (e.g., theme) and set default parameters for training jobs.
    - Admins can view system-level configuration paths.
- **Dark-Themed UI:** A sleek, modern, and user-friendly interface built with React, including a Light mode toggle.

## 3. Tech Stack

- **Backend:** Python 3, Flask
- **Frontend:** React.js
- **Database:** PostgreSQL (for production), SQLite (for development)
- **LLM Interaction:** PyTorch, Hugging Face `transformers` & `huggingface_hub`
- **Deployment:** Apache2 with `mod_wsgi` on Ubuntu Server

## 4. Deployment Guide (Ubuntu Server)

This guide walks you through deploying the AI Toolkit on a fresh Ubuntu Server using the automated installation script. For a manual guide, you can use the `install.sh` script as a command reference.

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
    The script will prompt you for all necessary configuration details.
    ```bash
    sudo ./install.sh
    ```
4.  **Access the Application:**
    Once the script finishes, you can access the application by navigating to `http://your_server_domain_or_ip` in your web browser. The first step will be to register your admin account.
