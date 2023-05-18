#!/usr/bin/env python3

import os
import sys
import errno
import logging
from dotenv import load_dotenv
import zipfile
import tarfile
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
    if build_type == 'linux':
        deploy_linux_build(build_path)
        
    elif build_type == 'webgl':
        deploy_webgl_build(build_path)

def deploy_webgl_build(build_path):
    # Implementation
    pass

def deploy_linux_build(build_path):
    """
    Implementation for Linux build deployment
    """
    print("Deploying Linux")
    
    # Create a .zip file for Linux server	
    # file = 'Server.zip'	
    # zipf = zipfile.ZipFile('Server.zip', 'w', zipfile.ZIP_DEFLATED)	
    # for root, dirs, files in os.walk(build_path):	
    #     for file in files:	
    #         file_path = os.path.join(root, file)  	
    #         zipf.write(os.path.join(root, file),	
    #             os.path.relpath(os.path.join(root, file),	
    #                 os.path.join(build_path, '..')))	
    # zipf.close()	
    # print('file zipped')
    
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
    key_path = os.path.expanduser(os.getenv('AWS_SSH_KEY'))  # Expanding ~ to the actual home directory

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
