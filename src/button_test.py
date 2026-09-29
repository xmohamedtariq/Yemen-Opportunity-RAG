import streamlit as st


st.set_page_config(
    page_title="Button Test",
    layout="centered",
)


if "page" not in st.session_state:
    st.session_state["page"] = "Home"


st.title("Streamlit Button Test")

st.write(
    "Current page:",
    st.session_state["page"],
)


col1, col2, col3 = st.columns(3)


with col1:
    if st.button(
        "Home",
        use_container_width=True,
    ):
        st.session_state["page"] = "Home"
        st.rerun()


with col2:
    if st.button(
        "Explore",
        use_container_width=True,
    ):
        st.session_state["page"] = "Explore"
        st.rerun()


with col3:
    if st.button(
        "Saved",
        use_container_width=True,
    ):
        st.session_state["page"] = "Saved"
        st.rerun()


if st.button("ASK AI TEST"):
    st.success("BUTTON WORKS ✅")


if st.session_state["page"] == "Home":
    st.info("HOME PAGE")

elif st.session_state["page"] == "Explore":
    st.success("EXPLORE PAGE ✅")

elif st.session_state["page"] == "Saved":
    st.warning("SAVED PAGE ✅")