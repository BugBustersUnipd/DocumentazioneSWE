# Architettura del Sistema MVP

> Documento tecnico completo per specifiche tecniche e presentazioni.
> Diagrammi C4 e di sequenza dettagliati in [DIAGRAMS.md](DIAGRAMS.md).

---

## Indice

1. [Panoramica del Sistema](#1-panoramica-del-sistema)
2. [Stack Tecnologico](#2-stack-tecnologico)
3. [Architettura a Livelli](#3-architettura-a-livelli)
4. [Pattern Architetturali](#4-pattern-architetturali)
5. [Struttura dei Moduli](#5-struttura-dei-moduli)
6. [Modello dei Dati](#6-modello-dei-dati)
7. [API REST](#7-api-rest)
8. [Architettura Frontend](#8-architettura-frontend)
9. [Architettura di Deploy](#9-architettura-di-deploy)
10. [Flussi Dati Principali](#10-flussi-dati-principali)
11. [Sicurezza e Qualità](#11-sicurezza-e-qualità)
12. [Decisioni Architetturali Chiave](#12-decisioni-architetturali-chiave)

---

## 1. Panoramica del Sistema

Il sistema MVP è una piattaforma AI per l'**estrazione intelligente di documenti** e la **generazione di contenuti**. Architettura client-server con backend API Rails e frontend Angular, comunicazione in tempo reale via WebSocket, elaborazione asincrona tramite job queue e integrazione con servizi AI su AWS.

```
┌─────────────────────────────────────────────────────────────┐
│                        UTENTE FINALE                        │
└─────────────────────────────────┬───────────────────────────┘
                                  │ HTTPS / WebSocket
                    ┌─────────────▼─────────────┐
                    │   Frontend Angular 21 SPA  │
                    │   PrimeNG · Bootstrap 5    │
                    └─────────────┬─────────────┘
                                  │ REST API + WebSocket
                    ┌─────────────▼─────────────┐
                    │   Backend Rails 8 API      │
                    │   Puma · Thruster          │
                    └──┬──────────┬──────────────┘
                       │          │
          ┌────────────▼──┐  ┌────▼──────────────┐
          │  PostgreSQL   │  │    AWS Services    │
          │  (primary +   │  │  Textract (OCR)    │
          │  solid stack) │  │  Bedrock (LLM)     │
          └───────────────┘  └────────────────────┘
```

### Caratteristiche principali

| Funzionalità | Descrizione |
|---|---|
| Estrazione documenti | Upload PDF/CSV/immagini → OCR → LLM → dati strutturati |
| Risoluzione destinatari | Fuzzy matching nome estratto → dipendente aziendale |
| Generazione contenuti | LLM + image generation per social media / marketing |
| Real-time updates | WebSocket per notifiche avanzamento elaborazione |
| Job queue | Code asincrone con worker distribuiti su PostgreSQL |
| Analytics | Dashboard analisi performance AI Copilot e Generator |

---

## 2. Stack Tecnologico

### Backend

| Componente | Tecnologia | Versione |
|---|---|---|
| Framework | Ruby on Rails (API mode) | 8.1.2 |
| Linguaggio | Ruby | 3.3 |
| Web server | Puma | 5+ |
| Reverse proxy / cache | Thruster | latest |
| Database principale | PostgreSQL | 16 |
| Job queue | Solid Queue | latest |
| Cache | Solid Cache | latest |
| WebSocket backing | Solid Cable | latest |
| File attachments | Active Storage | built-in Rails |
| OCR | AWS Textract | SDK v3 |
| LLM / Image gen | AWS Bedrock (Nova Lite, Claude) | SDK v3 |
| PDF processing | CombinePDF | latest |
| Image processing | image_processing | 1.2+ |
| Serialization | Custom Presenter objects | — |
| Testing | Minitest + SimpleCov + Mocha | — |
| Security scan | Brakeman + Bundler-audit | — |
| Linting | RuboCop Omakase | — |
| Deploy | Kamal | latest |

### Frontend

| Componente | Tecnologia | Versione |
|---|---|---|
| Framework | Angular (Standalone Components) | 21 |
| Linguaggio | TypeScript | 5.9 |
| UI Library | PrimeNG | 21.1 |
| CSS Framework | Bootstrap | 5.3 |
| Charting | Chart.js | 4.5 |
| Rich text editor | Quill | 2.0 |
| Reactive extensions | RxJS | 7.8 |
| Testing | Vitest + JSDOM | 4.x |

### Infrastruttura

| Componente | Tecnologia |
|---|---|
| Container | Docker (multi-stage build) |
| Orchestrazione locale | Docker Compose |
| Orchestrazione produzione | Kamal |
| CI/CD | GitHub Actions |
| Runtime immagine prod | Ruby 3.3-slim + jemalloc |

---

## 3. Architettura a Livelli

Il backend segue un'architettura **a livelli espliciti** con principi di **Clean Architecture / Hexagonal Architecture**.

```
┌──────────────────────────────────────────────────────────────┐
│  LAYER HTTP                                                   │
│  Controllers Rails – routing, validazione input, risposta    │
│  documents_controller · generated_data_controller · ...      │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│  LAYER COMANDI (Command Pattern)                              │
│  Oggetti con singolo #call – entry point use case            │
│  InitializeProcessing · InitializeFileProcessing             │
│  ReassignExtractedRange · CreateSending                       │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│  LAYER ORCHESTRATORI (Service Objects)                        │
│  Pipeline multi-step che coordinano domain services          │
│  ProcessSplitRun · ProcessDataItem · ProcessGenericFile       │
│  AiJobOrchestrator · AiGeneratorService                       │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│  LAYER DOMAIN SERVICES                                        │
│  Logica di business specializzata, iniettabile via DI        │
│  OCR · LlmService · DataExtractor · RecipientResolver        │
│  ConfidenceCalculator · PdfSplitter · CsvProcessor           │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│  LAYER REPOSITORY / PERSISTENCE                               │
│  Astrazione dal database, transazioni, locking ottimistico   │
│  DataItemRepository · SplitRunRepository · DbManager         │
│  FileStorage · ActionCableNotifier                            │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│  LAYER DATI (ActiveRecord Models)                             │
│  14 modelli con state machine, relazioni, validazioni        │
│  ExtractedDocument · ProcessingRun · UploadedDocument · ...   │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│  LAYER ADAPTER ESTERNI                                        │
│  Adattatori verso sistemi esterni, sostituibili in test       │
│  AWS Textract adapter · AWS Bedrock adapter                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Pattern Architetturali

### 4.1 Dependency Injection Container

`DocumentProcessing::Container` gestisce oltre 30 dipendenze con inizializzazione lazy. Permette di sostituire i collaboratori con implementazioni fake nei test (e.g. `FakeContainer` per AWS stub).

```ruby
# Esempio: container inietta le dipendenze negli orchestratori
container = DocumentProcessing::Container.new(config)
ocr        = container.ocr                           # → OCR adapter
llm        = container.llm_service                   # → Bedrock adapter
resolver   = container.recipient_resolver(company:)  # → RecipientResolver
```

**File:** [backend/app/services/document_processing/container.rb](backend/app/services/document_processing/container.rb)

### 4.2 Command Pattern

Ogni use case espone un oggetto comando con metodo `#call` che restituisce un hash standardizzato:

```ruby
result = InitializeProcessing.new(container).call(params)
# → { ok: true, uploaded_document_id: 42, job_id: "uuid" }
# → { ok: false, error: :duplicate_file, message: "File già caricato" }
```

### 4.3 Repository Pattern

I repository astraggono l'accesso al database e garantiscono isolamento transazionale:

```ruby
DataItemRepository.new.with_lock(extracted_document) do |doc|
  doc.update!(status: :in_progress)
  # operazioni atomiche
end
```

**File:** [backend/app/services/document_processing/persistence/](backend/app/services/document_processing/persistence/)

### 4.4 Strategy Pattern

`CsvProcessor` e `ImageProcessor` implementano un'interfaccia comune (`#call(file_path)`) e restituiscono lo stesso hash di output. Il `Container` seleziona e crea la strategia corretta in base al `file_kind`; l'orchestratore `ProcessGenericFile` riceve già il processore giusto e non sa nulla del tipo di file.

```ruby
# Container: unico punto di selezione della strategia
def file_processor(file_kind)
  case file_kind
  when "csv"   then csv_processor    # → CsvProcessor.new(...)
  when "image" then image_processor  # → ImageProcessor.new(...)
  end
end

def process_generic_file_service(file_kind:)
  ProcessGenericFile.new(file_processor: file_processor(file_kind), ...)
end

# Orchestratore: cieco al tipo, chiama sempre la stessa interfaccia
result = file_processor.call(file_path)
# → { ocr_text:, metadata:, confidence:, recipient:, employee: }
```

| `file_kind` | Strategia | Pipeline interna |
|---|---|---|
| `pdf` | `PdfSplitter` + `DataExtractionJob` | split → OCR → LLM (multi-pagina) |
| `csv` | `CsvProcessor` | parse CSV → LLM → match |
| `image` | `ImageProcessor` | OCR (Textract) → LLM → match |

Aggiungere un nuovo tipo (es. Excel) richiede solo una nuova classe con `#call(file_path)` e una riga nel `Container` — senza toccare `ProcessGenericFile` (Open/Closed Principle).

### 4.5 State Machine

`ExtractedDocument` e `ProcessingRun` implementano una state machine esplicita con transizioni controllate e persistite su database:

```
ExtractedDocument:
  queued → in_progress → done → validated → sent
                      ↘ failed

ProcessingRun:
  queued → splitting → processing → completed
                               ↘ failed
```

### 4.6 Observer Pattern (WebSocket)

`ActionCableNotifier` trasmette eventi di stato al frontend in tempo reale:

```ruby
notifier.broadcast(:split_completed, { run_id: run.id, pages: pages.count })
notifier.broadcast(:document_processed, { doc_id: doc.id, confidence: 0.94 })
notifier.broadcast(:processing_completed, { run_id: run.id })
```

### 4.7 Template Method

`AiAnalyst::ComputationService` definisce il template; le sottoclassi specializzano i passi:

```ruby
class AiCopilotComputationService < ComputationService
  def fetch_data = AiCopilotAnalysesDataManager.new.fetch
  def compute(data) = # ... logica specifica CoPilot
end
```

### 4.8 Presenter / Decorator

`ExtractedDocumentPresenter` trasforma i modelli in strutture JSON per le risposte API, separando la presentazione dalla persistenza.

---

## 5. Struttura dei Moduli

### Document Processing Module

```
backend/app/services/document_processing/
│
├── container.rb                       ← DI Container (30+ dipendenze)
├── upload_manager.rb                  ← Gestione upload file (checksum, storage)
│
├── commands/
│   ├── initialize_processing.rb       ← Upload PDF + enqueue split
│   ├── initialize_file_processing.rb  ← Upload CSV/immagine
│   └── reassign_extracted_range.rb    ← Aggiorna range pagine estratto
│
├── sendings/
│   └── create_sending.rb             ← Creazione invio documento
│
├── lookups/
│   ├── companies_fetcher.rb           ← Autocomplete aziende
│   └── users_fetcher.rb               ← Autocomplete dipendenti
│
├── persistence/
│   ├── data_item_repository.rb        ← CRUD ExtractedDocument / ProcessingItem
│   ├── split_run_repository.rb        ← Gestione stato ProcessingRun
│   ├── db_manager.rb                  ← Query di alto livello
│   └── file_storage.rb                ← Astrazione filesystem
│
├── presenters/
│   └── extracted_document_presenter.rb ← Serializzazione API
│
├── process_split_run.rb               ← Orchestratore: split PDF
├── process_data_item.rb               ← Orchestratore: OCR→LLM→Match
├── process_generic_file.rb            ← Orchestratore: CSV/immagine
│
├── ocr.rb                             ← Adapter AWS Textract
├── llm_service.rb                     ← Adapter AWS Bedrock
├── data_extractor.rb                  ← Estrazione dati via LLM
├── extracted_metadata_builder.rb      ← Builder struttura metadati estratti
├── recipient_resolver.rb              ← Fuzzy matching Jaro-Winkler+Dice
├── recipient_resolution_result.rb     ← Value object risultato risoluzione
├── confidence_calculator.rb           ← Scoring affidabilità
│
├── pdf_splitter.rb                    ← PDF → pagine individuali
├── page_range_pdf.rb                  ← Estrazione range pagine PDF
├── csv_processor.rb                   ← CSV → dati strutturati
├── image_processor.rb                 ← Immagine → OCR → estrazione
└── action_cable_notifier.rb           ← Broadcast WebSocket
```

### AI Generator Module

```
backend/app/services/ai_generator/
│
├── ai_generator_container.rb          ← DI Container
├── ai_job_orchestrator.rb             ← Coordinator job asincrono
├── ai_generator_service.rb            ← Orchestratore testo+immagine
├── text_generator_service.rb          ← Generazione testo via Bedrock
├── image_generator_service.rb         ← Generazione immagine via Bedrock
├── text_params_setter_service.rb
├── image_params_setter_service.rb
├── post_creator_service.rb            ← Creazione record Post
└── setter_factory.rb
```

### AI Analyst Module

```
backend/app/services/ai_analyst/
│
├── computation_service.rb             ← Abstract base (Template Method)
├── ai_copilot_computation_service.rb
├── ai_generator_computation_service.rb
└── managers/
    ├── analyses_data_manager.rb       ← Abstract
    ├── ai_copilot_analyses_data_manager.rb
    └── ai_generator_analyses_data_manager.rb
```

### Background Jobs

```
backend/app/jobs/
│
├── application_job.rb                 ← Base class
├── pdf_split_job.rb                   ← Queue: :split (single-thread)
├── data_extraction_job.rb             ← Queue: :data (concorrente)
├── generic_file_processing_job.rb     ← Queue: :data
└── ai_generator_job.rb                ← Queue: :default
```

---

## 6. Modello dei Dati

### Entità principali e relazioni

```
companies ──────────────────────────────────────────────────┐
    │ has_many                                               │
    ▼                                                        │
employees                          styles ──┐               │
    │ belongs_to user               tones ──┤               │
    │                                       │               │
users                           generated_data              │
                                    │ belongs_to ───────────┘
                                    │ has_many
                                   posts

uploaded_documents
    │ has_many
    ▼
extracted_documents ◄── matched_employee (User)
    │ has_many
    │
processing_runs
    │ has_many
    ▼
processing_items ──── belongs_to extracted_document

sendings ──── belongs_to extracted_document
         ──── belongs_to recipient (User)
         ──── belongs_to template

templates
```

### Schema tabelle principali

| Tabella | Campi chiave | Constraint |
|---|---|---|
| `uploaded_documents` | id, original_filename, checksum, file_kind, status, storage_path, page_count, employee_id | UNIQUE(checksum) |
| `extracted_documents` | id, uploaded_document_id, sequence, page_start, page_end, status, confidence_score, matched_employee_id, extracted_metadata (jsonb) | INDEX(status) |
| `processing_runs` | id, uploaded_document_id, original_filename, status, job_id | UNIQUE(job_id) |
| `processing_items` | id, processing_run_id, extracted_document_id, sequence (int), status | — |
| `generated_data` | id, company_id, style_id, tone_id, title, content, status | Active Storage image |
| `companies` | id, name, description (max 500) | — |
| `users` | id, name, email | — |
| `employees` | id, user_id, company_id | — |

> **Nota:** `generated_data.img_path` (stringa) è stato rimosso e sostituito con un attachment **Active Storage** (`has_one_attached :image`), consentendo storage polimorfico su filesystem/cloud.

### Database multipli (Solid Stack)

```yaml
# config/database.yml (produzione)
primary:  backend_production          # Dati applicazione
cache:    backend_production_cache    # Solid Cache
queue:    backend_production_queue    # Solid Queue jobs
cable:    backend_production_cable    # Solid Cable WebSocket
```

---

## 7. API REST

**Base URL:** `http://localhost:3000` (sviluppo)

### Documents

| Metodo | Endpoint | Descrizione |
|---|---|---|
| POST | `/documents/split` | Upload PDF, avvia splitting + estrazione |
| POST | `/documents/process_file` | Upload CSV/immagine |
| GET | `/documents/uploads` | Lista documenti caricati |
| GET | `/documents/uploads/:id/extracted` | Pagine estratte di un documento |
| GET | `/documents/uploads/:id/file` | Download file originale |
| GET | `/documents/extracted/:id` | Dettaglio documento estratto |
| GET | `/documents/extracted/:id/pdf` | Download range pagine come PDF |
| PATCH | `/documents/extracted/:id/metadata` | Aggiorna metadati estratti |
| PATCH | `/documents/extracted/:id/validate` | Valida documento |
| PATCH | `/documents/extracted/:id/reassign_range` | Riassegna range pagine estratto |
| POST | `/documents/uploads/:id/retry` | Riprova processing run fallito |
| POST | `/documents/extracted/:id/retry` | Riprova estrazione fallita |

### Lookups

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/lookups/companies` | Autocomplete nomi aziende |
| GET | `/lookups/users` | Autocomplete nomi dipendenti |

### Sendings (Invii)

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/sendings` | Lista invii effettuati |
| POST | `/sendings` | Crea un invio (documento → destinatario) |

### Templates

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/templates` | Lista template disponibili |
| GET | `/templates/:id` | Dettaglio template |
| POST | `/templates` | Crea nuovo template |

### Tones & Styles (parametri generazione)

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/tones` | Lista toni disponibili |
| POST | `/tones` | Crea tono |
| DELETE | `/tones/:id` | Elimina tono |
| GET | `/styles` | Lista stili disponibili |
| POST | `/styles` | Crea stile |
| DELETE | `/styles/:id` | Elimina stile |

### Posts

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/posts` | Lista post generati |
| POST | `/posts` | Crea post |
| DELETE | `/posts/:id` | Elimina post |

### Generated Data

| Metodo | Endpoint | Descrizione |
|---|---|---|
| POST | `/generated_data` | Crea contenuto AI (asincrono) |
| GET | `/generated_data/:id` | Stato e contenuto generazione |
| PATCH | `/generated_data/:id/rating` | Valuta contenuto generato |
| DELETE | `/generated_data/:id` | Elimina generazione |

### Analytics

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/ai_copilot_data_analyst` | Dati analisi CoPilot |
| GET | `/ai_generator_data_analyst` | Dati analisi Generator |

### Formato risposta standardizzato

```json
{
  "status": "ok | error | queued",
  "message": "Messaggio human-readable",
  "job_id": "uuid-per-tracking-asincrono",
  "uploaded_document_id": 42,
  "extracted_document_id": 123
}
```

---

## 8. Architettura Frontend

### Tipo: Angular 21 Standalone Components (no NgModules)

```
frontend/src/app/
│
├── app.routes.ts            ← Routing dichiarativo
├── app.config.ts            ← Bootstrap providers (PrimeNG, Router)
├── app.ts                   ← Root component
│
├── estrattore/              ← Pagina estrazione documenti
├── generatore/              ← Pagina generazione contenuti AI
├── risultato-generazione/   ← Visualizzazione risultato generazione
├── storico-ai-assistant/    ← Storico interazioni AI Assistant
├── storico-ai-copilot/      ← Storico analisi CoPilot
├── analytics-dashboard/     ← Dashboard charts e metriche
├── anteprima-documento/     ← Preview documento estratto
├── riconoscimento-documenti/ ← Interfaccia riconoscimento documenti
│
└── components/              ← 25+ componenti UI riutilizzabili (PrimeNG)
```

### Routing

```typescript
export const routes: Routes = [
  { path: 'generatore',              component: Generatore },
  { path: 'estrattore',              component: Estrattore },
  { path: 'risultato-generazione',   component: RisultatoGenerazione },
  { path: 'storico-ai-assistant',    component: StoricoAiAssistant },
  { path: 'storico-ai-copilot',      component: StoricoAiCopilot },
  { path: 'analytics-dashboard',     component: AnalyticsDashboard },
  { path: 'anteprima-documento',     component: AnteprimaDocumento },
  { path: 'riconoscimento-documenti',component: RiconoscimentoDocumenti }
];
```

### Componenti UI riutilizzabili (components/)

| Componente | Responsabilità |
|---|---|
| `add-dialog` | Dialog per aggiungere elementi |
| `analytics-charts` | Grafici Chart.js per analytics |
| `attach-file` | Upload file (drag & drop) |
| `button` | Bottone personalizzato |
| `date-range-picker` | Selettore intervallo date |
| `dialog` | Dialog generico riutilizzabile |
| `doc-summary` | Riepilogo documento estratto |
| `editor` | Editor rich text (Quill) |
| `extracted-employee-info` | Info dipendente abbinato |
| `filters` | Pannello filtri |
| `image-title` | Header con immagine |
| `input` | Input testuale stilizzato |
| `menu` | Barra navigazione principale |
| `menutendina` | Menu dropdown |
| `month-year` | Selettore mese/anno |
| `nested-tables` | Tabelle annidate per dati gerarchici |
| `other-extract-documents` | Lista documenti estratti correlati |
| `page-range-input` | Input per range pagine (es. "1-3") |
| `pdf-preview` | Anteprima inline PDF |
| `prompt` | Componente prompt AI |
| `select-employees-dialog` | Dialog selezione dipendente |
| `send-document-dialog` | Dialog invio documento |
| `status-pill` | Badge stato colorato |
| `tables` | Tabelle dati con PrimeNG |

### Servizi Angular

| Servizio | Responsabilità |
|---|---|
| `AiAssistantService` | Comunicazione backend per assistant |
| `AiCoPilotService` | Integrazione CoPilot |
| `AiAssistantAnalyticsService` | Fetch dati analytics |
| *(Abstract)* `AnalyticsBaseService` | Logica condivisa analytics |

### Stack UI

```
PrimeNG 21.1 (tema Aura)
├── Tabelle, Dialog, Form components
└── PrimeIcons 7.0

Bootstrap 5.3
├── Grid system
└── Utility classes

Chart.js 4.5       ← Grafici analytics
Quill 2.0          ← Editor rich text
```

---

## 9. Architettura di Deploy

### Ambiente locale (Docker Compose)

```
docker-compose.yml
│
├── db (postgres:16)
│   ├── Port: 5433:5432 (evita conflitti)
│   └── Volume: postgres_data
│
├── backend (Rails 8)
│   ├── Port: 3000:3000
│   ├── depends_on: db
│   ├── env_file: backend/.env
│   └── DATABASE_URL → db service
│
└── frontend (Angular 21)
    ├── Port: 4200:4200
    ├── --poll 2000 (compatibilità WSL file watching)
    └── Volume: /app/node_modules (isolamento npm)
```

### Build produzione (Multi-stage Dockerfile)

```dockerfile
# Stage 1: base
FROM ruby:3.3-slim
ENV RAILS_ENV=production
# jemalloc per ottimizzazione memoria

# Stage 2: build
RUN apt-get install build-essential libpq-dev
RUN bundle install
RUN bootsnap precompile  # Boot più rapido

# Stage 3: final
COPY --from=build /artifacts
RUN useradd -u 1000 rails  # Non-root user
EXPOSE 80
CMD ["thruster", "rails", "server"]
```

### Kamal (deploy produzione)

```yaml
# config/deploy.yml
service: backend
image: backend
registry:
  server: localhost:5555   # Registry Docker locale
servers:
  web:
    - <IP_SERVER>
env:
  clear:
    SOLID_QUEUE_IN_PUMA: true   # Job processing in-process
volumes:
  - backend_storage:/rails/storage
```

### CI/CD (GitHub Actions)

```
.github/workflows/ci.yml
│
On: push to main, pull_request
│
├── 1. Security Scan
│   ├── Brakeman (vulnerabilità Rails)
│   └── Bundler-audit (CVE nelle gem)
│
├── 2. Linting
│   └── RuboCop (omakase Rails style)
│
└── 3. Test Suite
    ├── Minitest (unit + integration)
    └── SimpleCov (coverage)
    └── PostgreSQL service container
```

---

## 10. Flussi Dati Principali

### Flusso A: Estrazione documento PDF

```
Cliente                Backend              AWS             Database
  │                      │                   │                 │
  │─POST /documents/split►│                   │                 │
  │                      │ validate + checksum│                 │
  │                      │────────────────────────────────────►│ create UploadedDocument
  │                      │ enqueue PdfSplitJob│                 │
  │◄─{ ok, job_id }──────│                   │                 │
  │                      │                   │                 │
  │    [JOB: PdfSplitJob]│                   │                 │
  │                      │ detect breakpoints │                 │
  │                      │───────────────────►Bedrock(LLM)     │
  │                      │◄──────────────────│                 │
  │                      │────────────────────────────────────►│ create ProcessingRun
  │                      │────────────────────────────────────►│ create ExtractedDocuments
  │                      │ enqueue DataExtractionJob x N        │
  │◄─WebSocket: split_completed                                 │
  │                      │                   │                 │
  │    [JOB: DataExtractionJob (per pagina)]  │                 │
  │                      │──────────────────►Textract(OCR)     │
  │                      │◄──────────────────│                 │
  │                      │──────────────────►Bedrock(extract)  │
  │                      │◄──────────────────│                 │
  │                      │ fuzzy match recipient               │
  │                      │ calcola confidence score            │
  │                      │────────────────────────────────────►│ update ExtractedDocument
  │◄─WebSocket: document_processed                              │
  │                      │                   │                 │
  │◄─WebSocket: processing_completed (ultimo job)              │
```

### Flusso B: Generazione contenuto AI

```
Cliente                Backend              AWS Bedrock      Database
  │                      │                   │                 │
  │─POST /generated_data─►│                   │                 │
  │                      │────────────────────────────────────►│ create GeneratedDatum (pending)
  │                      │ enqueue AiGeneratorJob              │
  │◄─{ ok, generation_id}│                   │                 │
  │                      │                   │                 │
  │    [JOB: AiGeneratorJob]                 │                 │
  │                      │────────────────────────────────────►│ update status: processing
  │                      │ fetch tone/style/company            │
  │                      │──────────────────►Nova Lite (text)  │
  │                      │◄──────────────────│                 │
  │                      │──────────────────►Bedrock (image)   │
  │                      │◄──────────────────│                 │
  │                      │────────────────────────────────────►│ update GeneratedDatum
  │                      │────────────────────────────────────►│ create Posts
  │◄─WebSocket: generation_completed                            │
```

---

## 11. Sicurezza e Qualità

### Misure di sicurezza

| Area | Misura |
|---|---|
| Analisi statica | Brakeman (Rails CVE scan) in CI |
| Dipendenze | Bundler-audit (gem CVE check) in CI |
| Container | User non-root (uid 1000) in produzione |
| Secrets | AWS credentials + RAILS_MASTER_KEY via env vars |
| CORS | Rack-CORS configurato per origini ammesse |
| Deduplicazione | Checksum SHA su file uploadati |
| Locking | `with_lock` su state machine transitions |

### Qualità del codice

| Strumento | Scopo |
|---|---|
| RuboCop Omakase | Stile Rails standard |
| SimpleCov | Coverage test |
| Minitest | Unit + integration test |
| Vitest + JSDOM | Test frontend Angular |
| FakeContainer | Stub AWS in test (no network) |

### Strategia di test

- **Backend:** FakeContainer sostituisce tutti gli adapter AWS; test non richiedono connessione a AWS
- **Frontend:** Vitest con JSDOM, no browser necessario
- **Isolation:** Test environment usa `test` adapter per ActionCable

---

## 12. Decisioni Architetturali Chiave

### Solid Stack invece di Redis

**Decisione:** Usare Solid Queue, Solid Cache, Solid Cable (tutti su PostgreSQL) al posto di Redis.

**Motivazione:** Ridurre la complessità infrastrutturale dell'MVP. Nessuna dipendenza esterna aggiuntiva, un solo database da gestire, deploy più semplice.

**Trade-off:** Minor throughput di caching rispetto a Redis in scenari ad alta concorrenza; accettabile per un MVP.

### AWS Bedrock invece di API OpenAI

**Decisione:** Integrare Claude/Nova via AWS Bedrock invece di chiamare direttamente l'API Anthropic/OpenAI.

**Motivazione:** Unificare OCR (Textract) e LLM (Bedrock) sullo stesso provider AWS. Gestione IAM centralizzata.

### Kamal invece di Kubernetes

**Decisione:** Deploy con Kamal (container SSH su server bare metal) invece di Kubernetes.

**Motivazione:** Complessità ridotta per MVP. Kamal offre deploy zero-downtime senza orchestrazione complessa.

### LLM per split PDF invece di algoritmo deterministico

**Decisione:** Usare LLM per individuare i breakpoint di splitting tra documenti nel PDF.

**Motivazione:** I documenti variano troppo in struttura per un algoritmo deterministico. Il LLM generalizza meglio.

**Configurazione:** Temperature 0.0 per output deterministico, max_tokens 500.

### Fuzzy matching multi-algoritmo

**Decisione:** Combinare Jaro-Winkler + Dice coefficient con soglia 0.72 per la risoluzione dei destinatari.

**Motivazione:** Il nome estratto via OCR/LLM può avere typo o varianti. La combinazione di algoritmi aumenta la robustezza.

---

*Per diagrammi C4 (Context, Container, Component), diagrammi di sequenza dettagliati e state machine, vedere [DIAGRAMS.md](DIAGRAMS.md).*
