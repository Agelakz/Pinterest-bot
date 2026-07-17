import unittest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from main import Pipeline

class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.data_path = Path("dummy.json")
        self.pipeline = Pipeline(self.data_path)
        
    @patch('main.ShopeeReader')
    @patch('main.KeywordPlanner')
    @patch('main.SearchOrchestrator')
    @patch('main.CandidateSelector')
    @patch('main.TikTokBackendClient')
    @patch('main.DownloadManager')
    @patch('main.PinterestSEOEngine')
    @patch('main.PinterestAPI')
    def test_pipeline_success(self, MockAPI, MockSEO, MockDL, MockClient, MockSelector, MockOrch, MockPlanner, MockReader):
        # Setup mocks
        self.pipeline.reader = MockReader.return_value
        self.pipeline.reader.load_products.return_value = {"success": True}
        self.pipeline.reader.get_random_product.return_value = {"success": True, "data": {"id": "p1"}}
        
        self.pipeline.planner = MockPlanner.return_value
        self.pipeline.planner.plan_keywords.return_value = {"success": True, "keywords": ["kw1"]}
        
        self.pipeline.orchestrator = MockOrch.return_value
        self.pipeline.orchestrator.search.return_value = {"success": True, "candidates": [MagicMock()]}
        
        mock_video = MagicMock()
        mock_video.id = "v1"
        mock_video.title = "test video"
        mock_video.author = "tester"
        mock_video.duration = 15
        mock_video.thumbnail = "thumb.jpg"
        mock_video.video_url = "http://tiktok/v1"
        
        self.pipeline.selector = MockSelector.return_value
        self.pipeline.selector.select_best.return_value = {"success": True, "candidate": mock_video}
        
        self.pipeline.tiktok_client = MockClient.return_value
        self.pipeline.tiktok_client.download_video.return_value = {"success": True, "download_url": "http://dl/v1.mp4"}
        
        self.pipeline.download_manager = MockDL.return_value
        self.pipeline.download_manager.download.return_value = {"success": True, "filepath": Path("temp/v1.mp4")}
        
        self.pipeline.seo_engine = MockSEO.return_value
        self.pipeline.seo_engine.generate_metadata.return_value = {
            "success": True, 
            "data": {"title": "T", "description": "D", "hashtags": ["#h1"], "destination_url": "http://s.id"}
        }
        
        self.pipeline.pinterest_api = MockAPI.return_value
        self.pipeline.pinterest_api.upload_media.return_value = {"success": True, "media_id": "m1"}
        self.pipeline.pinterest_api.create_pin.return_value = {"success": True, "pin_id": "pin1", "pin_url": "http://pin/1"}
        
        # Execute
        res = self.pipeline.run()
        
        # Verify
        self.assertTrue(res["success"])
        self.assertEqual(res["publish"]["pin_id"], "pin1")
        self.pipeline.download_manager.cleanup.assert_called_once()
        
    @patch('main.ShopeeReader')
    def test_pipeline_load_fail(self, MockReader):
        self.pipeline.reader = MockReader.return_value
        self.pipeline.reader.load_products.return_value = {"success": False, "error": "file not found"}
        
        res = self.pipeline.run()
        
        self.assertFalse(res["success"])
        self.assertEqual(res["step"], "load_product")

    @patch('main.ShopeeReader')
    @patch('main.KeywordPlanner')
    @patch('main.SearchOrchestrator')
    @patch('main.CandidateSelector')
    def test_pipeline_search_fail(self, MockSelector, MockOrch, MockPlanner, MockReader):
        self.pipeline.reader = MockReader.return_value
        self.pipeline.reader.load_products.return_value = {"success": True}
        self.pipeline.reader.get_random_product.return_value = {"success": True, "data": {"id": "p1"}}
        
        self.pipeline.planner = MockPlanner.return_value
        self.pipeline.planner.generate_search_keywords.return_value = {"success": True, "keywords": ["kw1"]}
        
        self.pipeline.orchestrator = MockOrch.return_value
        self.pipeline.orchestrator.run.return_value = {"success": False, "error": "api timeout"}
        
        self.pipeline.selector = MockSelector.return_value
        res = self.pipeline.run()
        
        self.assertFalse(res["success"])
        self.assertEqual(res["step"], "search_video")

    @patch('main.ShopeeReader')
    @patch('main.KeywordPlanner')
    @patch('main.SearchOrchestrator')
    @patch('main.CandidateSelector')
    @patch('main.TikTokBackendClient')
    def test_pipeline_download_backend_fail(self, MockClient, MockSelector, MockOrch, MockPlanner, MockReader):
        self.pipeline.reader = MockReader.return_value
        self.pipeline.reader.load_products.return_value = {"success": True}
        self.pipeline.reader.get_random_product.return_value = {"success": True, "data": {"id": "p1"}}
        self.pipeline.planner = MockPlanner.return_value
        self.pipeline.planner.generate_search_keywords.return_value = {"success": True, "keywords": ["kw1"]}
        self.pipeline.orchestrator = MockOrch.return_value
        self.pipeline.orchestrator.run.return_value = {"success": True, "candidates": [MagicMock()]}
        
        mock_video = MagicMock()
        mock_video.video_url = "http://tiktok/v1"
        
        self.pipeline.selector = MockSelector.return_value
        self.pipeline.selector.select_best.return_value = {"success": True, "candidate": mock_video}
        
        self.pipeline.tiktok_client = MockClient.return_value
        self.pipeline.tiktok_client.download_video.return_value = {"success": False, "error": "not found"}
        
        res = self.pipeline.run()
        
        self.assertFalse(res["success"])
        self.assertEqual(res["step"], "tiktok_backend")

    @patch('main.ShopeeReader')
    @patch('main.KeywordPlanner')
    @patch('main.SearchOrchestrator')
    @patch('main.CandidateSelector')
    @patch('main.TikTokBackendClient')
    @patch('main.DownloadManager')
    @patch('main.PinterestSEOEngine')
    @patch('main.PinterestAPI')
    def test_pipeline_upload_fail(self, MockAPI, MockSEO, MockDL, MockClient, MockSelector, MockOrch, MockPlanner, MockReader):
        # Setup mocks up to download
        self.pipeline.reader = MockReader.return_value
        self.pipeline.reader.load_products.return_value = {"success": True}
        self.pipeline.reader.get_random_product.return_value = {"success": True, "data": {"id": "p1"}}
        self.pipeline.planner = MockPlanner.return_value
        self.pipeline.planner.generate_search_keywords.return_value = {"success": True, "keywords": ["kw1"]}
        self.pipeline.orchestrator = MockOrch.return_value
        self.pipeline.orchestrator.run.return_value = {"success": True, "candidates": [MagicMock()]}
        mock_video = MagicMock()
        mock_video.video_url = "http://tiktok/v1"
        self.pipeline.selector = MockSelector.return_value
        self.pipeline.selector.select_best.return_value = {"success": True, "candidate": mock_video}
        self.pipeline.tiktok_client = MockClient.return_value
        self.pipeline.tiktok_client.download_video.return_value = {"success": True, "download_url": "http://dl/v1.mp4"}
        self.pipeline.download_manager = MockDL.return_value
        self.pipeline.download_manager.download.return_value = {"success": True, "filepath": Path("temp/v1.mp4")}
        self.pipeline.seo_engine = MockSEO.return_value
        self.pipeline.seo_engine.generate_metadata.return_value = {
            "success": True, 
            "data": {"title": "T", "description": "D", "hashtags": ["#h1"], "destination_url": "http://s.id"}
        }
        
        self.pipeline.pinterest_api = MockAPI.return_value
        self.pipeline.pinterest_api.upload_media.return_value = {"success": False, "error": "s3 error"}
        
        res = self.pipeline.run()
        
        self.assertFalse(res["success"])
        self.assertEqual(res["step"], "upload_media")
        # Cleanup should NOT be called on fail
        self.pipeline.download_manager.cleanup.assert_not_called()

if __name__ == '__main__':
    unittest.main()