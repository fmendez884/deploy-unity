#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()

WEBGL_BUILD_PATH = os.getenv('WEBGL_BUILD_PATH')
LINUX_BUILD_PATH = os.getenv('LINUX_BUILD_PATH')

AWS_SSH_KEY = os.getenv('AWS_SSH_KEY')
AWS_USER = os.getenv('AWS_USER')
AWS_IP = os.getenv('AWS_IP')

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

def get_build_type(build_path):
    """
    Determine the type of the Unity build.

    :param build_path: Path to the Unity build.
    :return: A string indicating the build type: 'webgl' or 'linux'.
    """
    # implementation
    pass

def deploy_webgl_build(build_path):
    """
    Deploy a WebGL Unity build to a GitHub repository.

    :param build_path: Path to the WebGL Unity build.
    """
    # implementation
    pass

def deploy_linux_build(build_path):
    """
    Deploy a Linux Unity build to an AWS instance.

    :param build_path: Path to the Linux Unity build.
    """
    # implementation
    pass

def main():
    """
    Main function that orchestrates the deployment of Unity builds based on their type.
    """
    # Determine the build type
    build_type = get_build_type(WEBGL_BUILD_PATH)

    # Depending on the build type, deploy the build
    if build_type == 'webgl':
        deploy_webgl_build(WEBGL_BUILD_PATH)
    elif build_type == 'linux':
        deploy_linux_build(LINUX_BUILD_PATH)
    else:
        print("Unsupported build type")
    
if __name__ == "__main__":
    main()
