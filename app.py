"""
RAG Explorer — Day 7 Lab UI
Run: streamlit run app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ── path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=False)

from src.chunking import (
    ChunkingStrategyComparator,
    CustomRecipeChunker,
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
)
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

# ── constants ─────────────────────────────────────────────────────────────────
DATA_FILES = {
    "Braised Tofu with Quail Eggs": ROOT / "data/Braised_Tofu.md",
    "Duck Porridge & Salad":        ROOT / "data/Duck_Porridge.md",
    "Savory Pancakes (Bánh Khọt)":  ROOT / "data/Savory_Pancakes.md",
    "Grilled Snails":               ROOT / "data/Grilled_Snails.md",
    "Orange Fruit Skin Jam":        ROOT / "data/Orange_Fruit_Skin_Jam.md",
}

FILE_METADATA = {
    "Braised_Tofu":        {"category": "main_dish", "difficulty": "easy"},
    "Duck_Porridge":       {"category": "main_dish", "difficulty": "medium"},
    "Savory_Pancakes":     {"category": "main_dish", "difficulty": "hard"},
    "Grilled_Snails":      {"category": "seafood",   "difficulty": "easy"},
    "Orange_Fruit_Skin_Jam": {"category": "dessert", "difficulty": "easy"},
}

CHUNKER_NAMES = ["FixedSize", "Sentence", "Recursive", "CustomRecipe"]

CATEGORY_OPTIONS = ["(all)", "main_dish", "seafood", "dessert"]
DIFFICULTY_OPTIONS = ["(all)", "easy", "medium", "hard"]

BENCHMARK_QUERIES = [
    "What ingredients are needed for braised tofu with quail eggs?",
    "How do you make the dipping sauce for grilled snails?",
    "What is the process for making duck porridge?",
    "Which dish is a dessert and how is it stored?",
    "Which dishes require shrimp as an ingredient?",
]

# ── helpers ───────────────────────────────────────────────────────────────────

def _chunk_size_label(name: str) -> str:
    return {"FixedSize": "chunk_size", "Sentence": "max_sentences", "Recursive": "chunk_size", "CustomRecipe": "—"}[name]


def build_chunker(name: str, chunk_size: int, overlap: int, max_sentences: int):
    if name == "FixedSize":
        return FixedSizeChunker(chunk_size=chunk_size, overlap=overlap)
    if name == "Sentence":
        return SentenceChunker(max_sentences_per_chunk=max_sentences)
    if name == "Recursive":
        return RecursiveChunker(chunk_size=chunk_size)
    return CustomRecipeChunker()


@st.cache_resource(show_spinner="Loading embedder…")
def get_embedder(provider: str):
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            st.warning("LocalEmbedder unavailable — falling back to mock.", icon="⚠️")
    elif provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            st.warning("OpenAIEmbedder unavailable — falling back to mock.", icon="⚠️")
    return _mock_embed


def load_documents(selected_names: list[str]) -> list[tuple[str, str, dict]]:
    raw = []
    for display_name in selected_names:
        path = DATA_FILES[display_name]
        stem = path.stem
        content = path.read_text(encoding="utf-8")
        meta = {"source": stem, "category": FILE_METADATA.get(stem, {}).get("category", ""),
                "difficulty": FILE_METADATA.get(stem, {}).get("difficulty", "")}
        raw.append((stem, content, meta))
    return raw


def make_store(raw_files, chunker, embedder, metadata_filter: dict) -> tuple[EmbeddingStore, list[Document]]:
    all_docs = []
    for doc_id, content, meta in raw_files:
        chunks = chunker.chunk(content)
        for i, chunk in enumerate(chunks):
            all_docs.append(Document(
                id=f"{doc_id}:{i}",
                content=chunk,
                metadata={**meta, "doc_id": doc_id, "chunk_index": i},
            ))
    store = EmbeddingStore(collection_name="ui_store", embedding_fn=embedder)
    store.add_documents(all_docs)
    return store, all_docs


def call_llm(prompt: str, use_openai: bool) -> str:
    if use_openai:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return "⚠️ OPENAI_API_KEY not set. Using mock answer."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "Answer using only the provided context. Be concise."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"⚠️ OpenAI error: {e}"
    # mock
    context = prompt.split("Context:")[1].split("Question:")[0].strip() if "Context:" in prompt else ""
    lines = [l.strip() for l in context.splitlines() if l.strip()]
    preview = " ".join(lines)[:400]
    return f"[Mock LLM] {preview}{'...' if len(preview)==400 else ''}"


def score_bar(score: float) -> str:
    filled = int(score * 10)
    return "█" * filled + "░" * (10 - filled) + f"  {score:.4f}"


# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Explorer — Day 7",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.chunk-card {
    background: #1e1e2e;
    border-left: 4px solid #7aa2f7;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.85rem;
}
.score-high { color: #9ece6a; font-weight: bold; }
.score-med  { color: #e0af68; font-weight: bold; }
.score-low  { color: #f7768e; font-weight: bold; }
.tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    margin-right: 4px;
    background: #24283b;
    color: #7dcfff;
    border: 1px solid #7dcfff44;
}
</style>
""", unsafe_allow_html=True)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🍜 RAG Explorer")
    st.caption("Day 7 — Embedding & Vector Store")
    st.divider()

    # Documents
    st.subheader("📄 Documents")
    selected_docs = st.multiselect(
        "Chọn tài liệu",
        options=list(DATA_FILES.keys()),
        default=list(DATA_FILES.keys()),
    )

    # Metadata filter
    st.subheader("🔖 Metadata Filter")
    filter_category   = st.selectbox("category", CATEGORY_OPTIONS)
    filter_difficulty = st.selectbox("difficulty", DIFFICULTY_OPTIONS)

    st.divider()

    # Chunking
    st.subheader("✂️ Chunking Strategy")
    chunker_name = st.selectbox("Strategy", CHUNKER_NAMES)

    col1, col2 = st.columns(2)
    with col1:
        chunk_size = st.slider("chunk_size", 100, 800, 300, 50,
                               disabled=chunker_name in ("Sentence", "CustomRecipe"))
    with col2:
        overlap = st.slider("overlap", 0, 200, 50, 10,
                            disabled=chunker_name != "FixedSize")

    max_sentences = st.slider("max_sentences", 1, 10, 3,
                              disabled=chunker_name != "Sentence")
    top_k = st.slider("top_k (retrieve)", 1, 10, 3)

    st.divider()

    # Embedding & LLM
    st.subheader("🧠 Embedding & LLM")
    provider = st.selectbox("Embedding provider",
                            ["mock", "local", "openai"],
                            index=["mock","local","openai"].index(
                                os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
                            ))
    use_openai_llm = st.toggle("Use OpenAI LLM (gpt-4o-mini)", value=bool(os.getenv("OPENAI_API_KEY")))

    st.divider()
    show_chunking_tab = st.toggle("Show Chunking Analysis tab", value=True)
    show_compare_tab  = st.toggle("Show Strategy Comparison tab", value=False)

# ── main area ─────────────────────────────────────────────────────────────────
st.title("🔍 RAG Explorer — Vietnamese Recipes")

if not selected_docs:
    st.warning("Chọn ít nhất 1 tài liệu ở sidebar.")
    st.stop()

# Build everything
embedder = get_embedder(provider)
chunker  = build_chunker(chunker_name, chunk_size, overlap, max_sentences)
raw_files = load_documents(selected_docs)

metadata_filter = {}
if filter_category   != "(all)": metadata_filter["category"]   = filter_category
if filter_difficulty != "(all)": metadata_filter["difficulty"]  = filter_difficulty

with st.spinner("Building vector store…"):
    store, all_docs = make_store(raw_files, chunker, embedder, metadata_filter)

# ── Status bar ────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Documents", len(raw_files))
c2.metric("Total chunks", store.get_collection_size())
c3.metric("Strategy", chunker_name)
c4.metric("Embedder", getattr(embedder, "_backend_name", type(embedder).__name__)[:22])

st.divider()

# ── tabs ──────────────────────────────────────────────────────────────────────
tab_labels = ["💬 Ask & RAG"]
if show_chunking_tab: tab_labels.append("✂️ Chunking Analysis")
if show_compare_tab:  tab_labels.append("⚖️ Strategy Comparison")

tabs = st.tabs(tab_labels)
tab_idx = 0

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Ask & RAG
# ══════════════════════════════════════════════════════════════════════════════
with tabs[tab_idx]:
    tab_idx += 1

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Query")

        # Init session state key for query box
        if "query_text" not in st.session_state:
            st.session_state["query_text"] = ""

        # Quick benchmark buttons — set session state BEFORE text_area renders
        st.caption("Quick benchmark queries:")
        btn_cols = st.columns(len(BENCHMARK_QUERIES))
        for i, (col, q) in enumerate(zip(btn_cols, BENCHMARK_QUERIES)):
            if col.button(f"Q{i+1}", use_container_width=True, help=q):
                st.session_state["query_text"] = q
                st.session_state["run_rag"] = True

        query = st.text_area(
            "Nhập câu hỏi",
            key="query_text",
            height=80,
            placeholder="VD: What ingredients are needed for braised tofu?",
            label_visibility="collapsed",
        )

        run_btn = st.button("🚀  Run RAG", type="primary", use_container_width=True)
        # Also trigger from Q-button click
        if st.session_state.get("run_rag", False):
            run_btn = True
            del st.session_state["run_rag"]

    with col_right:
        st.subheader("Active Settings")
        st.json({
            "strategy": chunker_name,
            "chunk_size": chunk_size if chunker_name not in ("Sentence","CustomRecipe") else "N/A",
            "overlap": overlap if chunker_name == "FixedSize" else "N/A",
            "max_sentences": max_sentences if chunker_name == "Sentence" else "N/A",
            "top_k": top_k,
            "metadata_filter": metadata_filter or "none",
            "llm": "gpt-4o-mini" if use_openai_llm else "mock",
        })

    st.divider()

    if run_btn and query.strip():

        # Retrieve
        if metadata_filter:
            results = store.search_with_filter(query, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = store.search(query, top_k=top_k)

        # Build prompt
        context = "\n\n".join(
            f"[Source: {r['metadata'].get('doc_id', r['id'])}]\n{r['content']}"
            for r in results
        )
        prompt = (
            "Answer the question using the context below.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\nAnswer:"
        )

        # LLM answer
        with st.spinner("Generating answer…"):
            answer = call_llm(prompt, use_openai_llm)

        # ── Answer ──
        st.subheader("🤖 Agent Answer")
        st.success(answer)

        # ── Retrieved chunks ──
        st.subheader(f"📚 Retrieved Chunks (top {len(results)})")
        for i, r in enumerate(results):
            score = r["score"]
            score_class = "score-high" if score > 0.6 else ("score-med" if score > 0.4 else "score-low")
            doc_id   = r["metadata"].get("doc_id", r["id"])
            chunk_no = r["metadata"].get("chunk_index", "?")
            cat      = r["metadata"].get("category", "")
            diff     = r["metadata"].get("difficulty", "")

            with st.expander(
                f"#{i+1} · **{doc_id}** chunk#{chunk_no}  —  score: {score:.4f}",
                expanded=(i == 0),
            ):
                score_col, meta_col = st.columns([2, 3])
                with score_col:
                    st.markdown(f"<span class='{score_class}'>{score_bar(score)}</span>", unsafe_allow_html=True)
                with meta_col:
                    if cat:  st.markdown(f"<span class='tag'>📂 {cat}</span>", unsafe_allow_html=True)
                    if diff: st.markdown(f"<span class='tag'>⚡ {diff}</span>", unsafe_allow_html=True)
                st.code(r["content"], language=None)

    elif run_btn:
        st.warning("Nhập câu hỏi trước.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Chunking Analysis
# ══════════════════════════════════════════════════════════════════════════════
if show_chunking_tab:
    with tabs[tab_idx]:
        tab_idx += 1

        st.subheader("✂️ Chunking Analysis")
        st.caption("Xem cách mỗi strategy chia văn bản trên từng document.")

        doc_choice = st.selectbox("Chọn document để xem", selected_docs)
        path = DATA_FILES[doc_choice]
        text = path.read_text(encoding="utf-8")

        st.markdown(f"**Độ dài gốc:** {len(text)} ký tự")

        # Comparator stats
        st.markdown("### Baseline Comparison (chunk_size=300, overlap=50)")
        comp = ChunkingStrategyComparator().compare(text, chunk_size=300, over_lap=50)
        stat_cols = st.columns(3)
        for i, (name, stats) in enumerate(comp.items()):
            with stat_cols[i]:
                st.metric(name, f"{stats['count']} chunks", f"avg {stats['avg_length']:.0f} chars")

        st.divider()

        # Active strategy chunks
        st.markdown(f"### Chunks với strategy hiện tại: **{chunker_name}**")
        active_chunks = chunker.chunk(text)
        st.metric("Chunk count", len(active_chunks),
                  f"avg {sum(len(c) for c in active_chunks)/max(len(active_chunks),1):.0f} chars")

        for i, chunk in enumerate(active_chunks):
            with st.expander(f"Chunk #{i} — {len(chunk)} chars", expanded=(i < 2)):
                st.code(chunk, language=None)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Strategy Comparison
# ══════════════════════════════════════════════════════════════════════════════
if show_compare_tab:
    with tabs[tab_idx]:
        st.subheader("⚖️ Strategy Comparison")
        st.caption("So sánh top-1 retrieved doc của 4 strategies trên cùng query và embedder.")

        cmp_query = st.text_input(
            "Query để so sánh",
            value=BENCHMARK_QUERIES[0],
        )
        run_cmp = st.button("▶  Compare all strategies", type="primary")

        if run_cmp and cmp_query.strip():
            strategies = {
                "FixedSize":    FixedSizeChunker(chunk_size=chunk_size, overlap=overlap),
                "Sentence":     SentenceChunker(max_sentences_per_chunk=max_sentences),
                "Recursive":    RecursiveChunker(chunk_size=chunk_size),
                "CustomRecipe": CustomRecipeChunker(),
            }

            result_rows = []
            detail_data = {}

            with st.spinner("Running all strategies…"):
                for sname, sck in strategies.items():
                    s_docs = []
                    for doc_id, content, meta in raw_files:
                        for ci, chunk in enumerate(sck.chunk(content)):
                            s_docs.append(Document(
                                id=f"{doc_id}:{ci}",
                                content=chunk,
                                metadata={**meta, "doc_id": doc_id, "chunk_index": ci},
                            ))
                    s_store = EmbeddingStore(collection_name=f"cmp_{sname}", embedding_fn=embedder)
                    s_store.add_documents(s_docs)
                    top = s_store.search(cmp_query, top_k=3)
                    detail_data[sname] = top
                    top1 = top[0] if top else {}
                    result_rows.append({
                        "Strategy": sname,
                        "Chunks": s_store.get_collection_size(),
                        "Top-1 Doc": top1.get("metadata", {}).get("doc_id", "—"),
                        "Top-1 Score": f"{top1.get('score', 0):.4f}" if top1 else "—",
                        "Top-1 Preview": top1.get("content", "")[:80].replace("\n", " ") + "…" if top1 else "—",
                    })

            import pandas as pd
            st.dataframe(pd.DataFrame(result_rows), use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("### Top-3 Detail per Strategy")
            cols = st.columns(len(strategies))
            for col, (sname, tops) in zip(cols, detail_data.items()):
                with col:
                    st.markdown(f"**{sname}**")
                    for r in tops:
                        score = r["score"]
                        color = "#9ece6a" if score > 0.6 else ("#e0af68" if score > 0.4 else "#f7768e")
                        doc_id = r["metadata"].get("doc_id", r["id"])
                        chunk_no = r["metadata"].get("chunk_index", "?")
                        st.markdown(
                            f"<div style='border-left:3px solid {color};padding:6px 10px;"
                            f"margin:4px 0;border-radius:4px;background:#1e1e2e;font-size:0.8rem'>"
                            f"<b>{doc_id}</b> #{chunk_no}<br>"
                            f"<span style='color:{color}'>{score:.4f}</span><br>"
                            f"<span style='color:#a9b1d6'>{r['content'][:80].replace(chr(10),' ')}…</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
