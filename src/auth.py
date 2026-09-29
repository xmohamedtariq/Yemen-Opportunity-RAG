import os
import re

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client


load_dotenv()


APP_URL = os.getenv(
    "APP_URL",
    "https://yemen-opportunity-navigator.streamlit.app",
).strip().rstrip("/")

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,24}$")


def get_supabase():
    """
    Create one Supabase client per Streamlit browser session.
    """
    if "supabase_client" not in st.session_state:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_PUBLISHABLE_KEY")

        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY is missing."
            )

        st.session_state.supabase_client = create_client(url, key)

    return st.session_state.supabase_client


def get_current_user():
    """
    Return the currently authenticated Supabase user.
    """
    try:
        supabase = get_supabase()
        response = supabase.auth.get_user()
        return response.user
    except Exception:
        return None


def get_username(user):
    """
    Return the username stored in Supabase user metadata.
    """
    if not user:
        return None

    metadata = getattr(user, "user_metadata", None) or {}

    username = metadata.get("username")

    if username:
        return str(username)

    if getattr(user, "email", None):
        return user.email.split("@")[0]

    return "User"


def sign_in(email: str, password: str):
    supabase = get_supabase()

    return supabase.auth.sign_in_with_password(
        {
            "email": email.strip(),
            "password": password,
        }
    )


def sign_up(email: str, password: str, username: str):
    """
    Create a new account and store the username
    in Supabase user metadata.
    """
    supabase = get_supabase()

    clean_username = username.strip().lstrip("@")

    return supabase.auth.sign_up(
        {
            "email": email.strip(),
            "password": password,
            "options": {
                "email_redirect_to": APP_URL,
                "data": {
                    "username": clean_username,
                },
            },
        }
    )


def handle_email_confirmation():
    """
    Handle the token_hash sent from the Supabase
    confirmation email.

    After successful verification, the user is
    authenticated automatically.
    """

    token_hash = st.query_params.get("token_hash")
    verification_type = st.query_params.get("type")

    if isinstance(token_hash, list):
        token_hash = token_hash[0] if token_hash else None

    if isinstance(verification_type, list):
        verification_type = (
            verification_type[0]
            if verification_type
            else None
        )

    if not token_hash:
        return

    if verification_type != "email":
        return

    try:
        supabase = get_supabase()

        response = supabase.auth.verify_otp(
            {
                "token_hash": token_hash,
                "type": "email",
            }
        )

        if not response.user or not response.session:
            raise RuntimeError(
                "Supabase did not return an authenticated session."
            )

        # Explicitly store the authenticated session
        supabase.auth.set_session(
            response.session.access_token,
            response.session.refresh_token,
        )

        # Remove verification token from browser URL
        st.query_params.clear()

        st.session_state["email_just_verified"] = True

        st.rerun()

    except Exception:
        st.query_params.clear()

        st.session_state["email_verification_error"] = (
            "The verification link is invalid or has expired. "
            "Please request a new verification email."
        )

        st.rerun()


def sign_out():
    supabase = get_supabase()

    try:
        supabase.auth.sign_out()

    finally:
        if "supabase_client" in st.session_state:
            del st.session_state["supabase_client"]


def render_auth_sidebar():
    """
    Authentication interface.

    Guests can continue using the RAG application.
    """

    # Process confirmation link before rendering auth UI
    handle_email_confirmation()

    with st.sidebar:
        st.markdown("## 👤 Account")

        if st.session_state.pop(
            "email_just_verified",
            False,
        ):
            st.success(
                "Email verified successfully. "
                "You are now signed in."
            )

        verification_error = st.session_state.pop(
            "email_verification_error",
            None,
        )

        if verification_error:
            st.error(verification_error)

        user = get_current_user()

        # =========================
        # SIGNED-IN USER
        # =========================
        if user:
            username = get_username(user)

            st.success(
                f"👋 Welcome, {username}"
            )

            st.markdown(
                f"### @{username}"
            )

            if user.email:
                st.caption(user.email)

            if st.button(
                "Sign Out",
                use_container_width=True,
                key="sign_out_button",
            ):
                sign_out()
                st.rerun()

            return user

        # =========================
        # GUEST
        # =========================
        st.info(
            "You are using Yemen Opportunity Navigator "
            "as a guest. You can create an account or "
            "sign in below."
        )

        sign_in_tab, sign_up_tab = st.tabs(
            ["Sign In", "Sign Up"]
        )

        # =========================
        # SIGN IN
        # =========================
        with sign_in_tab:

            with st.form("signin_form"):

                login_email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                    key="signin_email",
                )

                login_password = st.text_input(
                    "Password",
                    type="password",
                    key="signin_password",
                )

                login_submit = st.form_submit_button(
                    "Sign In",
                    use_container_width=True,
                )

            if login_submit:

                if not login_email or not login_password:
                    st.error(
                        "Please enter your email and password."
                    )

                else:
                    try:
                        response = sign_in(
                            login_email,
                            login_password,
                        )

                        if response.user:
                            st.success(
                                "Signed in successfully."
                            )

                            st.rerun()

                        else:
                            st.error(
                                "Unable to sign in."
                            )

                    except Exception as exc:

                        error_message = str(exc)

                        if (
                            "Email not confirmed"
                            in error_message
                        ):
                            st.warning(
                                "Please verify your email "
                                "address first."
                            )

                        elif (
                            "Invalid login credentials"
                            in error_message
                        ):
                            st.error(
                                "Incorrect email or password."
                            )

                        else:
                            st.error(
                                f"Sign in failed: "
                                f"{error_message}"
                            )

        # =========================
        # SIGN UP
        # =========================
        with sign_up_tab:

            with st.form("signup_form"):

                register_username = st.text_input(
                    "Username",
                    placeholder="mohammed_tariq",
                    key="signup_username",
                )

                register_email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                    key="signup_email",
                )

                register_password = st.text_input(
                    "Password",
                    type="password",
                    key="signup_password",
                )

                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    key="signup_confirm_password",
                )

                register_submit = st.form_submit_button(
                    "Create Account",
                    use_container_width=True,
                )

            if register_submit:

                clean_username = (
                    register_username
                    .strip()
                    .lstrip("@")
                )

                if not clean_username:
                    st.error(
                        "Please choose a username."
                    )

                elif not USERNAME_PATTERN.fullmatch(
                    clean_username
                ):
                    st.error(
                        "Username must be 3-24 characters "
                        "and contain only letters, numbers, "
                        "and underscores."
                    )

                elif not register_email:
                    st.error(
                        "Please enter an email address."
                    )

                elif not register_password:
                    st.error(
                        "Please enter a password."
                    )

                elif len(register_password) < 8:
                    st.error(
                        "Password must contain at least "
                        "8 characters."
                    )

                elif (
                    register_password
                    != confirm_password
                ):
                    st.error(
                        "Passwords do not match."
                    )

                else:
                    try:

                        response = sign_up(
                            register_email,
                            register_password,
                            clean_username,
                        )

                        if response.session:
                            st.success(
                                f"Welcome, "
                                f"{clean_username}!"
                            )

                            st.rerun()

                        elif response.user:
                            st.success(
                                "Account created successfully. "
                                "Check your email and click "
                                "Confirm Email. You will be "
                                "returned to Yemen Opportunity "
                                "Navigator and signed in "
                                "automatically."
                            )

                        else:
                            st.warning(
                                "Registration request "
                                "was submitted."
                            )

                    except Exception as exc:

                        error_message = str(exc)

                        if (
                            "already registered"
                            in error_message.lower()
                        ):
                            st.warning(
                                "An account with this email "
                                "already exists."
                            )

                        elif (
                            "email_address_not_authorized"
                            in error_message
                        ):
                            st.error(
                                "This email cannot receive "
                                "verification emails with the "
                                "current email configuration."
                            )

                        else:
                            st.error(
                                f"Sign up failed: "
                                f"{error_message}"
                            )

        st.caption(
            "You can continue using the opportunity "
            "search without an account."
        )

        return None