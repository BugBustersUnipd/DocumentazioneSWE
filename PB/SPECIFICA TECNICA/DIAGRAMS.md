# Diagrammi Architetturali – MVP

> Diagrammi C4, sequenze, state machine e struttura dati.
> Tutti i diagrammi usano sintassi **Mermaid** (renderizzabile su GitHub, VSCode, Notion, Obsidian).

---

## Indice

1. [C4 Level 1 – Contesto di sistema](#c4-level-1--contesto-di-sistema)
2. [C4 Level 2 – Container](#c4-level-2--container)
3. [C4 Level 3 – Componenti Document Processing](#c4-level-3--componenti-document-processing)
4. [C4 Level 3 – Componenti AI Generator](#c4-level-3--componenti-ai-generator)
5. [Diagramma di Sequenza – Estrazione PDF](#diagramma-di-sequenza--estrazione-pdf)
6. [Diagramma di Sequenza – Generazione Contenuti AI](#diagramma-di-sequenza--generazione-contenuti-ai)
7. [State Machine – ExtractedDocument](#state-machine--extracteddocument)
8. [State Machine – ProcessingRun](#state-machine--processingrun)
9. [Modello ER semplificato](#modello-er-semplificato)
10. [Architettura Deploy](#architettura-deploy)
11. [Pipeline CI/CD](#pipeline-cicd)

---

## C4 Level 1 – Contesto di sistema

Mostra il sistema nel suo contesto: chi lo usa e con quali sistemi esterni interagisce.

```mermaid
flowchart TB
    classDef person  fill:#08427b,color:#fff,stroke:#073b6f
    classDef system  fill:#1168bd,color:#fff,stroke:#0b4884
    classDef ext     fill:#6b6b6b,color:#fff,stroke:#575757

    U(["👤 Operatore
    ──────────────
    Carica documenti
    Valida estrazioni
    Genera contenuti"]):::person

    subgraph boundary [" "]
        MVP["🖥️  Piattaforma MVP
        ──────────────────────
        Estrazione documenti AI
        Generazione contenuti
        Analytics in tempo reale"]:::system
    end

    TX["☁️  AWS Textract
    ──────────────────
    OCR: estrazione testo
    da PDF e immagini"]:::ext

    BD["☁️  AWS Bedrock
    ──────────────────
    LLM: Claude / Nova Lite
    Text & Image generation"]:::ext

    U       -- "usa via browser  •  HTTPS / WebSocket" --> boundary
    boundary -- "OCR request  •  AWS SDK"               --> TX
    boundary -- "LLM inference  •  AWS SDK"              --> BD
```

---

## C4 Level 2 – Container

Mostra i container (processi/deployment unit) che compongono il sistema.

```mermaid
flowchart TB
    classDef person fill:#08427b,color:#fff,stroke:#073b6f
    classDef fe     fill:#1168bd,color:#fff,stroke:#0b4884
    classDef be     fill:#1168bd,color:#fff,stroke:#0b4884
    classDef db     fill:#2d6a4f,color:#fff,stroke:#1b4332
    classDef ext    fill:#6b6b6b,color:#fff,stroke:#575757

    U(["👤 Operatore"]):::person

    subgraph client ["  Browser  "]
        FE["Angular 21 SPA
        ────────────────
        TypeScript · PrimeNG
        Chart.js · Bootstrap 5"]:::fe
    end

    subgraph server ["  Backend  Rails 8 · Puma  "]
        direction LR
        BE["Rails API
        ────────────────
        Business logic
        REST · WebSocket"]:::be
        WK["Solid Queue Workers
        ────────────────
        Elaborazione asincrona
        PDF · OCR · LLM · Gen"]:::be
        BE -. "job dispatch" .- WK
    end

    subgraph pg ["  PostgreSQL 16  —  Solid Stack  "]
        direction LR
        DB1[("Primary
        Dati app")]:::db
        DB2[("Queue
        Job queue")]:::db
        DB3[("Cache
        App cache")]:::db
        DB4[("Cable
        WebSocket")]:::db
    end

    subgraph aws ["  AWS Cloud  "]
        direction LR
        TX["Textract
        OCR"]:::ext
        BD["Bedrock
        LLM · Image"]:::ext
    end

    U      -- "HTTPS / WebSocket"       --> client
    client -- "REST JSON · WebSocket"   --> BE
    BE     --> DB1 & DB3 & DB4
    WK     --> DB1 & DB2
    WK     -- "AWS SDK" --> TX & BD
```

---

## C4 Level 3 – Componenti Document Processing

Dettaglio del modulo principale di estrazione documenti nel backend.
Lettura da sinistra a destra: ogni colonna è uno strato architetturale.

```mermaid
flowchart LR
    classDef http    fill:#dbeafe,stroke:#2563eb,color:#1e3a5f
    classDef cmd     fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef orch    fill:#d1fae5,stroke:#059669,color:#064e3b
    classDef svc     fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef infra   fill:#fce7f3,stroke:#db2777,color:#500724
    classDef di      fill:#f1f5f9,stroke:#94a3b8,color:#0f172a

    subgraph L1 ["① HTTP Layer"]
        CTRL["DocumentsController
        ─────────────
        Routing
        Validazione
        Risposta HTTP"]:::http
    end

    subgraph L2 ["② Commands"]
        CMD1["InitializeProcessing
        ─────────────
        Checksum · Upload
        Enqueue split job"]:::cmd
        CMD2["InitializeFileProcessing
        ─────────────
        CSV / Immagine
        Enqueue file job"]:::cmd
    end

    subgraph L3 ["③ Orchestratori"]
        DI["DI Container
        ─────────────
        30+ dipendenze
        lazy-loaded"]:::di
        OR1["ProcessSplitRun
        ─────────────
        PDF → breakpoints
        → ExtractedDocs"]:::orch
        OR2["ProcessDataItem
        ─────────────
        OCR→LLM→Match
        →Confidence→WS"]:::orch
        OR3["ProcessGenericFile
        ─────────────
        Routing
        CSV / Immagine"]:::orch
    end

    subgraph L4 ["④ Domain Services"]
        OCR["OCR
        Textract adapter"]:::svc
        LLM["LlmService
        Bedrock adapter"]:::svc
        EXT["DataExtractor
        prompt engineering"]:::svc
        META["ExtractedMetadataBuilder
        struttura metadati"]:::svc
        RES["RecipientResolver
        Jaro-Winkler + Dice"]:::svc
        RRR["RecipientResolutionResult
        value object risultato"]:::svc
        CONF["ConfidenceCalculator
        OCR + match score"]:::svc
        PGPDF["PageRangePdf
        range pagine PDF"]:::svc
    end

    subgraph L5 ["⑤ Infrastructure"]
        R1["DataItemRepository
        CRUD + locking"]:::infra
        R2["SplitRunRepository
        state management"]:::infra
        NOT["ActionCableNotifier
        WebSocket broadcast"]:::infra
        PRES["ExtractedDocumentPresenter
        JSON serialization"]:::infra
        UPL["UploadManager
        checksum + storage"]:::infra
    end

    CTRL  --> CMD1 & CMD2
    CTRL  --> PRES
    CMD1  --> UPL & OR1 & OR2
    CMD2  --> UPL & OR3
    OR1 & OR2 & OR3 -. "riceve da" .-> DI
    OR1   --> LLM & R2 & PGPDF
    OR2   --> OCR & EXT & RES & CONF & R1 & NOT
    EXT   --> LLM & META
    RES   --> RRR
```

---

## C4 Level 3 – Componenti AI Generator

```mermaid
flowchart LR
    classDef http  fill:#dbeafe,stroke:#2563eb,color:#1e3a5f
    classDef orch  fill:#d1fae5,stroke:#059669,color:#064e3b
    classDef job   fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef svc   fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef infra fill:#fce7f3,stroke:#db2777,color:#500724
    classDef di    fill:#f1f5f9,stroke:#94a3b8,color:#0f172a

    subgraph L1 ["① HTTP Layer"]
        CTRL["GeneratedDataController
        ─────────────
        POST /generated_data
        GET status"]:::http
    end

    subgraph L2 ["② Async Dispatch"]
        ORCH["AiJobOrchestrator
        ─────────────
        Crea GeneratedDatum
        Enqueue → risposta subito"]:::orch
        JOB["AiGeneratorJob
        ─────────────
        Esegue in background
        Aggiorna status · WS"]:::job
    end

    subgraph L3 ["③ Pipeline Generazione"]
        direction TB
        GEN["AiGeneratorService
        ─────────────
        Coordina testo + immagine"]:::svc
        TEXT["TextGeneratorService
        ─────────────
        Prompt tone/style/company
        → Bedrock → parsing"]:::svc
        IMG["ImageGeneratorService
        ─────────────
        Prompt visivo
        → Bedrock → Storage"]:::svc
        POST["PostCreatorService
        ─────────────
        Crea Post records"]:::svc
    end

    subgraph L4 ["④ Infrastructure"]
        DMGR["AiGeneratorDataManager
        ─────────────
        Ciclo vita GeneratedDatum
        e Posts"]:::infra
        GCONT["AiGeneratorContainer
        ─────────────
        DI Container
        dipendenze modulo"]:::di
    end

    CTRL --> ORCH
    ORCH --> JOB
    JOB  --> GEN
    GEN  --> TEXT & IMG & POST
    GEN  --> DMGR
    GEN  -. "riceve da" .-> GCONT
```

---

## Diagramma di Sequenza – Estrazione PDF

```mermaid
sequenceDiagram
  actor U as Operatore
  participant FE as Frontend Angular
  participant API as Rails API
  participant DB as PostgreSQL
  participant Q as Solid Queue
  participant TX as AWS Textract
  participant BD as AWS Bedrock

  U->>FE: Upload file PDF
  FE->>API: POST /documents/split (multipart)
  API->>DB: CREATE uploaded_documents (checksum, status: pending)
  API->>Q: ENQUEUE PdfSplitJob
  API-->>FE: { ok: true, job_id, uploaded_document_id }

  Note over Q,BD: Job asincrono - PdfSplitJob

  Q->>BD: Prompt: individua breakpoints pagine
  BD-->>Q: breakpoints: [3, 7, 12, ...]
  Q->>DB: CREATE processing_run (status: splitting)
  Q->>DB: CREATE extracted_documents x N (status: queued)
  Q->>Q: ENQUEUE DataExtractionJob x N
  Q->>DB: UPDATE processing_run (status: processing)
  Q-->>FE: WebSocket: split_completed { run_id, pages_count }

  Note over Q,BD: Jobs concorrenti - DataExtractionJob (per ogni pagina)

  loop Per ogni pagina estratta
    Q->>DB: UPDATE extracted_document (status: in_progress)
    Q->>TX: OCR pagina PDF
    TX-->>Q: testo + confidence per riga
    Q->>BD: Prompt: estrai campi (destinatario, data, importo, ...)
    BD-->>Q: JSON campi estratti
    Q->>Q: fuzzy match destinatario → dipendente (Jaro-Winkler + Dice)
    Q->>Q: calcola confidence score
    Q->>DB: UPDATE extracted_document (status: done, campi, confidence, matched_employee_id)
    Q-->>FE: WebSocket: document_processed { doc_id, confidence }
  end

  Q->>DB: UPDATE processing_run (status: completed)
  Q-->>FE: WebSocket: processing_completed { run_id }
  FE-->>U: Mostra risultati estrazione
```

---

## Diagramma di Sequenza – Generazione Contenuti AI

```mermaid
sequenceDiagram
  actor U as Operatore
  participant FE as Frontend Angular
  participant API as Rails API
  participant DB as PostgreSQL
  participant Q as Solid Queue
  participant BD as AWS Bedrock

  U->>FE: Configura parametri (azienda, tone, style, topic)
  FE->>API: POST /generated_data
  API->>DB: CREATE generated_data (status: pending)
  API->>Q: ENQUEUE AiGeneratorJob
  API-->>FE: { ok: true, generation_id }

  Note over Q,BD: Job asincrono - AiGeneratorJob

  Q->>DB: UPDATE generated_data (status: processing)
  Q->>DB: READ company, style, tone descriptions
  Q->>BD: Prompt testo (con tone + style + company context)
  BD-->>Q: "Titolo | Contenuto testo..."
  Q->>Q: Parsing: estrai titolo e corpo
  Q->>BD: Prompt immagine (con descrizione visiva)
  BD-->>Q: Immagine generata (binary)
  Q->>DB: SAVE immagine su Active Storage
  Q->>DB: UPDATE generated_data (title, content, image_url, status: completed)
  Q->>DB: CREATE posts associati
  Q-->>FE: WebSocket: generation_completed { generation_id }

  FE->>API: GET /generated_data/:id
  API-->>FE: { title, content, image_url, posts }
  FE-->>U: Mostra contenuto generato
```

---

## State Machine – ExtractedDocument

```mermaid
stateDiagram-v2
  [*] --> queued : DataExtractionJob enqueued

  queued --> in_progress : Job inizia elaborazione\n(with_lock)
  in_progress --> done : OCR + LLM + match completati
  done --> validated : Operatore valida manualmente
  validated --> sent : Documento inviato (Sending creato)

  in_progress --> failed : Errore OCR o LLM
  done --> failed : Errore post-processing

  failed --> queued : Retry richiesto dall'operatore

  note right of in_progress
    OCR via Textract
    Estrazione campi via Bedrock
    Fuzzy match destinatario
    Calcolo confidence score
  end note

  note right of done
    Tutti i campi estratti
    confidence_score calcolato
    matched_employee_id assegnato
  end note
```

---

## State Machine – ProcessingRun

```mermaid
stateDiagram-v2
  [*] --> queued : PdfSplitJob enqueued

  queued --> splitting : Job avvia split PDF
  splitting --> processing : Split completato\nDataExtractionJob x N enqueued
  processing --> completed : Tutti i DataExtractionJob completati

  splitting --> failed : Errore split (PDF corrotto, LLM error)
  processing --> failed : Errore critico durante processing

  failed --> queued : Retry richiesto dall'operatore

  note right of splitting
    Carica PDF in memoria
    Chiede a Bedrock i breakpoints
    Crea ExtractedDocument records
  end note

  note right of processing
    N job paralleli in esecuzione
    WebSocket updates per ogni pagina
  end note
```

---

## Modello ER semplificato

```mermaid
erDiagram
  companies {
    int id PK
    string name
    string description "max 500 chars"
  }

  users {
    int id PK
    string name
    string email
  }

  employees {
    int id PK
    int user_id FK
    int company_id FK
  }

  uploaded_documents {
    int id PK
    string original_filename
    string checksum
    string file_kind
    string status
    string storage_path
    int page_count
    int employee_id FK
    datetime created_at
  }

  extracted_documents {
    int id PK
    int uploaded_document_id FK
    int sequence
    int page_start
    int page_end
    string status
    float confidence_score
    int matched_employee_id FK
    jsonb extracted_metadata
  }

  processing_runs {
    int id PK
    int uploaded_document_id FK
    string original_filename
    string status
    string job_id
  }

  processing_items {
    int id PK
    int processing_run_id FK
    int extracted_document_id FK
    string status
  }

  sendings {
    int id PK
    int extracted_document_id FK
    int recipient_id FK
    int template_id FK
    datetime sent_at
  }

  generated_data {
    int id PK
    int company_id FK
    int style_id FK
    int tone_id FK
    string title
    text content
    string status
    "ActiveStorage image attachment"
  }

  posts {
    int id PK
    int generated_datum_id FK
    text content
  }

  styles {
    int id PK
    int company_id FK
    string name
    text description
  }

  tones {
    int id PK
    int company_id FK
    string name
    text description
  }

  templates {
    int id PK
    string name
    text body
  }

  companies ||--o{ employees : "ha"
  users ||--o{ employees : "è"
  employees ||--o{ uploaded_documents : "carica (opzionale)"
  companies ||--o{ styles : "possiede"
  companies ||--o{ tones : "possiede"
  companies ||--o{ generated_data : "origina"
  styles ||--o{ generated_data : "usato in"
  tones ||--o{ generated_data : "usato in"
  generated_data ||--o{ posts : "genera"
  uploaded_documents ||--o{ extracted_documents : "contiene"
  uploaded_documents ||--o{ processing_runs : "ha"
  processing_runs ||--o{ processing_items : "include"
  processing_items ||--|| extracted_documents : "elabora"
  extracted_documents ||--o{ sendings : "distribuita via"
  users ||--o{ sendings : "riceve"
  templates ||--o{ sendings : "usa"
  users ||--o{ extracted_documents : "matched come destinatario"
```

---

## Architettura Deploy

```mermaid
graph TB
  subgraph local["Sviluppo Locale (Docker Compose)"]
    FE_DEV["Frontend\nAngular :4200"]
    BE_DEV["Backend\nRails :3000\n+ Active Storage"]
    DB_DEV["PostgreSQL\n:5433"]
    FE_DEV -->|REST + WS| BE_DEV
    BE_DEV -->|SQL| DB_DEV
  end

  subgraph prod["Produzione (Kamal + Docker)"]
    subgraph server["Server bare metal"]
      THRUSTER["Thruster\nHTTP/2 + asset cache\n:80"]
      PUMA["Puma\nRails API\n+ Solid Queue worker"]
      subgraph solid["Solid Stack (PostgreSQL)"]
        PG_MAIN["Primary DB"]
        PG_QUEUE["Queue DB"]
        PG_CACHE["Cache DB"]
        PG_CABLE["Cable DB"]
      end
    end
    THRUSTER --> PUMA
    PUMA --> PG_MAIN
    PUMA --> PG_QUEUE
    PUMA --> PG_CACHE
    PUMA --> PG_CABLE
  end

  subgraph aws["AWS"]
    TEXTRACT["Textract\n(OCR)"]
    BEDROCK["Bedrock\n(LLM + Image)"]
  end

  subgraph registry["Container Registry"]
    REG["Docker Registry\nlocalhost:5555"]
  end

  PUMA -->|AWS SDK| TEXTRACT
  PUMA -->|AWS SDK| BEDROCK
  REG -->|kamal deploy| server
```

---

## Pipeline CI/CD

```mermaid
flowchart LR
  push["Push to main\nor Pull Request"]

  push --> security["Security Scan\n• Brakeman (Rails CVE)\n• Bundler-audit (gem CVE)"]
  push --> lint["Linting\n• RuboCop omakase"]
  push --> test["Test Suite\n• Minitest\n• SimpleCov coverage\n• PostgreSQL container"]

  security -->|pass| gate{Tutti\npassed?}
  lint -->|pass| gate
  test -->|pass| gate

  gate -->|sì| ok["CI Green\nPR approvabile"]
  gate -->|no| fail["CI Red\nBlocked merge"]
```

---

*Documento generato dall'analisi del codice sorgente. Per la documentazione testuale completa vedere [ARCHITECTURE.md](ARCHITECTURE.md).*
