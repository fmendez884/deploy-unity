import os
import unittest
from unittest.mock import patch
from project import validate_build_path, determine_build_type, deploy_build

class TestDeployment(unittest.TestCase):
    webgl_path = 'c:/Users/fmend/source/repos/Unity/Damnation-Online/Builds/WebGL'
    linux_path = 'c:/Users/fmend/source/repos/Unity/Damnation-Online/Builds/Linux/Server'

    def test_validate_build_path_webgl(self):
        with patch('os.path.isdir', return_value=True):
            with patch('os.path.isfile', return_value=True):
                # The path is a valid webgl build
                self.assertIsNone(validate_build_path(self.webgl_path, 'webgl'))

    def test_validate_build_path_webgl_missing_html(self):
        with patch('os.path.isdir', return_value=True):
            with patch('os.path.isfile', return_value=False):
                # The path is missing the index.html file
                self.assertRaises(ValueError, validate_build_path, self.webgl_path, 'webgl')

    def test_validate_build_path_linux(self):
        with patch('os.path.isdir', return_value=True):
            # The path is a valid linux build
            self.assertIsNone(validate_build_path(self.linux_path, 'linux'))

    def test_validate_build_path_linux_not_directory(self):
        with patch('os.path.isdir', return_value=False):
            # The path is not a directory
            self.assertRaises(ValueError, validate_build_path, self.linux_path, 'linux')

    def test_determine_build_type_webgl(self):
        # WEBGL_BUILD_PATH is provided
        build_type = determine_build_type(self.webgl_path, None)
        self.assertEqual(build_type, 'webgl')

    def test_determine_build_type_linux(self):
        # LINUX_BUILD_PATH is provided
        build_type = determine_build_type(None, self.linux_path)
        self.assertEqual(build_type, 'linux')

    def test_determine_build_type_no_build_type(self):
        # No build type specified
        with self.assertRaises(ValueError):
            determine_build_type(None, None)

    @patch('project.validate_build_path')
    def test_deploy_build_webgl(self, mock_validate_build_path):
        mock_validate_build_path.return_value = None
        deploy_build(self.webgl_path, None)
        mock_validate_build_path.assert_called_once_with(self.webgl_path, 'webgl')
        # Additional assertions for webgl deployment

    @patch('project.validate_build_path')
    def test_deploy_build_linux(self, mock_validate_build_path):
        mock_validate_build_path.return_value = None
        deploy_build(None, self.linux_path)
        mock_validate_build_path.assert_called_once_with(self.linux_path, 'linux')
        # Additional assertions for linux deployment

    def test_deploy_webgl_build(self):
        # write tests here
        pass

    def test_deploy_linux_build(self):
        # write tests here
        pass

if __name__ == '__main__':
    unittest.main()
