import os
import secrets as _secrets
from dataclasses import dataclass
from threading import Lock
from typing import Any
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import streamlit as st
from supabase.client import Client, ClientOptions, create_client

try:
    from supabase_auth import SyncSupportedStorage
except ImportError:
    from gotrue import SyncSupportedStorage


@dataclass(frozen=True)
class SupabaseConfig:
    url: str
    publishable_key: str


def _get_secret(name: str) -> str | None:
    try:
        supabase_secrets = st.secrets.get("supabase", {})
        value = supabase_secrets.get(name)
    except Exception:
        value = None

    if value:
        return str(value)

    return os.getenv(f"SUPABASE_{name.upper()}")


def get_supabase_config() -> SupabaseConfig | None:
    url = _get_secret("url")
    publishable_key = _get_secret("publishable_key")

    if not url or not publishable_key:
        return None

    return SupabaseConfig(url=url, publishable_key=publishable_key)


# ---------------------------------------------------------------------------
# PKCE code_verifier storage
# ---------------------------------------------------------------------------
# CONFIRMED BY DEBUG TRACE: st.session_state does NOT survive the full-page
# round trip to GitHub's site and back, even in the same browser tab.
# Streamlit assigns a fresh session identity on that return navigation, so
# anything stored in session_state before leaving is gone by the time
# ?code=... comes back.
#
# Fix: store the PKCE code_verifier in a process-wide dict (plain Python
# memory shared by the whole running Streamlit server), keyed by a random
# one-time "flow_id" that we generate ourselves and carry through the
# redirect_to URL as a query parameter. Since we -- not Streamlit -- are
# responsible for round-tripping that key, it survives regardless of how
# Streamlit's session identity behaves across the navigation.
#
# This is safe for concurrent users: each sign-in attempt gets its own
# random flow_id, so there's no cross-user collision. Entries are removed
# after a successful (or failed) exchange so the dict doesn't grow forever.

_PKCE_LOCK = Lock()
_PKCE_VERIFIERS: dict[str, str] = {}
_VERIFIER_KEY_SUFFIX = "-code-verifier"


class ProcessPKCEStorage(SyncSupportedStorage):
    """Supabase auth storage backend that persists the PKCE code_verifier
    in process memory, keyed by an externally-supplied flow_id, instead of
    relying on Streamlit's per-session state."""

    def __init__(self) -> None:
        self._flow_id: str | None = None

    def set_flow_id(self, flow_id: str | None) -> None:
        self._flow_id = flow_id

    def get_item(self, key: str) -> str | None:
        if key.endswith(_VERIFIER_KEY_SUFFIX) and self._flow_id:
            with _PKCE_LOCK:
                return _PKCE_VERIFIERS.get(self._flow_id)
        return None

    def set_item(self, key: str, value: str) -> None:
        if key.endswith(_VERIFIER_KEY_SUFFIX) and self._flow_id:
            with _PKCE_LOCK:
                _PKCE_VERIFIERS[self._flow_id] = value

    def remove_item(self, key: str) -> None:
        if key.endswith(_VERIFIER_KEY_SUFFIX) and self._flow_id:
            with _PKCE_LOCK:
                _PKCE_VERIFIERS.pop(self._flow_id, None)


def create_supabase_client() -> tuple[Client, ProcessPKCEStorage] | tuple[None, None]:
    config = get_supabase_config()
    if config is None:
        return None, None

    storage = ProcessPKCEStorage()
    client = create_client(
        config.url,
        config.publishable_key,
        options=ClientOptions(
            storage=storage,
            flow_type="pkce",
        ),
    )
    return client, storage


def _read_field(value: Any, field: str) -> Any:
    if isinstance(value, dict):
        return value.get(field)

    return getattr(value, field, None)


def _store_session(auth_response: Any) -> bool:
    session = _read_field(auth_response, "session")
    user = _read_field(auth_response, "user")

    if session is None:
        return False

    st.session_state["auth_access_token"] = _read_field(session, "access_token")
    st.session_state["auth_refresh_token"] = _read_field(session, "refresh_token")
    st.session_state["auth_user"] = {
        "id": _read_field(user, "id"),
        "email": _read_field(user, "email"),
    }
    return True


def _clear_session() -> None:
    for key in ["auth_access_token", "auth_refresh_token", "auth_user"]:
        st.session_state.pop(key, None)


def restore_session(supabase: Client) -> bool:
    access_token = st.session_state.get("auth_access_token")
    refresh_token = st.session_state.get("auth_refresh_token")

    if not access_token or not refresh_token:
        return False

    try:
        response = supabase.auth.set_session(access_token, refresh_token)
    except Exception:
        _clear_session()
        return False

    return _store_session(response)


# ---------------------------------------------------------------------------
# GitHub OAuth support
# ---------------------------------------------------------------------------
# Supabase (with flow_type="pkce") redirects back with an authorization
# code in a query param: http://localhost:8501/?code=...&flow_id=...
# We read both, point the storage at the right flow_id so it can find the
# matching code_verifier, then exchange the code for a session.


def _get_redirect_url() -> str | None:
    return _get_secret("redirect_url")  # e.g. "https://your-app.streamlit.app"


def _append_query_param(url: str, key: str, value: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query))
    query[key] = value
    return urlunparse(parsed._replace(query=urlencode(query)))


def _consume_oauth_code(supabase: Client, storage: ProcessPKCEStorage) -> bool:
    code = st.query_params.get("code")
    flow_id = st.query_params.get("flow_id")

    if not code:
        return False

    storage.set_flow_id(flow_id)

    try:
        response = supabase.auth.exchange_code_for_session({"auth_code": code})
    except Exception as exc:
        st.error(f"GitHub sign-in failed: {exc}")
        storage.remove_item("supabase.auth.token" + _VERIFIER_KEY_SUFFIX)
        st.query_params.clear()
        return False

    storage.remove_item("supabase.auth.token" + _VERIFIER_KEY_SUFFIX)

    stored = _store_session(response)
    if stored:
        st.query_params.clear()
    return stored


def render_github_sign_in(supabase: Client, storage: ProcessPKCEStorage) -> None:
    redirect_url = _get_redirect_url()
    if not redirect_url:
        st.error("redirect_url is not configured in secrets. Cannot start GitHub sign-in.")
        return

    flow_id = _secrets.token_urlsafe(16)
    storage.set_flow_id(flow_id)
    redirect_to = _append_query_param(redirect_url, "flow_id", flow_id)

    try:
        response = supabase.auth.sign_in_with_oauth(
            {
                "provider": "github",
                "options": {"redirect_to": redirect_to},
            }
        )
    except Exception as exc:
        st.error(f"Could not start GitHub sign-in: {exc}")
        return

    oauth_url = _read_field(response, "url")
    if oauth_url:
        # target="_self" keeps the whole OAuth round trip in the same tab
        # (st.link_button opens a new tab, which we don't want here).
        st.markdown(
            f"""
            <a href="{oauth_url}" target="_self" style="text-decoration:none;">
                <div style="
                    display:flex; align-items:center; justify-content:center;
                    padding:0.5rem 1rem; border-radius:0.5rem;
                    border:1px solid rgba(250,250,250,0.2);
                    background-color:#262730; color:#fafafa;
                    font-weight:600; width:100%; cursor:pointer;">
                    Continue with GitHub
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Auth gate / UI
# ---------------------------------------------------------------------------


def render_auth_gate() -> Client | None:
    supabase, storage = create_supabase_client()

    if supabase is None:
        st.sidebar.warning("Supabase not configured. Auth disabled.")
        return None

    if _consume_oauth_code(supabase, storage):
        st.rerun()

    if restore_session(supabase):
        return supabase

    st.title("Dam Breach Studio")
    st.caption("Sign in to access the protected analysis workspace.")

    render_github_sign_in(supabase, storage)
    st.divider()

    sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])

    with sign_in_tab:
        with st.form("sign_in_form"):
            email = st.text_input("Email", key="sign_in_email")
            password = st.text_input("Password", type="password", key="sign_in_password")
            submitted = st.form_submit_button("Sign in", type="primary")

        if submitted:
            try:
                response = supabase.auth.sign_in_with_password(
                    {"email": email.strip(), "password": password}
                )
            except Exception as exc:
                st.error(f"Sign in failed: {exc}")
            else:
                if _store_session(response):
                    st.rerun()
                else:
                    st.error("Sign in did not return a session.")

    with sign_up_tab:
        with st.form("sign_up_form"):
            email = st.text_input("Email", key="sign_up_email")
            password = st.text_input("Password", type="password", key="sign_up_password")
            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="sign_up_confirm_password",
            )
            submitted = st.form_submit_button("Create account", type="primary")

        if submitted:
            if password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    response = supabase.auth.sign_up(
                        {"email": email.strip(), "password": password}
                    )
                except Exception as exc:
                    st.error(f"Account creation failed: {exc}")
                else:
                    if _store_session(response):
                        st.rerun()
                    else:
                        st.success("Account created. Check your email to confirm your address.")

    st.stop()


def render_user_menu(supabase: Client) -> None:
    user = st.session_state.get("auth_user", {})
    email = user.get("email") or "Signed-in user"

    with st.sidebar:
        st.divider()
        st.caption(email)
        if st.button("Sign out", width="stretch"):
            try:
                supabase.auth.sign_out()
            finally:
                _clear_session()
                st.rerun()
