FROM python:3.12.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git && rm -rf /var/lib/apt/lists/*
# Claude Code, pinned to 2.1.302 (the version the measurements used). Signs in with ANTHROPIC_API_KEY,
# passed at run time, never baked in.
RUN curl -fsSL https://claude.ai/install.sh | bash -s 2.1.302 && ln -sf /root/.local/bin/claude /usr/local/bin/claude && claude --version
RUN python -m venv /opt/mcpgit && /opt/mcpgit/bin/pip install --no-cache-dir mcp-server-git==2026.8.18
WORKDIR /lab
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/lab
