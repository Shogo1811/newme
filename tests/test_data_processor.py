"""
データ処理モジュールのテスト
"""
import unittest
import pandas as pd
from models.data_processor import parse_distance, clean_column_names, preprocess_data


class TestParseDistance(unittest.TestCase):
    """parse_distance関数のテスト"""

    def test_parse_minutes(self):
        """通常の分表記のテスト"""
        self.assertEqual(parse_distance("5分"), 5)
        self.assertEqual(parse_distance("10分"), 10)

    def test_parse_hours_minutes(self):
        """時間+分表記のテスト"""
        self.assertEqual(parse_distance("1H30分"), 90)
        self.assertEqual(parse_distance("2H0分"), 120)

    def test_parse_range(self):
        """範囲表記のテスト"""
        self.assertEqual(parse_distance("5～10分"), 7.5)
        self.assertEqual(parse_distance("10～20分"), 15.0)

    def test_parse_numeric(self):
        """数値がそのまま渡された場合のテスト"""
        self.assertEqual(parse_distance(10), 10)
        self.assertEqual(parse_distance(15.5), 15.5)


class TestCleanColumnNames(unittest.TestCase):
    """clean_column_names関数のテスト"""

    def test_clean_bom(self):
        """BOM削除のテスト"""
        df = pd.DataFrame({"\ufeff取引価格": [1000000]})
        cleaned = clean_column_names(df)
        self.assertIn("取引価格", cleaned.columns)
        self.assertNotIn("\ufeff取引価格", cleaned.columns)


class TestPreprocessData(unittest.TestCase):
    """preprocess_data関数のテスト"""

    def setUp(self):
        """テスト用データの作成"""
        self.test_df = pd.DataFrame({
            "取引価格（総額）": [50000000, 80000000],
            "面積（㎡）": [40.0, 60.0],
            "最寄駅：距離（分）": ["5分", "10分"],
            "建築年": ["2010年", "2015年"],
            "市区町村名": ["千代田区", "港区"],
            "取引時期": ["2024年第1四半期", "2024年第2四半期"]
        })

    def test_preprocess_data_structure(self):
        """前処理後のデータ構造をテスト"""
        result = preprocess_data(self.test_df)

        # 新しいカラムが追加されていることを確認
        self.assertIn("取引年", result.columns)
        self.assertIn("築年帯", result.columns)

        # 建築年が数値化されていることを確認
        self.assertTrue(pd.api.types.is_numeric_dtype(result["建築年"]))

    def test_dropna(self):
        """欠損値削除のテスト"""
        df_with_na = self.test_df.copy()
        df_with_na.loc[0, "建築年"] = None

        result = preprocess_data(df_with_na)

        # 欠損値を含む行が削除されていることを確認
        self.assertEqual(len(result), 1)


if __name__ == '__main__':
    unittest.main()
