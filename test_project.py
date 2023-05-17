import os
import shutil
import time
import tempfile
import zipfile
import unittest
from unittest.mock import patch, mock_open, MagicMock, call
from project import validate_build_path, determine_build_type, deploy_build, deploy_linux_build

class TestDeployment(unittest.TestCase):
    webgl_path = 'c:/Users/fmend/source/repos/Unity/Damnation-Online/Builds/WebGL'
    linux_path = 'c:/Users/fmend/source/repos/Unity/Damnation-Online/Builds/Linux/Server'
    test_dir = None

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree(cls.test_dir)
        except Exception as e:
            print("Error in tearDownClass: ", e)

    def setUp(self):
        # Additional setup steps for each test case
        pass

    def tearDown(self):
        # Additional teardown steps after each test case
        pass                          

    def test_validate_build_path_webgl(self):
        with patch('os.path.isdir', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch.dict(os.environ, {'WEBGL_BUILD_PATH': self.webgl_path}):
                    # The path is a valid webgl build
                    self.assertIsNone(validate_build_path(self.webgl_path, 'webgl'))

    def test_validate_build_path_webgl_missing_html(self):
        with patch('os.path.isdir', return_value=True):
            with patch('os.path.isfile', return_value=False):
                with patch.dict(os.environ, {'WEBGL_BUILD_PATH': self.webgl_path}):
                    # The path is missing the index.html file
                    self.assertRaises(ValueError, validate_build_path, self.webgl_path, 'webgl')

    def test_validate_build_path_linux(self):
        with patch('os.path.isdir', return_value=True):
            with patch.dict(os.environ, {'LINUX_BUILD_PATH': self.linux_path}):
                    # The path is a valid linux build
                    self.assertIsNone(validate_build_path(self.linux_path, 'linux'))

    def test_validate_build_path_linux_not_directory(self):
        with patch('os.path.isdir', return_value=False):
            with patch.dict(os.environ, {'LINUX_BUILD_PATH': self.linux_path}):
                    # The path is not a directory
                    self.assertRaises(ValueError, validate_build_path, self.linux_path, 'linux')

    def test_determine_build_type_webgl(self):
        with patch.dict(os.environ, {'WEBGL_BUILD_PATH': self.webgl_path}):
            # WEBGL_BUILD_PATH environment variable is set
            build_type = determine_build_type(self.webgl_path, None)
            self.assertEqual(build_type, 'webgl')

    def test_determine_build_type_no_build_type(self):
        with patch.dict(os.environ, {}):
            # No build type specified in environment variables
            with self.assertRaises(ValueError):
                determine_build_type(None, None)
                
    @patch('project.deploy_linux_build')
    @patch('project.deploy_webgl_build')
    @patch('project.validate_build_path')
    def test_deploy_build_linux_only(self, mock_validate_build_path, mock_deploy_webgl_build, mock_deploy_linux_build):
        os.environ['LINUX_BUILD_PATH'] = self.linux_path
        deploy_build(linux_path=self.linux_path)
        mock_validate_build_path.assert_called_once_with(self.linux_path, 'linux')
        mock_deploy_linux_build.assert_called_once_with(self.linux_path)
        mock_deploy_webgl_build.assert_not_called()

    @patch('project.deploy_linux_build')
    @patch('project.deploy_webgl_build')
    @patch('project.validate_build_path')
    def test_deploy_build_webgl_only(self, mock_validate_build_path, mock_deploy_webgl_build, mock_deploy_linux_build):
        os.environ['WEBGL_BUILD_PATH'] = self.webgl_path
        deploy_build(webgl_path=self.webgl_path)
        mock_validate_build_path.assert_called_once_with(self.webgl_path, 'webgl')
        mock_deploy_webgl_build.assert_called_once_with(self.webgl_path)
        mock_deploy_linux_build.assert_not_called()

    @patch('project.deploy_linux_build')
    @patch('project.deploy_webgl_build')
    @patch('project.validate_build_path')
    def test_deploy_build_both(self, mock_validate_build_path, mock_deploy_webgl_build, mock_deploy_linux_build):
        os.environ['WEBGL_BUILD_PATH'] = self.webgl_path
        os.environ['LINUX_BUILD_PATH'] = self.linux_path
        deploy_build(webgl_path=self.webgl_path, linux_path=self.linux_path)
        mock_validate_build_path.assert_any_call(self.webgl_path, 'webgl')
        mock_validate_build_path.assert_any_call(self.linux_path, 'linux')
        mock_deploy_webgl_build.assert_called_once_with(self.webgl_path)
        mock_deploy_linux_build.assert_called_once_with(self.linux_path)

    @patch('os.walk')
    @patch('zipfile.ZipFile')
    def test_deploy_linux_build(self, mock_zipfile, mock_os_walk):
        os.chdir(self.test_dir)
        build_path = 'path/to/build'
        mock_os_walk.return_value = [
            (build_path, ['subdir'], ['file1', 'file2']),
            (build_path + '/subdir', [], ['file3']),
        ]
        mock_zipfile.return_value.__enter__.return_value = MagicMock()  # Mock the context manager's __enter__ method
        deploy_linux_build(build_path)
        mock_zipfile.assert_called_once_with('Server.zip', 'w', zipfile.ZIP_DEFLATED)

    def test_deploy_linux_build_invalid_build_path(self):
        build_path = './path/to/nonexistent_build'
        with self.assertRaises(ValueError):
            deploy_linux_build(build_path)


if __name__ == '__main__':
    unittest.main()
