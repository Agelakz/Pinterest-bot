import json
import logging
import re
from typing import Dict, Any
from curl_cffi import requests

logger = logging.getLogger(__name__)


class AISeoEngine:
    def __init__(self):
        import os
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY is not set.")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            system_instruction=(
                "Identitas & Memori:\n"
                "Kamu adalah hibrida antara Pinterest Growth Hacker dan Kreator Konten Affiliate. Fokusmu merajut cerita pendek yang memikat sekaligus mengoptimalkan algoritma visual search. Kamu paham audiens Gen Z/Milenial: mereka butuh inspirasi visual dan narasi autentik, bukan iklan kaku.\n\n"
                "Misi Utama:\n"
                "Menciptakan SEO Copywriting untuk Pinterest Story Pins (Video) yang membangun koneksi emosional dan mengkonversi view menjadi klik (link affiliate).\n\n"
                "Kemampuan Utama yang Digunakan:\n"
                "1. Visual Storytelling: Deskripsi ditulis layaknya rekomendasi personal/review dari teman (bestie), memadukan solusi dan emosi.\n"
                "2. Persuasive Copywriting: Menggunakan Hook (Pattern Interrupt) di kalimat pertama, lalu diakhiri dengan Call-to-Action (CTA) berorientasi konversi yang halus.\n"
                "3. SEO Natural: Menyisipkan kata kunci pencarian tanpa terlihat seperti robot.\n\n"
                "Aturan Kritis (Standar Pinterest):\n"
                "- Tone: Kasual santai, aesthetic, helpful, berenergi.\n"
                "- Call-to-Action (CTA): Arahkan audiens untuk nge-klik tautan langsung pada Pin.\n"
                "- DILARANG menggunakan markdown."
            )
        )

    def _format_success(self, data: Any) -> Dict[str, Any]:
        return {"success": True, "data": data}

    def _format_error(self, message: str) -> Dict[str, Any]:
        return {"success": False, "error": message, "data": None}

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        try:
            res = self.model.generate_content(prompt)
            return self._format_success(res.text.strip())
        except Exception as e:
            return self._format_error(str(e))
            return self._format_error(f"Request failed: {str(e)}")

    def generate_title(self, product: Dict[str, Any]) -> Dict[str, Any]:
        nama = product.get("nama", "")
        kategori = product.get("kategori", "")

        prompt = f"""Buatkan Judul Pinterest Video Pin (Story Pin) untuk produk ini:
Nama produk: {nama}
Kategori: {kategori}

Tugas:
- Tulis SATU KALIMAT judul yang membuat orang penasaran untuk klik.
- Maksimal 100 karakter.
- Jangan sebut harga.
- Harus langsung ke poin/manfaat (contoh: "Akhirnya Nemu [Produk] Buat [Masalah]!").

Hanya balas dengan teks judulnya saja, tanpa tanda kutip atau penjelasan apapun."""

        result = self._call_gemini(prompt)
        if not result["success"]:
            return result

        title = result["data"][:100]
        return self._format_success(title)

    def generate_description(self, product: Dict[str, Any]) -> Dict[str, Any]:
        nama = product.get("nama", "")
        kategori = product.get("kategori", "")
        link = product.get("link_affiliate", "")

        prompt = f"""Buatkan deskripsi Pinterest Video Pin untuk produk ini:
Nama produk: {nama}
Kategori: {kategori}
Link Affiliate: {link}

Tugas:
- Tulis 2-3 kalimat (200-400 karakter).
- Gaya bahasa: Cerita pendek / rekomendasi personal seakan kamu udah pakai (Indo kasual santai).
- Jangan terlihat jualan keras (hard selling).
- Wajib sertakan Call-To-Action natural untuk nge-klik link/simpan pin.
- Jangan gunakan format bullet point kaku.
- DILARANG KERAS menggunakan format Markdown (seperti bintang * atau ** untuk italic/bold). Tulis sebagai plain text murni.

Hanya balas dengan teks deskripsinya saja, tanpa tanda kutip atau penjelasan tambahan."""

        result = self._call_gemini(prompt)
        if not result["success"]:
            return result

        # Bersihkan sisa markdown jika model masih bandel
        desc = result["data"]
        desc = desc.replace("*", "").replace("`", "")
        
        return self._format_success(desc[:500])

    def generate_hashtags(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simple hashtags from product name and category."""
        nama = product.get("nama", "").lower()
        kategori = product.get("kategori", "").lower()

        words = re.findall(r'\b\w+\b', nama + " " + kategori)
        words = [w for w in words if len(w) > 3][:6]

        hashtags = [f"#{w.replace(' ', '')}" for w in words]
        if not hashtags:
            hashtags = ["#shopee", "#affiliate", "#viral"]

        return self._format_success(hashtags[:8])

    def generate_metadata(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Generate title, description, and hashtags."""
        title_res = self.generate_title(product)
        if not title_res["success"]:
            return title_res

        desc_res = self.generate_description(product)
        if not desc_res["success"]:
            return desc_res

        hash_res = self.generate_hashtags(product)

        return self._format_success({
            "title": title_res["data"],
            "description": desc_res["data"],
            "hashtags": hash_res["data"] if hash_res["success"] else ["#shopee", "#affiliate"],
            "destination_url": product.get("link_affiliate", "")
        })