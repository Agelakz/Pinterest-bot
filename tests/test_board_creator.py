import unittest
from unittest.mock import MagicMock
from services.board_creator import BoardCreator

class TestBoardCreator(unittest.TestCase):
    
    def setUp(self):
        self.mock_session = MagicMock()
        self.csrftoken = "dummy_token"
        self.creator = BoardCreator(self.mock_session, self.csrftoken)

    def test_create_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resource_response": {
                "data": {
                    "id": "111222333",
                    "name": "Skincare"
                }
            }
        }
        self.mock_session.post.return_value = mock_response
        
        result = self.creator.create("Skincare")
        self.assertTrue(result.success)
        self.assertEqual(result.board_id, "111222333")
        self.assertEqual(result.board_name, "Skincare")

    def test_create_http_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 403
        self.mock_session.post.return_value = mock_response
        
        result = self.creator.create("Makeup")
        self.assertFalse(result.success)
        self.assertIsNone(result.board_id)
        
    def test_create_missing_id_in_response(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resource_response": {
                "data": {
                    # id missing
                    "name": "Makeup"
                }
            }
        }
        self.mock_session.post.return_value = mock_response
        
        result = self.creator.create("Makeup")
        self.assertFalse(result.success)
        self.assertIsNone(result.board_id)

if __name__ == '__main__':
    unittest.main()
