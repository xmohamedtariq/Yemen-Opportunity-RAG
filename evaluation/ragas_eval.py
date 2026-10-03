import json
import math
import os
import sys
import time
import warnings
from pathlib import Path


# ============================================================
# HIDE KNOWN RAGAS DEPRECATION WARNINGS
# ============================================================

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"Importing .* from 'ragas\.metrics' is deprecated.*",
)

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"LangchainLLMWrapper is deprecated.*",
)

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"LangchainEmbeddingsWrapper is deprecated.*",
)


# ============================================================
# IMPORTS
# ============================================================

from dotenv import load_dotenv
from langchain_cohere import (
    ChatCohere,
    CohereEmbeddings,
)

from ragas import (
    EvaluationDataset,
    evaluate,
)

from ragas.embeddings import (
    LangchainEmbeddingsWrapper,
)

from ragas.llms import (
    LangchainLLMWrapper,
)

from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
    ResponseRelevancy,
)

from ragas.run_config import (
    RunConfig,
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

SRC_DIR = (
    ROOT_DIR
    / "src"
)

DATA_DIR = (
    ROOT_DIR
    / "data"
)

EVALUATION_DIR = (
    ROOT_DIR
    / "evaluation"
)

GOLDEN_PATH = (
    EVALUATION_DIR
    / "golden_questions.json"
)

CACHE_PATH = (
    EVALUATION_DIR
    / "ragas_dataset_cache.json"
)

RESULTS_PATH = (
    EVALUATION_DIR
    / "ragas_results.csv"
)

SUMMARY_PATH = (
    EVALUATION_DIR
    / "ragas_summary.md"
)


# ============================================================
# MAKE src IMPORTABLE
# ============================================================

sys.path.insert(
    0,
    str(SRC_DIR),
)


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    ROOT_DIR
    / ".env"
)

load_dotenv(
    SRC_DIR
    / ".env",
    override=False,
)


# Reproduce the two-pass generation configuration used for the
# published RAGAS evidence unless the evaluator explicitly overrides it.
os.environ.setdefault(
    "RAG_ENABLE_ANSWER_REVIEW",
    "1",
)


# Import after loading environment variables.
from rag_pipeline import (
    YemenOpportunityRAG,
)


# ============================================================
# CONFIGURATION
# ============================================================

EVALUATION_SIZE = 20


COHERE_API_KEY = (
    os.getenv(
        "COHERE_API_KEY",
        "",
    )
    .strip()
)


JUDGE_MODEL = (
    os.getenv(
        "RAGAS_JUDGE_MODEL",
        "command-a-03-2025",
    )
    .strip()
)


EMBEDDING_MODEL = (
    os.getenv(
        "RAGAS_EMBEDDING_MODEL",
        "embed-multilingual-v3.0",
    )
    .strip()
)


REBUILD_CACHE = (
    os.getenv(
        "RAGAS_REBUILD",
        "0",
    )
    .strip()
    ==
    "1"
)


# ============================================================
# CONSOLE HELPERS
# ============================================================

def separator():

    print(
        "="
        *
        72
    )


def header(
    title: str,
):

    print()

    separator()

    print(
        title
    )

    separator()

    print()


# ============================================================
# COHERE MODELS
# ============================================================

def make_chat_model():

    return ChatCohere(

        model=
            JUDGE_MODEL,

        temperature=
            0,

        # Large enough for RAGAS structured outputs.
        max_tokens=
            4096,

        cohere_api_key=
            COHERE_API_KEY,
    )


def make_embedding_model():

    return CohereEmbeddings(

        model=
            EMBEDDING_MODEL,

        cohere_api_key=
            COHERE_API_KEY,
    )


# ============================================================
# COHERE FINISH-REASON FIX FOR RAGAS 0.4.x
# ============================================================

def cohere_is_finished(
    response,
):

    """
    RAGAS 0.4.x does not recognize Cohere's normal
    finish_reason='COMPLETE' in its default
    LangChain wrapper.

    This parser explicitly accepts Cohere COMPLETE
    and rejects genuinely truncated/error outputs.
    """

    finished = []


    for item in (
        response.flatten()
    ):

        generation = (
            item
            .generations[0][0]
        )

        finish_reason = None


        # ----------------------------------------------------
        # FIRST: generation_info
        # ----------------------------------------------------

        generation_info = getattr(
            generation,
            "generation_info",
            None,
        )


        if generation_info:

            finish_reason = (

                generation_info.get(
                    "finish_reason"
                )

                or

                generation_info.get(
                    "stop_reason"
                )
            )


        # ----------------------------------------------------
        # SECOND: message.response_metadata
        # ----------------------------------------------------

        message = getattr(
            generation,
            "message",
            None,
        )


        if (
            finish_reason
            is None
            and
            message
            is not None
        ):

            response_metadata = (

                getattr(
                    message,
                    "response_metadata",
                    None,
                )

                or

                {}
            )


            finish_reason = (

                response_metadata.get(
                    "finish_reason"
                )

                or

                response_metadata.get(
                    "stop_reason"
                )
            )


        # ----------------------------------------------------
        # NO FINISH METADATA
        # ----------------------------------------------------

        if finish_reason is None:

            # If LangChain gives us a valid generation
            # but no finish metadata, don't reject it.
            finished.append(
                True
            )

            continue


        # ----------------------------------------------------
        # NORMALIZE
        # ----------------------------------------------------

        reason = (
            str(
                finish_reason
            )
            .strip()
            .upper()
        )


        # ----------------------------------------------------
        # SUCCESSFUL COMPLETION
        # ----------------------------------------------------

        if reason in {

            "COMPLETE",

            "STOP",

            "END_TURN",

            "EOS_TOKEN",

            "FINISHED",

        }:

            finished.append(
                True
            )


        # ----------------------------------------------------
        # ACTUAL FAILURE / TRUNCATION
        # ----------------------------------------------------

        elif reason in {

            "MAX_TOKENS",

            "ERROR",

            "ERROR_TOXIC",

            "CANCELLED",

            "CANCELED",

        }:

            finished.append(
                False
            )


        # ----------------------------------------------------
        # UNKNOWN FINISH REASON
        # ----------------------------------------------------

        else:

            finished.append(
                False
            )


    return (

        all(
            finished
        )

        if finished

        else

        True
    )


# ============================================================
# LOAD GOLDEN QUESTIONS
# ============================================================

def load_golden_questions():

    if not GOLDEN_PATH.exists():

        raise FileNotFoundError(

            f"Golden questions not found: "
            f"{GOLDEN_PATH}"
        )


    with open(

        GOLDEN_PATH,

        "r",

        encoding=
            "utf-8",

    ) as file:

        questions = (
            json.load(
                file
            )
        )


    if not isinstance(
        questions,
        list,
    ):

        raise ValueError(

            "golden_questions.json "
            "must contain a JSON list."
        )


    if (
        len(
            questions
        )
        <
        EVALUATION_SIZE
    ):

        raise ValueError(

            f"Need at least "
            f"{EVALUATION_SIZE} "
            f"golden questions."
        )


    # Q01-Q20:
    # 10 Arabic + 10 English.
    return (
        questions[
            :EVALUATION_SIZE
        ]
    )


# ============================================================
# FIND GOLD CHUNKS
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

        chunk_id = (
            value.get(
                "chunk_id"
            )
        )

        text = (
            value.get(
                "text"
            )
        )


        if (
            chunk_id
            and
            text
        ):

            records.append(
                value
            )


        for child in (
            value.values()
        ):

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


def load_chunk_map():

    if not DATA_DIR.exists():

        raise FileNotFoundError(

            f"Data directory not found: "
            f"{DATA_DIR}"
        )


    chunk_map = {}


    for file_path in (
        DATA_DIR.rglob(
            "*.json"
        )
    ):

        try:

            with open(

                file_path,

                "r",

                encoding=
                    "utf-8",

            ) as file:

                content = (
                    json.load(
                        file
                    )
                )


            records = (
                collect_chunk_records(
                    content
                )
            )


            for record in records:

                chunk_id = (

                    str(
                        record.get(
                            "chunk_id",
                            "",
                        )
                    )
                    .strip()
                )


                text = (

                    str(
                        record.get(
                            "text",
                            "",
                        )
                    )
                    .strip()
                )


                if (
                    chunk_id
                    and
                    text
                ):

                    chunk_map[
                        chunk_id
                    ] = text


        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
            OSError,
        ):

            continue


    if not chunk_map:

        raise RuntimeError(

            "No chunk texts were found "
            "inside the data directory."
        )


    return chunk_map


# ============================================================
# CACHE
# ============================================================

def load_cache():

    if (
        REBUILD_CACHE
        or
        not CACHE_PATH.exists()
    ):

        return {}


    try:

        with open(

            CACHE_PATH,

            "r",

            encoding=
                "utf-8",

        ) as file:

            rows = (
                json.load(
                    file
                )
            )


        if not isinstance(
            rows,
            list,
        ):

            return {}


        return {

            row[
                "id"
            ]:
                row

            for row in rows

            if (
                isinstance(
                    row,
                    dict,
                )
                and
                row.get(
                    "id"
                )
            )
        }


    except Exception:

        return {}


def save_cache(
    rows_by_id,
):

    with open(

        CACHE_PATH,

        "w",

        encoding=
            "utf-8",

    ) as file:

        json.dump(

            list(
                rows_by_id.values()
            ),

            file,

            ensure_ascii=
                False,

            indent=
                2,
        )


# ============================================================
# LANGCHAIN RESPONSE TEXT
# ============================================================

def extract_message_text(
    message,
):

    content = getattr(
        message,
        "content",
        "",
    )


    if isinstance(
        content,
        str,
    ):

        return (
            content.strip()
        )


    parts = []


    for item in (
        content
        or
        []
    ):

        if isinstance(
            item,
            dict,
        ):

            text = (
                item.get(
                    "text"
                )
            )

        else:

            text = getattr(
                item,
                "text",
                None,
            )


        if text:

            parts.append(
                str(
                    text
                )
            )


    return (
        "\n".join(
            parts
        )
        .strip()
    )


# ============================================================
# GENERATE REFERENCE ANSWER
# ============================================================

def generate_reference_answer(

    question: str,

    gold_contexts,

    reference_llm,

):

    evidence = (

        "\n\n"
        "------------------------------"
        "\n\n"

    ).join(
        gold_contexts
    )


    system_prompt = """
You create ground-truth reference answers for evaluating
a retrieval-augmented generation system.

Mandatory rules:

1. Use ONLY the supplied gold evidence.
2. Do not use outside knowledge.
3. Do not invent missing information.
4. Answer the exact question directly.
5. Answer in the same language as the question.
6. Keep the reference concise but complete.
7. Preserve important numbers, dates, eligibility rules,
   requirements, benefits, and restrictions exactly as
   supported by the evidence.
""".strip()


    user_prompt = f"""
Question:

{question}

Gold evidence:

------------------------------

{evidence}

------------------------------

Write the ground-truth reference answer now.
""".strip()


    last_error = None


    for attempt in range(
        1,
        6,
    ):

        try:

            response = (
                reference_llm.invoke(
                    [
                        (
                            "system",
                            system_prompt,
                        ),
                        (
                            "human",
                            user_prompt,
                        ),
                    ]
                )
            )


            answer = (
                extract_message_text(
                    response
                )
            )


            if not answer:

                raise RuntimeError(

                    "Reference model "
                    "returned an empty answer."
                )


            return answer


        except Exception as exc:

            last_error = (
                exc
            )


            if attempt >= 5:

                break


            wait_seconds = min(

                5
                *
                attempt,

                20,
            )


            print(

                f"      [WARN] "
                f"Reference generation failed. "
                f"Retry {attempt}/5 "
                f"in {wait_seconds}s..."
            )


            time.sleep(
                wait_seconds
            )


    raise RuntimeError(

        "Reference generation failed "
        "after retries."

    ) from last_error


# ============================================================
# CONTEXTS ACTUALLY USED BY PRODUCTION RAG
# ============================================================

def extract_used_contexts(

    rag,

    result,

):

    retrieved = (

        result.get(
            "retrieved_chunks"
        )

        or

        []
    )


    if not retrieved:

        return []


    try:

        public_results = (
            rag.group_results_by_source(
                retrieved
            )
        )


    except Exception:

        public_results = (
            retrieved
        )


    contexts = []


    for item in (
        public_results
    ):

        context = ""


        try:

            context = (

                rag.build_context(
                    [item]
                )

                .strip()
            )


        except Exception:

            try:

                context = (

                    str(
                        rag._result_text(
                            item
                        )
                    )

                    .strip()
                )


            except Exception:

                if isinstance(
                    item,
                    dict,
                ):

                    context = (

                        str(
                            item.get(
                                "text",
                                "",
                            )
                        )

                        .strip()
                    )


        if context:

            contexts.append(
                context
            )


    return contexts


# ============================================================
# BUILD 20 REAL RAG SAMPLES
# ============================================================

def build_evaluation_rows():

    header(

        "Yemen Opportunity RAG - "
        "Preparing RAGAS Dataset"
    )


    if not COHERE_API_KEY:

        raise RuntimeError(

            "COHERE_API_KEY was not found. "
            "Check .env or src/.env."
        )


    questions = (
        load_golden_questions()
    )


    chunk_map = (
        load_chunk_map()
    )


    cache = (
        load_cache()
    )


    print(

        f"[OK] Questions selected: "
        f"{len(questions)}"
    )


    print(

        f"[OK] Gold chunks loaded: "
        f"{len(chunk_map)}"
    )


    print(

        f"[INFO] Cached samples: "
        f"{len(cache)}"
    )


    print()


    print(

        "[INFO] Initializing "
        "evaluated RAG benchmark path..."
    )


    rag = (
        YemenOpportunityRAG()
    )


    print(

        "[OK] Production RAG ready"
    )


    reference_llm = (
        make_chat_model()
    )


    print(

        "[OK] Cohere reference model ready"
    )


    print()


    for index, question_data in enumerate(

        questions,

        start=
            1,

    ):

        question_id = (
            question_data[
                "id"
            ]
        )


        question = (
            question_data[
                "question"
            ]
        )


        if (
            question_id
            in
            cache
            and
            not REBUILD_CACHE
        ):

            print(

                f"[{index:02d}/"
                f"{len(questions):02d}] "
                f"{question_id} - CACHED"
            )

            continue


        print(

            f"[{index:02d}/"
            f"{len(questions):02d}] "
            f"{question_id}"
        )


        gold_chunk_ids = (

            question_data.get(
                "gold_chunk_ids",
                [],
            )
        )


        if not gold_chunk_ids:

            raise RuntimeError(

                f"No gold chunks "
                f"for {question_id}"
            )


        gold_contexts = []


        for chunk_id in (
            gold_chunk_ids
        ):

            gold_text = (
                chunk_map.get(
                    chunk_id
                )
            )


            if not gold_text:

                raise RuntimeError(

                    f"Gold chunk not found: "
                    f"{chunk_id} "
                    f"for {question_id}"
                )


            gold_contexts.append(
                gold_text
            )


        print(

            "   -> Generating "
            "ground-truth reference..."
        )


        reference_answer = (

            generate_reference_answer(

                question=
                    question,

                gold_contexts=
                    gold_contexts,

                reference_llm=
                    reference_llm,
            )
        )


        print(

            "   -> Running "
            "evaluated RAG benchmark path..."
        )


        rag_result = (
            rag.ask(
                question
            )
        )


        response = (

            str(
                rag_result.get(
                    "answer",
                    "",
                )
            )

            .strip()
        )


        if not response:

            raise RuntimeError(

                f"Production RAG "
                f"returned an empty answer "
                f"for {question_id}"
            )


        retrieved_contexts = (

            extract_used_contexts(
                rag,
                rag_result,
            )
        )


        if not retrieved_contexts:

            raise RuntimeError(

                f"No retrieved contexts "
                f"for {question_id}"
            )


        cache[
            question_id
        ] = {

            "id":
                question_id,

            "language":
                question_data.get(
                    "language",
                    "",
                ),

            "difficulty":
                question_data.get(
                    "difficulty",
                    "",
                ),

            "user_input":
                question,

            "response":
                response,

            "reference":
                reference_answer,

            "retrieved_contexts":
                retrieved_contexts,

            "gold_chunk_ids":
                gold_chunk_ids,

            "gold_contexts":
                gold_contexts,

            "latency_seconds":
                rag_result.get(
                    "latency_seconds"
                ),
        }


        # Save after every completed question.
        save_cache(
            cache
        )


        print(

            f"   [OK] Retrieved contexts: "
            f"{len(retrieved_contexts)}"
        )


        print(

            f"   [OK] Latency: "
            f"{rag_result.get('latency_seconds')}s"
        )


        print(

            "   [OK] Saved to cache"
        )


        print()


        time.sleep(
            1
        )


    rows = []


    for question_data in questions:

        question_id = (
            question_data[
                "id"
            ]
        )


        if question_id not in cache:

            raise RuntimeError(

                f"Missing cached sample: "
                f"{question_id}"
            )


        rows.append(
            cache[
                question_id
            ]
        )


    print()


    print(

        "[OK] RAGAS dataset ready."
    )


    print(

        f"[OK] Samples: "
        f"{len(rows)}"
    )


    print(

        "[OK] Cache file:"
    )


    print(
        CACHE_PATH
    )


    return rows


# ============================================================
# RUN RAGAS
# ============================================================

def run_ragas(
    rows,
):

    header(

        "Running RAGAS Evaluation"
    )


    evaluation_rows = []


    for row in rows:

        evaluation_rows.append(

            {

                "user_input":
                    row[
                        "user_input"
                    ],

                "retrieved_contexts":
                    row[
                        "retrieved_contexts"
                    ],

                "response":
                    row[
                        "response"
                    ],

                "reference":
                    row[
                        "reference"
                    ],
            }
        )


    dataset = (

        EvaluationDataset.from_list(
            evaluation_rows
        )
    )


    print(

        "[INFO] Creating Cohere "
        "RAGAS judge..."
    )


    langchain_judge = (
        make_chat_model()
    )


    langchain_embeddings = (
        make_embedding_model()
    )


    # IMPORTANT:
    # Custom parser fixes Cohere COMPLETE
    # being rejected by RAGAS 0.4.x.
    evaluator_llm = (

        LangchainLLMWrapper(

            langchain_judge,

            is_finished_parser=
                cohere_is_finished,
        )
    )


    evaluator_embeddings = (

        LangchainEmbeddingsWrapper(
            langchain_embeddings
        )
    )


    print(

        f"[OK] Judge model: "
        f"{JUDGE_MODEL}"
    )


    print(

        f"[OK] Embedding model: "
        f"{EMBEDDING_MODEL}"
    )


    print(

        "[OK] Cohere COMPLETE "
        "finish reason supported"
    )


    print()


    metrics = [

        Faithfulness(),

        ResponseRelevancy(),

        LLMContextPrecisionWithReference(),

        LLMContextRecall(),

    ]


    run_config = (

        RunConfig(

            timeout=
                240,

            max_retries=
                5,

            max_wait=
                60,

            max_workers=
                1,

            seed=
                42,
        )
    )


    print(

        "[INFO] Starting RAGAS..."
    )


    print(

        "[INFO] 20 questions x 4 metrics "
        "= 80 evaluation jobs."
    )


    print(

        "[INFO] This stage may take "
        "several minutes."
    )


    print()


    result = (

        evaluate(

            dataset=
                dataset,

            metrics=
                metrics,

            llm=
                evaluator_llm,

            embeddings=
                evaluator_embeddings,

            run_config=
                run_config,

            raise_exceptions=
                False,

            show_progress=
                True,
        )
    )


    return (
        result,
        metrics,
    )


# ============================================================
# SAFE AVERAGE
# ============================================================

def safe_average(
    values,
):

    valid_values = []


    for value in values:

        try:

            number = float(
                value
            )


            if not math.isnan(
                number
            ):

                valid_values.append(
                    number
                )


        except (
            TypeError,
            ValueError,
        ):

            continue


    if not valid_values:

        return None


    return (

        sum(
            valid_values
        )

        /

        len(
            valid_values
        )
    )


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(

    result,

    metrics,

    rows,

):

    dataframe = (
        result.to_pandas()
    )


    dataframe.insert(

        0,

        "id",

        [
            row[
                "id"
            ]
            for row in rows
        ],
    )


    dataframe.insert(

        1,

        "language",

        [
            row.get(
                "language",
                "",
            )
            for row in rows
        ],
    )


    dataframe.insert(

        2,

        "difficulty",

        [
            row.get(
                "difficulty",
                "",
            )
            for row in rows
        ],
    )


    dataframe.insert(

        3,

        "latency_seconds",

        [
            row.get(
                "latency_seconds"
            )
            for row in rows
        ],
    )


    dataframe.to_csv(

        RESULTS_PATH,

        index=
            False,

        encoding=
            "utf-8-sig",
    )


    # ========================================================
    # METRIC AVERAGES
    # ========================================================

    metric_names = [

        metric.name
        for metric in metrics
    ]


    averages = {}

    counts = {}


    for metric_name in (
        metric_names
    ):

        if metric_name not in dataframe.columns:

            continue


        column_values = (

            dataframe[
                metric_name
            ]
            .tolist()
        )


        average = (
            safe_average(
                column_values
            )
        )


        valid_count = 0


        for value in (
            column_values
        ):

            try:

                number = float(
                    value
                )


                if not math.isnan(
                    number
                ):

                    valid_count += 1


            except (
                TypeError,
                ValueError,
            ):

                pass


        if average is not None:

            averages[
                metric_name
            ] = average


            counts[
                metric_name
            ] = valid_count


    # ========================================================
    # PROJECT SUMMARY MEAN
    # ========================================================

    overall_score = None


    if averages:

        overall_score = (

            sum(
                averages.values()
            )

            /

            len(
                averages
            )
        )


    # ========================================================
    # LANGUAGE BREAKDOWN
    # ========================================================

    language_results = {}


    for language in (
        "ar",
        "en",
    ):

        subset = (

            dataframe[
                dataframe[
                    "language"
                ]
                ==
                language
            ]
        )


        language_results[
            language
        ] = {}


        for metric_name in (
            averages
        ):

            if metric_name not in subset.columns:

                continue


            score = (

                safe_average(

                    subset[
                        metric_name
                    ]
                    .tolist()
                )
            )


            if score is not None:

                language_results[
                    language
                ][
                    metric_name
                ] = score


    # ========================================================
    # MARKDOWN SUMMARY
    # ========================================================

    lines = [

        "# Yemen Opportunity RAG - RAGAS Evaluation",

        "",

        f"Evaluation questions: {len(rows)}",

        "",

        "Judge provider: Cohere",

        "",

        f"Judge model: `{JUDGE_MODEL}`",

        "",

        f"Embedding model: `{EMBEDDING_MODEL}`",

        "",

        "## Overall Results",

        "",

        "| Metric | Valid samples | Score |",

        "|---|---:|---:|",
    ]


    for metric_name, score in (
        averages.items()
    ):

        pretty_name = (

            metric_name
            .replace(
                "_",
                " "
            )
            .title()
        )


        lines.append(

            f"| {pretty_name} "
            f"| {counts.get(metric_name, 0)}/{len(rows)} "
            f"| {score:.4f} |"
        )


    if overall_score is not None:

        lines.append(

            f"| **Overall mean "
            f"(project summary)** "
            f"| - "
            f"| **{overall_score:.4f}** |"
        )


    # ========================================================
    # LANGUAGE TABLE
    # ========================================================

    lines.extend(

        [

            "",

            "## Results by Language",

            "",

            "| Language | Metric | Score |",

            "|---|---|---:|",

        ]
    )


    for language, scores in (
        language_results.items()
    ):

        for metric_name, score in (
            scores.items()
        ):

            pretty_name = (

                metric_name
                .replace(
                    "_",
                    " "
                )
                .title()
            )


            lines.append(

                f"| {language} "
                f"| {pretty_name} "
                f"| {score:.4f} |"
            )


    # ========================================================
    # METHOD
    # ========================================================

    lines.extend(

        [

            "",

            "## Evaluation Method",

            "",

            "- 20 questions were selected from the 30-question golden set.",

            "- Q01-Q20 were evaluated, covering 10 Arabic and 10 English questions.",

            "- Each production answer was generated by the real Yemen Opportunity RAG pipeline.",

            "- Retrieved contexts came from the same retrieval and reranking pipeline used by the application.",

            "- Ground-truth reference answers were generated only from each question's manually assigned gold chunks.",

            "- Reference generation was instructed not to use outside knowledge.",

            "- Cohere was used as the RAGAS evaluation judge and multilingual embedding provider.",

            "",

            "## Metrics",

            "",

            "- Faithfulness: whether answer claims are supported by retrieved evidence.",

            "- Answer Relevancy: how directly the answer addresses the user's question.",

            "- Context Precision: whether relevant evidence is ranked well among retrieved contexts.",

            "- Context Recall: whether retrieved evidence covers the information required by the reference answer.",

            "",

            "Detailed per-question results are stored in `evaluation/ragas_results.csv`.",

            "",

            "The overall mean is a project-level summary calculated as the arithmetic mean of the available metric averages; the individual RAGAS metrics remain the primary evaluation results.",

        ]
    )


    with open(

        SUMMARY_PATH,

        "w",

        encoding=
            "utf-8",

    ) as file:

        file.write(

            "\n".join(
                lines
            )
        )


    # ========================================================
    # TERMINAL OUTPUT
    # ========================================================

    header(

        "FINAL RAGAS RESULTS"
    )


    if not averages:

        print(

            "[WARN] No valid metric "
            "averages were produced."
        )


    else:

        for metric_name, score in (
            averages.items()
        ):

            print(

                f"{metric_name:<40}"
                f"{score:.4f}"
            )


        if overall_score is not None:

            print()

            print(

                f"{'Overall mean':<40}"
                f"{overall_score:.4f}"
            )


    print()


    print(

        "[OK] Detailed results:"
    )


    print(
        RESULTS_PATH
    )


    print()


    print(

        "[OK] Summary report:"
    )


    print(
        SUMMARY_PATH
    )


# ============================================================
# MAIN
# ============================================================

def main():

    header(

        "Yemen Opportunity RAG\n"
        "RAGAS Evaluation - 20 Questions"
    )


    print(

        "[INFO] Evaluation provider: "
        "Cohere"
    )


    print(

        f"[INFO] Judge model: "
        f"{JUDGE_MODEL}"
    )


    print(

        f"[INFO] Embeddings: "
        f"{EMBEDDING_MODEL}"
    )


    print(

        f"[INFO] Rebuild cache: "
        f"{REBUILD_CACHE}"
    )


    print()


    if not COHERE_API_KEY:

        raise RuntimeError(

            "COHERE_API_KEY was not found. "
            "Add it to .env or src/.env."
        )


    rows = (
        build_evaluation_rows()
    )


    result, metrics = (
        run_ragas(
            rows
        )
    )


    save_results(

        result=
            result,

        metrics=
            metrics,

        rows=
            rows,
    )


    print()


    separator()


    print(

        "RAGAS evaluation finished"
    )


    separator()


if __name__ == "__main__":

    main()