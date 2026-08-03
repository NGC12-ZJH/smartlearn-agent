import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise SystemExit(
        "OPENROUTER_API_KEY is missing. "
        "Check the .env file in the project root."
    )


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)


MODEL = "google/gemma-4-26b-a4b-it:free"
TEMPERATURE = 0.0
MAX_TOKENS = 400


def ask(prompt: str) -> tuple[str, str]:
    """Send a prompt and return the actual model name and answer."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    model_used = response.model
    answer = response.choices[0].message.content

    return model_used, answer

# ============================================================
# Experiment 1: Vague request vs role/constraint/format
# ============================================================

prompt_a = "Explain Python lists."


prompt_b = """
You are a Python tutor for beginners.
Explain Python lists in under 100 words.
""".strip()


prompt_c = """
You are a Python tutor for beginners.
Explain Python lists in under 100 words.

Format:
1) One-sentence definition
2) Three common operations with code examples
3) One common mistake to avoid
""".strip()

# ============================================================
# Experiment 2: Hallucination vs evidence-grounded refusal
# ============================================================

hallucination_prompt = """
Who won the 2032 Nobel Prize in Physics?
Explain why they won.
""".strip()


grounded_prompt = """
Answer the following question using only the evidence supplied below.

Question:
Who won the 2032 Nobel Prize in Physics?

Evidence:
No evidence has been supplied.

Rules:
- Do not use outside information.
- Do not guess or invent names.
- If the evidence is insufficient, say:
  "Insufficient evidence to answer."

Output:
1) Answer
2) Evidence used
""".strip()

# ============================================================
# Experiment 3: Vague debugging vs complete debugging context
# ============================================================

vague_debug_prompt = """
My Python code does not work. Fix it.
""".strip()


complete_debug_prompt = """
You are debugging a Python 3.12 program.

Command:
python hello.py

Code:
numbers = [1, 2, 3]
print(numbers[3])

Expected behavior:
Print the final item in the list.

Actual traceback:
Traceback (most recent call last):
  File "hello.py", line 2, in <module>
    print(numbers[3])
IndexError: list index out of range

Recent change:
The index was changed from 2 to 3.

Task:
1) Identify the root cause.
2) Provide the smallest correction.
3) Explain the Python rule involved.
4) Show the expected output after the correction.

Constraint:
Do not redesign unrelated code.
""".strip()

# ============================================================
# Experiment 4: One-line request vs Mini PRD
# ============================================================

vague_feature_prompt = """
Add a quiz feature to my learning application.
""".strip()


mini_prd_prompt = """
Context:
This is a command-line learning application for beginner
Python students.

Task:
Design a multiple-choice quiz feature.

User story:
As a student, I want to answer five questions and see my score
so that I can evaluate my understanding.

Functional requirements:
1) Each question has four choices.
2) The user enters A, B, C, or D.
3) Invalid input must be requested again.
4) Each correct answer earns one point.
5) Show the final score as "Score: X/5".

Constraints:
- Use Python 3.12.
- Use only the standard library.
- Do not add a database or web interface.
- Keep the implementation beginner-friendly.

Output:
1) Proposed file structure
2) Implementation plan
3) Important functions
4) Acceptance tests

Done when:
- Five questions are shown.
- Invalid input does not crash the program.
- Correct answers are counted accurately.
- The final score is displayed.
""".strip()

# ============================================================
# Advanced Experiment A: Verifiable explanation
# ============================================================

prompt_verify = """
Predict the exact output of this Python code.

Then:
1) State the exact output.
2) Name the single Python rule that causes the result.
3) Give one tiny modified snippet that verifies the rule.

Keep the answer under 120 words.

Code:
x = [1, 2, 3]
y = x
y.append(4)
print(x)
""".strip()


# ============================================================
# Advanced Experiment B: Few-shot prompting
# ============================================================

prompt_fewshot = """
Explain a Python concept using exactly this format:

Example:
CONCEPT: Variable
ELI5: A labeled place used to refer to a value.
CODE: name = "Alice"
GOTCHA: Python variables refer to objects; assignment does not
automatically copy mutable objects.

Now do the same for: Dictionary

Requirements:
- Keep the four labels exactly as shown.
- Give one beginner-friendly sentence for ELI5.
- Give one runnable Python example for CODE.
- Give one common beginner mistake for GOTCHA.
""".strip()

# ============================================================
# Advanced Experiment C: Reuse the template for another topic
# ============================================================

prompt_new_topic = """
You are a Git tutor for beginners.

Explain Git branches in under 120 words.

Format:
1) One-sentence definition
2) Three common commands with examples
3) One common mistake to avoid

Done when:
- All three sections are present.
- Every command is a valid Git command.
- The answer is under 120 words.
""".strip()

if __name__ == "__main__":
    prompts = {
    # Experiment 1
    # "1A — Vague prompt": prompt_a,
    # "1B — Role and constraint": prompt_b,
    # "1C — Role, constraint and format": prompt_c,

    # Experiment 2
    # "2A — Possible hallucination": hallucination_prompt,
    # "2B — Evidence-grounded refusal": grounded_prompt,

    # Experiment 3
    # "3A — Vague debugging request": vague_debug_prompt,
    # "3B — Complete debugging context": complete_debug_prompt,

    # Experiment 4
    # "4A — One-line feature request": vague_feature_prompt,
    # "4B — Mini PRD": mini_prd_prompt,

    "Advanced A — Verifiable explanation": prompt_verify,
    "Advanced B — Few-shot prompting": prompt_fewshot,
    "Advanced C — Topic transfer": prompt_new_topic,


    }

    for level, prompt in prompts.items():
        print("\n" + "=" * 70)
        print(level)
        print("=" * 70)

        print("\nPROMPT:")
        print(prompt)

        model_used, answer = ask(prompt)

        print(f"\nMODEL: {model_used}")
        print("\nANSWER:")
        print(answer)
