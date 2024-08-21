# tests/test_connect_dataparc.py
import os, sys
# 프로젝트 루트 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from dataparc.connect_dataparc import DataParcConnector


class TestDataParcConnector(unittest.TestCase):

    def setUp(self):
        self.connector = DataParcConnector(
            site_abbreviation="TEST",
            server="localhost",
            user="test_user",
            password="test_password",
            timezone="UTC"
        )

    @patch('dataparc.connect_dataparc.pymssql.connect')
    def test_check_connection(self, mock_connect):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # 성공하는 경우를 테스트
        response = self.connector.check_connection()
        self.assertEqual(response['status_code'], 200)
        self.assertIn("Connection successful", response['message'])

        # 실패하는 경우를 테스트
        mock_connect.side_effect = Exception("Connection failed")
        response = self.connector.check_connection()
        self.assertEqual(response['status_code'], 500)
        self.assertIn("Connection failed", response['message'])

    @patch('dataparc.connect_dataparc.pymssql.connect')
    def test_fetch_latest_values(self, mock_connect):
        now = datetime.now().replace(microsecond=0)
        mock_data = [
            {'tagName': 'Test.Tag1', 'timestamp': now, 'value': 123.45, 'quality': 192},
            {'tagName': 'Test.Tag2', 'timestamp': now, 'value': 678.90, 'quality': 192},
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_data
        
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_connect.return_value = mock_conn

        response = self.connector.fetch_latest_values(['Test.Tag1', 'Test.Tag2'])
        
        self.assertEqual(response['status_code'], 200)
        self.assertIn('Test.Tag1', response['result'])
        self.assertEqual(response['result']['Test.Tag1'].value, 123.45)
        self.assertEqual(response['result']['Test.Tag1'].quality_str(), 'Good')

        mock_connect.assert_called_once_with(self.connector.server, self.connector.user, self.connector.password, self.connector.database)
        mock_conn.cursor.assert_called_once_with(as_dict=True)
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()

    @patch('dataparc.connect_dataparc.pymssql.connect')
    def test_fetch_raw_data(self, mock_connect):
        now = datetime.now().replace(microsecond=0)
        mock_data = [
            {'tagName': 'Test.Tag1', 'timestamp': now, 'value': 123.45, 'quality': 192},
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_data
        
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_connect.return_value = mock_conn

        start_time = now - timedelta(days=1)
        end_time = now
        response = self.connector.fetch_raw_data(['Test.Tag1'], start_time, end_time)
        
        self.assertEqual(response['status_code'], 200)
        self.assertIn('Test.Tag1', response['result'])
        self.assertEqual(len(response['result']['Test.Tag1']), 1)
        self.assertEqual(response['result']['Test.Tag1'][0].value, 123.45)

    def test_fetch_latest_values_empty_tag_list(self):
        response = self.connector.fetch_latest_values([])
        self.assertEqual(response['status_code'], 400)
        self.assertEqual(response['message'], "Tag list cannot be empty")

    @patch('dataparc.connect_dataparc.pymssql.connect')
    def test_fetch_interpolated_data(self, mock_connect):
        now = datetime.now().replace(microsecond=0)
        mock_data = [
            {'tagName': 'Test.Tag1', 'timestamp': now, 'value': 123.45, 'quality': 192},
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = mock_data
        
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_connect.return_value = mock_conn

        start_time = now - timedelta(days=1)
        end_time = now
        response = self.connector.fetch_interpolated_data(['Test.Tag1'], start_time, end_time, 60, 'AVG')
        
        self.assertEqual(response['status_code'], 200)
        self.assertIn('Test.Tag1', response['result'])
        self.assertEqual(len(response['result']['Test.Tag1']), 1)
        self.assertEqual(response['result']['Test.Tag1'][0].value, 123.45)

    def test_fetch_raw_data_invalid_time_range(self):
        start_time = datetime.now()
        end_time = start_time - timedelta(days=1)
        response = self.connector.fetch_raw_data(["Test.Tag1"], start_time, end_time)
        self.assertEqual(response['status_code'], 400)
        self.assertEqual(response['message'], "Start time must be before end time")

    def test_fetch_interpolated_data_step_size_zero(self):
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now()
        response = self.connector.fetch_interpolated_data(["Test.Tag1"], start_time, end_time, 0, "AVG")
        self.assertEqual(response['status_code'], 400)
        self.assertEqual(response['message'], "Step size must be greater than zero")

    def test_fetch_data_at_times_empty_timestamps(self):
        response = self.connector.fetch_data_at_times(["Test.Tag1"], [])
        self.assertEqual(response['status_code'], 400)
        self.assertEqual(response['message'], "Timestamps list cannot be empty")

if __name__ == '__main__':
    unittest.main()
