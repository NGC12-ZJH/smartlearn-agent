"""CLI Q&A Tool — answer questions about provided text using an LLM.

Usage:
    python cli_qa.py                  # paste text, end with END
    python cli_qa.py --file FILE      # load text from FILE
"""

import argparse
import os
import re
import sys

from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL = "qwen/qwen3.5-flash-02-23"
TEMPERATURE = 0.0
MISSING = "The text does not provide this information."

load_dotenv()

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a precise research assistant.

Rules:
1. Answer ONLY using information from the provided text.
2. After EVERY claim, add a citation in the format [Paragraph X].
3. If a sentence uses information from multiple paragraphs, cite all of them.
4. If the text does not contain the answer, reply exactly:
   'The text does not provide this information.'
5. Do NOT add any information beyond what is in the text.

Example:
If the text says:
[Paragraph 1] The sky is blue.
[Paragraph 2] Grass is green.

And the question is: 'What color is the sky?'
Your answer should be: 'The sky is blue [Paragraph 1].'
"""

USER_PROMPT = """Here is the text:

{numbered_text}

Question: {question}"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_text() -> str:
    """Read multi-line text from stdin until a line containing only 'END'."""
    print("请粘贴文本（输入 END 结束）：")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def load_text_file(path: str) -> str:
    """Read text from a file."""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def split_paragraphs(text: str) -> list[str]:
    """Split text into non-empty paragraphs on blank lines (possibly containing whitespace)."""
    return [
        p.strip()
        for p in re.split(r"\n\s*\n", text)
        if p.strip()
    ]


def number_paragraphs(paragraphs: list[str]) -> str:
    """Return a string with each paragraph labelled by its 1-based index."""
    numbered: list[str] = []
    for i, para in enumerate(paragraphs, 1):
        numbered.append(f"[Paragraph {i}]\n{para}")
    return "\n\n".join(numbered)


def build_messages(numbered_text: str, question: str) -> list[dict]:
    """Build the message list for the chat completion call."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_PROMPT.format(
                numbered_text=numbered_text, question=question
            ),
        },
    ]


def ask_question(client: OpenAI, numbered_text: str, question: str) -> str:
    """Send the question + numbered text to the LLM and return the answer."""
    messages = build_messages(numbered_text, question)
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # ---- Parse command-line arguments -----------------------------------
    parser = argparse.ArgumentParser(description="CLI Q&A Tool")
    parser.add_argument(
        "--file",
        help="Path to a text file to use as input (instead of pasting)",
    )
    args = parser.parse_args()

    # ---- Read the text --------------------------------------------------
    if args.file:
        text = load_text_file(args.file)
        print(f"已从文件 {args.file} 读取文本。")
    else:
        text = read_text()

    paragraphs = split_paragraphs(text)
    if not paragraphs:
        raise SystemExit(
            "No text was provided. Paste text or choose a non-empty file."
        )
    print(f"\n检测到 {len(paragraphs)} 个段落。")

    numbered_text = number_paragraphs(paragraphs)

    # ---- Init OpenRouter client -----------------------------------------
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit(
            "Error: OPENROUTER_API_KEY is missing. Check the .env file."
        )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # ---- Q&A loop -------------------------------------------------------
    print("你可以连续提问，输入 quit 退出。\n")

    while True:
        question = input("请输入你的问题（quit 退出）：")

        if question.strip().lower() == "quit":
            print("再见！")
            break

        print("\n正在思考...\n")
        answer = ask_question(client, numbered_text, question)

        print("回答：")
        print(answer)
        print()


if __name__ == "__main__":
    main()
