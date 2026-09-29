from pathlib import Path
import os

from dotenv import load_dotenv
from openai import OpenAI
import cohere


ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = ROOT / ".env"


def main():
    print()
    print("=" * 60)
    print("Yemen Opportunity RAG")
    print("API Key Test")
    print("=" * 60)
    print()

    # Load .env
    load_dotenv(ENV_FILE)

    openai_key = os.getenv("OPENAI_API_KEY")
    cohere_key = os.getenv("COHERE_API_KEY")

    # -----------------------------------------------------
    # Check that keys exist
    # -----------------------------------------------------

    if openai_key:
        print("[OK] OPENAI_API_KEY found")
    else:
        print("[FAILED] OPENAI_API_KEY missing")

    if cohere_key:
        print("[OK] COHERE_API_KEY found")
    else:
        print("[FAILED] COHERE_API_KEY missing")

    print()

    # -----------------------------------------------------
    # Test OpenAI Embeddings
    # -----------------------------------------------------

    if openai_key:
        try:
            client = OpenAI(
                api_key=openai_key
            )

            client.embeddings.create(
                model="text-embedding-3-small",
                input="Yemen scholarship test",
            )

            print(
                "[OK] OpenAI embedding API works"
            )

        except Exception as error:
            print(
                "[FAILED] OpenAI API:"
            )
            print(
                type(error).__name__,
                str(error),
            )

    # -----------------------------------------------------
    # Test Cohere Embeddings
    # -----------------------------------------------------

    if cohere_key:
        try:
            co = cohere.ClientV2(
                api_key=cohere_key
            )

            co.embed(
                model="embed-multilingual-v3.0",
                texts=[
                    "منحة دراسية في اليمن"
                ],
                input_type="search_document",
                embedding_types=[
                    "float"
                ],
            )

            print(
                "[OK] Cohere embedding API works"
            )

        except Exception as error:
            print(
                "[FAILED] Cohere API:"
            )
            print(
                type(error).__name__,
                str(error),
            )

    print()
    print("=" * 60)
    print("API test finished")
    print("=" * 60)


if __name__ == "__main__":
    main()