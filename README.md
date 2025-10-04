# DefHack project


## Development with uv

This project uses [uv](https://github.com/astral-sh/uv) for Python package management and development workflow. uv is a fast Python package manager and build tool that replaces pip and virtualenv for most tasks.

### Getting Started

1. **Install uv** (if you don't have it):
	```pwsh
	pip install uv
	```

2. **Install dependencies:**
	```pwsh
	uv pip install -r requirements.txt
	```
	Or, if using `pyproject.toml`:
	```pwsh
	uv pip install -r pyproject.toml
	```

3. **Add a new dependency:**
	```pwsh
	uv pip install <package>
	```
	This will update your lockfile automatically.

4. **Update dependencies:**
	```pwsh
	uv pip update
	```

### Development Workflow

- Make all changes in a feature branch.
- Use `uv` to manage dependencies and environments.
- Run your code and tests using the uv-managed environment.
- Keep `pyproject.toml` and `uv.lock` up to date.
- Before pushing, ensure all dependencies are locked and documented.

For more details, see the [uv documentation](https://github.com/astral-sh/uv).


## Clarity Opsbot Telegram Bot

The `DefHack.clarity_opsbot` package contains a Telegram bot that can operate in unit group chats and private messages.

- **Group chats:** the bot listens for text and location posts, enriches them with MGRS coordinates, and queues the content for optional Gemini analysis.
- **Direct messages:** use `/frago` to launch a short dialogue that assembles a FRAGO order scaffold from the latest subordinate observations (dummy data for now). Finish with `/cancel` to abort.

To run the bot locally, provide the `TELEGRAM_BOT_TOKEN` (and optional Gemini credentials) and start the application:

```bash
export TELEGRAM_BOT_TOKEN=your_bot_token
python -m DefHack.clarity_opsbot
```


