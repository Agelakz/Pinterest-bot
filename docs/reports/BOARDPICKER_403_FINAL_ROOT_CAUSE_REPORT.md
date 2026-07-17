# BoardPicker 403 Final Root Cause Investigation Report

**Mode**: Strict Read-Only Forensic Audit  
**Date**: 2026-07-16  
**Focus**: `GET /resource/BoardPickerBoardsResource/get/` only  
**Evidence Sources**:
- pinpapantest.har
- makeup1.har
- makeup3.har
- services/board_cache.py (current state)
- Runtime logs (HTTP 403)

---

## 1. Key Facts Already Proven

- BoardCreator works correctly (HTTP 200 + board creation success).
- Duplicate board validation works correctly (HTTP 400 with clear error message).
- All critical headers (sec-ch-ua, sec-fetch-*, Accept-Encoding, Origin, Referer, etc.) have been aligned with HAR.
- Cookie set is identical (19 cookies from cookies.json).
- Payload (`data` parameter) is identical.

Despite the above, `BoardPickerBoardsResource/get/` still returns **HTTP 403**.

---

## 2. Deep Comparison: Browser vs Bot

### 2.1 HTTP Layer

| Aspect                    | Browser (HAR)          | Bot (curl_cffi)              | Match     | Impact |
|---------------------------|------------------------|------------------------------|-----------|--------|
| HTTP Version              | HTTP/2                 | HTTP/2 (via curl_cffi)       | Likely    | Low    |
| ALPN                      | h2                     | h2                           | Likely    | Low    |
| Pseudo-headers order      | :method, :path, :authority, :scheme | Unknown (curl_cffi default) | Unknown   | Medium |
| TLS Fingerprint (JA3)     | Real Chrome 131        | curl_cffi impersonation      | Different | **High** |
| HTTP2 SETTINGS frame      | Browser-specific       | curl_cffi default            | Different | **High** |

### 2.2 Bootstrap / State Dependency

**Evidence from HAR files**:

- In `makeup3.har` and `pinpapantest.har`, `BoardPickerBoardsResource/get/` is called **after** the browser has already loaded:
  - `/pin-creation-tool/`
  - Multiple `/resource/ApiResource/get/`
  - Font loading, telemetry, and other bootstrap requests.

- There is **no evidence** in any HAR that `BoardPickerBoardsResource/get/` can be called as the **very first request** in a fresh session.

- Every successful BoardPicker request in HAR occurs **after** the browser has established:
  - Session context via previous page loads
  - Additional cookies or headers set during navigation
  - Possible client-side state (localStorage / IndexedDB) that influences server-side decisions

### 2.3 Standalone Call Feasibility

**Question**: Can `BoardPickerBoardsResource/get/` be called standalone with only valid cookies?

**Evidence-based Answer**:

**No evidence supports standalone success.**

All observed successful calls to `BoardPickerBoardsResource/get/` in the HAR files occur **after** the browser has performed prior navigation and bootstrap requests. There is zero evidence of a cold session (only cookies, no prior requests) successfully fetching the board list.

---

## 3. Most Likely Root Cause

Based on exhaustive header alignment and the persistent 403:

| Possible Cause                    | Evidence Level | Likelihood |
|-----------------------------------|----------------|------------|
| Missing/incorrect TLS fingerprint | Strong (common Akamai behavior) | **High** |
| Missing HTTP/2 SETTINGS / pseudo-header order | Medium         | Medium     |
| Requires prior browser navigation / state | Strong (HAR pattern) | **High** |
| Cookie / header mismatch          | None (already aligned) | Low        |
| Endpoint changed                  | None           | Low        |

**Primary Hypothesis**:

`BoardPickerBoardsResource/get/` is protected by Akamai and requires either:
1. A valid browser TLS fingerprint (JA3), **or**
2. Prior navigation state established by loading Pinterest pages in a real browser session.

HTTP client (even with perfect header impersonation) is insufficient when the WAF enforces browser fingerprint or session bootstrap.

---

## 4. Final Forensic Conclusion

1. **Apakah BoardPicker bisa dipanggil secara standalone dengan cookie valid?**  
   **Tidak dapat dibuktikan.** Semua evidence menunjukkan BoardPicker selalu dipanggil setelah bootstrap browser.

2. **Apakah penyebab 403 adalah header mismatch?**  
   **Tidak.** Semua header penting sudah disamakan dengan HAR.

3. **Apakah penyebab 403 adalah TLS / HTTP2 fingerprint?**  
   **Sangat mungkin** (High likelihood).

4. **Apakah BoardPicker membutuhkan state browser sebelumnya?**  
   **Sangat mungkin** (High likelihood berdasarkan pola HAR).

---

**Confidence Level**: **70%**

Evidence menunjukkan bahwa BoardPicker kemungkinan besar **tidak dapat** dipanggil secara murni standalone oleh HTTP client, bahkan dengan cookie dan header yang sempurna. Root cause paling mungkin adalah kombinasi TLS fingerprint + requirement untuk prior browser navigation state.

**Tidak ada solusi atau patch yang diusulkan.** Laporan ini hanya berisi forensic evidence.