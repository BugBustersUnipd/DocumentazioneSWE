#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
glossary_auto_scanner.py - Scanner automatico termini da Glossario (VERSIONE MIGLIORATA)

Carica automaticamente i termini dal file glossario.tex o glossario.json
e verifica la presenza del TAG G nei documenti LaTeX.

MIGLIORAMENTI:
- Gestione acronimi: POC (Proof of Concept) → cerca sia "POC" che "Proof of Concept"
- Gestione traduzioni: Affidabilità (Reliability) → cerca entrambe
- Pattern regex migliorati per acronimi e termini speciali
- Supporto per entrambi i formati di TAG: \textsubscript{\scalebox{0.6}{\textbf{G}}} e \G
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import re
import json
from pathlib import Path

# --------------------------- COSTANTI --------------------------------
TAG_G_FULL = r"\textsubscript{\scalebox{0.6}{\textbf{G}}}"
TAG_G_SHORT = r"\G"

# ------------------------- FUNZIONI PARSING GLOSSARIO -----------------

def extract_terms_from_tex(tex_path, progress_callback=None):
    """
    Estrae tutti i termini dal file glossario.tex
    Cerca le definizioni nel formato \subsection{Termine}
    """
    if progress_callback:
        progress_callback(0, "Lettura file .tex...")
    
    try:
        with open(tex_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        try:
            with open(tex_path, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception as e:
            raise Exception(f"Errore lettura glossario.tex: {e}")
    
    if progress_callback:
        progress_callback(30, "Estrazione termini...")
    
    # Pattern per estrarre i termini dalle subsection
    pattern = r'\\subsection\{([^}]+)\}'
    matches = re.findall(pattern, content)
    
    if progress_callback:
        progress_callback(70, "Pulizia e rimozione duplicati...")
    
    # Rimuovi duplicati e pulisci
    terms = []
    seen = set()
    for i, term in enumerate(matches):
        if progress_callback and i % 10 == 0:
            progress = 70 + (i / len(matches)) * 25
            progress_callback(progress, f"Elaborazione termine {i+1}/{len(matches)}...")
        
        # Pulisci il termine da eventuali comandi LaTeX residui
        clean_term = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', term)
        clean_term = clean_term.strip()
        
        # Evita duplicati (case-insensitive)
        if clean_term.lower() not in seen:
            terms.append(clean_term)
            seen.add(clean_term.lower())
    
    if progress_callback:
        progress_callback(100, "Completato!")
    
    return sorted(terms)

def extract_terms_from_json(json_path, progress_callback=None):
    """
    Estrae tutti i termini dal file glossario.json
    """
    if progress_callback:
        progress_callback(0, "Lettura file .json...")
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if progress_callback:
            progress_callback(40, "Estrazione termini...")
        
        terms = []
        seen = set()
        
        if "terms" in data and isinstance(data["terms"], list):
            total = len(data["terms"])
            for i, item in enumerate(data["terms"]):
                if progress_callback and i % 5 == 0:
                    progress = 40 + (i / total) * 50
                    progress_callback(progress, f"Elaborazione termine {i+1}/{total}...")
                
                if "term" in item:
                    term = item["term"].strip()
                    # Evita duplicati (case-insensitive)
                    if term.lower() not in seen:
                        terms.append(term)
                        seen.add(term.lower())
        
        if progress_callback:
            progress_callback(100, "Completato!")
        
        return sorted(terms)
    except Exception as e:
        raise Exception(f"Errore lettura glossario.json: {e}")

def load_glossary_terms(glossary_path, progress_callback=None):
    """
    Carica i termini dal glossario (auto-rileva formato .tex o .json)
    """
    if glossary_path is None:
        return None, "Nessun file glossario selezionato"
    
    if not os.path.exists(glossary_path):
        return None, f"File non trovato: {glossary_path}"
    
    try:
        if glossary_path.endswith('.tex') or glossary_path.endswith('.latex'):
            terms = extract_terms_from_tex(glossary_path, progress_callback)
            return terms, None
        elif glossary_path.endswith('.json'):
            terms = extract_terms_from_json(glossary_path, progress_callback)
            return terms, None
        else:
            return None, "Formato file non supportato (usa .tex, .latex o .json)"
    except Exception as e:
        return None, str(e)

# ------------------------- FUNZIONI ANALISI MIGLIORATE -----------------------------

def generate_term_variants(term):
    """
    Genera tutte le varianti possibili di un termine per la ricerca.
    Gestisce:
    - Acronimi con descrizione: "POC (Proof of Concept)" -> ["POC", "Proof of Concept"]
    - Termini con traduzioni: "Affidabilità (Reliability)" -> ["Affidabilità", "Reliability"]
    - Termini con caratteri speciali
    """
    variants = set()
    
    # Aggiungi sempre il termine originale
    variants.add(term)
    
    # Pattern per acronimi con descrizione: "ACRONIMO (Descrizione Completa)"
    # Es: "POC (Proof of Concept)", "AI (Artificial Intelligence)"
    acronym_pattern = r'^([A-Z]{2,})\s*\(([^)]+)\)$'
    match = re.match(acronym_pattern, term)
    
    if match:
        acronym = match.group(1).strip()  # Es: "POC"
        full_form = match.group(2).strip()  # Es: "Proof of Concept"
        
        variants.add(acronym)
        variants.add(full_form)
        
        # Aggiungi anche varianti con trattini se presenti nella forma estesa
        if '-' in full_form:
            variants.add(full_form.replace('-', ' '))
        
        return variants
    
    # Pattern per termini con descrizione/traduzione tra parentesi
    # Es: "Affidabilità (Reliability)", "Verifica (Verification)"
    paren_pattern = r'^(.+?)\s*\(([^)]+)\)$'
    match = re.match(paren_pattern, term)
    
    if match:
        main_term = match.group(1).strip()  # Es: "Affidabilità"
        alt_term = match.group(2).strip()   # Es: "Reliability"
        
        variants.add(main_term)
        variants.add(alt_term)
        
        # Se il termine alternativo ha trattini, aggiungi versione con spazi
        if '-' in alt_term:
            variants.add(alt_term.replace('-', ' '))
    
    return variants

def is_inside_url_or_path(text, start, end):
    """
    Verifica se una posizione nel testo deve essere ESCLUSA dall'analisi.
    Ritorna True se il termine è dentro:
    - Comandi LaTeX con path (\includegraphics, \input, ecc.)
    - URL reali
    - Percorsi assoluti di filesystem
    """
    # Espandi il contesto intorno alla posizione trovata
    context_start = max(0, start - 150)
    context_end = min(len(text), end + 50)
    context = text[context_start:context_end]
    
    # Posizione relativa nel contesto
    rel_start = start - context_start
    rel_end = end - context_start
    
    # Controlla se siamo dentro un comando LaTeX con argomento tra graffe
    # Pattern: \comando{...contenuto...}
    latex_commands_with_paths = [
        r'\\includegraphics(?:\[[^\]]*\])?\{[^}]+\}',
        r'\\input\{[^}]+\}',
        r'\\include\{[^}]+\}',
        r'\\graphicspath\{\{[^}]+\}\}',
        r'\\bibliographystyle\{[^}]+\}',
        r'\\bibliography\{[^}]+\}',
    ]
    
    for pattern in latex_commands_with_paths:
        for match in re.finditer(pattern, context):
            match_start, match_end = match.span()
            # Se siamo dentro questo comando LaTeX, ESCLUDI
            if match_start <= rel_start < match_end or match_start < rel_end <= match_end:
                return True  # ESCLUDI, è dentro un comando LaTeX
    
    # Controlla URL VERI (devono essere completi con protocollo o www)
    url_patterns = [
        r'https?://[^\s\}]+',     # http:// o https://
        r'www\.[^\s\}]+',          # www.
        r'ftp://[^\s\}]+',         # ftp://
    ]
    
    for pattern in url_patterns:
        for match in re.finditer(pattern, context):
            match_start, match_end = match.span()
            if match_start <= rel_start < match_end or match_start < rel_end <= match_end:
                return True  # È dentro un URL vero, ESCLUDI
    
    # Controlla percorsi ASSOLUTI di filesystem (non relativi)
    # Solo percorsi che iniziano con C:\ o /home/ o /var/ ecc.
    absolute_path_patterns = [
        r'[A-Za-z]:\\[^\s\}]+',                    # Windows assoluto: C:\Users\...
        r'/(?:home|var|usr|opt|etc|tmp)/[^\s\}]+', # Unix assoluto comune
    ]
    
    for pattern in absolute_path_patterns:
        for match in re.finditer(pattern, context):
            match_start, match_end = match.span()
            if match_start <= rel_start < match_end or match_start < rel_end <= match_end:
                return True  # È dentro un path assoluto vero, ESCLUDI
    
    return False  # Non è in nessun contesto da escludere, INCLUDI nell'analisi

def find_occurrences_with_tag(text, term):
    """
    Cerca tutte le occorrenze case-insensitive di un termine e le sue varianti.
    Ritorna lista di tuple: (start, end, lineno, line_text, tag_present, matched_variant)
    
    MODIFICATO: 
    - Ora cerca sia TAG_G_FULL che TAG_G_SHORT
    - Esclude occorrenze all'interno di URL e percorsi file
    - Gestisce TAG dopo acronimi: "Requirements and Technology Baseline (RTB)\G" 
      tagga sia il termine completo che l'acronimo
    """
    results = []
    variants = generate_term_variants(term)
    
    for variant in variants:
        # Scegli il pattern regex in base al tipo di variante
        
        # 1. Acronimi (solo lettere maiuscole, 2+ caratteri)
        if re.match(r'^[A-Z]{2,}$', variant):
            # Per acronimi usa lookahead/lookbehind per evitare match parziali
            # Es: "POC" non deve matchare "EPOCH"
            pattern = r'(?<![A-Za-z])' + re.escape(variant) + r'(?![A-Za-z])'
            flags = 0  # case-sensitive per acronimi
        
        # 2. Termini con trattini (es: "Test-Driven Development")
        elif '-' in variant:
            # Permetti match anche con spazi invece dei trattini
            # Es: "Test-Driven" matcha anche "Test Driven"
            escaped = re.escape(variant).replace(r'\-', r'[\s\-]')
            pattern = r'\b' + escaped + r'\b'
            flags = re.IGNORECASE
        
        # 3. Termini normali
        else:
            # Match standard con word boundary
            pattern = r'\b' + re.escape(variant) + r'\b'
            flags = re.IGNORECASE
        
        # Cerca tutte le occorrenze
        for match in re.finditer(pattern, text, flags):
            start, end = match.span()
            
            # SALTA occorrenze all'interno di URL o percorsi file
            if is_inside_url_or_path(text, start, end):
                continue
            
            # Trova numero di riga e contenuto riga
            lineno = text[:start].count('\n') + 1
            line_start = text.rfind('\n', 0, start) + 1
            line_end = text.find('\n', end)
            if line_end == -1:
                line_end = len(text)
            line_text = text[line_start:line_end].strip()
            
            # Verifica presenza TAG subito dopo il match
            # MODIFICATO: Cerca ENTRAMBI i formati di TAG come comandi LaTeX
            after_match = text[end:end+200]
            
            # Cerca il TAG corto (\G) - deve essere un comando LaTeX completo
            # Pattern: \G seguito da qualsiasi carattere NON alfabetico (o fine stringa)
            # MODIFICATO: Permette anche } e ) prima di \G per gestire \textit{termine}\G e (RTB)\G
            tag_short_match = re.match(r'[\)\s\}]*\\G(?:[^a-zA-Z]|$)', after_match)
            
            # Cerca il TAG completo - escapa le parentesi graffe ma non i backslash
            tag_full_pattern = r'\\textsubscript\{\\scalebox\{0\.6\}\{\\textbf\{G\}\}\}'
            tag_full_match = re.match(r'[\)\s\}]*' + tag_full_pattern, after_match)
            
            # NUOVO: Gestione TAG dopo acronimo in parentesi
            # Pattern: "Termine (ACRONIMO)\G" o "Termine (**ACRONIMO**)\G"
            # Permette spazi, markdown (*, _), } tra termine e acronimo E dentro le parentesi
            # La } è necessaria per termini in \textit{...} o \textbf{...}
            acronym_with_tag_pattern = r'[\s\*\_\}]*\([\s\*\_]*[A-Z]{2,}[\s\*\_]*\)[\s\*\_]*\\G(?:[^a-zA-Z]|$)'
            acronym_tag_match = re.match(acronym_with_tag_pattern, after_match)
            
            # Anche con TAG completo dopo acronimo
            acronym_with_full_tag_pattern = r'[\s\*\_\}]*\([\s\*\_]*[A-Z]{2,}[\s\*\_]*\)[\s\*\_]*' + tag_full_pattern
            acronym_full_tag_match = re.match(acronym_with_full_tag_pattern, after_match)
            
            tag_present = bool(tag_short_match or tag_full_match or 
                             acronym_tag_match or acronym_full_tag_match)
            
            results.append((start, end, lineno, line_text, tag_present, variant))
    
    return results

def analyze_text(text, terms, progress_callback=None):
    """
    Analizza un testo LaTeX e trova:
    1. Termini del glossario presenti nel testo ma SENZA TAG G
    2. Termini del glossario MAI citati nel documento
    
    MODIFICATO: 
    - Ora riconosce sia TAG_G_FULL che TAG_G_SHORT
    - Gestisce priorità: termini più lunghi/specifici hanno precedenza su quelli più corti
      (es: "Verbale interno" ha priorità su "Verbale")
    - Per acronimi (es: "RTB (Requirements and Technology Baseline)"), se una variante
      ha il TAG, tutte le varianti sono considerate taggate
    """
    # Ordina i termini per lunghezza decrescente per dare priorità ai termini più specifici
    # Es: "Verbale interno" verrà processato prima di "Verbale"
    sorted_terms = sorted(terms, key=lambda t: len(t), reverse=True)
    
    terms_with_missing_tag = {}  # Termini trovati nel testo senza TAG
    terms_not_found = []          # Termini mai citati
    
    # Teniamo traccia delle posizioni già coperte da termini più specifici
    # per evitare che "Verbale" matchi in "Verbale interno\G"
    covered_positions = set()
    
    total = len(sorted_terms)
    
    for i, term in enumerate(sorted_terms):
        if progress_callback and i % 10 == 0:
            progress = (i / total) * 100
            progress_callback(progress, f"Analisi termine {i+1}/{total}...")
        
        # Cerca occorrenze del termine e sue varianti
        occurrences = find_occurrences_with_tag(text, term)
        
        # Filtra le occorrenze che non sono già coperte da termini più specifici
        valid_occurrences = []
        for start, end, lineno, line_text, tag_present, variant in occurrences:
            # Controlla se questa posizione è già stata coperta
            position_range = set(range(start, end))
            if not position_range & covered_positions:  # Nessuna sovrapposizione
                valid_occurrences.append((start, end, lineno, line_text, tag_present, variant))
                # Marca queste posizioni come coperte
                covered_positions.update(position_range)
        
        if not valid_occurrences:
            # Termine mai citato (o tutte le sue occorrenze erano già coperte)
            if not any(set(range(s, e)) & covered_positions 
                      for s, e, _, _, _, _ in occurrences):
                terms_not_found.append(term)
        else:
            # GESTIONE ACRONIMI: Se almeno UNA variante ha il TAG in una occorrenza,
            # consideriamo TUTTE le occorrenze di TUTTE le varianti come taggate
            
            # Raggruppa occorrenze per riga
            occurrences_by_line = {}
            for start, end, lineno, line_text, tag_present, variant in valid_occurrences:
                if lineno not in occurrences_by_line:
                    occurrences_by_line[lineno] = []
                occurrences_by_line[lineno].append((start, end, line_text, tag_present, variant))
            
            # Per ogni riga, se ALMENO UNA variante ha il TAG, considera tutte taggate
            matches_without_tag = []
            for lineno, line_occurrences in occurrences_by_line.items():
                # Controlla se almeno una variante in questa riga ha il TAG
                has_any_tag = any(tag_present for _, _, _, tag_present, _ in line_occurrences)
                
                if not has_any_tag:
                    # Nessuna variante ha il TAG in questa riga, segnala tutte
                    for start, end, line_text, tag_present, variant in line_occurrences:
                        matches_without_tag.append((lineno, line_text, variant))
            
            if matches_without_tag:
                terms_with_missing_tag[term] = {
                    "total_matches": len(valid_occurrences),
                    "matches_without_tag": matches_without_tag
                }
    
    if progress_callback:
        progress_callback(100, "Analisi completata!")
    
    return terms_with_missing_tag, terms_not_found

def find_latex_files(path):
    """Trova tutti i file .tex in un percorso (file o directory)"""
    if os.path.isfile(path):
        return [path] if path.endswith('.tex') else []
    
    latex_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.tex'):
                latex_files.append(os.path.join(root, file))
    
    return latex_files

# ---------------------------- GUI ------------------------------------

class GlossaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scanner Glossario Automatico v2.1 - Supporto TAG \\G")
        self.root.geometry("1000x750")
        
        self.terms = []
        self.glossary_path_var = tk.StringVar()
        self.doc_path_var = tk.StringVar()
        
        self.terms_with_missing_tag = None
        self.terms_not_found = None
        
        self.create_widgets()
        
    def create_widgets(self):
        """Crea l'interfaccia grafica"""
        
        # ========== FRAME SUPERIORE: Selezione Glossario ==========
        glossary_frame = ttk.LabelFrame(self.root, text="📚 1. Carica Glossario", padding=10)
        glossary_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(glossary_frame, text="File glossario (.tex o .json):").grid(
            row=0, column=0, sticky="w", padx=5)
        ttk.Entry(glossary_frame, textvariable=self.glossary_path_var, width=60).grid(
            row=0, column=1, padx=5)
        ttk.Button(glossary_frame, text="Sfoglia...", 
                  command=self.browse_glossary).grid(row=0, column=2, padx=5)
        ttk.Button(glossary_frame, text="Carica Termini", 
                  command=self.load_glossary).grid(row=0, column=3, padx=5)
        
        # Progress bar per caricamento glossario
        self.glossary_progress = ttk.Progressbar(glossary_frame, mode='determinate', length=400)
        self.glossary_progress.grid(row=1, column=0, columnspan=4, pady=5, sticky="ew")
        
        self.glossary_progress_label = ttk.Label(glossary_frame, text="")
        self.glossary_progress_label.grid(row=2, column=0, columnspan=4)
        
        # ========== FRAME CENTRALE: Selezione Documento ==========
        doc_frame = ttk.LabelFrame(self.root, text="📄 2. Seleziona Documento/Cartella", padding=10)
        doc_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(doc_frame, text="File/Cartella da analizzare:").grid(
            row=0, column=0, sticky="w", padx=5)
        ttk.Entry(doc_frame, textvariable=self.doc_path_var, width=60).grid(
            row=0, column=1, padx=5)
        ttk.Button(doc_frame, text="File...", 
                  command=self.browse_file).grid(row=0, column=2, padx=5)
        ttk.Button(doc_frame, text="Cartella...", 
                  command=self.browse_folder).grid(row=0, column=3, padx=5)
        
        # ========== FRAME ANALISI ==========
        analysis_frame = ttk.LabelFrame(self.root, text="🔍 3. Esegui Analisi", padding=10)
        analysis_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(analysis_frame, text="▶ AVVIA ANALISI", 
                  command=self.run_analysis, 
                  style="Accent.TButton").pack(pady=5)
        
        # Progress bar per analisi
        self.analysis_progress = ttk.Progressbar(analysis_frame, mode='determinate', length=600)
        self.analysis_progress.pack(pady=5, fill="x")
        
        self.analysis_progress_label = ttk.Label(analysis_frame, text="")
        self.analysis_progress_label.pack()
        
        # Info box
        info_text = ("ℹ️ FUNZIONALITÀ:\n"
                    "• Supporta acronimi: POC (Proof of Concept) → cerca POC e Proof of Concept\n"
                    "• Supporta traduzioni: Affidabilità (Reliability) → cerca entrambe\n"
                    "• Riconosce ENTRAMBI i formati di TAG: \\textsubscript{{...}} e \\G\n"
                    "• Ricerca case-insensitive intelligente\n"
                    "• Analisi file singoli o cartelle intere")
        info_label = ttk.Label(analysis_frame, text=info_text, 
                             background="#e8f4f8", relief="solid", padding=10)
        info_label.pack(fill="x", pady=5)
        
        # ========== FRAME RISULTATI ==========
        results_frame = ttk.LabelFrame(self.root, text="📊 4. Risultati", padding=10)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Area testo con scrollbar
        self.results_text = scrolledtext.ScrolledText(
            results_frame, wrap=tk.WORD, width=100, height=20, 
            font=("Courier", 9))
        self.results_text.pack(fill="both", expand=True)
        
        # Pulsanti azioni
        buttons_frame = ttk.Frame(results_frame)
        buttons_frame.pack(fill="x", pady=5)
        
        ttk.Button(buttons_frame, text="💾 Esporta Risultati", 
                  command=self.export_results).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="🗑️ Pulisci", 
                  command=self.clear_results).pack(side="left", padx=5)
        
    def browse_glossary(self):
        """Seleziona il file glossario"""
        filename = filedialog.askopenfilename(
            title="Seleziona il file glossario",
            filetypes=[
                ("File LaTeX/JSON", "*.tex *.latex *.json"),
                ("File LaTeX", "*.tex *.latex"),
                ("File JSON", "*.json"),
                ("Tutti i file", "*.*")
            ]
        )
        if filename:
            self.glossary_path_var.set(filename)
            
    def browse_file(self):
        """Seleziona un singolo file .tex"""
        filename = filedialog.askopenfilename(
            title="Seleziona file LaTeX",
            filetypes=[("File LaTeX", "*.tex"), ("Tutti i file", "*.*")]
        )
        if filename:
            self.doc_path_var.set(filename)
            
    def browse_folder(self):
        """Seleziona una cartella"""
        foldername = filedialog.askdirectory(title="Seleziona cartella con file LaTeX")
        if foldername:
            self.doc_path_var.set(foldername)
    
    def update_glossary_progress(self, value, message):
        """Aggiorna la progress bar del glossario"""
        self.glossary_progress['value'] = value
        self.glossary_progress_label.config(text=message)
        self.root.update_idletasks()
    
    def update_analysis_progress(self, value, message):
        """Aggiorna la progress bar dell'analisi"""
        self.analysis_progress['value'] = value
        self.analysis_progress_label.config(text=message)
        self.root.update_idletasks()
            
    def load_glossary(self):
        """Carica i termini dal glossario"""
        glossary_path = self.glossary_path_var.get().strip()
        
        if not glossary_path:
            messagebox.showwarning("Attenzione", "Seleziona prima un file glossario.")
            return
        
        self.root.config(cursor="watch")
        self.glossary_progress['value'] = 0
        
        try:
            terms, error = load_glossary_terms(glossary_path, self.update_glossary_progress)
            
            if error:
                messagebox.showerror("Errore", error)
                self.terms = []
            else:
                self.terms = terms
                messagebox.showinfo("Successo", 
                    f"✅ Caricati {len(terms)} termini dal glossario!\n\n"
                    f"File: {os.path.basename(glossary_path)}\n\n"
                    f"Supporto TAG:\n"
                    f"• \\textsubscript{{\\scalebox{{0.6}}{{\\textbf{{G}}}}}}\n"
                    f"• \\G")
                
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il caricamento:\n{e}")
            self.terms = []
        finally:
            self.root.config(cursor="")
            self.glossary_progress['value'] = 0
            self.glossary_progress_label.config(text="")
            
    def run_analysis(self):
        """Esegue l'analisi del documento o della cartella"""
        if not self.terms:
            messagebox.showwarning("Attenzione", "Carica prima i termini dal glossario.")
            return
            
        doc_path = self.doc_path_var.get().strip()
        if not doc_path:
            messagebox.showwarning("Attenzione", "Seleziona un file o una cartella da analizzare.")
            return
            
        if not os.path.exists(doc_path):
            messagebox.showerror("Errore", f"Percorso non trovato: {doc_path}")
            return
        
        self.root.config(cursor="watch")
        self.analysis_progress['value'] = 0
        
        try:
            # Trova i file da analizzare
            latex_files = find_latex_files(doc_path)
            
            if not latex_files:
                messagebox.showwarning("Attenzione", "Nessun file LaTeX trovato nel percorso selezionato.")
                return
            
            self.update_analysis_progress(0, f"Trovati {len(latex_files)} file da analizzare...")
            
            # Analizza tutti i file
            all_results = {}
            total_files = len(latex_files)
            
            for i, file_path in enumerate(latex_files):
                file_progress = (i / total_files) * 100
                self.update_analysis_progress(
                    file_progress, 
                    f"Analisi file {i+1}/{total_files}: {os.path.basename(file_path)}..."
                )
                
                # Leggi il file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                except Exception:
                    try:
                        with open(file_path, "r", encoding="latin-1") as f:
                            text = f.read()
                    except Exception:
                        continue  # Salta file non leggibili
                
                # Analizza
                terms_missing, terms_not_found = analyze_text(
                    text, self.terms, 
                    lambda p, m: self.update_analysis_progress(
                        file_progress + (p / total_files), m
                    )
                )
                
                if terms_missing or terms_not_found:
                    all_results[file_path] = {
                        'missing_tag': terms_missing,
                        'not_found': terms_not_found
                    }
            
            self.update_analysis_progress(100, "Analisi completata!")
            
            # Mostra risultati
            self.display_results(all_results, latex_files)
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'analisi:\n{e}")
        finally:
            self.root.config(cursor="")
            self.analysis_progress['value'] = 0
            self.analysis_progress_label.config(text="")
            
    def display_results(self, all_results, all_files):
        """Mostra i risultati dell'analisi"""
        self.results_text.delete("1.0", tk.END)
        
        # Header
        header = (f"📊 ANALISI COMPLETATA\n"
                 f"📚 Termini nel glossario: {len(self.terms)}\n"
                 f"📄 File analizzati: {len(all_files)}\n"
                 f"🏷️  TAG riconosciuti: \\textsubscript{{...}} e \\G\n"
                 f"{'='*70}\n\n")
        self.results_text.insert(tk.END, header)
        
        if not all_results:
            self.results_text.insert(tk.END, 
                "🎉 PERFETTO! Nessun problema trovato in tutti i file analizzati!\n\n"
                "✅ Tutti i termini del glossario presenti hanno il TAG G corretto.\n")
            
            messagebox.showinfo("Analisi Completata", 
                              "✅ Nessun problema trovato!\n\n"
                              f"• Analizzati {len(all_files)} file\n"
                              "• Tutti i termini presenti hanno il TAG G")
            return
        
        # Mostra problemi per ogni file
        total_not_found = 0
        total_missing_tags = 0
        
        for file_path, results in all_results.items():
            self.results_text.insert(tk.END, 
                f"📄 {os.path.basename(file_path)}\n")
            self.results_text.insert(tk.END, 
                f"   Percorso: {file_path}\n")
            
            # Termini non trovati
            if results['not_found']:
                total_not_found += len(results['not_found'])
                self.results_text.insert(tk.END, 
                    f"   ❌ Termini non presenti nel documento: {len(results['not_found'])}\n")
            
            # Termini senza TAG
            if results['missing_tag']:
                count = sum(len(v["matches_without_tag"]) 
                          for v in results['missing_tag'].values())
                total_missing_tags += count
                
                self.results_text.insert(tk.END, 
                    f"   ⚠️  Termini presenti ma SENZA TAG G: "
                    f"{len(results['missing_tag'])} termini ({count} occorrenze)\n")
                
                for phrase, data in results['missing_tag'].items():
                    self.results_text.insert(tk.END, f"      • {phrase}:\n")
                    
                    for ln, line_text, variant in data["matches_without_tag"]:
                        # Tronca il testo se troppo lungo
                        if len(line_text) > 80:
                            line_text = line_text[:77] + "..."
                        
                        # Evidenzia la variante trovata
                        highlighted_text = line_text
                        if variant in line_text:
                            highlighted_text = line_text.replace(variant, f"**{variant}**")
                        
                        self.results_text.insert(tk.END, 
                            f"        riga {ln:4d}: {highlighted_text}\n")
                        self.results_text.insert(tk.END,
                            f"                  (trovata variante: '{variant}')\n")
            
            self.results_text.insert(tk.END, "\n")
        
        # Riepilogo finale
        summary = (f"{'='*70}\n"
                  f"📊 RIEPILOGO TOTALE:\n"
                  f"   • File con problemi: {len(all_results)}/{len(all_files)}\n")
        
        if total_not_found > 0:
            summary += f"   • Totale termini non presenti: {total_not_found}\n"
        if total_missing_tags > 0:
            summary += f"   • Totale occorrenze senza TAG G: {total_missing_tags}\n"
        
        self.results_text.insert(tk.END, summary)
        
        messagebox.showwarning("Problemi Trovati", 
            f"Trovati problemi in {len(all_results)}/{len(all_files)} file:\n\n"
            f"• Termini non presenti: {total_not_found}\n"
            f"• Occorrenze senza TAG G: {total_missing_tags}")
        
    def export_results(self):
        """Esporta i risultati"""
        if not self.results_text.get("1.0", "end-1c"):
            messagebox.showwarning("Attenzione", "Nessun risultato da esportare.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("File di testo", "*.txt"), ("Tutti i file", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== SCANNER GLOSSARIO AUTOMATICO - RISULTATI (v2.1) ===\n\n")
                    f.write(f"Termini glossario: {len(self.terms)}\n")
                    f.write(f"File glossario: {self.glossary_path_var.get()}\n\n")
                    f.write("FUNZIONALITÀ:\n")
                    f.write("• Gestione acronimi: POC (Proof of Concept) → cerca POC e Proof of Concept\n")
                    f.write("• Gestione traduzioni: Affidabilità (Reliability) → cerca entrambe\n")
                    f.write("• Supporto TAG: \\textsubscript{\\scalebox{0.6}{\\textbf{G}}} e \\G\n")
                    f.write("• Ricerca case-insensitive migliorata\n\n")
                    f.write(self.results_text.get("1.0", tk.END))
                    
                messagebox.showinfo("Successo", f"Risultati esportati in:\n{filename}")
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile esportare:\n{e}")
                
    def clear_results(self):
        """Pulisce i risultati"""
        self.results_text.delete("1.0", tk.END)
        self.terms_with_missing_tag = None
        self.terms_not_found = None

# ---------------------------- MAIN ------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = GlossaryApp(root)
    root.mainloop()
