#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
import zipfile
import paramiko

# Load environment variables from .env file
load_dotenv()

WEBGL_BUILD_PATH = os.getenv('WEBGL_BUILD_PATH')
LINUX_BUILD_PATH = os.getenv('LINUX_BUILD_PATH')

# Variables for staging environment
STAGING_AWS_SSH_KEY = os.getenv('AWS_STAGE_SSH_KEY')
STAGING_AWS_USER = os.getenv('AWS_STAGE_USER')
STAGING_AWS_IP = os.getenv('AWS_STAGE_IP')

# Variables for production environment
PRODUCTION_AWS_SSH_KEY = os.getenv('AWS_PROD_SSH_KEY')
PRODUCTION_AWS_USER = os.getenv('AWS_PROD_USER')
PRODUCTION_AWS_IP = os.getenv('AWS_PROD_IP')

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

def determine_environment():
    branch = os.getenv('GITHUB_REF', 'refs/heads/main')
    if branch.startswith('refs/heads/staging'):
        os.environ['MY_APP_ENV'] = 'staging'
        os.environ['AWS_USER'] = STAGING_AWS_USER
        os.environ['AWS_IP'] = STAGING_AWS_IP
        os.environ['AWS_SSH_KEY'] = STAGING_AWS_SSH_KEY
    else:
        os.environ['MY_APP_ENV'] = 'production'
        os.environ['AWS_USER'] = PRODUCTION_AWS_USER
        os.environ['AWS_IP'] = PRODUCTION_AWS_IP
        os.environ['AWS_SSH_KEY'] = PRODUCTION_AWS_SSH_KEY

def validate_build_path(build_path, build_type):
    if not build_path:
        raise ValueError("Invalid build path provided")

    if build_type == 'webgl':
        if not os.path.isdir(build_path) or not os.path.isfile(os.path.join(build_path, 'index.html')):
            raise ValueError("WebGL build path is invalid or missing 'index.html' file")
    elif build_type == 'linux':
        if not os.path.isdir(build_path):
            raise ValueError("Linux build path is not a directory")
    else:
        raise ValueError("Invalid build type provided")

def deploy_build(build_type, build_path):
    """
    Orchestrates the deployment of Unity builds based on the build type and validated build path.
    """
    validate_build_path(build_path, build_type)
    if build_type == 'webgl':
        deploy_webgl_build(build_path)
    elif build_type == 'linux':
        deploy_linux_build(build_path)

def deploy_webgl_build(build_path):
    # Implementation
    pass

def deploy_linux_build(build_path):
    """
    Implementation for Linux build deployment
    """
    # Create a .zip file for Linux server
    zipf = zipfile.ZipFile('Server.zip', 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(build_path):
        for file in files:
            zipf.write(os.path.join(root, file),
                os.path.relpath(os.path.join(root, file),
                    os.path.join(build_path, '..')))
    zipf.close()
    
    user = os.getenv('AWS_USER')
    ip = os.getenv('AWS_IP')
    key_path = os.getenv('AWS_SSH_KEY')
    
    local_file = 'Server.zip'
    remote_path = os.path.join(user, local_file)
    # SCP the zip file to the AWS instance
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=ip, username=user, key_filename=key_path)
    scp = ssh.open_sftp()
    scp.put(local_file, remote_path)
    scp.close()

def main():
    """
    Main function for initiating the deployment process.
    """
    determine_environment()
    # Check if running in GitHub actions
    if os.getenv('GITHUB_ACTIONS') == 'true':
        build_type = os.getenv('BUILD_TYPE')
        if build_type == 'webgl':
            deploy_build(build_type, WEBGL_BUILD_PATH)
        elif build_type == 'linux':
            deploy_build(build_type, LINUX_BUILD_PATH)
        else:
            print("No valid build type provided.")
    else:  # Running locally
        if LINUX_BUILD_PATH:
            deploy_build('linux', LINUX_BUILD_PATH)
        if WEBGL_BUILD_PATH:
            deploy_build('webgl', WEBGL_BUILD_PATH)
        
if __name__ == "__main__":
    main()
