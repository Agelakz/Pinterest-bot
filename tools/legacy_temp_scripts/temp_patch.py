import re

with open('/home/ubuntu/pinterest-bot/services/pinterest_api.py', 'r') as f:
    content = f.read()

# 1. Update upload_media signature and return
old_upload = """    def upload_media(self, video_path: str) -> Dict[str, Any]:
        \"\"\"
        Upload video menggunakan metode Story Pin / Idea Pin (v3).
        \"\"\"
        try:
            logger.info("Checking file...")
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"File {video_path} not found")
            
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            if size_mb > self.MAX_FILE_SIZE_MB:
                raise ValueError(f"File too large ({size_mb:.1f}MB)")
            
            # 1. Register Upload (Minta AWS S3 URL dari Pinterest)
            logger.info("Registering media upload...")
            media_id = str(uuid.uuid4())
            register_data = {
                "media_info_list": json.dumps([{"id": media_id, "media_type": "video-story-pin"}], separators=(',', ':'))
            }
            
            reg_resp = self.request_v3("ApiResource", "create", "/v3/media/uploads/register/batch/", register_data)
            
            try:
                # Navigasi schema respons internal Pinterest
                upload_info = reg_resp["resource_response"]["data"][media_id]
                upload_url = upload_info["upload_url"]
                upload_params = upload_info["upload_parameters"]
            except KeyError as e:
                raise ValueError(f"Struktur respons registrasi tidak dikenali: {e} - {reg_resp}")

            # 2. Upload biner ke AWS S3 (tanpa header cookie Pinterest)
            logger.info(f"Uploading media ({size_mb:.1f}MB) ke AWS S3...")
            with open(video_path, 'rb') as f:
                # Pastikan menggunakan requests standar untuk S3 agar cookie Pinterest tidak bocor/mengganggu
                import requests as std_requests
                s3_resp = std_requests.post(upload_url, data=upload_params, files={'file': f})
                
            if not s3_resp.ok:
                raise Exception(f"S3 Upload failed: {s3_resp.status_code} - {s3_resp.text}")
                
            logger.info("Upload completed")
            return {
                "success": True,
                "media_id": media_id,
                "status": "uploaded"
            }"""

new_upload = """    def _get_video_metadata(self, video_path: str):
        # Gunakan cv2 untuk baca properties video (fallback cepat)
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                return width, height
        except Exception:
            pass
        return 1080, 1920

    def upload_media(self, video_path: str) -> Dict[str, Any]:
        \"\"\"
        Upload video menggunakan metode Story Pin / Idea Pin (v3).
        \"\"\"
        try:
            logger.info("Checking file...")
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"File {video_path} not found")
            
            width, height = self._get_video_metadata(video_path)
            
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            if size_mb > self.MAX_FILE_SIZE_MB:
                raise ValueError(f"File too large ({size_mb:.1f}MB)")
            
            # 1. Register Upload (Minta AWS S3 URL dari Pinterest)
            logger.info("Registering media upload...")
            media_id = str(uuid.uuid4())
            register_data = {
                "media_info_list": json.dumps([{"id": media_id, "media_type": "video-story-pin", "upload_aux_data": {"clips": [{"durationMs": 5042, "isFromImage": False, "startTimestampMs": -1}]}}], separators=(',', ':'))
            }
            
            reg_resp = self.request_v3("ApiResource", "create", "/v3/media/uploads/register/batch/", register_data)
            
            try:
                # Navigasi schema respons internal Pinterest
                upload_info = reg_resp["resource_response"]["data"][media_id]
                upload_url = upload_info["upload_url"]
                upload_params = upload_info["upload_parameters"]
                upload_id = upload_info["upload_id"]
            except KeyError as e:
                raise ValueError(f"Struktur respons registrasi tidak dikenali: {e} - {reg_resp}")

            # 2. Upload biner ke AWS S3 (tanpa header cookie Pinterest)
            logger.info(f"Uploading media ({size_mb:.1f}MB) ke AWS S3...")
            with open(video_path, 'rb') as f:
                import requests as std_requests
                s3_resp = std_requests.post(upload_url, data=upload_params, files={'file': f})
                
            if not s3_resp.ok:
                raise Exception(f"S3 Upload failed: {s3_resp.status_code} - {s3_resp.text}")
                
            # Coba ambil ETag dari response S3
            video_signature = s3_resp.headers.get("ETag", "").strip('"')
            
            # Jika AWS memblokir CORS ETag, ambil via GET API (Polling)
            if not video_signature:
                logger.info("Meminta video_signature via GET /v3/media/uploads/")
                poll_resp = self.request_v3("ApiResource", "get", "/v3/media/uploads/", {"upload_ids": [upload_id]})
                try:
                    video_signature = poll_resp["resource_response"]["data"][upload_id]["signature"]
                except KeyError:
                    logger.warning("Gagal mendapatkan signature dari GET /v3/media/uploads/. Menggunakan empty string.")
            
            logger.info(f"Upload completed. Upload ID: {upload_id}, Signature: {video_signature}, Width: {width}, Height: {height}")
            return {
                "success": True,
                "media_id": media_id,
                "upload_id": upload_id,
                "video_signature": video_signature,
                "width": width,
                "height": height,
                "status": "uploaded"
            }"""

content = content.replace(old_upload, new_upload)

# 2. Update create_pin method signature and mapping
old_create = """    def create_pin(self, media_id: str, title: str, description: str, board_id: str, destination_url: str) -> Dict[str, Any]:
        \"\"\"
        Membuat Story Pin / Idea Pin (Final Publish Endpoint).
        Berdasarkan bukti HAR, POST /v3/storypins/ mengeksekusi pin menjadi LIVE.
        \"\"\"
        try:
            # TODO: image_signature saat ini belum diambil dari respons upload_media karena logic upload_media memotongnya.
            # Menggunakan empty placeholder atau default hardcode dari HAR saat ini (sebelum direfactor di upload).
            image_signature = "25c85ebdd56ac66398572d848190dffd"
            
            # TODO: tracking_id idealnya diambil dari response AWS S3 register
            tracking_id = "3681965237893972992" 
            
            logger.info("Executing Final Publish POST /v3/storypins/ ...")
            
            # Format story_pin structure persis sesuai dengan HAR bukti
            story_pin_meta = {
                "metadata": {
                    "pin_title": title,
                    "pin_image_signature": image_signature,
                    "canvas_aspect_ratio": 1
                },
                "pages": [
                    {
                        "blocks": [
                            {
                                "block_style": {"height": 100, "width": 100, "x_coord": 0, "y_coord": 0},
                                "image_signature": image_signature,
                                "tracking_id": tracking_id,
                                "type": 2
                            }
                        ],
                        "clips": [
                            {
                                "clip_type": 0,
                                "end_time_ms": -1,
                                "is_converted_from_image": False,
                                "source_media_height": 1024,
                                "source_media_width": 1024,
                                "start_time_ms": -1
                            }
                        ],
                        "layout": 0,
                        "style": {"background_color": "#f2f1f1"}
                    }
                ]
            }"""

new_create = """    def create_pin(self, media_info: Dict[str, Any], title: str, description: str, board_id: str, destination_url: str) -> Dict[str, Any]:
        \"\"\"
        Membuat Story Pin / Idea Pin (Final Publish Endpoint).
        Berdasarkan bukti HAR, POST /v3/storypins/ mengeksekusi pin menjadi LIVE.
        \"\"\"
        try:
            tracking_id = media_info.get("upload_id")
            video_signature = media_info.get("video_signature", "")
            width = media_info.get("width", 1080)
            height = media_info.get("height", 1920)
            
            aspect_ratio = width / height if height > 0 else 0.5625
            
            # Fallback cover. Saat ini HAR browser menggunakan image upload terpisah.
            # Menggunakan empty placeholder atau default hardcode dari HAR untuk cover image.
            image_signature = "5a14f93aab3366250e1c961f6f213d25"
            
            logger.info("Executing Final Publish POST /v3/storypins/ ...")
            logger.info(f"Using tracking_id: {tracking_id}")
            logger.info(f"Using video_signature: {video_signature}")
            logger.info(f"Aspect Ratio: {aspect_ratio:.4f}")
            
            # Format story_pin structure persis sesuai dengan HAR bukti
            story_pin_meta = {
                "metadata": {
                    "pin_title": title,
                    "pin_image_signature": image_signature,
                    "canvas_aspect_ratio": aspect_ratio
                },
                "pages": [
                    {
                        "blocks": [
                            {
                                "block_style": {"height": 100, "width": 100, "x_coord": 0, "y_coord": 0},
                                "tracking_id": tracking_id,
                                "video_signature": video_signature,
                                "type": 3
                            }
                        ],
                        "clips": [
                            {
                                "clip_type": 1,
                                "end_time_ms": -1,
                                "is_converted_from_image": False,
                                "source_media_height": height,
                                "source_media_width": width,
                                "start_time_ms": -1
                            }
                        ],
                        "layout": 0,
                        "style": {"background_color": "#FFFFFF"}
                    }
                ]
            }"""

content = content.replace(old_create, new_create)

with open('/home/ubuntu/pinterest-bot/services/pinterest_api.py', 'w') as f:
    f.write(content)
