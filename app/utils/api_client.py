import requests

BACKEND_URL = "http://localhost:8000/api"
TIMEOUT = 30


def trigger_img_detection(image_bytes, file_name, file_type):
    files = {
        "file": (file_name, image_bytes, file_type)
    }

    try:
        resp = requests.post(
            f"{BACKEND_URL}/detect",
            files=files,
            timeout=TIMEOUT
        )

        if resp.status_code != 200:
            return {
                "error": f"Backend returned {resp.status_code}",
                "detail": resp.text
            }

        return resp.json()

    except requests.exceptions.Timeout:
        return {"error": "Backend timeout"}

    except requests.exceptions.ConnectionError:
        return {"error": "Backend not reachable"}

    except Exception as e:
        return {"error": str(e)}


def fetch_violations():
    try:
        resp = requests.get(
            f"{BACKEND_URL}/violations",
            timeout=TIMEOUT
        )

        if resp.status_code != 200:
            return []

        return resp.json()

    except Exception:
        return []

def save_record(payload: dict):
    try:
        resp = requests.post(
            f"{BACKEND_URL}/save",
            json=payload,
            timeout=TIMEOUT
        )

        if resp.status_code != 200:
            return {
                "error": f"Backend returned {resp.status_code}",
                "detail": resp.text
            }

        return resp.json()

    except requests.exceptions.Timeout:
        return {"error": "Backend timeout"}

    except requests.exceptions.ConnectionError:
        return {"error": "Backend not reachable"}

    except Exception as e:
        return {"error": str(e)}

