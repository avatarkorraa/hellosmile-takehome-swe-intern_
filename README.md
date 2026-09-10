# HelloSmile — Take-Home Assignment (Software Engineer Intern)

Tempo previsto: **~2-2.5 ore** (Task 1-3 core, Task 4 bonus). Task 2 richiede
un account gratuito su [LiveKit Cloud](https://cloud.livekit.io/) — mettilo
in conto nel tempo di setup.

## Contesto

HelloSmile gestisce prenotazioni di studi odontoiatrici via voce (telefono,
LiveKit): il paziente chiama, parla con l'assistente vocale, che
prenota/riprogramma/cancella appuntamenti. Lo staff usa una dashboard per
gestire tutto.

Qui lavori su due componenti reali del prodotto, ridotti all'osso:

1. **API Service** (root, `main.py`): genera i token per le sessioni voce,
   tiene il context della clinica (orari, sede, servizi), registra le
   chiamate concluse.
2. **LiveKit Agent** (`./livekit`): l'assistente vocale.

**Obiettivo**: non impressionarci con infrastruttura, dimostrare che capisci
il problema abbastanza da costruire la soluzione più semplice che lo risolve
correttamente. Valutiamo codice, giudizio ingegneristico e le risposte
scritte sotto.

Puoi usare un AI coding assistant — anzi, usalo. Ma sei responsabile di ogni
riga: se propone middleware, layer di astrazione o gestione di casi che qui
non esistono, buttali via.

> Info mancanti o requisiti ambigui: fai un'assunzione ragionevole, commenta
> la scelta in una riga.

## Setup

Richiede Python 3.11+ e [uv](https://github.com/astral-sh/uv).

```bash
uv sync
cp .env.example .env
```

Inserisci in `.env` le credenziali di un progetto gratuito su [LiveKit
Cloud](https://cloud.livekit.io/) (URL, API Key, Secret). Basta quello: STT/
LLM/TTS passano dal gateway di inferenza di LiveKit, niente chiavi separate
per Deepgram/Gemini/Cartesia.

*Aggiungi pure qualunque pacchetto ti serva.*

**API Service**

```bash
uv run uvicorn main:app --reload
```

Parte subito (`curl http://localhost:8000/health`). `/token`,
`/rooms/active` e `PATCH /context` esistono ma **non sono protetti** — Task 1.

Per generare token di test:

```bash
uv run python -m utils.auth
```

Stampa un token "staff" e uno "patient" (claim `{sub, role[, patient_id]}`),
da usare come `Authorization: Bearer <token>`.

**LiveKit Agent** (con l'API service già in esecuzione)

```bash
uv run -m livekit.main console   # locale, mic/speaker
uv run -m livekit.main dev       # via agents-playground.livekit.io
```

**Test**

```bash
uv run pytest
```

## Task 1 — Auth + FastAPI (core, ~60 min)

`utils/auth.py` ha già `create_test_token(sub, role, patient_id=None)`: token
fittizio `<payload-base64>.<firma-hmac-hex>`, non un vero JWT — formato
minimo per non richiedere librerie esterne.

`main.py` genera già token LiveKit **reali** (`utils/livekit_tokens.py`) ma
non verifica chi chiama:

- `POST /token` — chiunque, per qualsiasi room/identity.
- `GET /rooms/active` — chiunque.
- `PATCH /context` — chiunque può cambiare orari/sede/servizi.

Da fare:

1. Verifica del token con solo `hmac`, `hashlib`, `base64`, `json` (già
   disponibili in `utils/auth.py`) — niente `python-jose`, `authlib`, SDK
   Auth0 o simili.
2. Regole:
   - `staff` → qualsiasi room, `/rooms/active`, `PATCH /context` OK.
   - `patient` → solo token per `patient-{patient_id}` proprio (altrimenti
     `403`); `403` fisso su `/rooms/active` e `PATCH /context`.
   - Token assente/malformato/firma invalida → `401`.
3. `GET /context` e `POST /calls` restano pubblici (li chiama l'agente) —
   non toccarli.

## Task 2 — LiveKit reale (core, ~50 min)

`livekit/main.py` è quasi completo. Da fare:

1. **Verifica il flusso token → identity → room**: prendi un token da
   `POST /token` (protetto al Task 1) ed entra davvero in una room via
   `console`/`dev`. Un token "patient" deve funzionare solo sulla propria
   `patient-{patient_id}`.
2. **Fetch del context**: all'avvio, `GET {API_BASE_URL}/context` e
   iniettalo nelle istruzioni dell'`Assistant` — niente dati hardcoded.
3. **Report della chiamata**: a fine sessione, `POST {API_BASE_URL}/calls`
   con transcript (`session.history`) e durata.

Niente riconnessioni o retry sofisticati: fetch/report semplice e diretto.

## Task 3 — Prompt Engineering (core, ~15 min)

Il prompt in `Assistant.__init__` è deliberatamente mediocre: tono generico,
nessun vincolo su lunghezza risposte, out-of-scope o emergenze.

Riscrivilo per HelloSmile, con indicazioni chiare su:

- **Tono**: è una telefonata, non una chat.
- **Lunghezza**: niente muri di testo via voce.
- **Fuori scope**: cosa risponde se la richiesta non è prenotazione/
  riprogrammazione/cancellazione.
- **Emergenze dentali**: dolore acuto, trauma, sanguinamento — niente
  diagnosi o consigli medici, indirizza al contatto dello studio.

Aggiungi 3-5 righe di commento sopra il prompt con le scelte fatte.

## Task 4 — Bug Hunting (bonus, ~15 min)

`bonus.py` è un webhook per eventi join/leave, con **2-3 bug reali** non
segnalati. Se hai tempo: trovali, correggili, aggiungi test che falliscano
prima della fix e passino dopo. Non ti diciamo dove sono — è concorrenza e
input non fidato, il resto è capire dove può rompersi.

## Vincoli

Non sono suggerimenti:

- Niente DB esterno, Redis, cache: solo in-memory (già impostato).
- Niente scalabilità multi-processo/worker — ottimizza per semplicità.
- Niente librerie di auth esterne nel Task 1 (solo `utils/` + stdlib). Le
  dipendenze già in `pyproject.toml` — FastAPI, LiveKit, pydantic-settings —
  sono starter, non contano.
- Task 1: soluzione in **meno di ~100 righe** applicative (escluso starter/
  config/boilerplate). Molto di più è un segnale da guardare, non un
  traguardo.

## Domande di design (2-4 righe ciascuna, qui sotto)

1. Perché questo approccio per i permessi staff/patient, invece di
   un'alternativa (ruoli generici, tabella permessi, ...)?

Perchè per il contesto del task aggiungere ulteriore complessità tramite una tabella dei permessi e ruoli generici va contro la semplicità richiesta dal task stesso all'interno della traccia, non serve complicare la struttura del codice e la logica implementativa in quanto con la divisione degli accessi tra Staff e Utente normale si riesce già a gestire le autorizzazioni e gli accessi.

2. Due richieste concorrenti sulla stessa room: il tuo codice lo gestisce?
   Come, o perché no?

No, non è implementato un vero controllo di concorrenza sulla room. Non sono presenti database o strutture condivise all'interno del codice che necessitano del controllo contemporaneo della risorsa, se due richieste avvengono contemporaneamente sulla stessa room semplicemente avviene la verifica del token. L'architettura attuale non lo richiede.

3. Ci sono componenti che potresti togliere mantenendo la funzionalità? Se
   sì perché li hai tenuti, se no perché è già minimale?

No, l'architettura del task è già minimale in quanto ci sono solamente i componenti essenziali per lo svolgimento dello stesso, l'agente, la creazione del token con relativa verifica, la gestione dei ruoli e dell'accesso.

## Bonus extra

- Test aggiuntivi per l'API service oltre al Task 4.
- `docker-compose.yml` per API + agent (dev mode) con un comando.

## Consegna

1. Clicca **"Use this template" → "Create a new repository"** in alto su
   GitHub: ti crea una tua copia **privata**, indipendente da questa (non è
   un fork).
2. Aggiungi `PaulMagos` come collaboratore alla tua copia.
3. Commit incrementali (uno per auth check, uno per permessi, uno per
   Task 2, uno per il prompt, uno per eventuali fix del bonus) — niente
   commit unico "solution".
4. Rispondi alle domande di design qui sopra, poi manda il link al team.
