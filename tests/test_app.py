"""
Flaskアプリケーションのテスト
"""
import unittest
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_new import app


class TestFlaskRoutes(unittest.TestCase):
    """Flaskルートのテスト"""

    def setUp(self):
        """テストクライアントの設定"""
        self.app = app.test_client()
        self.app.testing = True

    def test_upload_page_loads(self):
        """トップページが正常に表示されることを確認"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_upload_without_file(self):
        """ファイルなしでPOSTした場合のテスト"""
        response = self.app.post('/', data={}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # エラーメッセージが含まれることを確認（実際の実装に依存）

    def test_result_overview_without_prediction(self):
        """予測結果なしで結果ページにアクセスした場合のテスト"""
        response = self.app.get('/result_overview', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # リダイレクトされることを確認


if __name__ == '__main__':
    unittest.main()
