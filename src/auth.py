import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client


load_dotenv()


def get_supabase():
    """
    Create one Supabase client per Streamlit browser session.
    Do not cache one global client for all users.
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
    Returns the authenticated Supabase user.
    Returns None for guests.
    """
    try:
        supabase = get_supabase()
        response = supabase.auth.get_user()
        return response.user
    except Exception:
        return None


def sign_in(email: str, password: str):
    """
    Sign in an existing user with email and password.
    """
    supabase = get_supabase()

    response = supabase.auth.sign_in_with_password(
        {
            "email": email.strip(),
            "password": password,
        }
    )

    return response


def sign_up(email: str, password: str):
    """
    Create a new Supabase account.

    After the user confirms their email address,
    Supabase redirects them back to the deployed
    Yemen Opportunity Navigator application.
    """
    supabase = get_supabase()

    app_url = os.getenv(
        "APP_URL",
        "https://yemen-opportunity-navigator.streamlit.app",
    ).strip()

    response = supabase.auth.sign_up(
        {
            "email": email.strip(),
            "password": password,
            "options": {
                "email_redirect_to": app_url,
            },
        }
    )

    return response


def sign_out():
    """
    Sign the current user out and remove the
    Supabase client from the Streamlit session.
    """
    supabase = get_supabase()

    try:
        supabase.auth.sign_out()
    finally:
        if "supabase_client" in st.session_state:
            del st.session_state["supabase_client"]


def render_auth_sidebar():
    """
    Authentication UI.

    The RAG application remains accessible to guests.
    Registered users can sign in with email/password.
    """

    with st.sidebar:
        st.markdown("## 👤 Account")

        user = get_current_user()

        if user:
            st.success("Signed in")

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

        st.info(
            "You are using Yemen Opportunity Navigator as a guest. "
            "You can create an account or sign in below."
        )

        sign_in_tab, sign_up_tab = st.tabs(
            ["Sign In", "Sign Up"]
        )

        # -------------------------
        # SIGN IN
        # -------------------------
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

                        if "Email not confirmed" in error_message:
                            st.warning(
                                "Please verify your email address first."
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
                                f"Sign in failed: {error_message}"
                            )

        # -------------------------
        # SIGN UP
        # -------------------------
        with sign_up_tab:
            with st.form("signup_form"):
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

                if not register_email:
                    st.error(
                        "Please enter an email address."
                    )

                elif not register_password:
                    st.error(
                        "Please enter a password."
                    )

                elif len(register_password) < 8:
                    st.error(
                        "Password must contain at least 8 characters."
                    )

                elif register_password != confirm_password:
                    st.error(
                        "Passwords do not match."
                    )

                else:
                    try:
                        response = sign_up(
                            register_email,
                            register_password,
                        )

                        if response.session:
                            st.success(
                                "Account created and signed in "
                                "successfully."
                            )
                            st.rerun()

                        elif response.user:
                            st.success(
                                "Account created successfully. "
                                "Check your email and click the "
                                "verification link. After verification, "
                                "you will be redirected back to Yemen "
                                "Opportunity Navigator. Then sign in "
                                "with your email and password."
                            )

                        else:
                            st.warning(
                                "Registration request was submitted."
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
                                "current Supabase email setup."
                            )

                        else:
                            st.error(
                                f"Sign up failed: {error_message}"
                            )

        st.caption(
            "You can continue using the opportunity search "
            "without an account."
        )

        return None