#!/usr/bin/env python3

import os
import sys
import errno
import logging
from dotenv import load_dotenv
import zipfile
import paramiko
import subprocess

# Load environment variables from .env file
load_dotenv()

# Build Paths
WEBGL_BUILD_PATH = os.environ['WEBGL_BUILD_PATH']
LINUX_BUILD_PATH = os.environ['LINUX_BUILD_PATH']

def get_current_git_branch():
    try:
        command = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None

def determine_environment():
    env = os.getenv('DEPLOY_ENV', None)
    if env is None:  # If DEPLOY_ENV is not set, use the Git branch
        branch = get_current_git_branch()
        env = 'staging' if branch == 'staging' else 'production'
    
    if env == 'staging':
        os.environ['AWS_USER'] = os.environ.get('AWS_STAGE_USER', '')
        os.environ['AWS_IP'] = os.environ.get('AWS_STAGE_IP', '')
        os.environ['AWS_SSH_KEY'] = os.environ.get('AWS_STAGE_SSH_KEYPAIR', '')
    else:  # Default to production
        os.environ['AWS_USER'] = os.environ.get('AWS_PROD_USER', '')
        os.environ['AWS_IP'] = os.environ.get('AWS_PROD_IP', '')
        os.environ['AWS_SSH_KEY'] = os.environ.get('AWS_PROD_SSH_KEYPAIR', '')

    print(f"Deploying to {env}")

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
    print("Deploying Linux")
    # Create a .zip file for Linux server
    zipf = zipfile.ZipFile('Server.zip', 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(build_path):
        for file in files:
            file_path = os.path.join(root, file)  
            zipf.write(os.path.join(root, file),
                os.path.relpath(os.path.join(root, file),
                    os.path.join(build_path, '..')))
    zipf.close()
    print('file zipped')

    # Define the file path
    file = 'Server.zip'
    current_directory = os.getcwd()
    local_file = os.path.join(current_directory, file)

    print(f'Local file path: {local_file}')

    # Define AWS credentials and SSH key
    user = os.getenv('AWS_USER')
    ip = os.getenv('AWS_IP')
    key_path = os.path.expanduser(os.getenv('AWS_SSH_KEY'))  # Expanding ~ to the actual home directory

    print(f'AWS user: {user}, IP: {ip}, SSH key path: {key_path}')

    # Define remote file path
    remote_dir = '.'  # '.' denotes the home directory of the user
    # remote_file = os.path.join(remote_dir, file)
    remote_file = '.' + file
    print(f'Remote file path: {remote_file}')

    # Connect and transfer file
    print('Establishing SSH connection...')
    logging.basicConfig(level=logging.DEBUG)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=ip, username=user, key_filename=key_path)

    print('SSH connection established. Opening SFTP session...')
    sftp = ssh.open_sftp()

    print('Starting file transfer...')
    try:
        sftp.stat(remote_file)
        print("File already exists, overwriting...")
    except IOError as e:
        if e.errno == errno.ENOENT:
            # If file does not exist, then upload it
            print("File does not exist, creating...")
        else:
            raise

    sftp.put(local_file, remote_file)

    print('File transfer completed. Closing SFTP session...')
    sftp.close()  # Make sure to close the connection after the file transfer is complete.
    
import subprocess

def execute_commands():
    # Move certificate files
    subprocess.run(["mv", "./Server/cert.json", "./"])
    subprocess.run(["mv", "./Server/cert.pfx", "./"])

    # Remove old server directory
    subprocess.run(["rm", "-r", "./Server"])

    # Unzip new server files
    subprocess.run(["unzip", "./Server.zip"])

    # Change to the server directory
    subprocess.run(["cd", "./Server"], shell=True)

    # Make the server file executable
    subprocess.run(["chmod", "+x", "./Server.x86_64"])

    # Run the server in the background with nohup and provide input
    subprocess.run(["nohup", "./Server.x86_64"], input="\n", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def compress_files():
    # Compress the server files using tar and xz compression
    subprocess.run(["tar", "-cJf", "Server.tar.xz", "Server"])


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
