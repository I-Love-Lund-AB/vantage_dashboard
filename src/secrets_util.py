"""Läser konfiguration från os.environ och Streamlit Secrets (Cloud)."""
import os
from typing import Any, Optional


DEFAULT_VANTAGE_API_URL = "https://vantage-api.euroclear.com/anz/api/external"


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Env först, sedan st.secrets[key] (inte .get — det misslyckas ofta på Cloud)."""
    value = os.getenv(key)
    if value is not None and str(value).strip():
        return str(value).strip()
    try:
        import streamlit as st

        if key in st.secrets:
            raw = st.secrets[key]
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
        # Sök i TOML-sektioner, t.ex. [connections]
        for section in st.secrets:
            section_val = st.secrets[section]
            if isinstance(section_val, dict) and key in section_val:
                raw = section_val[key]
                if isinstance(raw, str) and raw.strip():
                    return raw.strip()
    except Exception:
        pass
    return default


def apply_streamlit_secrets_to_environ() -> None:
    """Kopierar alla sträng-hemligheter från st.secrets till os.environ."""
    try:
        import streamlit as st

        def _walk(node: Any, prefix: str = "") -> None:
            if isinstance(node, dict):
                items = node.items()
            elif hasattr(node, "keys"):
                items = ((k, node[k]) for k in node.keys())
            else:
                return
            for k, v in items:
                if str(k).startswith("_"):
                    continue
                env_key = f"{prefix}_{k}" if prefix else str(k)
                if isinstance(v, str) and v.strip():
                    os.environ.setdefault(env_key, v.strip())
                elif isinstance(v, (dict,)) or (hasattr(v, "keys") and not isinstance(v, str)):
                    _walk(v, env_key)

        _walk(st.secrets)
    except Exception:
        pass


def ensure_vantage_api_url() -> str:
    """Garanterar att VANTAGE_API_URL alltid finns (behövs inte i Secrets)."""
    url = get_secret("VANTAGE_API_URL") or DEFAULT_VANTAGE_API_URL
    os.environ["VANTAGE_API_URL"] = url
    return url
