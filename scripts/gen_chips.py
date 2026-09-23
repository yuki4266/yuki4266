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
    ("AGENTS", "#7FA36B", "#5E8B4F", [
        ("modelcontextprotocol", "modelcontextprotocol", "MCP",
         "Model Context Protocol — the open standard that lets any model talk to any tool or data source through one interface. The USB-C of AI 🔌"),
        ("a2a", None, "A2A",
         "Agent2Agent — the open protocol, started by Google and now under the Linux Foundation, for agents to discover each other via Agent Cards and hand tasks across vendors."),
        ("agentskills", "agentskills", "Agent Skills",
         "Open standard for packaging know-how as folders of instructions, scripts and resources that an agent loads on demand — portable across agent hosts."),
        ("langgraph", "langgraph", "LangGraph",
         "Graph-based agent orchestration: nodes are steps, edges are control flow, with built-in state, checkpointing and human-in-the-loop support."),
        ("pydanticai", "pydantic", "Pydantic AI",
         "Type-safe agent framework from the Pydantic team: schema-validated structured outputs, dependency injection for tools, and model-agnostic runs with tracing built in."),
        ("temporal", "temporal", "Temporal",
         "Durable execution: workflows survive crashes and restarts with their state intact — the backbone for long-running, retry-heavy agent loops and human approvals."),
        ("playwright", "playwright", "Playwright",
         "Browser automation from Microsoft: one API driving Chromium, Firefox and WebKit — the hands of browser-using agents and the harness for end-to-end tests."),
    ]),
    ("INFERENCE", "#EEA53A", "#D98828", [
        ("vllm", "vllm", "vLLM",
         "High-throughput inference engine built on PagedAttention and continuous batching — the de-facto standard for serving open models in production 🚀"),
        ("sglang", None, "SGLang",
         "Fast serving engine from the LMSYS lineage: RadixAttention prefix caching and a structured-generation frontend, trading blows with vLLM on throughput."),
        ("tensorrtllm", "nvidia", "TensorRT-LLM",
         "NVIDIA's compiled inference stack: fused kernels, FP8/INT4 quantization, in-flight batching and speculative decoding for the last drop of GPU throughput."),
        ("llamacpp", None, "llama.cpp",
         "Pure C/C++ inference with GGUF quantization: runs models on CPUs, Apple silicon and phones, and is the engine underneath Ollama, LM Studio and friends."),
        ("mlx", None, "MLX",
         "Apple's array framework for Apple silicon: unified memory, lazy evaluation and mlx-lm for running and fine-tuning models locally on a Mac 🍎"),
        ("ray", "ray", "Ray",
         "Distributed compute for Python: Ray Serve for multi-model inference, Ray Train and Ray Data for scaling jobs across a cluster without rewriting them."),
        ("modal", "modal", "Modal",
         "Serverless cloud for Python: decorate a function, get GPUs on demand, with containers that cold-start in seconds — the quick path to hosting fine-tunes and batch jobs."),
    ]),
    ("TRAINING", "#F4795B", "#E2542F", [
        ("pytorch", "pytorch", "PyTorch",
         "The dominant deep-learning framework: dynamic computation graphs, torch.compile, FSDP, and the training backbone of nearly every open model 🔥"),
        ("transformers", "huggingface", "Transformers",
         "Hugging Face's model library: one API for loading, training and exporting thousands of architectures, with Datasets, Accelerate and PEFT alongside 🤗"),
        ("trl", None, "TRL",
         "Transformer Reinforcement Learning: SFT, DPO, GRPO and reward-model trainers built on Transformers — the standard toolkit for post-training open models."),
        ("verl", None, "verl",
         "ByteDance's RL training framework for LLMs: a hybrid-engine design that scales GRPO and PPO post-training across GPU clusters, behind many reasoning-model releases."),
        ("unsloth", None, "Unsloth",
         "Hand-written Triton kernels that make LoRA and full fine-tunes about 2x faster with far less memory — a 70B fine-tune fits on a single GPU."),
        ("wandb", "weightsandbiases", "W&B",
         "Weights & Biases: experiment tracking, sweeps and model registry for training runs, plus Weave for tracing and evaluating LLM applications."),
        ("cuda", "nvidia", "CUDA",
         "NVIDIA's GPU compute platform: the kernels, cuBLAS/cuDNN and NCCL collectives that every training and inference stack ultimately runs on."),
    ]),
    ("RAG / DATA", "#E86F9E", "#C64C7C", [
        ("postgresql", "postgresql", "pgvector",
         "Postgres extension adding vector columns, distance operators and ANN indexes — RAG memory without leaving your relational database."),
        ("qdrant", "qdrant", "Qdrant",
         "Rust-built vector database for semantic search: HNSW indexing, rich payload filtering and hybrid dense+sparse retrieval over embeddings."),
        ("lancedb", None, "LanceDB",
         "Embedded vector database on the Lance columnar format: multimodal data, vectors and full-text in one file-based store that scales from a laptop to object storage."),
        ("elasticsearch", "elasticsearch", "Elasticsearch",
         "The search engine behind hybrid retrieval: BM25 keyword scoring, dense vector kNN and reciprocal-rank fusion in one query, with mature filtering and aggregations."),
        ("neo4j", "neo4j", "Neo4j",
         "Graph database for GraphRAG: entities and relationships as first-class citizens, Cypher queries, and vector indexes so retrieval can walk the graph, not just embed it."),
        ("duckdb", "duckdb", "DuckDB",
         "In-process analytical database: columnar, vectorized SQL over Parquet, CSV and DataFrames at laptop scale — the SQLite of analytics 🦆"),
        ("polars", "polars", "Polars",
         "Rust-powered DataFrame library with a lazy query engine: multithreaded, out-of-core, and many times faster than pandas on the same machine."),
    ]),
    ("LANG / OPS", "#9986D4", "#7361BE", [
        ("python", "python", "Python",
         "The lingua franca of AI — every major ML framework, agent SDK and inference engine speaks it first 🐍"),
        ("uv", "uv", "uv",
         "Astral's Rust-powered Python package and project manager: lockfiles, virtualenvs, tool runs and Python installs in one very fast binary — the pip/poetry successor."),
        ("rust", "rust", "Rust",
         "Memory-safe systems language that now underpins the AI toolchain: uv, Polars, Lance, tokenizers, candle and a growing share of inference engines 🦀"),
        ("typescript", "typescript", "TypeScript",
         "JavaScript with static types: catches bugs at compile time and powers reliable large-scale frontends and Node services."),
        ("docker", "docker", "Docker",
         "Containers package code together with its environment: build once, run anywhere. The unit of deployment for modern services 🐳"),
        ("kubernetes", "kubernetes", "Kubernetes",
         "Container orchestration: declarative deployments, autoscaling and self-healing — how GPU inference fleets are operated in production."),
        ("opentelemetry", "opentelemetry", "OpenTelemetry",
         "Vendor-neutral traces, metrics and logs; its emerging GenAI semantic conventions are becoming the shared language for LLM observability tools."),
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
