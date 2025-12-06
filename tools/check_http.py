# tools/check_stream_http.py
import requests, sys

url = sys.argv[1]
try:
    r = requests.get(url, stream=True, timeout=5)
    print("HTTP status:", r.status_code)
    ctype = r.headers.get("Content-Type")
    print("Content-Type:", ctype)
    # read small chunk
    chunk = next(r.iter_content(chunk_size=1024))
    print("First chunk length:", len(chunk))
    r.close()
except Exception as e:
    print("ERROR:", e)
