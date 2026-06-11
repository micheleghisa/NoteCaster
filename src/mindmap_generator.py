import json
from src.llm_client import chat

SYSTEM_PROMPT = """Sei un esperto di organizzazione della conoscenza. Analizza il testo fornito ed estrai una mappa concettuale strutturata.

Restituisci SOLO un JSON valido con questa struttura esatta:
{
  "nodes": [
    {"id": "1", "label": "Concetto Centrale", "level": 0},
    {"id": "2", "label": "Argomento principale", "level": 1},
    {"id": "3", "label": "Sottoconcetto", "level": 2},
    {"id": "4", "label": "Dettaglio", "level": 3}
  ],
  "edges": [
    {"source": "1", "target": "2"},
    {"source": "2", "target": "3"}
  ]
}

Regole:
- level 0: 1 solo nodo centrale (argomento generale del documento)
- level 1: 4-7 argomenti principali
- level 2: 2-4 sottoconcetti per ogni argomento principale
- level 3: concetti specifici, farmaci, valori numerici importanti (opzionale)
- Etichette brevi: max 4-5 parole
- IDs: stringhe numeriche progressive ("1", "2", "3", ...)
- Nessun testo fuori dal JSON"""


def generate_mindmap(full_text: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Testo da analizzare:\n\n{full_text[:8000]}"},
    ]
    raw = chat(messages, temperature=0.3, max_tokens=2000)

    # Extract JSON from response (in case the model adds extra text)
    raw = raw.strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("Risposta non valida: nessun JSON trovato")
    return json.loads(raw[start:end])
