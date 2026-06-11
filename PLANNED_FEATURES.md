# Feature Planning

## 📝 Note automatiche

Già implementata in `src/notes_generator.py` e `app.py` (tab nascosta).
Da riabilitare quando si vuole rilasciare.

**Funzionalità:**
- Selettore sorgente: sbobina singola o tutto il notebook
- Tipi: Guida allo studio, FAQ, Riassunto, Mappa concettuale (testuale), Timeline
- Download .md del risultato
- Cache per sorgente + tipo (switching tra documenti non sovrascrive)

**Per riabilitare:**
1. In `app.py`, cambia la riga dei tabs in:
   `tab_chat, tab_notes, tab_podcast = st.tabs(["💬 Chat", "📝 Note", "🎙️ Podcast"])`
2. Reinserisci il blocco `with tab_notes:` (vedi git history: commit `e2fe104`)

---

## 🗺️ Mappa concettuale interattiva

Già implementata in `src/mindmap_generator.py`.
Richiede il pacchetto `streamlit-agraph` (da aggiungere a `requirements.txt`).

**Funzionalità:**
- Grafo interattivo con nodi colorati per livello gerarchico
- Selettore: sbobina singola o tutto l'esame
- Più mappe generabili e confrontabili nella stessa sessione

**Per implementare:**
1. Aggiungere `streamlit-agraph` a `requirements.txt`
2. Aggiungere tab `🗺️ Mappa` nella riga dei tabs
3. Reinserire il blocco `with tab_map:` (vedi git history: commit `3366cab`, file `app.py` originale)
4. Aggiungere selettore sorgente per sbobina singola (stesso pattern di Note e Podcast)
