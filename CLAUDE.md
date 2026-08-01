# SmartLearn Agent

## Project
SmartLearn Agent is an AI-powered learning assistant that answers
questions based on provided course materials.

## Tech Stack
- Backend: Python + FastAPI
- Frontend: React + Vite
- LLM: OpenRouter
- Vector Search: FAISS (Day 3)

## AI Coding Environment
- Claude Code uses DeepSeek directly through ANTHROPIC_BASE_URL
- OpenRouter is only for the student Python API exercises
- Never route Claude Code through OpenRouter
- Never print or expose API keys

## Conventions
- Store API keys in .env and never commit them
- Use the project venv for Python dependencies
- Prefer python -m pip over system pip
- Commit messages use: type: description
- Allowed commit types include feat, fix, docs, refactor and test
- Review changes before committing

## Do Not Modify
- .env
- venv/
- .git/