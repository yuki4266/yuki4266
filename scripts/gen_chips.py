#!/usr/bin/env python3
"""Tech-garden chips: one animated SVG per technology, a flower label per row,
and a "field guide" card per row that explains every chip. Icons come from
Simple Icons; the README block between the Tech Garden markers is rewritten.

    python3 scripts/gen_chips.py
"""
import html
import random
import re
import textwrap
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "chips"
ICON_URL = "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{}.svg"
FONT = "Segoe UI, Ubuntu, Helvetica, Arial, sans-serif"
CHIP_COLOURS = ["#E2542F", "#F4795B", "#ED8B66", "#7FA36B"]  # cycles along each row
GREY = "#8b949e"

# (row label, petal colour, centre colour, chips)
# chip = (file slug, Simple Icons slug or None, label, description)
STACK = [
    ("LLMS", "#F4795B", "#E2542F", [
        ("claude", "claude", "Claude",
         "Anthropic's model family, strong at coding, long-context reasoning and agentic tool use; Claude Code brings it into the terminal as a coding agent 🌸"),
        ("openai", "openai", "GPT",
         "OpenAI's flagship line behind ChatGPT and the Responses API: reasoning models, native tool use, and the open-weight gpt-oss releases for self-hosting."),
        ("googlegemini", "googlegemini", "Gemini",
         "Google's natively multimodal model family: text, images, audio and video share one context window, with long-context variants reaching 1M+ tokens."),
        ("deepseek", "deepseek", "DeepSeek",
         "Open-weight Mixture-of-Experts models. DeepSeek-R1 popularized RL-trained chain-of-thought reasoning at a fraction of frontier training and inference cost."),
        ("qwen", "qwen", "Qwen",
         "Alibaba's open-weight model family: sizes from edge devices to hundreds of billions of parameters, top-tier multilingual coverage, plus Coder and Vision-Language variants."),
        ("kimi", "kimi", "Kimi",
         "Moonshot AI's open-weight Kimi K2 line: trillion-parameter Mixture-of-Experts models tuned for long-horizon agentic tool use and coding 🌙"),
        ("glm", None, "GLM",
         "Zhipu (Z.ai)'s open-weight GLM series: hybrid thinking modes, strong agentic coding, and MIT-licensed weights that made it a favourite base for self-hosting."),
    ]),
    ("AGENTS", "#7FA36B", "#5E8B4F", [
        ("claudecode", "claudecode", "Claude Code",
         "Anthropic's terminal-native coding agent, and the Claude Agent SDK underneath it — the same harness, tools and permission model, exposed for building your own agents."),
        ("langgraph", "langgraph", "LangGraph",
         "Graph-based agent orchestration: nodes are steps, edges are control flow, with built-in state, checkpointing and human-in-the-loop support."),
        ("openaiagents", "openai", "OpenAI Agents",
         "OpenAI's lightweight Agents SDK: agents, handoffs, guardrails and sessions with tracing built in, and MCP servers usable as first-class tools."),
        ("modelcontextprotocol", "modelcontextprotocol", "MCP",
         "Model Context Protocol — the open standard that lets any model talk to any tool or data source through one interface. The USB-C of AI 🔌"),
        ("agentskills", "agentskills", "Agent Skills",
         "Open standard for packaging know-how as folders of instructions, scripts and resources that an agent loads on demand — portable across Claude Code and other agent hosts."),
        ("dify", "dify", "Dify",
         "Open-source, self-hostable LLM-app platform: visual workflow builder, RAG pipeline, model gateway and observability in one box."),
        ("n8n", "n8n", "n8n",
         "Source-available workflow automation with hundreds of integrations; its AI-agent nodes are the fastest way to wire LLMs into real business flows."),
    ]),
    ("INFERENCE", "#EEA53A", "#D98828", [
        ("ollama", "ollama", "Ollama",
         "Runs LLMs locally with a single command: GGUF quantized models served behind an OpenAI-compatible API, on laptop-class hardware."),
        ("vllm", "vllm", "vLLM",
         "High-throughput inference engine built on PagedAttention and continuous batching — the de-facto standard for serving open models in production 🚀"),
        ("sglang", None, "SGLang",
         "Fast serving engine from the LMSYS lineage: RadixAttention prefix caching and a structured-generation frontend, trading blows with vLLM on throughput."),
        ("huggingface", "huggingface", "Hugging Face",
         "The GitHub of machine learning: model hub, datasets, Spaces demos, and the transformers library that standardized how models are loaded 🤗"),
        ("openrouter", "openrouter", "OpenRouter",
         "One API key, every model: a unified gateway that routes OpenAI-style requests to hundreds of commercial and open models with automatic failover."),
        ("modal", "modal", "Modal",
         "Serverless cloud for Python: decorate a function, get GPUs on demand, with containers that cold-start in seconds — the quick path to hosting fine-tunes and batch jobs."),
    ]),
    ("RAG / DATA", "#E86F9E", "#C64C7C", [
        ("qdrant", "qdrant", "Qdrant",
         "Rust-built vector database for semantic search: HNSW indexing, rich payload filtering and hybrid dense+sparse retrieval over embeddings."),
        ("milvus", "milvus", "Milvus",
         "Cloud-native distributed vector database designed for billion-scale similarity search, with GPU-accelerated index options."),
        ("postgresql", "postgresql", "pgvector",
         "Postgres extension adding vector columns, distance operators and ANN indexes — RAG memory without leaving your relational database."),
        ("redis", "redis", "Redis",
         "In-memory data store serving as cache, queue and session store; sub-millisecond reads make it the classic hot path of LLM apps ⚡"),
        ("supabase", "supabase", "Supabase",
         "Open-source Firebase alternative built on Postgres: auth, storage, realtime and edge functions, with pgvector built in for AI workloads."),
    ]),
    ("LANG / OPS", "#9986D4", "#7361BE", [
        ("python", "python", "Python",
         "The lingua franca of AI — every major ML framework, agent SDK and inference engine speaks it first 🐍"),
        ("uv", "uv", "uv",
         "Astral's Rust-powered Python package and project manager: lockfiles, virtualenvs, tool runs and Python installs in one very fast binary — the pip/poetry successor."),
        ("typescript", "typescript", "TypeScript",
         "JavaScript with static types: catches bugs at compile time and powers reliable large-scale frontends and Node services."),
        ("pytorch", "pytorch", "PyTorch",
         "The dominant deep-learning framework: dynamic computation graphs, torch.compile, and the training backbone of nearly every open model 🔥"),
        ("fastapi", "fastapi", "FastAPI",
         "Async Python web framework: type-hint-driven validation via Pydantic and auto-generated OpenAPI docs — the standard for serving ML APIs."),
        ("docker", "docker", "Docker",
         "Containers package code together with its environment: build once, run anywhere. The unit of deployment for modern services 🐳"),
        ("kubernetes", "kubernetes", "Kubernetes",
         "Container orchestration: declarative deployments, autoscaling and self-healing — how GPU inference fleets are operated in production."),
    ]),
]

# Arial Bold advance widths (per 1000 em) — a safe upper bound for the Segoe/Helvetica stack
_W = {**{c: 722 for c in "ABCDHKNRU"}, "E": 667, "F": 611, "G": 778, "I": 278, "J": 556, "L": 611, "M": 833,
      "O": 778, "P": 667, "Q": 778, "S": 667, "T": 611, "V": 667, "W": 944, "X": 667, "Y": 667, "Z": 611,
      **{c: 556 for c in "acekssxyv"}, **{c: 611 for c in "bdghnopqu"}, "f": 333, "i": 278, "j": 278, "l": 278,
      "m": 889, "r": 389, "t": 333, "w": 778, "z": 500, " ": 278, ".": 278, "/": 278, "-": 333, "+": 584}


def text_width(s, size):
    return sum(_W.get(c, 611) for c in s) * size / 1000


_icons = {}


def icon_path(slug):
    if slug not in _icons:
        with urllib.request.urlopen(ICON_URL.format(slug), timeout=20) as r:
            svg = r.read().decode()
        m = re.search(r'<path d="([^"]+)"', svg)
        if not m:
            raise SystemExit(f"no path in Simple Icons svg for {slug}")
        _icons[slug] = m.group(1)
    return _icons[slug]


def svg(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="{FONT}">'
            f'<title>{html.escape(title)}</title>{body}</svg>\n')


def flower(x, y, petal, centre, dur):
    petals = "".join(f'<circle cx="{cx}" cy="{cy}" r="3.4" fill="{petal}"/>'
                     for cx, cy in [(0, -6.5), (6.2, -2), (3.8, 5.3), (-3.8, 5.3), (-6.2, -2)])
    return (f'<g transform="translate({x},{y})"><g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="{dur}s" repeatCount="indefinite"/>'
            f'{petals}</g><circle r="2.8" fill="{centre}"/></g>')


def chip(slug, icon, label, colour):
    rnd = random.Random(label)
    dur, beg = 3.5 + rnd.random(), -rnd.random() * 4
    tw = int(text_width(label, 12)) + 2
    if icon:
        w = 32 + tw + 13
        inner = (f'<g transform="translate(12,8) scale(0.5833)"><path d="{icon_path(icon)}" fill="{colour}"/></g>'
                 f'<text x="32" y="19" font-size="12" font-weight="600" fill="{colour}">{html.escape(label)}</text>')
    else:
        w = 12 + tw + 12
        inner = f'<text x="{w / 2:g}" y="19" text-anchor="middle" font-size="12" font-weight="600" fill="{colour}">{html.escape(label)}</text>'
    body = ('<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="0s" dur="0.5s" fill="freeze"/>'
            f'<g><animateTransform attributeName="transform" type="translate" values="0 1.2;0 -1.2;0 1.2" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
            f'<rect x="1" y="4" width="{w - 2}" height="22" rx="11" fill="{colour}" fill-opacity="0.07" stroke="{colour}" stroke-width="1.3"/>'
            f'{inner}</g></g>')
    return svg(w, 30, label, body)


def label_chip(text, petal, centre):
    w = round(30 + len(text) * 7.6 + 5)
    return svg(w, 30, text, flower(14, 15, petal, centre, 14) +
               f'<text x="30" y="19" font-size="11" letter-spacing="1.5" fill="{GREY}">{html.escape(text)}</text>')


def guide(text, centre, chips):
    h = len(chips) * 62 + 48
    parts = [f'\n<rect x="1" y="1" width="858" height="{h - 2}" rx="14" fill="#F4795B" fill-opacity="0.04" stroke="#F4795B" stroke-opacity="0.35" stroke-width="1.2"/>\n',
             flower(30, 26, centre, centre, 16) + "\n",
             f'<text x="48" y="30" font-size="11" letter-spacing="2" fill="{GREY}">{html.escape(text)}</text>\n']
    for i, (slug, icon, label, desc) in enumerate(chips):
        y, c = 50 + 62 * i, CHIP_COLOURS[i % 4]
        lines = textwrap.wrap(desc, 108)
        if len(lines) > 2:
            raise SystemExit(f"{label}: description needs {len(lines)} lines, max 2")
        glyph = f'<g transform="translate(38,{y}) scale(0.8)"><path d="{icon_path(icon)}" fill="{c}"/></g>' if icon else ""
        body = "".join(f'<text x="76" y="{y + 25 + 16 * k}" font-size="12" fill="{GREY}">{html.escape(l)}</text>' for k, l in enumerate(lines))
        rule = f'<path d="M76 {y + 48} H 820" stroke="{c}" stroke-opacity="0.15" stroke-width="1"/>' if i < len(chips) - 1 else ""
        parts.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{0.15 + 0.09 * i:.2f}s" dur="0.5s" fill="freeze"/>'
                     f'{glyph}<text x="76" y="{y + 8}" font-size="13" font-weight="700" fill="{c}">{html.escape(label)}</text>{body}{rule}</g>\n')
    return svg(860, h, f"{text} field guide", "".join(parts))


def readme_block():
    rows, guides = [], []
    for i, (text, petal, centre, chips) in enumerate(STACK):
        imgs = [f'<img src="chips/label-{i}.svg" alt="{html.escape(text)}" />']
        imgs += [f'<img src="chips/{slug}.svg" alt="{html.escape(label)}" />' for slug, _, label, _ in chips]
        rows.append(" ".join(imgs))
        guides.append(f'<img src="chips/guide-{i}.svg" alt="{html.escape(text)} field guide" /><br/>')
    return ('<!-- ============ Tech Garden ============ -->\n<div align="center">\n\n'
            + "\n<br/>\n".join(rows) + "\n\n<details>\n"
            '<summary>🌱 &nbsp;<b>Field guide</b> — open to read what every chip actually is</summary>\n<br/>\n<div align="center">\n'
            + "\n".join(guides) + "\n</div>\n</details>\n\n</div>\n")


def main():
    OUT.mkdir(exist_ok=True)
    keep = set()
    for i, (text, petal, centre, chips) in enumerate(STACK):
        for slug, icon, label, desc in chips:
            (OUT / f"{slug}.svg").write_text(chip(slug, icon, label, CHIP_COLOURS[chips.index((slug, icon, label, desc)) % 4]))
            keep.add(f"{slug}.svg")
        (OUT / f"label-{i}.svg").write_text(label_chip(text, petal, centre))
        (OUT / f"guide-{i}.svg").write_text(guide(text, centre, chips))
        keep |= {f"label-{i}.svg", f"guide-{i}.svg"}
    stale = [p for p in OUT.glob("*.svg") if p.name not in keep]
    for p in stale:
        p.unlink()

    readme = ROOT / "README.md"
    s = readme.read_text()
    start = s.index("<!-- ============ Tech Garden ============ -->")
    end_marker = "</details>\n\n</div>\n"
    end = s.index(end_marker, start) + len(end_marker)
    readme.write_text(s[:start] + readme_block() + s[end:])
    print(f"{len(keep)} svgs written, {len(stale)} stale removed: {', '.join(p.name for p in stale) or '-'}")


if __name__ == "__main__":
    main()
