import asyncio
import os
import re
import time
import tempfile

import edge_tts
from pydub import AudioSegment

from src.llm_client import chat

# ---------------------------------------------------------------------------
# Voice configuration
# ---------------------------------------------------------------------------
VOICES_IT = {"MARCO": "it-IT-DiegoNeural", "SOFIA": "it-IT-ElsaNeural"}
VOICES_EN = {"ALEX": "en-US-GuyNeural", "EMMA": "en-US-JennyNeural"}

OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "podcasts")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Detail level configuration
#
# chunk_chars:    chars fed to each LLM call in multi-chunk mode
# max_text_chars: hard cap on total text used (None = use everything)
# words_range:    target script length per chunk
# minutes_range:  expected audio duration per chunk (shown in prompt)
# max_tokens:     LLM output cap per call
# multi_chunk:    True = split full text into chunks and concatenate audio
# ---------------------------------------------------------------------------
_DETAIL_CONFIG: dict[str, dict] = {
    "Panoramica": {
        "chunk_chars": None,
        "max_text_chars": 5_000,
        "words_range": "400-600",
        "minutes_range": "3-5",
        "max_tokens": 1_400,
    },
    "Approfondito": {
        "chunk_chars": None,
        "max_text_chars": 22_000,
        "words_range": "1600-2200",
        "minutes_range": "12-18",
        "max_tokens": 3_800,
    },
    # chunk_chars=13_000: ~2.000 parole di testo fonte per chunk.
    # Copre tutti gli argomenti del materiale con profondità di studio, non da esame.
    # chunk_chars=22_000: ~3 chunk su 50k chars → ~20 min totali.
    # Meno giunture = meno ripetizioni tra sezioni.
    "Completo": {
        "chunk_chars": 22_000,
        "max_text_chars": None,
        "words_range": "1200-1600",
        "minutes_range": "10-13",
        "max_tokens": 3_200,
    },
    # chunk_chars=14_000: ~4 chunk su 50k chars → ~35-40 min totali.
    "Dettagliato (esame)": {
        "chunk_chars": 14_000,
        "max_text_chars": None,
        "words_range": "1500-2000",
        "minutes_range": "12-16",
        "max_tokens": 4_000,
    },
    "Overview": {
        "chunk_chars": None,
        "max_text_chars": 5_000,
        "words_range": "400-600",
        "minutes_range": "3-5",
        "max_tokens": 1_400,
    },
    "In-depth": {
        "chunk_chars": None,
        "max_text_chars": 22_000,
        "words_range": "1600-2200",
        "minutes_range": "12-18",
        "max_tokens": 3_800,
    },
    "Complete": {
        "chunk_chars": 22_000,
        "max_text_chars": None,
        "words_range": "1200-1600",
        "minutes_range": "10-13",
        "max_tokens": 3_200,
    },
    "Detailed (exam)": {
        "chunk_chars": 14_000,
        "max_text_chars": None,
        "words_range": "1500-2000",
        "minutes_range": "12-16",
        "max_tokens": 4_000,
    },
}

_FALLBACK_CONFIG: dict = _DETAIL_CONFIG["Approfondito"]

# Exported for app.py selectors
DETAIL_LEVELS_IT = {
    "Panoramica": (
        "Divulgativo — solo i concetti chiave, ideale per un primo approccio. (~3-5 min)"
    ),
    "Approfondito": (
        "Intermedio — terminologia corretta, meccanismi fisiopatologici, collegamento clinico. (~12-18 min)"
    ),
    "Completo": (
        "Studio completo — tutti gli argomenti del materiale coperti con meccanismi, classificazioni, "
        "clinica, diagnostica e terapia. Mnemoniche e analogie. (~15-20 min, scala con il materiale)"
    ),
    "Dettagliato (esame)": (
        "Ripetizione da esame — ogni argomento trattato per intero: eziopatogenesi, classificazioni, "
        "clinica, diagnostica (lab/ECG/imaging), diagnosi differenziale, terapia. "
        "Nessuna omissione. Analogie, mnemoniche e battute per fissare ogni concetto. "
        "(~35-40 min, scala con il materiale)"
    ),
}
DETAIL_LEVELS_EN = {
    "Overview": (
        "Introductory — key concepts only, ideal for a first approach. (~3-5 min)"
    ),
    "In-depth": (
        "Intermediate — correct terminology, pathophysiological mechanisms, clinical links. (~12-18 min)"
    ),
    "Complete": (
        "Full study — every topic in the material covered with mechanisms, classifications, "
        "clinical picture, diagnostics and treatment. Mnemonics and analogies. (~15-20 min, scales with material)"
    ),
    "Detailed (exam)": (
        "Exam repetition — every topic covered in full: etiopathogenesis, classifications, "
        "clinical features, diagnostics (labs/ECG/imaging), differential diagnosis, treatment. "
        "No omissions. Analogies, mnemonics and humour to anchor every concept. "
        "(~35-40 min, scales with material)"
    ),
}


# ---------------------------------------------------------------------------
# 1. Language detection
# ---------------------------------------------------------------------------
def detect_language(text: str) -> str:
    """Return 'it' if Italian marker density >4% in first 200 words, else 'en'."""
    italian_markers = {
        "della", "dello", "degli", "nella", "nelle", "questo", "questa",
        "sono", "anche", "quindi", "oppure", "però", "viene", "mentre", "dopo",
    }
    words = text.lower().split()
    if not words:
        return "en"
    sample = words[:200]
    hits = sum(1 for w in sample if w in italian_markers)
    return "it" if hits / len(sample) > 0.04 else "en"


# ---------------------------------------------------------------------------
# 2. Semantic chunking
# ---------------------------------------------------------------------------
def _split_into_chunks(text: str, chunk_chars: int, overlap: int = 400) -> list[str]:
    """Split text into ~chunk_chars pieces, preferring paragraph/sentence boundaries."""
    text = text.strip()
    if len(text) <= chunk_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_chars, len(text))
        if end < len(text):
            boundary = text.rfind("\n\n", start + chunk_chars // 2, end)
            if boundary == -1:
                boundary = text.rfind(". ", start + chunk_chars // 2, end)
                if boundary != -1:
                    boundary += 1
            if boundary != -1:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        next_start = end - overlap
        start = next_start if next_start > start else end

    return chunks


# ---------------------------------------------------------------------------
# 3. Prompt builders
# ---------------------------------------------------------------------------
def _build_system_prompt(
    language: str,
    detail_level: str,
    words_range: str,
    minutes_range: str,
    topic: str,
    segment_role: str | None,
    previous_context: str = "",
) -> str:
    is_exam = detail_level in ("Dettagliato (esame)", "Detailed (exam)")
    is_complete = detail_level in ("Completo", "Complete")
    is_it = language == "it"

    detail_desc = (
        DETAIL_LEVELS_IT.get(detail_level, DETAIL_LEVELS_IT["Approfondito"])
        if is_it else
        DETAIL_LEVELS_EN.get(detail_level, DETAIL_LEVELS_EN["In-depth"])
    )

    if is_it:
        topic_block = (
            f"\n\nARGOMENTO OBBLIGATORIO: «{topic}»\n"
            "Tratta ESCLUSIVAMENTE questo argomento. Ignora le sezioni del materiale non pertinenti."
            if topic else ""
        )
        complete_block = ""
        exam_block = (
            """

MODALITÀ RIPETIZIONE DA ESAME — REGOLE ASSOLUTE:
- Tratta questo materiale come se stessi ripetendo le sbobbine ad alta voce per prepararti all'esame
- NESSUNA omissione: se nel testo appare un argomento, una patologia, una classificazione, \
un esame diagnostico, un farmaco, una tecnica — lo trattate nel dettaglio. Punto.
- Se il materiale elenca 5 patologie, le trattate tutte e 5. Se elenca 3 tecniche di imaging, \
le spiegate tutte e 3 (cosa mostrano, quando si usa una vs l'altra, limitazioni)
- Per ogni argomento principale coprite TUTTO nell'ordine: definizione → eziopatogenesi → \
fisiopatologia → classificazione (con criteri) → quadro clinico → diagnostica (lab, ECG, \
imaging — ogni tecnica spiegata nel dettaglio) → diagnosi differenziale → terapia medica \
e interventistica (con nomi dei farmaci, indicazioni, controindicazioni) → prognosi
- NON riassumere, NON fare panoramiche generali: approfondisci ogni punto come farebbe \
un medico che interroga uno studente all'esame
- Usa analogie e metafore vivide per ogni concetto fisiopatologico difficile \
(es. "il ventricolo sinistro è come un pistone che deve vincere la pressione aortica…")
- Inserisci battute o osservazioni ironiche per alleggerire senza perdere rigore clinico
- Usa tecniche mnemoniche: acronimi, rime, storie brevi — ancorate ai concetti reali
- Fai sbagliare Marco su un dettaglio tecnico specifico in ogni segmento: Sofia lo corregge \
con precisione — questo crea un momento di ancoraggio forte per chi ascolta"""
            if is_exam else ""
        )
        if segment_role == "first":
            segment_block = (
                "\n\nQuesto è il PRIMO segmento. "
                "Apri con un hook coinvolgente (domanda provocatoria, caso clinico breve, statistica sorprendente)."
            )
        elif segment_role == "middle":
            segment_block = (
                "\n\nQuesto è un segmento INTERMEDIO. "
                "Inizia direttamente con 'Continuiamo con…' o simile — niente riepilogo, niente intro. "
                "Puoi terminare a metà di un concetto se il materiale lo richiede."
            )
        elif segment_role == "last":
            segment_block = (
                "\n\nQuesto è l'ULTIMO segmento. "
                "Chiudi con 2-3 takeaway pratici ad alta densità mnemonica e un finale naturale."
            )
        else:
            segment_block = ""

        context_block = (
            f"\n\nARGOMENTI GIÀ TRATTATI nei segmenti precedenti — NON ripetere, NON riepilogare, prosegui direttamente:\n{previous_context}"
            if previous_context else ""
        )

        length_instruction = f"~{words_range} parole ({minutes_range} minuti di audio) — rispetta il range"
        extra_block = exam_block or complete_block

        return f"""Sei un produttore di podcast educativi di alto livello.
Crea uno script per un podcast a due conduttori che discutono materiale medico/scientifico.

I conduttori:
- MARCO: studente avanzato, curioso, fa domande intelligenti, a volte anticipa (e sbaglia), collega i concetti tra loro
- SOFIA: medico/esperta, spiega in profondità, porta esempi clinici reali, corregge con precisione e calore umano

Requisiti dello script:
- Autenticamente conversazionale — mai una lista letta ad alta voce
- {length_instruction}
- Interjections naturali: "Aspetta—", "Quindi vuoi dire che…", "Esatto, e questo è fondamentale perché…"{extra_block}

Livello di dettaglio: {detail_desc}{topic_block}{context_block}{segment_block}

FORMATO OBBLIGATORIO — una battuta per riga, nessun altro testo:
MARCO: [testo della battuta]
SOFIA: [testo della battuta]"""

    else:
        topic_block = (
            f"\n\nMANDATORY TOPIC: «{topic}»\n"
            "Cover ONLY this topic. Ignore unrelated sections in the source material."
            if topic else ""
        )
        complete_block = ""
        exam_block = (
            """

EXAM REPETITION MODE — ABSOLUTE RULES:
- Treat this material as if you are reciting lecture notes aloud to prepare for an exam
- NO omissions: if the text mentions a topic, pathology, classification, diagnostic test, \
drug, or technique — discuss it in full detail. No exceptions.
- If the material lists 5 pathologies, cover all 5. If it lists 3 imaging techniques, \
explain all 3 (what each shows, when to use one vs the other, limitations)
- For every main topic cover EVERYTHING in order: definition → etiopathogenesis → \
pathophysiology → classification (with criteria) → clinical picture → diagnostics (labs, ECG, \
imaging — each technique explained in detail) → differential diagnosis → medical and \
interventional treatment (drug names, indications, contraindications) → prognosis
- Do NOT summarize, do NOT give general overviews: go deep on every point as a physician \
would when examining a student in an oral exam
- Use vivid analogies and metaphors for every difficult pathophysiological concept \
(e.g. "the left ventricle is like a piston that must overcome aortic pressure…")
- Include jokes or witty observations to keep it engaging without sacrificing clinical rigour
- Use mnemonic devices: acronyms, rhymes, short stories — anchored to real concepts
- Have Alex get a specific technical detail wrong in every segment: Emma corrects him \
precisely — this creates a strong anchor moment for the listener"""
            if is_exam else ""
        )
        if segment_role == "first":
            segment_block = (
                "\n\nThis is the FIRST segment. "
                "Open with an engaging hook (provocative question, brief case, surprising statistic)."
            )
        elif segment_role == "middle":
            segment_block = (
                "\n\nThis is a MIDDLE segment. "
                "Start directly with 'Let's continue with…' or similar — no recap, no intro. "
                "You may end mid-concept if the material requires it."
            )
        elif segment_role == "last":
            segment_block = (
                "\n\nThis is the LAST segment. "
                "Close with 2-3 high-density mnemonic takeaways and a natural ending."
            )
        else:
            segment_block = ""

        context_block = (
            f"\n\nTOPICS ALREADY COVERED in previous segments — do NOT repeat, do NOT recap, continue directly:\n{previous_context}"
            if previous_context else ""
        )

        length_instruction = f"~{words_range} words ({minutes_range} minutes of audio) — stay within this range"
        extra_block = exam_block or complete_block

        return f"""You are a high-quality educational podcast producer.
Create a script for a two-host podcast discussing scientific/academic material.

The hosts:
- ALEX: advanced student, curious, asks smart questions, sometimes anticipates (and gets things wrong), connects concepts
- EMMA: clinician/expert, explains in depth, brings real clinical examples, corrects with precision and warmth

Script requirements:
- Authentically conversational — never a list read aloud
- {length_instruction}
- Natural interjections: "Wait—", "So you're saying that…", "Exactly, and that matters because…"{extra_block}

Detail level: {detail_desc}{topic_block}{context_block}{segment_block}

MANDATORY FORMAT — one line per turn, nothing else:
ALEX: [line text]
EMMA: [line text]"""


# ---------------------------------------------------------------------------
# 4. Script generation for a single chunk
# ---------------------------------------------------------------------------
def _generate_chunk_script(
    text: str,
    language: str,
    detail_level: str,
    topic: str,
    config: dict,
    segment_role: str | None,
    previous_context: str = "",
) -> str:
    system = _build_system_prompt(
        language,
        detail_level,
        config["words_range"],
        config["minutes_range"],
        topic,
        segment_role,
        previous_context=previous_context,
    )
    if language == "it":
        user_content = (
            f"ARGOMENTO: {topic}\n\nMateriale fonte:\n\n{text}"
            if topic else
            f"Materiale fonte:\n\n{text}"
        )
    else:
        user_content = (
            f"TOPIC: {topic}\n\nSource material:\n\n{text}"
            if topic else
            f"Source material:\n\n{text}"
        )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]
    return chat(messages, temperature=0.88, max_tokens=config["max_tokens"])


# ---------------------------------------------------------------------------
# 5. Script parsing
# ---------------------------------------------------------------------------
def _extract_topics_header(script: str, max_lines: int = 8) -> str:
    """Estrae le prime battute dello script per indicare al chunk successivo gli argomenti già trattati."""
    lines = [l.strip() for l in script.strip().splitlines() if l.strip()]
    return "\n".join(lines[:max_lines])


def parse_script(script: str) -> list[tuple[str, str]]:
    """Parse a script string into a list of (SPEAKER, text) tuples."""
    lines: list[tuple[str, str]] = []
    for raw in script.strip().splitlines():
        raw = raw.strip()
        if not raw:
            continue
        m = re.match(r"^(MARCO|SOFIA|ALEX|EMMA)\s*:\s*(.+)$", raw, re.IGNORECASE)
        if m:
            lines.append((m.group(1).upper(), m.group(2).strip()))
    return lines


# ---------------------------------------------------------------------------
# 6. TTS synthesis
# ---------------------------------------------------------------------------
async def _synthesize_line(text: str, voice: str, path: str, retries: int = 3) -> None:
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(path)
            return
        except Exception:
            if attempt < retries - 1:
                await asyncio.sleep(1.5 * (attempt + 1))
            else:
                raise


async def _lines_to_audio_segment(
    lines: list[tuple[str, str]],
    voices: dict,
    global_offset: int,
    total_lines: int,
    progress_cb=None,
) -> AudioSegment:
    inter_silence = AudioSegment.silent(duration=350)
    combined = AudioSegment.empty()

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, (speaker, text) in enumerate(lines):
            voice = voices.get(speaker, next(iter(voices.values())))
            tmp = os.path.join(tmpdir, f"line_{i:04d}.mp3")
            await _synthesize_line(text, voice, tmp)
            combined += AudioSegment.from_mp3(tmp) + inter_silence
            if progress_cb:
                progress_cb(global_offset + i + 1, total_lines)
            # piccola pausa tra le chiamate TTS per evitare rate limiting
            if i < len(lines) - 1:
                await asyncio.sleep(0.1)

    return combined


# ---------------------------------------------------------------------------
# 7. Public entry point
# ---------------------------------------------------------------------------
def generate_podcast(
    full_text: str,
    notebook_id: str,
    language: str = "auto",
    topic: str = "",
    detail_level: str = "",
    progress_cb=None,
    status_cb=None,
) -> tuple[str, str]:
    """
    Generate a two-host podcast from source text.

    Args:
        full_text:    raw text extracted from uploaded documents
        notebook_id:  used to name the output file
        language:     'it', 'en', or 'auto'
        topic:        optional topic filter written by the user
        detail_level: key from DETAIL_LEVELS_IT / DETAIL_LEVELS_EN
        progress_cb:  callable(done: int, total: int) for audio synthesis progress
        status_cb:    callable(msg: str) for status updates during script generation

    Returns:
        (combined_script, output_path)
    """
    def _status(msg: str) -> None:
        if status_cb:
            status_cb(msg)

    if language == "auto":
        language = detect_language(full_text)

    config = _DETAIL_CONFIG.get(detail_level, _FALLBACK_CONFIG)

    # ── Prepare chunks ────────────────────────────────────────────────────────
    if config["max_text_chars"] is not None:
        chunks = [full_text[: config["max_text_chars"]].strip()]
    else:
        chunks = _split_into_chunks(full_text, config["chunk_chars"])

    chunks = [c for c in chunks if c]
    if not chunks:
        raise ValueError("Nessun testo disponibile per generare il podcast.")

    n = len(chunks)
    voices = VOICES_IT if language == "it" else VOICES_EN

    # ── Generate scripts ──────────────────────────────────────────────────────
    scripts: list[str] = []
    all_lines: list[list[tuple[str, str]]] = []
    previous_context: str = ""

    for i, chunk in enumerate(chunks):
        if n == 1:
            role = None
        elif i == 0:
            role = "first"
        elif i == n - 1:
            role = "last"
        else:
            role = "middle"

        if n > 1:
            _status(f"Generazione script — segmento {i + 1} di {n}…")
        else:
            _status("Generazione script…")

        script = _generate_chunk_script(
            chunk, language, detail_level, topic, config, role,
            previous_context=previous_context,
        )
        lines = parse_script(script)
        if not lines:
            raise ValueError(
                f"Script non valido al segmento {i + 1} — nessuna battuta riconosciuta."
            )
        scripts.append(script)
        all_lines.append(lines)
        previous_context = _extract_topics_header(script)

    # ── Build audio ───────────────────────────────────────────────────────────
    total_lines = sum(len(l) for l in all_lines)
    segment_gap = AudioSegment.silent(duration=1_500)

    async def _assemble() -> AudioSegment:
        combined = AudioSegment.empty()
        done = 0
        for idx, lines in enumerate(all_lines):
            chunk_audio = await _lines_to_audio_segment(
                lines, voices, done, total_lines, progress_cb
            )
            combined += chunk_audio
            done += len(lines)
            if idx < len(all_lines) - 1:
                combined += segment_gap
        return combined

    _status("Sintesi audio in corso…")
    loop = asyncio.new_event_loop()
    try:
        final_audio = loop.run_until_complete(_assemble())
    finally:
        loop.close()

    filename = f"podcast_{notebook_id}_{int(time.time())}.mp3"
    output_path = os.path.join(OUTPUTS_DIR, filename)
    final_audio.export(output_path, format="mp3", bitrate="128k")

    return ("\n\n---\n\n".join(scripts), output_path)
