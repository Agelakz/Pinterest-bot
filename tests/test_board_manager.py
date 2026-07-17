import unittest
from unittest.mock import MagicMock
from services.board_manager import BoardManager
from services.board_resolver import BoardResolution

class TestBoardManager(unittest.TestCase):
    
    def setUp(self):
        self.mock_classifier = MagicMock()
        self.mock_cache = MagicMock()
        self.mock_resolver = MagicMock()
        self.mock_creator = MagicMock()
        
        self.manager = BoardManager(
            self.mock_classifier,
            self.mock_cache,
            self.mock_resolver,
            self.mock_creator
        )

    def test_case_1_board_exists_no_create(self):
        # Empty cache simulation triggers lazy load
        self.mock_cache.get_all.return_value = []
        self.mock_cache.refresh.return_value = True
        
        # Resolver finds it
        self.mock_resolver.resolve.return_value = BoardResolution("Makeup", "111", True)
        
        board_id = self.manager.resolve_board("Skintific")
        
        self.assertEqual(board_id, "111")
        self.mock_cache.refresh.assert_called_once() # Only initial load
        self.mock_creator.create.assert_not_called()

    def test_case_2_board_not_exists_auto_create(self):
        # Cache already has some items, no lazy load needed
        self.mock_cache.get_all.return_value = [{"id": "999", "name": "General"}]
        
        # First resolve: Not found
        self.mock_resolver.resolve.side_effect = [
            BoardResolution("Skincare", None, False), # Pass 1
            BoardResolution("Skincare", "222", True)  # Pass 2 (After sync)
        ]
        
        # Creator succeeds
        mock_create_res = MagicMock()
        mock_create_res.success = True
        mock_create_res.board_id = "222"
        self.mock_creator.create.return_value = mock_create_res
        
        # Cache refresh succeeds
        self.mock_cache.refresh.return_value = True
        
        board_id = self.manager.resolve_board("Glad2Glow")
        
        self.assertEqual(board_id, "222")
        self.mock_creator.create.assert_called_once()
        self.mock_cache.refresh.assert_called_once() # Called after creation

    def test_case_3_create_fails(self):
        self.mock_cache.get_all.return_value = [{"id": "999", "name": "General"}]
        self.mock_resolver.resolve.return_value = BoardResolution("Skincare", None, False)
        
        # Creator fails
        mock_create_res = MagicMock()
        mock_create_res.success = False
        self.mock_creator.create.return_value = mock_create_res
        
        board_id = self.manager.resolve_board("Glad2Glow")
        
        self.assertIsNone(board_id)
        self.mock_creator.create.assert_called_once()
        self.mock_cache.refresh.assert_not_called() # No refresh if create fails

    def test_case_4_initial_refresh_fails(self):
        self.mock_cache.get_all.return_value = []
        self.mock_cache.refresh.return_value = False
        
        board_id = self.manager.resolve_board("Skintific")
        self.assertIsNone(board_id)
        self.mock_resolver.resolve.assert_not_called()

if __name__ == '__main__':
    unittest.main()
