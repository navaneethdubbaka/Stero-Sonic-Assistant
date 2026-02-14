# Local LLM (Ollama) Setup

You can run Stereo Sonic with a local LLM via [Ollama](https://ollama.ai) instead of Gemini or OpenAI APIs.

## Quick start

1. **Install Ollama** from [ollama.ai/download](https://ollama.ai/download) and start it (e.g. run `ollama serve` or use the desktop app).

2. **Pull a model** (e.g. for chat):
   ```bash
   ollama pull llama3.2
   ```
   For image analysis (vision), pull a vision-capable model:
   ```bash
   ollama pull llava
   ```

3. **Set environment variables** (e.g. in `.env` in the project root):
   ```env
   LOCAL_LLM=True
   OLLAMA_MODEL=llama3.2
   OLLAMA_VISION_MODEL=llava
   ```
   Optional:
   - `OLLAMA_BASE_URL` – default `http://localhost:11434` if Ollama runs elsewhere.

4. **Run the backend** as usual. Chat, tools, data analyzer, and image analysis will use your local Ollama models when `LOCAL_LLM=True`.

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOCAL_LLM` | Set to `True`, `true`, `1`, or `yes` to use Ollama | unset (use API) |
| `OLLAMA_MODEL` | Model name for chat and code generation | `llama3.2` |
| `OLLAMA_BASE_URL` | Ollama API base URL | `http://localhost:11434` |
| `OLLAMA_VISION_MODEL` | Model for image analysis when using local LLM | `llava` |

When `LOCAL_LLM` is not set or false, the app uses `LLM_PROVIDER` (Gemini or OpenAI) and the corresponding API keys as before.

## Switching between local and API

- **Use local Ollama**: set `LOCAL_LLM=True` (and optionally `OLLAMA_MODEL`, `OLLAMA_VISION_MODEL`). No `GEMINI_API_KEY` or `OPENAI_API_KEY` needed for the LLM.
- **Use Gemini/OpenAI**: leave `LOCAL_LLM` unset or set to `False`, and set `LLM_PROVIDER` and the appropriate API keys.

No code or frontend changes are required; only the backend LLM source changes based on the env flag.
