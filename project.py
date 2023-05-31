#!/usr/bin/env python3

import os
import sys
import errno
import json
import zipfile
import tarfile
import base64
import shutil
import logging
import requests
import paramiko
import subprocess
import tempfile
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the current working directory
current_dir = os.getcwd()

# Get the parent directory
parent_dir = os.path.dirname(current_dir)

# Build Paths
WEBGL_BUILD_PATH = os.path.join(os.path.dirname(parent_dir), os.getenv('WEBGL_BUILD_PATH', 'Builds/WebGL'))
LINUX_BUILD_PATH = os.path.join(os.path.dirname(parent_dir), os.getenv('LINUX_BUILD_PATH', 'Builds/Server'))
ACCESS_TOKEN_GITHUB = os.getenv("ACCESS_TOKEN_GITHUB")
WEBAPP_REPO_GITHUB = os.getenv("WEBAPP_REPO_GITHUB")
REPO_NAME = os.getenv('WEBAPP_REPO_GITHUB').split('/')[-1].split('.git')[0]  # Get repo name from URL
USER_NAME = os.getenv('WEBAPP_REPO_GITHUB').split('/')[-2]  # Get username from URL
COMMIT_MESSAGE = 'Upload WebGL build'

def create_ssh_keyfile(key_value):
    """
    If key_value is a path to a file, it returns the path unchanged.
    If key_value is SSH key content, it creates a temporary file and writes the SSH key content into it.
    Returns the path to the existing or created temporary file.
    """
    if os.path.isfile(key_value):
        return key_value  # Key value is a path to an existing file.

    # Key value is the content of the key, create a temporary file.
    temp_dir = tempfile.mkdtemp()
    ssh_key_file_path = os.path.join(temp_dir, 'id_rsa')
    with open(ssh_key_file_path, 'w') as ssh_key_file:
        ssh_key_file.write(key_value)

    # Change file permissions to -rw-------, as required by SSH.
    os.chmod(ssh_key_file_path, 0o600)
    return ssh_key_file_path

def get_current_git_branch():
    try:
        command = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
        result = subprocess.run(command, capture_output=True, text=True)
        branch = result.stdout.strip()

        if branch not in ['staging', 'main']:
            print(f"Warning: current branch '{branch}' is neither 'staging' nor 'main'. Defaulting to 'staging'.")
            return 'staging'

        return branch
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return 'staging'  # Default to 'staging' in case of error

def determine_environment():
    env = os.getenv('DEPLOY_ENV', None)
    if env is None:  # If DEPLOY_ENV is not set, use the Git branch
        branch = get_current_git_branch()
        env = 'staging' if branch == 'staging' else 'production'
    
    if env == 'production':
        os.environ['AWS_USER'] = os.environ.get('AWS_PROD_USER', '')
        os.environ['AWS_IP'] = os.environ.get('AWS_PROD_IP', '')
        os.environ['AWS_SSH_KEY'] = os.environ.get('AWS_PROD_SSH_KEYPAIR', '')
    else:  # Default to staging
        os.environ['AWS_USER'] = os.environ.get('AWS_STAGE_USER', '')
        os.environ['AWS_IP'] = os.environ.get('AWS_STAGE_IP', '')
        os.environ['AWS_SSH_KEY'] = os.environ.get('AWS_STAGE_SSH_KEYPAIR', '')

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
    if build_type == 'linux':
        deploy_linux_build(build_path)
        
    elif build_type == 'webgl':
        deploy_webgl_build(build_path)

def deploy_linux_build(build_path):
    """
    Implementation for Linux build deployment
    """
    print("Deploying Linux")
    
    # Create a .tar.gz file for Linux server
    file_name = 'Server.tar.gz'
    with tarfile.open(file_name, 'w:gz') as tar:
        for root, dirs, files in os.walk(build_path):
            for file in files:
                file_path = os.path.join(root, file)
                tar.add(file_path, arcname=os.path.relpath(file_path, build_path))
    
    print('Files compressed.')

    # Define the local file path
    current_directory = os.getcwd()
    local_file = os.path.join(current_directory, file_name)
    print(f'Local file path: {local_file}')

    # Define AWS credentials and SSH key
    user = os.getenv('AWS_USER')
    ip = os.getenv('AWS_IP')
    
    key_path = create_ssh_keyfile(os.getenv('AWS_SSH_KEY'))
    key_path = os.path.expanduser(key_path)  # Expanding ~ to the actual home directory

    print(f'AWS user: {user}, IP: {ip}, SSH key path: {key_path}')

    # Define remote file path
    remote_dir = './'
    remote_file = remote_dir + file_name
    print(f'Remote file path: {remote_file}')

    # Connect and transfer file
    print('Establishing SSH connection...')
    logging.basicConfig(level=logging.DEBUG)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=ip, username=user, key_filename=key_path)

    print('SSH connection established. Opening SFTP session...')
    scp = ssh.open_sftp()

    print('Starting file transfer...', local_file, ' > ', remote_file)
    scp.put(local_file, remote_file)

    print('File transfer completed. Closing SFTP session...')
    scp.close()

    print('File transferred.')

    # Perform further operations on the remote server
    execute_remote_commands(ssh)
    
    if not os.path.isfile(os.getenv('AWS_SSH_KEY')):
        os.remove(key_path)
        os.rmdir(os.path.dirname(key_path))

    # Close the SSH connection
    ssh.close()

def execute_remote_commands(ssh):
    # Execute commands on the remote server
    commands = [
        "pwd",
        'ls',
        "pkill -f 'Server.x86_64' || true",
        "ls",
        "mv ./Server/cert.json ./",
        "mv ./Server/cert.pfx ./",
        "rm -r ./Server",
        'pwd',
        "ls",
        "mkdir -p ./Server",
        'ls',
        "tar -xzf ./Server.tar.gz -C ./Server",
        "ls",
        "mv ./cert.pfx ./Server",
        "mv ./cert.json ./Server",
        'ls',
        'ls ./Server',
        "chmod +x ./Server/Server.x86_64",
        "(cd ./Server && screen -dmS game ./Server.x86_64) && exit"
    ]

    for command in commands:
        try:
            stdin, stdout, stderr = ssh.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                print(f'Error executing command: {command}')
                error_message = stderr.read().decode().strip()
                print(f'Error message: {error_message}')
            else:
                print(f'Command executed successfully: {command}')
                print('Command output:')
                print(stdout.read().decode().strip())
        except Exception as e:
            print(f'Exception during command execution: {command}')
            print(f'Exception details: {str(e)}')
    return True  # return True only if all commands execute successfully

def deploy_webgl_build(webgl_build_path):
    print("Deploying WebGL")
    current_branch = get_current_git_branch()
    file_paths = []
    for root, _, files in os.walk(webgl_build_path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    push_files_to_github(file_paths, COMMIT_MESSAGE, current_branch)

def get_file_content_base64(file_path):
    with open(file_path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

def create_blob(file_path):
    url = f'https://api.github.com/repos/{USER_NAME}/{REPO_NAME}/git/blobs'
    headers = {'Authorization': f'token {ACCESS_TOKEN_GITHUB}'}
    data = {
        'content': get_file_content_base64(file_path),
        'encoding': 'base64'
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # Ensure we get a 200 response
    return response.json()['sha']

def push_files_to_github(files, commit_message, branch):
    base_url = f'https://api.github.com/repos/{USER_NAME}/{REPO_NAME}'

    # Get the SHA of the latest commit on the branch
    url = f'{base_url}/git/refs/heads/{branch}'
    headers = {'Authorization': f'token {ACCESS_TOKEN_GITHUB}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Ensure we get a 200 response
    latest_commit_sha = response.json()['object']['sha']

    # Create a blob for each file
    tree = []
    for file_path in files:
        blob_sha = create_blob(file_path)
        os_path_in_repo = os.path.join('ClientApp', 'public', 'Build', os.path.basename(file_path))
        path_in_repo = os_path_in_repo.replace('\\', '/')
        tree.append({
            'path': path_in_repo,
            'mode': '100644',  # This means "file"
            'type': 'blob',
            'sha': blob_sha
        })

    # Create a tree
    url = f'{base_url}/git/trees'
    data = {
        'base_tree': latest_commit_sha,
        'tree': tree
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # Ensure we get a 200 response
    tree_sha = response.json()['sha']

    # Create a commit
    url = f'{base_url}/git/commits'
    data = {
        'message': commit_message,
        'tree': tree_sha,
        'parents': [latest_commit_sha]
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # Ensure we get a 200 response
    commit_sha = response.json()['sha']

    # Update the branch to point to the new commit
    url = f'{base_url}/git/refs/heads/{branch}'
    data = {
        'sha': commit_sha
    }
    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()  # Ensure we get a 200 response

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
