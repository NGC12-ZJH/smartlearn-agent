"""PDF Summary Tool — read a PDF and print a structured LLM summary.

Usage:
    python3 pdf_summary.py <path-to-pdf>
    python3 pdf_summary.py <path-to-pdf> --pages 1-5
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL = "qwen/qwen3.5-flash-02-23"
TEMPERATURE = 0.0
MAX_TOKENS = 1024
MAX_PDF_CHARS = 30_000  # safety cap to stay well within context limits

SYSTEM_PROMPT = """You are a precise research assistant. Summarise the provided document.

Rules:
1. Output exactly three sections with these exact headings:
   ## Overview
   ## Key Points
   ## Limitations
2. The Overview section gives a 2-3 sentence summary of the document.
3. Every bullet in Key Points MUST end with a [Page X] citation.
4. The Limitations section notes extraction quality issues, missing context,
   or other caveats.
5. Use ONLY information from the provided text. Do not invent facts.
6. If the text is too short or seems corrupted, say so in Limitations.
"""

load_dotenv()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_page_range(range_str: str) -> tuple[int, int]:
    """Parse a page range string like '1-5' into (start, end).

    Raises ValueError with a friendly message on malformed input.
    """
    parts = range_str.split("-")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid page range '{range_str}'. "
            "Expected format: START-END (e.g., 1-5)."
        )
    try:
        start = int(parts[0].strip())
        end = int(parts[1].strip())
    except ValueError:
        raise ValueError(
            f"Invalid page range '{range_str}'. "
            "START and END must be integers (e.g., 1-5)."
        )
    if start < 1:
        raise ValueError("START page must be at least 1.")
    if end < start:
        raise ValueError(
            f"END page ({end}) must be greater than or equal to "
            f"START page ({start})."
        )
    return start, end


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------

def extract_text(
    pdf_path: str, page_range: tuple[int, int] | None = None
) -> tuple[str, list[str]]:
    """Return (full_text, per_page_texts) from a PDF file.

    Raises FileNotFoundError if the path does not exist.
    Returns ("", []) when no extractable text is found in any page.
    If page_range is given, only pages within [start, end] are included.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    try:
        import pdfplumber
    except ImportError:
        raise SystemExit(
            "pdfplumber is required. Install it with:\n"
            "    pip install pdfplumber"
        )

    pages: list[str] = []
    full_text: str = ""

    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        if page_range:
            start, end = page_range
            if end > total:
                print(
                    f"Note: Requested pages {start}-{end}, "
                    f"but the PDF only has {total} page(s). "
                    f"Showing pages {start}-{min(end, total)}."
                )
        for idx, page in enumerate(pdf.pages, 1):
            if page_range and (idx < page_range[0] or idx > page_range[1]):
                continue
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
                full_text += page_text + "\n"
            print(f"Extracting page {idx}/{total}...")

    return full_text.strip(), pages


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def build_numbered_text(pages: list[str]) -> str:
    """Return the document text with each page labelled by its number."""
    chunks: list[str] = []
    for i, page_text in enumerate(pages, 1):
        chunks.append(f"[Page {i}]\n{page_text}")
    return "\n\n".join(chunks)


def build_messages(numbered_text: str) -> list[dict]:
    """Build the chat completion message list."""
    user_content = (
        f"Summarise the following document:\n\n{numbered_text}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def summarise(client: OpenAI, numbered_text: str) -> str:
    """Send the numbered text to the LLM and return the summary."""
    # Safety cap: if text is extremely long, truncate with a note
    if len(numbered_text) > MAX_PDF_CHARS:
        numbered_text = numbered_text[:MAX_PDF_CHARS] + (
            "\n\n[Note: The document was truncated because it exceeds "
            "the length limit. The summary below covers only the first portion.]"
        )

    messages = build_messages(numbered_text)
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarise a PDF file with an LLM."
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to summarise",
    )
    parser.add_argument(
        "--pages",
        help="Page range to summarise, e.g. 1-5 (default: all pages)",
    )
    args = parser.parse_args()

    # ---- Parse page range ------------------------------------------------
    page_range: tuple[int, int] | None = None
    if args.pages:
        try:
            page_range = parse_page_range(args.pages)
        except ValueError as exc:
            print(f"Error: {exc}")
            sys.exit(1)

    # ---- Extract text -----------------------------------------------------
    try:
        full_text, pages = extract_text(args.pdf_path, page_range)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    if not full_text:
        print(
            "No extractable text found in this PDF. "
            "It may be a scanned document or contain only images. "
            "This tool works with text-based PDFs."
        )
        sys.exit(0)

    numbered_text = build_numbered_text(pages)

    # ---- Init OpenRouter client -------------------------------------------
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit(
            "Error: OPENROUTER_API_KEY is missing. Check the .env file."
        )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # ---- Summarise --------------------------------------------------------
    print("Sending to LLM for summarisation...\n")
    summary = summarise(client, numbered_text)
    print(summary)


if __name__ == "__main__":
    main()
