import os
from dataclasses import dataclass
from typing import Any

import streamlit as st
from supabase import Client, create_client


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


def create_supabase_client() -> Client | None:
    config = get_supabase_config()
    if config is None:
        return None

    return create_client(config.url, config.publishable_key)


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


def render_auth_gate() -> Client | None:
    supabase = create_supabase_client()

    if supabase is None:
        st.sidebar.warning("Supabase not configured. Auth disabled.")
        return None

    if restore_session(supabase):
        return supabase

    st.title("Dam Breach Studio")
    st.caption("Sign in to access the protected analysis workspace.")

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
