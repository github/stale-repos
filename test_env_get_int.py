"""Test the get_int_env_var function"""

import os
import unittest
from unittest.mock import patch

from env import get_int_env_var


class TestEnvGetInt(unittest.TestCase):
    """Test the get_int_env_var function"""

    @patch.dict(os.environ, {"TEST_INT": "1234"}, clear=True)
    def test_get_int_env_var_that_exists_and_has_value(self):
        """Test that gets an integer environment variable that exists and has value"""
        result = get_int_env_var("TEST_INT")
        self.assertEqual(result, 1234)

    @patch.dict(os.environ, {"TEST_INT": "nope"}, clear=True)
    def test_get_int_env_var_that_exists_and_is_none_due_to_invalid_value(self):
        """Test that gets None due to an invalid value"""
        result = get_int_env_var("TEST_INT")
        self.assertIsNone(result)

    @patch.dict(os.environ, {"TEST_INT": ""}, clear=True)
    def test_get_int_env_var_that_exists_and_is_none_due_to_empty_string(self):
        """Test that gets None due to an empty string"""
        result = get_int_env_var("TEST_INT")
        self.assertIsNone(result)

    def test_get_int_env_var_that_does_not_exist_and_default_value_returns_none(self):
        """Test that gets an integer environment variable that does not exist
        and default value returns: none
        """
        result = get_int_env_var("DOES_NOT_EXIST")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
