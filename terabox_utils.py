import requests
import os

def upload_to_terabox(file_path, ndus_cookie):
    """Uploads file using the multipart/form-data method."""
    # TeraBox Direct Upload URL
    url = "https://www.terabox.com/api/upload"
    cookies = {"ndus": ndus_cookie}
    
    filename = os.path.basename(file_path)
    # Target path in TeraBox
    params = {
        "path": f"/TG_Uploads/{filename}",
        "ondup": "overwrite"
    }

    try:
        with open(file_path, "rb") as f:
            files = {"file": (filename, f)}
            # We use a standard user-agent to avoid being flagged
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            response = requests.post(url, headers=headers, cookies=cookies, files=files, params=params)
            
        res_data = response.json()
        print(f"TeraBox Upload Response: {res_data}") # Logs for Railway
        
        if res_data.get("errno") == 0:
            return res_data.get("fs_id")
        else:
            print(f"TeraBox Error: {res_data.get('errno')}")
            return None
    except Exception as e:
        print(f"Upload logic exception: {e}")
        return None

def get_share_link(ndus_cookie, fs_id):
    """Creates a public sharing link for the uploaded file."""
    url = "https://www.terabox.com/share/set"
    cookies = {"ndus": ndus_cookie}
    data = {
        "fid_list": f"[{fs_id}]",
        "schannel": "4",
        "channel_list": "[]",
        "period": "0" 
    }
    
    try:
        response = requests.post(url, cookies=cookies, data=data)
        res_data = response.json()
        if res_data.get("errno") == 0:
            return res_data.get("shorturl")
    except Exception as e:
        print(f"Sharing exception: {e}")
    return None
