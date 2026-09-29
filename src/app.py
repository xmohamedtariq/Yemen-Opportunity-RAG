import html
import json
import logging
import re
import textwrap
from pathlib import Path

import streamlit as st

from auth import (
    get_current_user,
    get_supabase,
    sign_in,
    sign_out,
    sign_up,
)

from rag_pipeline import YemenOpportunityRAG


# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="Yemen Opportunity",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)


logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(
    "yemen_opportunity"
)


# ============================================================
# HTML HELPER
# ============================================================

def ui_html(content: str) -> None:

    st.html(
        textwrap.dedent(
            content
        ).strip()
    )


# ============================================================
# GLOBAL DESIGN SYSTEM
# ============================================================

ui_html(
    """
    <style>

    @import url(
    'https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Inter:wght@400;500;600;700;800&display=swap'
    );


    :root {

        --green: #0F7A5A;
        --green-dark: #095D44;
        --green-bright: #23A77A;
        --green-soft: #EAF7F2;

        --ink: #10201A;
        --body: #405048;
        --muted: #718078;

        --bg: #FAFBFA;
        --surface: #FFFFFF;
        --border: #DFE7E3;

        --shadow:
            0 18px 50px
            rgba(16, 55, 40, 0.07);
    }


    html,
    body,
    [class*="css"] {

        font-family:
            "Inter",
            system-ui,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
    }


    .stApp {

        background:

            radial-gradient(
                circle at 88% 0%,
                rgba(15, 122, 90, 0.07),
                transparent 28%
            ),

            var(--bg);

        color:
            var(--ink);
    }


    .block-container {

        max-width:
            1240px;

        padding-top:
            1.35rem !important;

        padding-bottom:
            3.5rem;
    }


    /* ======================================================
       REMOVE STREAMLIT CHROME COMPLETELY
       This also removes the invisible click layer.
    ====================================================== */

    section[data-testid="stSidebar"],
    header[data-testid="stHeader"],
    [data-testid="stAppDeployButton"],
    [data-testid="stToolbar"],
    #MainMenu,
    footer {

        display:
            none !important;
    }


    h1,
    h2,
    h3 {

        color:
            var(--ink);
    }


    p {

        color:
            var(--body);
    }


    /* ======================================================
       BUTTONS
    ====================================================== */

    .stButton > button {

        min-height:
            44px !important;

        border-radius:
            12px !important;

        border:
            1px solid
            #DCE5E1 !important;

        background:
            #FFFFFF !important;

        color:
            #183129 !important;

        font-weight:
            600 !important;

        transition:
            transform 0.12s ease,
            border-color 0.12s ease,
            background 0.12s ease !important;
    }


    .stButton > button:hover {

        transform:
            translateY(-1px);

        border-color:
            #9FC9B7 !important;

        background:
            #F3F9F6 !important;
    }


    .stButton > button[kind="primary"] {

        background:
            var(--green) !important;

        border-color:
            var(--green) !important;

        color:
            #FFFFFF !important;

        box-shadow:
            0 8px 24px
            rgba(15, 122, 90, 0.14);
    }


    .stButton > button[kind="primary"]:hover {

        background:
            var(--green-dark) !important;

        border-color:
            var(--green-dark) !important;
    }


    .stButton > button[kind="primary"] *,
    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span,
    div[data-testid="stFormSubmitButton"]
    button[kind="primary"] *,
    div[data-testid="stFormSubmitButton"]
    button[kind="primary"] p {

        color:
            #FFFFFF !important;
    }


    .stButton > button:focus-visible,
    div[data-testid="stLinkButton"] > a:focus-visible,
    div[data-testid="stTextInput"] input:focus-visible {

        outline:
            3px solid
            rgba(35, 167, 122, 0.28) !important;

        outline-offset:
            2px !important;
    }


    .stButton > button:disabled {

        background:
            #EEF3F0 !important;

        color:
            #7A8981 !important;

        border-color:
            #DFE7E3 !important;

        opacity:
            1 !important;
    }


    /* ======================================================
       OFFICIAL LINK BUTTONS
    ====================================================== */

    div[data-testid="stLinkButton"] > a {

        min-height:
            44px !important;

        display:
            flex !important;

        align-items:
            center !important;

        justify-content:
            center !important;

        border-radius:
            12px !important;

        border:
            1px solid
            #CFE1D9 !important;

        background:
            #FFFFFF !important;

        color:
            #0D6C50 !important;

        font-weight:
            600 !important;

        text-decoration:
            none !important;
    }


    div[data-testid="stLinkButton"] > a:hover {

        background:
            #EFF8F4 !important;

        border-color:
            #9DC8B5 !important;
    }


    /* ======================================================
       INPUTS
    ====================================================== */

    div[data-testid="stTextInput"] input {

        min-height:
            54px !important;

        border-radius:
            13px !important;

        border:
            1px solid
            #DCE5E1 !important;

        background:
            #FFFFFF !important;

        color:
            var(--ink) !important;

        font-size:
            0.96rem !important;
    }


    div[data-testid="stTextInput"] input::placeholder {

        color:
            #89968F !important;

        opacity:
            1 !important;
    }


    div[data-baseweb="select"] > div {

        border-radius:
            12px !important;

        background:
            #FFFFFF !important;
    }


    /* ======================================================
       CONTAINERS
    ====================================================== */

    div[data-testid="stVerticalBlockBorderWrapper"] {

        border:
            1px solid
            var(--border) !important;

        border-radius:
            18px !important;

        background:
            #FFFFFF !important;

        box-shadow:
            0 5px 22px
            rgba(20, 60, 45, 0.025);
    }


    /* ======================================================
       BRAND
    ====================================================== */

    .brand-wrap {

        display:
            flex;

        align-items:
            center;

        gap:
            12px;

        padding:
            4px 0;
    }


    .brand-logo {

        width:
            44px;

        height:
            44px;

        display:
            flex;

        align-items:
            center;

        justify-content:
            center;

        flex:
            0 0 44px;

        border-radius:
            14px;

        background:
            linear-gradient(
                145deg,
                #0F7A5A,
                #28AA7C
            );

        color:
            #FFFFFF;

        font-size:
            20px;

        font-weight:
            800;

        box-shadow:
            0 10px 24px
            rgba(15, 122, 90, 0.16);
    }


    .brand-title {

        color:
            var(--ink);

        font-size:
            1rem;

        font-weight:
            760;

        letter-spacing:
            -0.03em;
    }


    .brand-subtitle {

        color:
            var(--muted);

        font-size:
            0.7rem;

        margin-top:
            2px;
    }


    /* ======================================================
       HERO
    ====================================================== */

    .hero {

        max-width:
            930px;

        margin:
            4.8rem auto
            2.3rem;

        text-align:
            center;
    }


    .hero-badge {

        display:
            inline-block;

        padding:
            7px 14px;

        margin-bottom:
            1.45rem;

        background:
            #EFF9F5;

        border:
            1px solid
            #CFE9DD;

        border-radius:
            999px;

        color:
            #0E7154;

        font-size:
            0.76rem;

        font-weight:
            700;
    }


    .hero h1 {

        margin:
            0;

        color:
            var(--ink);

        font-size:
            clamp(
                3rem,
                6vw,
                5rem
            );

        line-height:
            1;

        font-weight:
            800;

        letter-spacing:
            -0.065em;
    }


    .hero-green {

        color:
            var(--green-bright);
    }


    .hero p {

        max-width:
            720px;

        margin:
            1.55rem auto
            0;

        color:
            var(--muted);

        font-size:
            1.02rem;

        line-height:
            1.8;
    }


    /* ======================================================
       PAGE HEADERS
    ====================================================== */

    .page-header {

        margin:
            3.7rem 0
            2rem;
    }


    .page-header h1 {

        margin:
            0;

        color:
            var(--ink);

        font-size:
            clamp(
                2.2rem,
                5vw,
                3rem
            );

        font-weight:
            780;

        letter-spacing:
            -0.05em;
    }


    .page-header p {

        max-width:
            680px;

        margin-top:
            10px;

        color:
            var(--muted);

        line-height:
            1.75;
    }


    /* ======================================================
       SECTION HEADERS
    ====================================================== */

    .section-head {

        margin:
            4.4rem 0
            1.45rem;
    }


    .section-label {

        color:
            var(--green);

        font-size:
            0.7rem;

        font-weight:
            750;

        letter-spacing:
            0.11em;

        text-transform:
            uppercase;

        margin-bottom:
            8px;
    }


    .section-title {

        color:
            var(--ink);

        font-size:
            clamp(
                1.8rem,
                4vw,
                2.3rem
            );

        font-weight:
            760;

        letter-spacing:
            -0.045em;

        line-height:
            1.15;
    }


    .section-copy {

        max-width:
            680px;

        color:
            var(--muted);

        font-size:
            0.9rem;

        line-height:
            1.7;

        margin-top:
            8px;
    }


    /* ======================================================
       OPPORTUNITY CARD
    ====================================================== */

    .type-chip {

        display:
            inline-block;

        padding:
            5px 9px;

        margin-bottom:
            10px;

        border-radius:
            999px;

        background:
            var(--green-soft);

        color:
            var(--green);

        font-size:
            0.67rem;

        font-weight:
            750;
    }


    .opportunity-name {

        min-height:
            58px;

        color:
            var(--ink);

        font-size:
            1rem;

        font-weight:
            700;

        line-height:
            1.4;
    }


    .opportunity-provider {

        min-height:
            28px;

        margin-top:
            6px;

        color:
            var(--muted);

        font-size:
            0.76rem;
    }


    /* ======================================================
       ANSWERS + CITATIONS
    ====================================================== */

    .answer-card {

        padding:
            1.8rem;

        background:
            #FFFFFF;

        border:
            1px solid
            var(--border);

        border-radius:
            20px;

        box-shadow:
            var(--shadow);

        margin-bottom:
            1.2rem;
    }


    .answer-en,
    .answer-ar {

        color:
            #20312A;

        font-size:
            0.98rem;

        line-height:
            1.9;
    }


    .answer-ar {

        direction:
            rtl;

        text-align:
            right;

        font-family:
            "Amiri",
            serif;

        font-size:
            1.27rem;

        line-height:
            2.02;
    }


    .answer-en p,
    .answer-ar p {

        margin:
            0.2rem 0
            0.8rem;
    }


    .answer-en ul,
    .answer-ar ul {

        margin:
            0.45rem 0
            0.8rem;

        padding-inline-start:
            1.4rem;
    }


    .answer-ar ul {

        padding-inline-start:
            0;

        padding-inline-end:
            1.4rem;
    }


    .source-ref {

        display:
            inline-flex;

        min-width:
            22px;

        height:
            22px;

        align-items:
            center;

        justify-content:
            center;

        padding:
            0 6px;

        margin:
            0 2px;

        border-radius:
            999px;

        background:
            var(--green-soft);

        color:
            var(--green-dark);

        font-size:
            0.72rem;

        font-weight:
            750;

        vertical-align:
            middle;
    }


    .source-index {

        width:
            28px;

        height:
            28px;

        display:
            inline-flex;

        align-items:
            center;

        justify-content:
            center;

        border-radius:
            50%;

        background:
            var(--green-soft);

        color:
            var(--green-dark);

        font-size:
            0.76rem;

        font-weight:
            800;

        margin-bottom:
            0.65rem;
    }


    /* ======================================================
       MARKETING CARDS
    ====================================================== */

    .feature-card {

        min-height:
            175px;

        padding:
            1.35rem;

        border:
            1px solid
            var(--border);

        border-radius:
            18px;

        background:
            #FFFFFF;
    }


    .feature-icon {

        font-size:
            1.35rem;

        margin-bottom:
            0.9rem;
    }


    .feature-title {

        color:
            var(--ink);

        font-weight:
            720;
    }


    .feature-copy {

        color:
            var(--muted);

        font-size:
            0.78rem;

        line-height:
            1.65;

        margin-top:
            0.5rem;
    }


    /* ======================================================
       TRUST
    ====================================================== */

    .trust-strip {

        display:
            grid;

        grid-template-columns:
            repeat(
                3,
                1fr
            );

        gap:
            14px;

        margin-top:
            4.4rem;
    }


    .trust-box {

        padding:
            1.35rem;

        border:
            1px solid
            var(--border);

        border-radius:
            18px;

        background:
            #FFFFFF;
    }


    .trust-value {

        color:
            var(--green);

        font-size:
            1.35rem;

        font-weight:
            780;
    }


    .trust-title {

        margin-top:
            0.35rem;

        color:
            var(--ink);

        font-weight:
            700;
    }


    .trust-copy {

        margin-top:
            0.4rem;

        color:
            var(--muted);

        font-size:
            0.76rem;

        line-height:
            1.6;
    }


    /* ======================================================
       ABOUT
    ====================================================== */

    .about-hero {

        max-width:
            920px;

        margin:
            4.4rem 0
            3.3rem;
    }


    .about-hero h1 {

        color:
            var(--ink);

        font-size:
            clamp(
                2.6rem,
                6vw,
                4.6rem
            );

        line-height:
            1.03;

        font-weight:
            800;

        letter-spacing:
            -0.06em;

        margin:
            0;
    }


    .about-hero p {

        max-width:
            760px;

        color:
            var(--muted);

        font-size:
            1.02rem;

        line-height:
            1.85;

        margin-top:
            1.4rem;
    }


    .founder-card {

        padding:
            2rem;

        border:
            1px solid
            #DDE8E3;

        border-radius:
            22px;

        background:
            linear-gradient(
                145deg,
                #FFFFFF,
                #F4FAF7
            );
    }


    .founder-label {

        color:
            var(--green);

        font-size:
            0.69rem;

        font-weight:
            750;

        letter-spacing:
            0.1em;
    }


    .founder-name {

        margin-top:
            9px;

        color:
            var(--ink);

        font-size:
            1.45rem;

        font-weight:
            760;
    }


    .founder-role {

        margin-top:
            3px;

        color:
            var(--muted);

        font-size:
            0.8rem;
    }


    .founder-text {

        margin-top:
            1.2rem;

        color:
            #4D5E55;

        font-size:
            0.88rem;

        line-height:
            1.75;
    }


    .mission-card {

        margin:
            3.4rem 0;

        padding:
            2.35rem;

        border-radius:
            24px;

        background:
            linear-gradient(
                135deg,
                #0F7A5A,
                #095D44
            );

        color:
            #FFFFFF;
    }


    .mission-label {

        opacity:
            0.76;

        font-size:
            0.68rem;

        font-weight:
            700;

        letter-spacing:
            0.12em;
    }


    .mission-text {

        max-width:
            900px;

        margin-top:
            12px;

        font-size:
            clamp(
                1.35rem,
                3vw,
                1.8rem
            );

        font-weight:
            650;

        line-height:
            1.4;
    }


    /* ======================================================
       FOOTER
    ====================================================== */

    .site-footer {

        margin-top:
            5rem;

        padding:
            2rem 0;

        border-top:
            1px solid
            var(--border);

        color:
            var(--muted);

        font-size:
            0.72rem;

        line-height:
            1.7;
    }


    /* ======================================================
       RESPONSIVE
    ====================================================== */

    @media(max-width:900px) {

        .block-container {

            padding-left:
                1rem;

            padding-right:
                1rem;
        }


        .hero {

            margin-top:
                3.6rem;
        }


        .trust-strip {

            grid-template-columns:
                1fr;
        }
    }


    @media(max-width:768px) {

        .block-container {

            padding-left:
                0.8rem;

            padding-right:
                0.8rem;

            padding-top:
                0.8rem !important;
        }


        .brand-logo {

            width:
                40px;

            height:
                40px;

            flex-basis:
                40px;

            border-radius:
                12px;
        }


        .brand-title {

            font-size:
                0.92rem;
        }


        .brand-subtitle {

            font-size:
                0.64rem;
        }


        .hero {

            margin-top:
                2.6rem;

            margin-bottom:
                1.8rem;
        }


        .hero h1 {

            font-size:
                3rem;

            letter-spacing:
                -0.055em;
        }


        .hero p {

            font-size:
                0.93rem;

            line-height:
                1.7;
        }


        .page-header {

            margin-top:
                2.6rem;
        }


        .section-head {

            margin-top:
                3.3rem;
        }


        .answer-card {

            padding:
                1.2rem;
        }


        .mission-card {

            padding:
                1.65rem;
        }


        .about-hero {

            margin-top:
                2.8rem;
        }


        .feature-card {

            min-height:
                auto;
        }
    }


    @media(max-width:480px) {

        .hero h1 {

            font-size:
                2.42rem;
        }


        .about-hero h1 {

            font-size:
                2.32rem;
        }


        .mission-text {

            font-size:
                1.22rem;
        }
    }

    </style>
    """
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {

    "page":
        "Home",

    "hero_query":
        "",

    "explore_query":
        "",

    "pending_ai_query":
        None,

    "last_result":
        None,

    "favorites":
        [],

    "history":
        [],

    "saved_toast":
        False,

    "_loaded_user_id":
        None,

    "_cloud_storage_ok":
        True,
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# GENERAL HELPERS
# ============================================================

def valid_url(value) -> bool:

    return (
        bool(
            value
        )
        and
        str(
            value
        )
        .strip()
        .startswith(
            (
                "https://",
                "http://",
            )
        )
    )


# ============================================================
# CITATION CLEANUP
# ============================================================

def normalize_citations(
    text: str,
) -> str:

    """
    Converts internal citations such as:
    [S1]
    [S1, S2]
    [S2, S4]

    into public citations:
    [1]
    [1, 2]
    [2, 4]
    """

    if not text:

        return ""


    def replace_citation(
        match,
    ):

        numbers = re.findall(
            r"S?(\d+)",
            match.group(
                1
            ),
            flags=re.IGNORECASE,
        )


        if not numbers:

            return match.group(
                0
            )


        return (
            "["
            +
            ", ".join(
                numbers
            )
            +
            "]"
        )


    return re.sub(
        r"\[([^\]]*S\d+[^\]]*)\]",
        replace_citation,
        text,
        flags=re.IGNORECASE,
    )


def inline_answer_html(
    text: str,
) -> str:

    escaped = (
        html.escape(
            text
        )
    )


    return re.sub(
        r"\[(\d+(?:\s*,\s*\d+)*)\]",
        lambda match:
        " ".join(
            (
                f'<span class="source-ref">'
                f'{number.strip()}'
                f'</span>'
            )

            for number
            in
            match.group(
                1
            ).split(
                ","
            )
        ),
        escaped,
    )


def answer_to_html(
    text: str,
    language: str,
) -> str:

    lines = (
        normalize_citations(
            text
        )
        .splitlines()
    )


    output = []

    in_list = False


    def close_list():

        nonlocal in_list


        if in_list:

            output.append(
                "</ul>"
            )

            in_list = False


    for raw_line in lines:

        line = (
            raw_line
            .strip()
        )


        if not line:

            close_list()

            continue


        if line.startswith(
            (
                "- ",
                "• ",
            )
        ):

            if not in_list:

                output.append(
                    "<ul>"
                )

                in_list = True


            output.append(
                "<li>"
                +
                inline_answer_html(
                    line[2:]
                    .strip()
                )
                +
                "</li>"
            )


        else:

            close_list()


            output.append(
                "<p>"
                +
                inline_answer_html(
                    line
                )
                +
                "</p>"
            )


    close_list()


    css_class = (
        "answer-ar"
        if
        language
        ==
        "ar"
        else
        "answer-en"
    )


    return (
        f'<div class="answer-card">'
        f'<div class="{css_class}">'
        +
        "".join(
            output
        )
        +
        "</div>"
        "</div>"
    )


# ============================================================
# RAG
# ============================================================

@st.cache_resource(
    show_spinner=False
)
def load_rag():

    return (
        YemenOpportunityRAG()
    )


# ============================================================
# LOAD OPPORTUNITY DATA
# ============================================================

def collect_chunk_records(
    value,
):

    records = []


    if isinstance(
        value,
        list,
    ):

        for item in value:

            records.extend(
                collect_chunk_records(
                    item
                )
            )


    elif isinstance(
        value,
        dict,
    ):

        if (
            value.get(
                "source_id"
            )
            and
            value.get(
                "chunk_id"
            )
        ):

            records.append(
                value
            )


        else:

            for child in value.values():

                if isinstance(
                    child,
                    (
                        dict,
                        list,
                    ),
                ):

                    records.extend(
                        collect_chunk_records(
                            child
                        )
                    )


    return records


@st.cache_data(
    show_spinner=False
)
def load_catalog():

    data_dir = (
        Path(__file__)
        .resolve()
        .parents[1]
        /
        "data"
    )


    chunks = []


    if data_dir.exists():

        for file_path in data_dir.rglob(
            "*.json"
        ):

            if (
                file_path.name
                ==
                "opportunity_catalog.json"
            ):

                continue


            try:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8",
                ) as file:

                    chunks.extend(
                        collect_chunk_records(
                            json.load(
                                file
                            )
                        )
                    )


            except Exception:

                continue


    grouped = {}


    for chunk in chunks:

        source_id = (
            chunk.get(
                "source_id"
            )
        )


        if not source_id:

            continue


        grouped.setdefault(
            source_id,
            {
                "source_id":
                    source_id,

                "title":
                    chunk.get(
                        "title",
                        "Opportunity",
                    ),

                "provider":
                    chunk.get(
                        "provider",
                        "",
                    ),

                "category":
                    chunk.get(
                        "category",
                        "Opportunity",
                    ),

                "url":
                    chunk.get(
                        "url",
                        "",
                    ),

                "country":
                    chunk.get(
                        "country",
                        "",
                    ),

                "funding":
                    chunk.get(
                        "funding",
                        "",
                    ),

                "deadline":
                    chunk.get(
                        "deadline",
                        "",
                    ),

                "eligibility":
                    chunk.get(
                        "eligibility",
                        "",
                    ),

                "_text":
                    [],
            },
        )


        if chunk.get(
            "text"
        ):

            grouped[
                source_id
            ][
                "_text"
            ].append(
                chunk[
                    "text"
                ]
            )


    structured_path = (
        data_dir
        /
        "opportunity_catalog.json"
    )


    if structured_path.exists():

        try:

            with open(
                structured_path,
                "r",
                encoding="utf-8",
            ) as file:

                structured = (
                    json.load(
                        file
                    )
                )


            if isinstance(
                structured,
                dict,
            ):

                structured = (
                    structured.get(
                        "opportunities",
                        [],
                    )
                )


            if isinstance(
                structured,
                list,
            ):

                for item in structured:

                    source_id = (
                        item.get(
                            "source_id"
                        )
                    )


                    if not source_id:

                        continue


                    grouped.setdefault(
                        source_id,
                        {
                            "source_id":
                                source_id,

                            "title":
                                item.get(
                                    "title",
                                    "Opportunity",
                                ),

                            "provider":
                                item.get(
                                    "provider",
                                    "",
                                ),

                            "category":
                                item.get(
                                    "category",
                                    "Opportunity",
                                ),

                            "url":
                                item.get(
                                    "url",
                                    "",
                                ),

                            "country":
                                "",

                            "funding":
                                "",

                            "deadline":
                                "",

                            "eligibility":
                                "",

                            "_text":
                                [],
                        },
                    )


                    for field in (
                        "title",
                        "provider",
                        "category",
                        "url",
                        "country",
                        "funding",
                        "deadline",
                        "eligibility",
                    ):

                        if item.get(
                            field
                        ):

                            grouped[
                                source_id
                            ][
                                field
                            ] = item[
                                field
                            ]


        except Exception:

            logger.exception(
                "Could not read opportunity catalog."
            )


    opportunities = []


    for item in grouped.values():

        item[
            "_search"
        ] = (
            " ".join(
                [
                    item.get(
                        "title",
                        "",
                    ),

                    item.get(
                        "provider",
                        "",
                    ),

                    item.get(
                        "category",
                        "",
                    ),

                    item.get(
                        "country",
                        "",
                    ),

                    item.get(
                        "funding",
                        "",
                    ),

                    item.get(
                        "eligibility",
                        "",
                    ),

                    " ".join(
                        item.get(
                            "_text",
                            [],
                        )
                    ),
                ]
            )
            .lower()
        )


        item.pop(
            "_text",
            None,
        )


        opportunities.append(
            item
        )


    return sorted(
        opportunities,
        key=lambda item:
        (
            item.get(
                "title"
            )
            or
            ""
        ).lower(),
    )
# ============================================================
# SUPABASE ACCOUNT STORAGE
# ============================================================

def current_uid():

    user = (
        st.session_state.get(
            "_current_user"
        )
    )


    return str(
        getattr(
            user,
            "id",
            "",
        )
        or
        ""
    )


def load_account_data(
    user,
) -> None:

    user_id = str(
        getattr(
            user,
            "id",
            "",
        )
        or
        ""
    )


    if not user_id:

        return


    if (
        st.session_state.get(
            "_loaded_user_id"
        )
        ==
        user_id
    ):

        return


    try:

        client = (
            get_supabase()
        )


        favorites_response = (
            client
            .table(
                "favorites"
            )
            .select(
                "source_id,title,provider,"
                "category,url,country,"
                "funding,deadline"
            )
            .eq(
                "user_id",
                user_id,
            )
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )


        history_response = (
            client
            .table(
                "search_history"
            )
            .select(
                "query,answer,language,sources"
            )
            .eq(
                "user_id",
                user_id,
            )
            .order(
                "created_at",
                desc=True,
            )
            .limit(
                30
            )
            .execute()
        )


        st.session_state[
            "favorites"
        ] = list(
            favorites_response.data
            or
            []
        )


        st.session_state[
            "history"
        ] = list(
            history_response.data
            or
            []
        )


        st.session_state[
            "_cloud_storage_ok"
        ] = True


    except Exception:

        logger.exception(
            "Could not load account data."
        )


        st.session_state[
            "_cloud_storage_ok"
        ] = False


    finally:

        st.session_state[
            "_loaded_user_id"
        ] = user_id


def persist_favorite(
    item: dict,
) -> None:

    user_id = (
        current_uid()
    )


    if not user_id:

        return


    payload = {

        "user_id":
            user_id,

        "source_id":
            item.get(
                "source_id"
            ),

        "title":
            item.get(
                "title"
            ),

        "provider":
            item.get(
                "provider"
            ),

        "category":
            item.get(
                "category"
            ),

        "url":
            item.get(
                "url"
            ),

        "country":
            item.get(
                "country"
            ),

        "funding":
            item.get(
                "funding"
            ),

        "deadline":
            item.get(
                "deadline"
            ),
    }


    try:

        (
            get_supabase()
            .table(
                "favorites"
            )
            .upsert(
                payload,
                on_conflict=(
                    "user_id,source_id"
                ),
            )
            .execute()
        )


    except Exception:

        logger.exception(
            "Could not persist favorite."
        )


        st.session_state[
            "_cloud_storage_ok"
        ] = False


def delete_persisted_favorite(
    source_id: str,
) -> None:

    user_id = (
        current_uid()
    )


    if not user_id:

        return


    try:

        (
            get_supabase()
            .table(
                "favorites"
            )
            .delete()
            .eq(
                "user_id",
                user_id,
            )
            .eq(
                "source_id",
                source_id,
            )
            .execute()
        )


    except Exception:

        logger.exception(
            "Could not delete favorite."
        )


def persist_history(
    item: dict,
) -> None:

    user_id = (
        current_uid()
    )


    if not user_id:

        return


    try:

        (
            get_supabase()
            .table(
                "search_history"
            )
            .insert(
                {
                    "user_id":
                        user_id,

                    "query":
                        item.get(
                            "query"
                        ),

                    "answer":
                        item.get(
                            "answer"
                        ),

                    "language":
                        item.get(
                            "language"
                        ),

                    "sources":
                        item.get(
                            "sources"
                        )
                        or
                        [],
                }
            )
            .execute()
        )


    except Exception:

        logger.exception(
            "Could not persist history."
        )


def clear_persisted_history():

    user_id = (
        current_uid()
    )


    if not user_id:

        return


    try:

        (
            get_supabase()
            .table(
                "search_history"
            )
            .delete()
            .eq(
                "user_id",
                user_id,
            )
            .execute()
        )


    except Exception:

        logger.exception(
            "Could not clear history."
        )


# ============================================================
# AUTH DIALOGS
# ============================================================

@st.dialog(
    "Sign in",
    width="small",
)
def sign_in_dialog():

    st.markdown(
        "### Welcome back"
    )


    st.caption(
        "Sign in to continue to Yemen Opportunity."
    )


    with st.form(
        "signin_form"
    ):

        email = (
            st.text_input(
                "Email",
                placeholder="you@example.com",
            )
        )


        password = (
            st.text_input(
                "Password",
                type="password",
            )
        )


        submitted = (
            st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True,
            )
        )


    if not submitted:

        return


    if (
        not email
        or
        not password
    ):

        st.error(
            "Enter your email and password."
        )

        return


    try:

        response = (
            sign_in(
                email,
                password,
            )
        )


        if response.user:

            st.rerun()


        st.error(
            "Unable to sign in."
        )


    except Exception as exc:

        message = str(
            exc
        )


        if (
            "Invalid login credentials"
            in message
        ):

            st.error(
                "Incorrect email or password."
            )


        elif (
            "Email not confirmed"
            in message
        ):

            st.warning(
                "Verify your email before signing in."
            )


        else:

            logger.exception(
                "Sign in failed."
            )


            st.error(
                "Sign in failed. Please try again."
            )


@st.dialog(
    "Create account",
    width="small",
)
def sign_up_dialog():

    st.markdown(
        "### Join Yemen Opportunity"
    )


    st.caption(
        "Create a free account to keep "
        "your saved opportunities and history."
    )


    with st.form(
        "signup_form"
    ):

        email = (
            st.text_input(
                "Email",
                placeholder="you@example.com",
            )
        )


        password = (
            st.text_input(
                "Password",
                type="password",
            )
        )


        confirmation = (
            st.text_input(
                "Confirm password",
                type="password",
            )
        )


        submitted = (
            st.form_submit_button(
                "Create account",
                type="primary",
                use_container_width=True,
            )
        )


    if not submitted:

        return


    if not email:

        st.error(
            "Enter your email."
        )

        return


    if len(
        password
    ) < 8:

        st.error(
            "Password must contain "
            "at least 8 characters."
        )

        return


    if (
        password
        !=
        confirmation
    ):

        st.error(
            "Passwords do not match."
        )

        return


    try:

        response = (
            sign_up(
                email,
                password,
            )
        )


        if response.session:

            st.success(
                "Account created successfully."
            )

            st.rerun()


        elif response.user:

            st.success(
                "Account created. "
                "Check your email to verify "
                "your address, then sign in."
            )


        else:

            st.info(
                "Registration submitted."
            )


    except Exception as exc:

        if (
            "already registered"
            in
            str(
                exc
            )
            .lower()
        ):

            st.warning(
                "An account with this email "
                "already exists."
            )


        else:

            logger.exception(
                "Sign up failed."
            )


            st.error(
                "Account creation failed. "
                "Please try again."
            )


# ============================================================
# CURRENT USER
# ============================================================

try:

    current_user = (
        get_current_user()
    )


except Exception:

    logger.exception(
        "Could not load current user."
    )


    current_user = None


st.session_state[
    "_current_user"
] = current_user


if current_user:

    load_account_data(
        current_user
    )


else:

    st.session_state[
        "_loaded_user_id"
    ] = None


if st.session_state.pop(
    "saved_toast",
    False,
):

    st.toast(
        "Opportunity saved ✓"
    )


# ============================================================
# HEADER
# ============================================================

brand_col, account_col = (
    st.columns(
        [
            3,
            2,
        ],
        vertical_alignment="center",
    )
)


with brand_col:

    ui_html(
        """
        <div class="brand-wrap">

            <div class="brand-logo">
                Y
            </div>

            <div>

                <div class="brand-title">
                    Yemen Opportunity
                </div>

                <div class="brand-subtitle">
                    Global opportunities. Clearer access.
                </div>

            </div>

        </div>
        """
    )


with account_col:

    if current_user:

        user_col, logout_col = (
            st.columns(
                [
                    1.8,
                    1,
                ]
            )
        )


        with user_col:

            st.caption(
                getattr(
                    current_user,
                    "email",
                    None,
                )
                or
                "Signed in"
            )


        with logout_col:

            if st.button(
                "Log out",
                key="top_logout",
                use_container_width=True,
            ):

                sign_out()


                st.session_state[
                    "favorites"
                ] = []


                st.session_state[
                    "history"
                ] = []


                st.session_state[
                    "last_result"
                ] = None


                st.session_state[
                    "_loaded_user_id"
                ] = None


                st.rerun()


    else:

        signin_col, signup_col = (
            st.columns(
                2
            )
        )


        with signin_col:

            if st.button(
                "Sign in",
                key="top_signin",
                use_container_width=True,
            ):

                sign_in_dialog()


        with signup_col:

            if st.button(
                "Join free",
                key="top_signup",
                type="primary",
                use_container_width=True,
            ):

                sign_up_dialog()


# ============================================================
# NAVIGATION
# ============================================================

nav_columns = (
    st.columns(
        5
    )
)


navigation = (
    "Home",
    "Explore",
    "Saved",
    "History",
    "About",
)


for index, page_name in enumerate(
    navigation
):

    with nav_columns[
        index
    ]:

        active = (
            st.session_state[
                "page"
            ]
            ==
            page_name
        )


        if st.button(
            page_name,
            key=f"nav_{page_name}",
            type=(
                "primary"
                if
                active
                else
                "secondary"
            ),
            use_container_width=True,
        ):

            st.session_state[
                "page"
            ] = page_name


            st.rerun()


# ============================================================
# RAG SEARCH
# ============================================================

def run_search(
    query: str,
) -> None:

    query = (
        str(
            query
        )
        .strip()
    )


    if not query:

        st.warning(
            "Enter a question first. "
            "/ الرجاء كتابة سؤال."
        )

        return


    try:

        with st.spinner(
            "Searching trusted sources..."
        ):

            result = (
                load_rag()
                .ask(
                    query
                )
            )


        st.session_state[
            "last_result"
        ] = result


        history_item = {

            "query":
                query,

            "answer":
                result.get(
                    "answer",
                    "",
                ),

            "language":
                result.get(
                    "language",
                    "en",
                ),

            "sources":
                result.get(
                    "sources",
                    [],
                ),
        }


        st.session_state[
            "history"
        ].insert(
            0,
            history_item,
        )


        st.session_state[
            "history"
        ] = (
            st.session_state[
                "history"
            ][
                :30
            ]
        )


        if current_user:

            persist_history(
                history_item
            )


    except Exception:

        logger.exception(
            "RAG search failed."
        )


        st.error(
            "We couldn't complete this search "
            "right now. Please try again in a moment."
        )


# ============================================================
# SOURCES
# ============================================================

def render_sources(
    sources,
) -> None:

    sources = [
        source

        for source
        in
        (
            sources
            or
            []
        )

        if isinstance(
            source,
            dict,
        )
    ]


    if not sources:

        return


    st.subheader(
        "Sources"
    )


    st.caption(
        "Always confirm deadlines, eligibility "
        "and application requirements on the "
        "official provider website."
    )


    for index, source in enumerate(
        sources,
        start=1,
    ):

        with st.container(
            border=True
        ):

            left, right = (
                st.columns(
                    [
                        4,
                        1.3,
                    ],
                    vertical_alignment="center",
                )
            )


            with left:

                ui_html(
                    f"""
                    <div class="source-index">
                        {index}
                    </div>
                    """
                )


                st.markdown(
                    f"**{source.get('title') or 'Official source'}**"
                )


                if source.get(
                    "provider"
                ):

                    st.caption(
                        source[
                            "provider"
                        ]
                    )


            with right:

                url = (
                    source.get(
                        "url"
                    )
                    or
                    ""
                )


                if valid_url(
                    url
                ):

                    st.link_button(
                        "Open source ↗",
                        url,
                        use_container_width=True,
                    )


# ============================================================
# ANSWER
# ============================================================

def render_answer() -> None:

    result = (
        st.session_state.get(
            "last_result"
        )
    )


    if not result:

        return


    ui_html(
        """
        <div class="section-head">

            <div class="section-label">
                ANSWER
            </div>

            <div class="section-title">
                What we found
            </div>

            <div class="section-copy">
                A clear response grounded in information
                retrieved from trusted sources.
            </div>

        </div>
        """
    )


    ui_html(
        answer_to_html(
            result.get(
                "answer",
                "",
            ),

            result.get(
                "language",
                "en",
            ),
        )
    )


    render_sources(
        result.get(
            "sources",
            [],
        )
    )
    # ============================================================
# OPPORTUNITY CARD
# ============================================================

def render_opportunity_card(
    opportunity,
    key_prefix: str,
) -> None:

    source_id = (
        opportunity.get(
            "source_id"
        )
        or
        key_prefix
    )


    title = (
        opportunity.get(
            "title"
        )
        or
        "Opportunity"
    )


    provider = (
        opportunity.get(
            "provider"
        )
        or
        ""
    )


    category = (
        opportunity.get(
            "category"
        )
        or
        "Opportunity"
    )


    url = (
        opportunity.get(
            "url"
        )
        or
        ""
    )


    country = (
        opportunity.get(
            "country"
        )
        or
        ""
    )


    funding = (
        opportunity.get(
            "funding"
        )
        or
        ""
    )


    deadline = (
        opportunity.get(
            "deadline"
        )
        or
        ""
    )


    with st.container(
        border=True
    ):

        ui_html(
            f"""
            <div class="type-chip">
                {html.escape(str(category))}
            </div>

            <div class="opportunity-name">
                {html.escape(str(title))}
            </div>

            <div class="opportunity-provider">
                {html.escape(str(provider))}
            </div>
            """
        )


        metadata = []


        if country:

            metadata.append(
                f"📍 {country}"
            )


        if funding:

            metadata.append(
                f"💰 {funding}"
            )


        if deadline:

            metadata.append(
                f"🗓️ {deadline}"
            )


        if metadata:

            st.caption(
                " · ".join(
                    metadata
                )
            )


        website_col, save_col = (
            st.columns(
                2
            )
        )


        with website_col:

            if valid_url(
                url
            ):

                st.link_button(
                    "Official site ↗",
                    url,
                    use_container_width=True,
                )


            else:

                st.button(
                    "Link unavailable",
                    key=(
                        f"{key_prefix}_"
                        f"nolink_"
                        f"{source_id}"
                    ),
                    disabled=True,
                    use_container_width=True,
                )


        already_saved = any(
            item.get(
                "source_id"
            )
            ==
            source_id

            for item
            in
            st.session_state[
                "favorites"
            ]
        )


        with save_col:

            if already_saved:

                st.button(
                    "★ Saved",
                    key=(
                        f"{key_prefix}_"
                        f"saved_"
                        f"{source_id}"
                    ),
                    disabled=True,
                    use_container_width=True,
                )


            elif st.button(
                "☆ Save",
                key=(
                    f"{key_prefix}_"
                    f"save_"
                    f"{source_id}"
                ),
                use_container_width=True,
            ):

                favorite = {

                    "source_id":
                        source_id,

                    "title":
                        title,

                    "provider":
                        provider,

                    "category":
                        category,

                    "url":
                        url,

                    "country":
                        country,

                    "funding":
                        funding,

                    "deadline":
                        deadline,
                }


                st.session_state[
                    "favorites"
                ].append(
                    favorite
                )


                if current_user:

                    persist_favorite(
                        favorite
                    )


                st.session_state[
                    "saved_toast"
                ] = True


                st.rerun()


        if st.button(
            "Ask about this opportunity →",
            key=(
                f"{key_prefix}_"
                f"ask_"
                f"{source_id}"
            ),
            type="primary",
            use_container_width=True,
        ):

            st.session_state[
                "pending_ai_query"
            ] = (
                f"Tell me about {title}. "
                "Explain eligibility, benefits, requirements, "
                "application process, deadlines if available, "
                "and important details. "
                "Use only the indexed official sources."
            )


            st.session_state[
                "page"
            ] = "Home"


            st.rerun()


# ============================================================
# HOME PAGE
# ============================================================

def render_home() -> None:

    ui_html(
        """
        <div class="hero">

            <div class="hero-badge">
                ✦ Global opportunities, made accessible from Yemen
            </div>

            <h1>

                Find the opportunity

                <br>

                that moves you

                <span class="hero-green">
                    forward.
                </span>

            </h1>

            <p>

                Discover scholarships, internships,
                fellowships, competitions and professional
                programs from trusted organizations
                around the world.

                Search naturally in Arabic or English.

            </p>

        </div>
        """
    )


    with st.form(
        "main_search_form"
    ):

        query = (
            st.text_input(
                "Search",
                key="hero_query",
                label_visibility="collapsed",
                placeholder=(
                    "Search opportunities "
                    "or ask a question..."
                ),
            )
        )


        submitted = (
            st.form_submit_button(
                "Search opportunities →",
                type="primary",
                use_container_width=True,
            )
        )


    if submitted:

        run_search(
            query
        )


    st.caption(
        "Try: Google Summer of Code eligibility · "
        "UNICEF internships · منح ممولة بالكامل"
    )


    render_answer()


    # --------------------------------------------------------
    # CATEGORIES
    # --------------------------------------------------------

    ui_html(
        """
        <div class="section-head">

            <div class="section-label">
                DISCOVER
            </div>

            <div class="section-title">
                Explore by opportunity type
            </div>

            <div class="section-copy">
                Start with the path that fits
                where you want to go next.
            </div>

        </div>
        """
    )


    categories = (

        (
            "🎓 Scholarships",
            "Scholarship",
        ),

        (
            "💼 Internships",
            "Internship",
        ),

        (
            "🌍 Fellowships",
            "Fellowship",
        ),

        (
            "🚀 Accelerators",
            "Accelerator",
        ),

        (
            "🏆 Competitions",
            "Competition",
        ),

        (
            "💡 Training",
            "Training",
        ),
    )


    columns = (
        st.columns(
            3
        )
    )


    for index, (
        label,
        search_term,
    ) in enumerate(
        categories
    ):

        with columns[
            index % 3
        ]:

            if st.button(
                label,
                key=f"category_{index}",
                use_container_width=True,
            ):

                st.session_state[
                    "explore_query"
                ] = search_term


                st.session_state[
                    "page"
                ] = "Explore"


                st.rerun()


    # --------------------------------------------------------
    # FEATURED
    # --------------------------------------------------------

    catalog = (
        load_catalog()
    )


    preferred_ids = (

        "OPP-001",

        "OPP-002",

        "OPP-025",

        "OPP-042",

        "OPP-046",

        "OPP-048",
    )


    featured = [

        item

        for source_id
        in preferred_ids

        for item
        in catalog

        if item.get(
            "source_id"
        )
        ==
        source_id
    ]


    if len(
        featured
    ) < 6:

        used = {
            item.get(
                "source_id"
            )

            for item
            in featured
        }


        for item in catalog:

            if (
                item.get(
                    "source_id"
                )
                not in
                used
            ):

                featured.append(
                    item
                )


            if len(
                featured
            ) >= 6:

                break


    if featured:

        ui_html(
            """
            <div class="section-head">

                <div class="section-label">
                    FEATURED
                </div>

                <div class="section-title">
                    Opportunities worth exploring
                </div>

                <div class="section-copy">
                    A curated starting point
                    from trusted official providers.
                </div>

            </div>
            """
        )


        columns = (
            st.columns(
                3
            )
        )


        for index, opportunity in enumerate(
            featured[
                :6
            ]
        ):

            with columns[
                index % 3
            ]:

                render_opportunity_card(
                    opportunity,
                    f"featured_{index}",
                )


    # --------------------------------------------------------
    # TRUST
    # --------------------------------------------------------

    ui_html(
        f"""
        <div class="trust-strip">

            <div class="trust-box">

                <div class="trust-value">
                    {len(catalog)}
                </div>

                <div class="trust-title">
                    Trusted sources
                </div>

                <div class="trust-copy">
                    Official program and organization
                    sources brought into one discovery
                    experience.
                </div>

            </div>


            <div class="trust-box">

                <div class="trust-value">
                    AR + EN
                </div>

                <div class="trust-title">
                    Bilingual discovery
                </div>

                <div class="trust-copy">
                    Search naturally in Arabic
                    or English.
                </div>

            </div>


            <div class="trust-box">

                <div class="trust-value">
                    Official
                </div>

                <div class="trust-title">
                    Source verification
                </div>

                <div class="trust-copy">
                    Critical information stays connected
                    to the official provider.
                </div>

            </div>

        </div>
        """
    )


# ============================================================
# EXPLORE PAGE
# ============================================================

def render_explore() -> None:

    ui_html(
        """
        <div class="page-header">

            <h1>
                Explore opportunities
            </h1>

            <p>
                Browse trusted scholarships,
                internships, fellowships,
                competitions and professional programs.
            </p>

        </div>
        """
    )


    catalog = (
        load_catalog()
    )


    if not catalog:

        st.info(
            "No opportunities are available right now."
        )

        return


    search_query = (
        st.text_input(
            "Search opportunities",
            key="explore_query",
            placeholder=(
                "Search by title, provider, "
                "type or keyword..."
            ),
        )
    )


    categories = sorted(
        {
            item.get(
                "category"
            )

            for item
            in catalog

            if item.get(
                "category"
            )
        }
    )


    providers = sorted(
        {
            item.get(
                "provider"
            )

            for item
            in catalog

            if item.get(
                "provider"
            )
        }
    )


    filter_a, filter_b = (
        st.columns(
            2
        )
    )


    with filter_a:

        selected_categories = (
            st.multiselect(
                "Opportunity type",
                categories,
            )
        )


    with filter_b:

        selected_provider = (
            st.selectbox(
                "Provider",
                [
                    "All providers"
                ]
                +
                providers,
            )
        )


    normalized_query = (
        search_query
        .strip()
        .lower()
    )


    filtered = []


    for item in catalog:

        if (
            normalized_query
            and
            normalized_query
            not in
            item.get(
                "_search",
                "",
            )
        ):

            continue


        if (
            selected_categories
            and
            item.get(
                "category"
            )
            not in
            selected_categories
        ):

            continue


        if (
            selected_provider
            !=
            "All providers"
            and
            item.get(
                "provider"
            )
            !=
            selected_provider
        ):

            continue


        filtered.append(
            item
        )


    st.subheader(
        f"{len(filtered)} opportunities"
    )


    st.caption(
        f"Browsing {len(catalog)} trusted sources."
    )


    if not filtered:

        st.info(
            "No opportunities match "
            "your current filters."
        )

        return


    columns = (
        st.columns(
            3
        )
    )


    for index, opportunity in enumerate(
        filtered
    ):

        with columns[
            index % 3
        ]:

            render_opportunity_card(
                opportunity,
                f"explore_{index}",
            )


# ============================================================
# SAVED PAGE
# ============================================================

def render_saved() -> None:

    ui_html(
        """
        <div class="page-header">

            <h1>
                Saved opportunities
            </h1>

            <p>
                Keep promising opportunities together
                and return to them when you are ready.
            </p>

        </div>
        """
    )


    favorites = (
        st.session_state[
            "favorites"
        ]
    )


    if not favorites:

        st.info(
            "You haven't saved any opportunities yet."
        )


        if st.button(
            "Explore opportunities →",
            key="saved_explore",
            type="primary",
        ):

            st.session_state[
                "page"
            ] = "Explore"


            st.rerun()


        return


    for index, opportunity in enumerate(
        favorites
    ):

        with st.container(
            border=True
        ):

            st.markdown(
                f"### {opportunity.get('title') or 'Opportunity'}"
            )


            if opportunity.get(
                "provider"
            ):

                st.caption(
                    opportunity[
                        "provider"
                    ]
                )


            site_col, ask_col, remove_col = (
                st.columns(
                    [
                        1.3,
                        1.3,
                        1,
                    ]
                )
            )


            with site_col:

                url = (
                    opportunity.get(
                        "url"
                    )
                    or
                    ""
                )


                if valid_url(
                    url
                ):

                    st.link_button(
                        "Official site ↗",
                        url,
                        use_container_width=True,
                    )


            with ask_col:

                if st.button(
                    "Ask about it →",
                    key=f"saved_ai_{index}",
                    type="primary",
                    use_container_width=True,
                ):

                    title = (
                        opportunity.get(
                            "title"
                        )
                        or
                        "this opportunity"
                    )


                    st.session_state[
                        "pending_ai_query"
                    ] = (
                        f"Tell me about {title}. "
                        "Explain eligibility, benefits, requirements, "
                        "application process and deadlines if available. "
                        "Use only indexed official sources."
                    )


                    st.session_state[
                        "page"
                    ] = "Home"


                    st.rerun()


            with remove_col:

                if st.button(
                    "Remove",
                    key=f"saved_remove_{index}",
                    use_container_width=True,
                ):

                    removed = (
                        st.session_state[
                            "favorites"
                        ]
                        .pop(
                            index
                        )
                    )


                    if current_user:

                        delete_persisted_favorite(
                            removed.get(
                                "source_id",
                                "",
                            )
                        )


                    st.rerun()


    if not current_user:

        st.caption(
            "Guest saves are kept for this browser session. "
            "Sign in to keep them across sessions."
        )


# ============================================================
# HISTORY PAGE
# ============================================================

def render_history() -> None:

    ui_html(
        """
        <div class="page-header">

            <h1>
                Search history
            </h1>

            <p>
                Revisit recent questions and continue
                your discovery journey.
            </p>

        </div>
        """
    )


    history = (
        st.session_state[
            "history"
        ]
    )


    if not history:

        st.info(
            "Your search history is empty."
        )

        return


    left, right = (
        st.columns(
            [
                4,
                1,
            ]
        )
    )


    with left:

        st.caption(
            f"{len(history)} recent searches"
        )


    with right:

        if st.button(
            "Clear history",
            key="clear_history",
            use_container_width=True,
        ):

            st.session_state[
                "history"
            ] = []


            st.session_state[
                "last_result"
            ] = None


            if current_user:

                clear_persisted_history()


            st.rerun()


    for index, item in enumerate(
        history
    ):

        with st.container(
            border=True
        ):

            query = (
                item.get(
                    "query"
                )
                or
                ""
            )


            answer = (
                normalize_citations(
                    item.get(
                        "answer"
                    )
                    or
                    ""
                )
            )


            st.markdown(
                f"### {query}"
            )


            preview = (
                answer[
                    :420
                ]
                +
                "..."

                if len(
                    answer
                ) > 420

                else
                answer
            )


            if (
                item.get(
                    "language"
                )
                ==
                "ar"
            ):

                ui_html(
                    answer_to_html(
                        preview,
                        "ar",
                    )
                )


            else:

                st.write(
                    preview
                )


            if st.button(
                "Ask again →",
                key=f"history_again_{index}",
                type="primary",
            ):

                st.session_state[
                    "pending_ai_query"
                ] = query


                st.session_state[
                    "page"
                ] = "Home"


                st.rerun()
                # ============================================================
# ABOUT PAGE
# ============================================================

def render_about() -> None:

    ui_html(
        """
        <div class="about-hero">

            <div class="section-label">
                ABOUT YEMEN OPPORTUNITY
            </div>

            <h1>
                Opportunity should not depend
                on knowing where to look.
            </h1>

            <p>

                Yemen Opportunity is a bilingual
                opportunity-discovery platform built
                to help young people in Yemen find,
                understand and act on trusted
                opportunities from around the world.

            </p>

        </div>
        """
    )


    story_col, founder_col = (
        st.columns(
            [
                1.5,
                1,
            ]
        )
    )


    # --------------------------------------------------------
    # STORY
    # --------------------------------------------------------

    with story_col:

        st.markdown(
            textwrap.dedent(
                """
                ### Why Yemen Opportunity exists

                Global opportunities are published across
                universities, governments, international
                organizations, foundations and technology
                companies.

                The information is valuable, but often
                fragmented across many websites and
                application pages.

                For a young person trying to move forward,
                the hardest part can be knowing **where to
                search, what matters, and whether an
                opportunity is relevant**.

                Yemen Opportunity brings trusted sources
                into one discovery experience.

                Users can search naturally in Arabic or
                English, understand important requirements
                more quickly, and return to the original
                provider whenever they are ready to verify
                or apply.
                """
            ).strip()
        )


    # --------------------------------------------------------
    # FOUNDER
    # --------------------------------------------------------

    with founder_col:

        ui_html(
            """
            <div class="founder-card">

                <div class="founder-label">
                    FOUNDER
                </div>

                <div class="founder-name">
                    Mohammed Tariq Al-Saqqaf
                </div>

                <div class="founder-role">
                    Founder of Yemen Opportunity
                </div>

                <div class="founder-text">

                    Mohammed Tariq Al-Saqqaf founded
                    Yemen Opportunity with a clear goal:
                    make high-quality global opportunities
                    easier for young people in Yemen
                    to discover and understand.

                    <br><br>

                    The platform combines trusted
                    information, bilingual discovery
                    and AI-assisted guidance to reduce
                    the distance between opportunity
                    and access.

                </div>

            </div>
            """
        )


    # --------------------------------------------------------
    # MISSION
    # --------------------------------------------------------

    ui_html(
        """
        <div class="mission-card">

            <div class="mission-label">
                OUR MISSION
            </div>

            <div class="mission-text">

                Make access to global opportunity
                simpler, clearer and more equitable
                for the next generation of Yemeni talent.

            </div>

        </div>
        """
    )


    # --------------------------------------------------------
    # WHAT WE DO
    # --------------------------------------------------------

    ui_html(
        """
        <div class="section-head">

            <div class="section-label">
                WHAT WE DO
            </div>

            <div class="section-title">
                One place to discover what comes next
            </div>

            <div class="section-copy">
                A simpler path from question
                to trusted opportunity information.
            </div>

        </div>
        """
    )


    features = (

        (
            "🔎",
            "Discover",
            "Explore scholarships, internships, "
            "fellowships, competitions and "
            "professional programs.",
        ),

        (
            "🌐",
            "Search bilingually",
            "Use Arabic or English naturally "
            "without changing how you ask your question.",
        ),

        (
            "🎯",
            "Find what matters",
            "Relevant information is prioritized "
            "so you can focus on opportunities "
            "that fit your goals.",
        ),

        (
            "🤖",
            "Understand faster",
            "AI-assisted explanations make complex "
            "opportunity information easier "
            "to understand.",
        ),

        (
            "🔗",
            "Verify officially",
            "Original provider links stay available "
            "for final confirmation and application.",
        ),

        (
            "⭐",
            "Build your shortlist",
            "Save promising opportunities and return "
            "to them as you compare your options.",
        ),
    )


    columns = (
        st.columns(
            3
        )
    )


    for index, (
        icon,
        title,
        copy,
    ) in enumerate(
        features
    ):

        with columns[
            index % 3
        ]:

            ui_html(
                f"""
                <div class="feature-card">

                    <div class="feature-icon">
                        {icon}
                    </div>

                    <div class="feature-title">
                        {html.escape(title)}
                    </div>

                    <div class="feature-copy">
                        {html.escape(copy)}
                    </div>

                </div>
                """
            )


    # --------------------------------------------------------
    # HOW IT WORKS
    # --------------------------------------------------------

    ui_html(
        """
        <div class="section-head">

            <div class="section-label">
                HOW IT WORKS
            </div>

            <div class="section-title">
                From question to trusted answer
            </div>

            <div class="section-copy">
                The technology stays in the background.
                The experience stays clear.
            </div>

        </div>
        """
    )


    steps = (

        (
            "1",
            "Understand",
            "Your question is interpreted "
            "across Arabic and English.",
        ),

        (
            "2",
            "Search",
            "Relevant information is retrieved "
            "from trusted sources.",
        ),

        (
            "3",
            "Prioritize",
            "The strongest evidence is identified "
            "and ranked.",
        ),

        (
            "4",
            "Explain",
            "AI turns retrieved information "
            "into a clear response.",
        ),

        (
            "5",
            "Verify",
            "Official provider sources remain "
            "available for confirmation.",
        ),
    )


    columns = (
        st.columns(
            5
        )
    )


    for index, (
        number,
        title,
        copy,
    ) in enumerate(
        steps
    ):

        with columns[
            index
        ]:

            with st.container(
                border=True
            ):

                st.caption(
                    number
                )


                st.markdown(
                    f"**{title}**"
                )


                st.caption(
                    copy
                )


    # --------------------------------------------------------
    # TRUST
    # --------------------------------------------------------

    ui_html(
        """
        <div class="section-head">

            <div class="section-label">
                TRUST & QUALITY
            </div>

            <div class="section-title">
                Designed for reliable discovery
            </div>

            <div class="section-copy">

                Yemen Opportunity combines trusted
                source selection, bilingual retrieval
                and evidence-grounded AI to help users
                discover opportunities with greater
                clarity and confidence.

            </div>

        </div>
        """
    )


    quality_columns = (
        st.columns(
            4
        )
    )


    metrics = (

        (
            str(
                len(
                    load_catalog()
                )
            ),
            "Trusted sources",
        ),

        (
            "AR + EN",
            "Bilingual search",
        ),

        (
            "Official",
            "Source links",
        ),

        (
            "AI",
            "Grounded assistance",
        ),
    )


    for index, (
        value,
        label,
    ) in enumerate(
        metrics
    ):

        with quality_columns[
            index
        ]:

            st.metric(
                label,
                value,
            )


    # --------------------------------------------------------
    # VISION
    # --------------------------------------------------------

    ui_html(
        """
        <div class="section-head">

            <div class="section-label">
                OUR VISION
            </div>

            <div class="section-title">
                From opportunity search
                to opportunity intelligence
            </div>

            <div class="section-copy">

                The long-term vision is to help young
                people not only find opportunities,
                but better understand which opportunities
                fit them, what they need,
                and what to do next.

            </div>

        </div>
        """
    )


    vision = (

        (
            "Personalized discovery",
            "Help people find opportunities aligned "
            "with their education, skills and goals.",
        ),

        (
            "Clearer opportunity data",
            "Make funding, eligibility, deadlines "
            "and application steps easier to understand.",
        ),

        (
            "Built from Yemen",
            "Create globally useful technology shaped "
            "by the real access needs of Yemeni youth.",
        ),
    )


    columns = (
        st.columns(
            3
        )
    )


    for index, (
        title,
        copy,
    ) in enumerate(
        vision
    ):

        with columns[
            index
        ]:

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### {title}"
                )


                st.caption(
                    copy
                )


    # --------------------------------------------------------
    # RESPONSIBLE USE
    # --------------------------------------------------------

    ui_html(
        """
        <div class="section-head">

            <div class="section-label">
                RESPONSIBLE USE
            </div>

            <div class="section-title">
                AI supports discovery.
                Official sources make it final.
            </div>

            <div class="section-copy">

                Deadlines, eligibility and funding
                conditions can change.

                Always confirm critical information
                with the official provider before
                making an application decision.

            </div>

        </div>
        """
    )


    if st.button(
        "Explore opportunities →",
        key="about_explore",
        type="primary",
    ):

        st.session_state[
            "page"
        ] = "Explore"


        st.rerun()


# ============================================================
# PROCESS PENDING AI QUESTION
# ============================================================

if (
    st.session_state.get(
        "page"
    )
    ==
    "Home"

    and

    st.session_state.get(
        "pending_ai_query"
    )
):

    pending_query = (
        st.session_state[
            "pending_ai_query"
        ]
    )


    st.session_state[
        "pending_ai_query"
    ] = None


    run_search(
        pending_query
    )


# ============================================================
# ROUTER
# ============================================================

page = (
    st.session_state.get(
        "page",
        "Home",
    )
)


if page == "Home":

    render_home()


elif page == "Explore":

    render_explore()


elif page == "Saved":

    render_saved()


elif page == "History":

    render_history()


elif page == "About":

    render_about()


else:

    st.session_state[
        "page"
    ] = "Home"


    render_home()


# ============================================================
# FOOTER
# ============================================================

ui_html(
    """
    <div class="site-footer">

        <strong style="color:#10201A;">
            Yemen Opportunity
        </strong>

        <br>

        Global opportunities. Clearer access.

        <br><br>

        Scholarships · Internships · Fellowships ·
        Competitions · Professional programs

        <br><br>

        Yemen Opportunity helps users discover
        and understand opportunities.

        Always confirm final eligibility,
        deadlines and application requirements
        with the official provider.

        <br><br>

        © 2026 Yemen Opportunity

    </div>
    """
)