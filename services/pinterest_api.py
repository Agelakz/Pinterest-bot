import os
import json
import uuid
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlencode

# Menggunakan curl_cffi untuk bypass WAF/Akamai TLS fingerprinting
from curl_cffi import requests

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class PinterestAPI:
    """
    Pinterest API client using Internal Web API (v3) via HAR approach.
    Uses curl_cffi to bypass TLS fingerprinting.
    """
    BASE_URL = "https://id.pinterest.com/resource"
    MAX_FILE_SIZE_MB = 200

    def __init__(self, cookies_file: str = "cookies.json"):
        """
        Initialize the API client.
        Requires a cookies.json file exported from a logged-in Pinterest session.
        """
        self.session = requests.Session(impersonate="chrome110")
        
        self.cookies_file = cookies_file
        self._load_cookies()
        
        self.csrftoken = None
        for cookie in self.session.cookies.jar:
            if cookie.name == "csrftoken":
                self.csrftoken = cookie.value
                break
                
        if not self.csrftoken:
            logger.warning("csrftoken tidak ditemukan di cookies. Mutasi (POST) mungkin gagal.")
            
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
            "X-Pinterest-AppState": "active",
            "X-CSRFToken": self.csrftoken or "",
            "Origin": "https://id.pinterest.com",
            "Referer": "https://id.pinterest.com/pin-creation-tool/"
        })

    def _load_cookies(self):
        """Membaca cookies dari file JSON atau TXT dan memasukkannya ke session."""
        if not os.path.exists(self.cookies_file):
            logger.error(f"File cookies {self.cookies_file} tidak ditemukan!")
            return
            
        try:
            if self.cookies_file.endswith('.txt'):
                self._load_netscape_cookies()
            else:
                with open(self.cookies_file, 'r') as f:
                    cookies_data = json.load(f)
                    
                # Format cookies export biasanya list of dicts: [{"name": "...", "value": "..."}, ...]
                if isinstance(cookies_data, list):
                    for cookie in cookies_data:
                        self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', '.pinterest.com'))
                # Atau format dictionary sederhana: {"name": "value"}
                elif isinstance(cookies_data, dict):
                    for name, value in cookies_data.items():
                        self.session.cookies.set(name, value, domain=".pinterest.com")
                        
            logger.info(f"Loaded {len(self.session.cookies.jar)} cookies dari {self.cookies_file}")
        except Exception as e:
            logger.error(f"Gagal memuat cookies: {e}")

    def _load_netscape_cookies(self):
        """Membaca cookies dari format Netscape TXT."""
        with open(self.cookies_file, 'r') as f:
            for line in f:
                # Abaikan komentar dan baris kosong
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split('\t')
                # Format Netscape: domain, flag, path, secure, expiration, name, value
                if len(parts) >= 7:
                    domain, _, path, _, _, name, value = parts[:7]
                    self.session.cookies.set(name, value, domain=domain, path=path)

    def _build_payload(self, options_url: str, options_data: Dict[str, Any] = None) -> str:
        """
        Membangun payload urlencoded x-www-form-urlencoded ala Pinterest v3.
        source_url=/pin-creation-tool/&data={"options":{"url":"...","data":{...}},"context":{}}
        """
        data_obj = {
            "options": {
                "url": options_url
            },
            "context": {}
        }
        
        if options_data is not None:
            data_obj["options"]["data"] = options_data
            
        return urlencode({
            "source_url": "/pin-creation-tool/",
            "data": json.dumps(data_obj, separators=(',', ':'))
        })

    def request_v3(self, resource_name: str, action: str, options_url: str, options_data: Dict[str, Any] = None):
        """
        Melakukan request ke internal API.
        Contoh: resource_name="ApiResource", action="create" -> POST /resource/ApiResource/create/
        """
        url = f"{self.BASE_URL}/{resource_name}/{action}/"
        payload = self._build_payload(options_url, options_data)
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        # Perbarui token dari header jika ada pergantian di response sebelumnya
        if self.csrftoken:
            headers["X-CSRFToken"] = self.csrftoken

        resp = self.session.post(url, data=payload, headers=headers)
        
        # Pinterest kadang merotasi csrftoken di header respons
        for cookie in resp.cookies.jar:
            if cookie.name == "csrftoken" and cookie.value != self.csrftoken:
                self.csrftoken = cookie.value
                self.session.headers.update({"X-CSRFToken": self.csrftoken})

        if not resp.ok:
            logger.error(f"API Error {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            
        return resp.json()

    def _get_video_metadata(self, video_path: str):
        # Gunakan cv2 untuk baca properties video & ekstrak cover frame
        cover_path = None
        try:
            import cv2
            import os
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                # Ekstrak 1 frame untuk cover image
                ret, frame = cap.read()
                if ret:
                    cover_tmp = f"{video_path}_cover.jpg"
                    cv2.imwrite(cover_tmp, frame)
                    cover_path = cover_tmp
                cap.release()
                return width, height, cover_path
        except Exception as e:
            logger.warning(f"Gagal memproses cv2: {e}")
        return 1080, 1920, None

    def upload_media(self, video_path: str) -> Dict[str, Any]:
        """
        Upload video menggunakan metode Story Pin / Idea Pin (v3).
        Juga mengupload cover image hasil ekstraksi frame agar pin_image_signature valid.
        """
        try:
            logger.info("Checking file...")
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"File {video_path} not found")
            
            width, height, cover_path = self._get_video_metadata(video_path)
            
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            if size_mb > self.MAX_FILE_SIZE_MB:
                raise ValueError(f"File too large ({size_mb:.1f}MB)")
            
            # --- 1. UPLOAD COVER IMAGE ---
            image_signature = ""
            cover_upload_id = ""
            if cover_path and os.path.exists(cover_path):
                try:
                    logger.info("Registering COVER IMAGE upload...")
                    c_media_id = str(uuid.uuid4())
                    c_reg_data = {
                        "media_info_list": json.dumps([{"id": c_media_id, "media_type": "image-story-pin"}], separators=(',', ':'))
                    }
                    c_reg_resp = self.request_v3("ApiResource", "create", "/v3/media/uploads/register/batch/", c_reg_data)
                    c_upload_info = c_reg_resp["resource_response"]["data"][c_media_id]
                    c_upload_url = c_upload_info["upload_url"]
                    c_upload_params = c_upload_info["upload_parameters"]
                    cover_upload_id = c_upload_info["upload_id"]
                    
                    logger.info("Uploading COVER IMAGE ke AWS S3...")
                    with open(cover_path, 'rb') as f:
                        import requests as std_requests
                        c_s3_resp = std_requests.post(c_upload_url, data=c_upload_params, files={'file': f})
                    if c_s3_resp.ok:
                        image_signature = c_s3_resp.headers.get("ETag", "").strip('"')
                        if not image_signature:
                            poll_resp = self.request_v3("ApiResource", "get", "/v3/media/uploads/", {"upload_ids": [cover_upload_id]})
                            image_signature = poll_resp["resource_response"]["data"][cover_upload_id]["signature"]
                        logger.info(f"Cover image uploaded. ID: {cover_upload_id}, Signature: {image_signature}")
                except Exception as e:
                    logger.warning(f"Gagal mengunggah cover image, melanjutkan tanpa dinamis signature: {e}")
            
            # --- 2. UPLOAD VIDEO ASLI ---
            logger.info("Registering VIDEO upload...")
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

            # Upload biner ke AWS S3 (tanpa header cookie Pinterest)
            logger.info(f"Uploading VIDEO ({size_mb:.1f}MB) ke AWS S3...")
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
            
            logger.info(f"Upload completed. Upload ID Video: {upload_id}, Video Signature: {video_signature}, Cover Upload ID: {cover_upload_id}, Cover Signature: {image_signature}")
            
            # Cleanup cover tmp
            if cover_path and os.path.exists(cover_path):
                os.remove(cover_path)
                
            return {
                "success": True,
                "media_id": media_id,
                "upload_id": upload_id,
                "video_signature": video_signature,
                "image_signature": image_signature,
                "width": width,
                "height": height,
                "status": "uploaded"
            }
            
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            return {"success": False, "error": str(e), "status": "failed"}

    def create_pin(self, media_info: Dict[str, Any], title: str, description: str, board_id: str, destination_url: str) -> Dict[str, Any]:
        """
        Membuat Story Pin / Idea Pin (Final Publish Endpoint).
        Berdasarkan bukti HAR, POST /v3/storypins/ mengeksekusi pin menjadi LIVE.
        """
        try:
            tracking_id = media_info.get("upload_id")
            video_signature = media_info.get("video_signature", "")
            width = media_info.get("width", 1080)
            height = media_info.get("height", 1920)
            
            aspect_ratio = width / height if height > 0 else 0.5625
            
            # Fallback cover jika image dinamis gagal dibuat
            image_signature = media_info.get("image_signature") or "5a14f93aab3366250e1c961f6f213d25"
            
            logger.info("Executing Final Publish POST /v3/storypins/ ...")
            logger.info(f"Using tracking_id: {tracking_id}")
            logger.info(f"Using video_signature: {video_signature}")
            logger.info(f"Using pin_image_signature: {image_signature}")
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
            }
            
            publish_data = {
                "alt_text": "",
                "allow_shopping_rec": True,
                "board_id": board_id,
                "description": description,
                "fields": ["pin.id", "pin.image_signature", "pin.image_square_url", "pin.story_pin_data_id"],
                "is_comments_allowed": True,
                "is_unified_builder": True,
                "link": destination_url or "",
                "method": "uploaded",
                "story_pin": json.dumps(story_pin_meta, separators=(',', ':')),
                "user_mention_tags": "[]"
            }
            
            publish_resp = self.request_v3("ApiResource", "create", "/v3/storypins/", publish_data)
            
            status = publish_resp.get("resource_response", {}).get("status")
            if status != "success":
                raise ValueError(f"Gagal mempublikasikan pin. Response: {publish_resp}")
                
            pin_data = publish_resp.get("resource_response", {}).get("data", {})
            pin_id = pin_data.get("id")
            story_pin_data_id = pin_data.get("story_pin_data_id")
            
            if not pin_id:
                raise ValueError(f"Berhasil request tapi pin.id tidak ditemukan di response. Response: {publish_resp}")
                
            pin_url = f"https://www.pinterest.com/pin/{pin_id}/"
            logger.info("Pin Published Successfully!")
            logger.info(f"Pin ID: {pin_id}")
            logger.info(f"Story Pin Data ID: {story_pin_data_id}")
            logger.info(f"URL: {pin_url}")
            
            return {
                "success": True,
                "pin_id": str(pin_id),
                "story_pin_data_id": story_pin_data_id,
                "pin_url": pin_url,
                "status": "published"
            }
            
        except Exception as e:
            logger.error(f"Create Pin failed: {str(e)}")
            return {"success": False, "error": str(e), "status": "failed"}