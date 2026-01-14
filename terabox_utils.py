import requests
import os

def upload_to_terabox(file_path, ndus_cookie):
    """Uploads file and returns the fs_id"""
    url = "https://www.terabox.com/api/upload"
    cookies = {"ndus": ndus_cookie}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    filename = os.path.basename(file_path)
    # TeraBox requires specific params for the upload request
    params = {
        "path": f"/TG_Uploads/{filename}",
        "ondup": "overwrite"
    }

    with open(file_path, "rb") as f:
        files = {"file": (filename, f)}
        response = requests.post(url, headers=headers, cookies=cookies, files=files, params=params)
    
    if response.status_code == 200:
        res_json = response.json()
        return res_json.get("fs_id")
    return None

def get_share_link(ndus_cookie, fs_id):
    """Converts fs_id into a public clickable short link"""
    url = "https://www.terabox.com/share/set"
    cookies = {"ndus": ndus_cookie}
    data = {
        "fid_list": f"[{fs_id}]",
        "schannel": "4",
        "channel_list": "[]",
        "period": "0" # Permanent link
    }
    
    response = requests.post(url, cookies=cookies, data=data)
    res_data = response.json()
    
    if res_data.get("errno") == 0:
        return res_data.get("shorturl")
    return None
