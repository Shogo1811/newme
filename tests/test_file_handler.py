"""
ファイルハンドラのテスト
"""
import unittest
from unittest.mock import Mock
from utils.file_handler import allowed_file, validate_uploaded_file


class TestAllowedFile(unittest.TestCase):
    """allowed_file関数のテスト"""

    def test_csv_file_allowed(self):
        """CSVファイルが許可されることを確認"""
        self.assertTrue(allowed_file("test.csv"))
        self.assertTrue(allowed_file("data.CSV"))

    def test_other_file_not_allowed(self):
        """CSV以外のファイルが拒否されることを確認"""
        self.assertFalse(allowed_file("test.txt"))
        self.assertFalse(allowed_file("data.xlsx"))
        self.assertFalse(allowed_file("image.png"))

    def test_no_extension(self):
        """拡張子なしのファイルが拒否されることを確認"""
        self.assertFalse(allowed_file("testfile"))


class TestValidateUploadedFile(unittest.TestCase):
    """validate_uploaded_file関数のテスト"""

    def test_no_file(self):
        """ファイルなしの場合のテスト"""
        is_valid, error = validate_uploaded_file(None)
        self.assertFalse(is_valid)
        self.assertIn("選択されていません", error)

    def test_empty_filename(self):
        """ファイル名が空の場合のテスト"""
        mock_file = Mock()
        mock_file.filename = ""

        is_valid, error = validate_uploaded_file(mock_file)
        self.assertFalse(is_valid)
        self.assertIn("空です", error)

    def test_invalid_extension(self):
        """不正な拡張子のテスト"""
        mock_file = Mock()
        mock_file.filename = "test.txt"

        is_valid, error = validate_uploaded_file(mock_file)
        self.assertFalse(is_valid)
        self.assertIn("許可されていない", error)

    def test_valid_file(self):
        """正常なファイルのテスト"""
        mock_file = Mock()
        mock_file.filename = "test.csv"

        is_valid, error = validate_uploaded_file(mock_file)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")


if __name__ == '__main__':
    unittest.main()
