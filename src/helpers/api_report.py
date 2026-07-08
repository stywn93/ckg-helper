import json
import os
import time
import urllib.error
import urllib.request


API_SECRET_KEY = "API_SECRET"
API_BASE_URL_KEY = "API_BASE_URL"
DEFAULT_API_BASE_URL = "https://playwright-status-api.stywn93.workers.dev"
DEFAULT_API_SECRET = "0505f32f1a01fb8d950a23b6265634b79dad5de1f607a6bef42513dde53c0b03"


def _get_api_config() -> tuple[str, str] | None:
    secret = os.getenv(API_SECRET_KEY) or DEFAULT_API_SECRET
    base_url = os.getenv(API_BASE_URL_KEY) or DEFAULT_API_BASE_URL
    if not secret:
        return None
    return base_url, secret


def report_execution(
    script_name: str,
    status: str,
    duration_ms: int,
    error_message: str | None = None,
) -> None:
    config = _get_api_config()
    if config is None:
        return

    base_url, secret = config
    body = {
        "script_name": script_name,
        "status": status,
        "duration_ms": duration_ms,
    }
    if error_message is not None:
        body["error_message"] = error_message

    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        base_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": secret,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError:
        pass
    except urllib.error.URLError:
        pass


def monitored_main(script_name: str, main_func):
    start = time.monotonic()
    try:
        result = main_func()
        duration_ms = int((time.monotonic() - start) * 1000)
        if isinstance(result, dict):
            status = result.get("status", "success")
            error_message = result.get("error_message")
            report_execution(script_name, status, duration_ms, error_message)
        else:
            report_execution(script_name, "success", duration_ms)
    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        report_execution(script_name, "failed", duration_ms, str(exc))
        raise