"""
测试DifySite类的基本功能
"""
import unittest
from unittest.mock import patch, MagicMock
from pydify.site import DifySite, DifyAppMode

class TestDifySite(unittest.TestCase):
    
    @patch('requests.post')
    def test_login(self, mock_post):
        # 模拟登录响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token'
            }
        }
        mock_post.return_value = mock_response
        
        # 初始化DifySite（会自动登录）
        site = DifySite('http://test-dify.com', 'test@example.com', 'password')
        
        # 验证登录请求
        mock_post.assert_called_once()
        self.assertEqual(site.access_token, 'test_access_token')
        self.assertEqual(site.refresh_token, 'test_refresh_token')
    
    @patch('requests.post')
    def test_login_failed(self, mock_post):
        # 模拟登录失败
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Invalid credentials'
        mock_post.return_value = mock_response
        
        # 验证登录失败时抛出异常
        with self.assertRaises(Exception) as context:
            DifySite('http://test-dify.com', 'test@example.com', 'wrong_password')
        
        self.assertIn('登录失败', str(context.exception))
    
    @patch('requests.post')
    @patch('requests.get')
    def test_fetch_apps(self, mock_get, mock_post):
        # 模拟登录响应
        login_response = MagicMock()
        login_response.status_code = 200
        login_response.json.return_value = {
            'data': {
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token'
            }
        }
        mock_post.return_value = login_response
        
        # 模拟获取应用列表响应
        apps_response = MagicMock()
        apps_response.status_code = 200
        apps_response.json.return_value = {
            'page': 1,
            'limit': 10,
            'total': 2,
            'has_more': False,
            'data': [
                {
                    'id': 'app1',
                    'name': 'Test App 1',
                    'mode': 'chat'
                },
                {
                    'id': 'app2',
                    'name': 'Test App 2',
                    'mode': 'completion'
                }
            ]
        }
        mock_get.return_value = apps_response
        
        # 初始化DifySite并获取应用列表
        site = DifySite('http://test-dify.com', 'test@example.com', 'password')
        result = site.fetch_apps(limit=10)
        
        # 验证请求和结果
        mock_get.assert_called_once()
        self.assertEqual(len(result['data']), 2)
        self.assertEqual(result['data'][0]['name'], 'Test App 1')
    
    @patch('requests.post')
    def test_create_app(self, mock_post):
        # 模拟登录响应
        login_response = MagicMock()
        login_response.status_code = 200
        login_response.json.return_value = {
            'data': {
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token'
            }
        }
        
        # 模拟创建应用响应
        create_app_response = MagicMock()
        create_app_response.status_code = 201
        create_app_response.json.return_value = {
            'id': 'new_app_id',
            'name': 'New Test App',
            'mode': 'chat'
        }
        
        # 设置模拟响应的顺序
        mock_post.side_effect = [login_response, create_app_response]
        
        # 初始化DifySite并创建应用
        site = DifySite('http://test-dify.com', 'test@example.com', 'password')
        result = site.create_app('New Test App', 'Test description', DifyAppMode.CHAT)
        
        # 验证请求和结果
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(result['id'], 'new_app_id')
        self.assertEqual(result['name'], 'New Test App')
    
    @patch('requests.post')
    @patch('webbrowser.open')
    def test_jump_to_app(self, mock_open, mock_post):
        # 模拟登录响应
        login_response = MagicMock()
        login_response.status_code = 200
        login_response.json.return_value = {
            'data': {
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token'
            }
        }
        mock_post.return_value = login_response
        
        # 初始化DifySite并跳转到应用
        site = DifySite('http://test-dify.com', 'test@example.com', 'password')
        site.jump_to_app('app_id', DifyAppMode.CHAT)
        
        # 验证调用了正确的URL
        expected_url = 'http://test-dify.com/console/apps/app_id/chat'
        mock_open.assert_called_once_with(expected_url)


if __name__ == '__main__':
    unittest.main() 