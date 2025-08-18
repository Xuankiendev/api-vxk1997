import requests

try:
    response = requests.post(
        "https://ssvid.net/api/ajax/search?hl=en",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0"
        },
        data={"query": url}
    )

    if response.status_code != 200:
        return {"error": f"Failed with status {response.status_code}"}

    try:
        return {"data": response.json()}
    except Exception:
        return {"error": "Response is not JSON", "raw": response.text[:500]}
except Exception as e:
    return {"error": f"Failed to fetch: {str(e)}"}
