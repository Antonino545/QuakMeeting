import ipaddress
import socket
import urllib.parse
import time
import logging
from typing import Tuple, Optional
import requests
import requests.adapters
import urllib3.connection
from urllib3.util.connection import create_connection

from core.notifications.payload import NotificationPayload
from core.notifications.channels.base_channel import BaseNotificationChannel

logger = logging.getLogger("QuakMeeting.WebhookChannel")

BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fe80::/10"),
]

def sanitize_url_credentials(url: Optional[str]) -> Optional[str]:
    """Strip sensitive query parameters like password, token, or auth from join URLs."""
    if not url:
        return None
    try:
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        sensitive_keys = {"pwd", "password", "token", "auth", "passcode", "key"}
        sanitized = [(k, v) for k, v in query_params if k.lower() not in sensitive_keys]
        new_query = urllib.parse.urlencode(sanitized)
        return urllib.parse.urlunparse(parsed._replace(query=new_query))
    except Exception:
        return None

class HostHeaderAdapter(requests.adapters.HTTPAdapter):
    """
    Adapter that resolves the hostname to a validated IP once, then forces the connection
    to that IP while preserving the original Host header, preventing DNS Rebinding TOCTOU attacks.
    """
    def __init__(self, resolved_ip: str, original_host: str, **kwargs):
        self.resolved_ip = resolved_ip
        self.original_host = original_host
        super().__init__(**kwargs)

    def get_connection(self, url, proxies=None):
        conn = super().get_connection(url, proxies)
        
        # We override the connection creator for this specific pool
        class CustomConnection(conn.ConnectionCls):
            _resolved_ip = self.resolved_ip
            _original_host = self.original_host

            def _new_conn(self):
                # Force connection to the resolved IP instead of looking up host again
                extra_kw = {}
                if self.source_address:
                    extra_kw['source_address'] = self.source_address
                if self.socket_options:
                    extra_kw['socket_options'] = self.socket_options

                conn = create_connection(
                    (self._resolved_ip, self.port),
                    self.timeout,
                    **extra_kw
                )
                return conn
                
        conn.ConnectionCls = CustomConnection
        return conn


class WebhookChannel(BaseNotificationChannel):
    def __init__(self, endpoint_url: str, allow_private: bool = False):
        self.endpoint_url = endpoint_url
        self.allow_private = allow_private
        self._failure_count = 0
        self._circuit_open_until = 0.0

    def _validate_and_resolve(self) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            parsed = urllib.parse.urlparse(self.endpoint_url)
            if parsed.scheme.lower() != "https" and not (self.allow_private and parsed.scheme.lower() == "http"):
                return False, "Webhook URLs must use HTTPS.", None
            
            hostname = parsed.hostname
            if not hostname:
                return False, "Invalid webhook hostname.", None
            
            addr_info = socket.getaddrinfo(hostname, None)
            resolved_ip = addr_info[0][4][0]
            ip_obj = ipaddress.ip_address(resolved_ip)
            
            if not self.allow_private:
                for net in BLOCKED_NETWORKS:
                    if ip_obj in net:
                        return False, f"Egress blocked: Host resolves to protected network ({resolved_ip}).", None
            
            return True, None, resolved_ip
        except Exception as e:
            return False, f"URL validation failed: {e}", None

    def send(self, payload: NotificationPayload) -> bool:
        now = time.monotonic()
        if now < self._circuit_open_until:
            logger.warning("Webhook circuit breaker active. Skipping dispatch.")
            return False

        valid, err, resolved_ip = self._validate_and_resolve()
        if not valid or not resolved_ip:
            logger.error(f"Webhook rejected by security policy: {err}")
            return False

        minimized_payload = {
            "event_id": payload.event_id,
            "title": payload.title,
            "stage_minutes": payload.stage_minutes,
            "urgency_level": payload.urgency_level,
            "target_time_iso": payload.target_time.isoformat() if payload.target_time else None,
            "action_url": sanitize_url_credentials(payload.action_url),
            "is_quiet": payload.is_quiet,
            "is_travel": payload.is_travel
        }

        try:
            session = requests.Session()
            parsed = urllib.parse.urlparse(self.endpoint_url)
            # Mount the custom adapter for this specific protocol to prevent DNS Rebinding
            adapter = HostHeaderAdapter(resolved_ip=resolved_ip, original_host=parsed.hostname)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            headers = {"Host": parsed.hostname}
            
            resp = session.post(
                self.endpoint_url,
                json=minimized_payload,
                headers=headers,
                timeout=(2.0, 3.0),
                allow_redirects=False # Prevent redirection to internal IPs
            )
            
            if resp.status_code < 400:
                self._failure_count = 0
                return True
            else:
                logger.error(f"Webhook returned HTTP {resp.status_code}")
                self._record_failure()
                return False
        except Exception as e:
            logger.error(f"Webhook dispatch failed: {e}")
            self._record_failure()
            return False

    def _record_failure(self):
        self._failure_count += 1
        if self._failure_count >= 3:
            logger.warning("Webhook circuit breaker tripped: disabling for 300 seconds.")
            self._circuit_open_until = time.monotonic() + 300.0
