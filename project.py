#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
import zipfile

# Load environment variables from .env file
load_dotenv()

WEBGL_BUILD_PATH = os.getenv('WEBGL_BUILD_PATH')
LINUX_BUILD_PATH = os.getenv('LINUX_BUILD_PATH')

AWS_SSH_KEY = os.getenv('AWS_SSH_KEY')
AWS_USER = os.getenv('AWS_USER')
AWS_IP = os.getenv('AWS_IP')

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

def validate_build_path(build_path, build_type):
    """
    Validate the build path to ensure it exists and matches the expected conditions.

    :param build_path: Path to the Unity build.
    :type build_path: str
    :raises ValueError: If the build path is invalid or doesn't match the expected conditions.
    """
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

def determine_build_type(webgl_path, linux_path):
    """
    Determine the build type based on the presence of environment variables.

    :return: A string indicating the build type: 'webgl' or 'linux'.
    :rtype: str
    :raises ValueError: If no build type is specified in the environment variables.
    """
    if webgl_path:
        return 'webgl'
    elif linux_path:
        return 'linux'
    else:
        raise ValueError("No build type specified in environment variables")

def deploy_build(webgl_path=None, linux_path=None):
    """
    Orchestrates the deployment of Unity builds based on the build type and validated build path.
    """
    # Determine the build type
    build_type = determine_build_type(webgl_path, linux_path)

    if build_type == 'webgl':
        build_path = webgl_path
    elif build_type == 'linux':
        build_path = linux_path
    
    # Validate the build path
    validate_build_path(build_path, build_type)
    
    # Perform the deployment based on the build type and validated build path
    if build_type == 'webgl':
        deploy_webgl_build(build_path)
    elif build_type == 'linux':
        deploy_linux_build(build_path)
    else:
        print("Unsupported build type")

def deploy_webgl_build(build_path):
    """
    Deploy a WebGL Unity build to a GitHub repository.

    :param build_path: Path to the WebGL Unity build.
    """
    # Implementation
    pass

def deploy_linux_build(build_path):
    """
    Deploy a Linux Unity build to an AWS instance.

    :param build_path: Path to the Linux Unity build.
    """
    # Create a .zip file for Linux server
    zipf = zipfile.ZipFile('Server.zip', 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(build_path):
        for file in files:
            zipf.write(os.path.join(root, file),
                os.path.relpath(os.path.join(root, file),
                    os.path.join(build_path, '..')))
    zipf.close()
    # Implementation for AWS deployment
    pass

def main():
    """
    Main function for initiating the deployment process.
    """
    deploy_build(WEBGL_BUILD_PATH, LINUX_BUILD_PATH)

if __name__ == "__main__":
    main()
