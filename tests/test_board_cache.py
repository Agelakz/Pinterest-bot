import unittest
import json
from unittest.mock import MagicMock
from services.board_cache import BoardCache

class TestBoardCache(unittest.TestCase):
    
    def setUp(self):
        self.mock_session = MagicMock()
        self.csrftoken = "dummy_token"
        
        # Mocking the JSON response mirroring HAR structure
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resource_response": {
                "data": {
                    "all_boards": [
                        {"id": "111", "name": "Fashion Pria", "type": "board"},
                        {"id": "222", "name": "Makeup", "type": "board"},
                        {"id": "333", "name": "GENERAL", "type": "board"}
                    ]
                }
            }
        }
        self.mock_session.get.return_value = mock_response
        self.cache = BoardCache(self.mock_session, self.csrftoken)

    def test_refresh_loads_boards(self):
        success = self.cache.refresh()
        self.assertTrue(success)
        self.assertEqual(len(self.cache.get_all()), 3)

    def test_find_by_name_exact_case_insensitive(self):
        self.cache.refresh()
        
        # Exact match
        board = self.cache.find_by_name("Makeup")
        self.assertIsNotNone(board)
        self.assertEqual(board["id"], "222")
        
        # Lowercase search matches Capitalized board
        board_lower = self.cache.find_by_name("makeup")
        self.assertIsNotNone(board_lower)
        self.assertEqual(board_lower["id"], "222")
        
        # Different case input matches Uppercase board
        board_general = self.cache.find_by_name("general")
        self.assertIsNotNone(board_general)
        self.assertEqual(board_general["id"], "333")

    def test_find_by_name_not_found(self):
        self.cache.refresh()
        board = self.cache.find_by_name("TidakAda")
        self.assertIsNone(board)

if __name__ == '__main__':
    unittest.main()
