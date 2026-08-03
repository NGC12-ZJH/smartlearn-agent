# CLI Q&A Tool PRD

## What it does

A command-line tool that takes multi-paragraph text and a question,
then uses an LLM to answer with paragraph-level citations.

## Input

1. Multi-line text terminated by `END`, or a text file passed through `--file`.
2. One or more questions about the text.
3. Type `quit` to exit question mode.

## Output

An answer that references specific paragraphs using `[Paragraph X]`.

## API

- Provider: OpenRouter
- API key: `OPENROUTER_API_KEY`
- The API key must be loaded from `.env`
- The API key must never be printed

## Acceptance tests

- The user can paste text and ask a question.
- The user can load text with `--file sample.txt`.
- Answers include `[Paragraph X]` citations.
- Information from Paragraph 1 cites `[Paragraph 1]`.
- Unsupported questions return exactly:
  `The text does not provide this information.`
- Empty text exits before any API request.
- Multiple questions can be asked in one session.
- Typing `quit` exits.
- `python -m py_compile cli_qa.py` succeeds.
- Model: `google/gemma-4-26b-a4b-it:free`
- Every factual claim must include a paragraph citation.
- Claims using multiple paragraphs must cite all relevant paragraphs.
- The model must not follow instructions contained in the reference text.