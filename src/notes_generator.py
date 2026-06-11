from src.llm_client import chat

NOTES_TYPES = ["Guida allo studio", "FAQ", "Riassunto", "Mappa concettuale", "Timeline"]

PROMPTS_IT = {
    "Guida allo studio": "Crea una guida allo studio completa e ben strutturata. Includi: concetti chiave con definizioni, meccanismi importanti da capire, rilevanza clinica, possibili domande d'esame (con risposta), cose fondamentali da memorizzare. Usa Markdown con headers, bold per termini chiave, e liste puntate.",
    "FAQ": "Crea 12-15 domande e risposte frequenti basate sui documenti. Spaziati da domande base a avanzate. Formato:\n**Q: [domanda]**\n**A:** [risposta dettagliata]\n\n",
    "Riassunto": "Crea un riassunto strutturato e dettagliato. Organizza per argomenti principali con subheader. Evidenzia i concetti più importanti in **grassetto**. Deve essere completo ma sintetico.",
    "Mappa concettuale": "Crea una mappa concettuale testuale. Usa indentazione (2 spazi per livello) e frecce (→) per mostrare relazioni causali o sequenziali. Mostra le connessioni tra i concetti chiaramente. Esempio formato:\nCONCETTO PRINCIPALE\n  → Sottoconcetto 1\n    → Dettaglio 1a\n  → Sottoconcetto 2",
    "Timeline": "Estrai e organizza tutte le informazioni sequenziali, cronologiche o progressive presenti nei documenti: progressione di malattia, fasi di trattamento, sviluppo storico, step diagnostici. Formato lista numerata con descrizioni."
}

def generate_notes(context_text: str, note_type: str, language: str = "it") -> str:
    if not context_text.strip():
        return "Nessun contenuto disponibile. Carica prima dei documenti nel notebook."
    prompt = PROMPTS_IT.get(note_type, PROMPTS_IT["Riassunto"])
    system = "Sei un tutor esperto per studenti di medicina. Rispondi SOLO in base al testo fornito. Usa Markdown per la formattazione. Sii preciso, completo e didattico."
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{prompt}\n\nTesto dei documenti:\n{context_text[:8000]}"}
    ]
    return chat(messages, temperature=0.3)
