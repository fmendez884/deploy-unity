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
    if webgl_path and linux_path:
        raise ValueError("Both WebGL and Linux build paths are specified. Please specify only one.")
    elif webgl_path:
        return 'webgl'
    elif linux_path:
        return 'linux'
    else:
        raise ValueError("No build type specified in environment variables")

def deploy_build(webgl_path=None, linux_path=None):
    """
    Orchestrates the deployment of Unity builds based on the build type and validated build path.
    """
    if webgl_path and linux_path:
        # Deploy both builds
        validate_build_path(webgl_path, 'webgl')
        deploy_webgl_build(webgl_path)
        validate_build_path(linux_path, 'linux')
        deploy_linux_build(linux_path)
    elif webgl_path:
        # Deploy only the WebGL build
        validate_build_path(webgl_path, 'webgl')
        deploy_webgl_build(webgl_path)
    elif linux_path:
        # Deploy only the Linux build
        validate_build_path(linux_path, 'linux')
        deploy_linux_build(linux_path)
    else:
        print("No valid build paths provided.")

def deploy_webgl_build(build_path):
    # Implementation
    pass

def deploy_linux_build(build_path):
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
    deployment_context = os.getenv('DEPLOYMENT_CONTEXT')

    if deployment_context == 'CI':
        # In CI/CD environment, deploy the build based on the provided build path
        if WEBGL_BUILD_PATH:
            deploy_build(webgl_path=WEBGL_BUILD_PATH)
        elif LINUX_BUILD_PATH:
            deploy_build(linux_path=LINUX_BUILD_PATH)
    else:
        # In local environment, deploy both builds if paths are provided
        deploy_build(webgl_path=WEBGL_BUILD_PATH, linux_path=LINUX_BUILD_PATH)
        
if __name__ == "__main__":
    main()
