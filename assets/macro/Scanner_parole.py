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
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import re
import json
from pathlib import Path

# --------------------------- COSTANTI --------------------------------
TAG_G = r"\textsubscript{\scalebox{0.6}{\textbf{G}}}"

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

def find_occurrences_with_tag(text, term):
    """
    Cerca tutte le occorrenze case-insensitive di un termine e le sue varianti.
    Ritorna lista di tuple: (start, end, lineno, line_text, tag_present, matched_variant)
    """
    results = []
    variants = generate_term_variants(term)
    
    for variant in variants:
        # Scegli il pattern regex in base al tipo di variante
        
        # 1. Acronimi (solo lettere maiuscole, 2+ caratteri)
        if re.match(r'^[A-Z]{2,}$', variant):
            # Per acronimi usa lookahead/lookbehind per evitare match parziali
            # Es: "POC" non deve matchare "EPOCH"
            pattern = r'(?<![a-zA-Z])' + re.escape(variant) + r'(?![a-zA-Z])'
        
        # 2. Frasi multi-parola
        elif ' ' in variant:
            # Per frasi con spazi, assicurati che non ci siano caratteri word prima/dopo
            pattern = r'(?<!\w)' + re.escape(variant) + r'(?!\w)'
        
        # 3. Parole singole normali
        else:
            # Usa word boundary standard
            pattern = r'\b' + re.escape(variant) + r'\b'
        
        # Cerca tutte le occorrenze (case-insensitive)
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start = match.start()
            end = match.end()
            
            # Calcola numero di riga
            lineno = text[:start].count("\n") + 1
            lines = text.splitlines()
            line_text = lines[lineno - 1] if 0 <= lineno - 1 < len(lines) else ""
            
            # Cerca TAG_G dopo la parola (salta solo spazi bianchi)
            after_idx = end
            max_skip = 100
            skipped = 0
            
            while after_idx < len(text) and skipped < max_skip and text[after_idx].isspace():
                after_idx += 1
                skipped += 1
            
            tag_present = text.startswith(TAG_G, after_idx)
            
            # Verifica che tra parola e tag ci siano SOLO spazi bianchi
            if tag_present:
                text_between = text[end:after_idx]
                if text_between.strip():  # Se c'è qualcosa oltre agli spazi
                    tag_present = False
            
            results.append((start, end, lineno, line_text.strip(), tag_present, variant))
    
    return results

def analyze_text(text, phrases, progress_callback=None):
    """
    Analizza il testo cercando i termini del glossario (versione migliorata).
    """
    terms_with_missing_tag = {}  # Termini presenti ma senza TAG
    terms_not_found = []  # Termini non presenti nel documento
    
    total = len(phrases)
    
    for i, phrase in enumerate(phrases):
        if progress_callback:
            progress = (i / total) * 100
            progress_callback(progress, f"Analisi termine {i+1}/{total}: {phrase[:30]}...")
        
        # Usa la funzione migliorata che gestisce varianti
        occurrences = find_occurrences_with_tag(text, phrase)
        
        if not occurrences:
            # Nessuna occorrenza trovata per questo termine
            terms_not_found.append(phrase)
        else:
            # Filtra solo le occorrenze SENZA TAG
            matches_without_tag = []
            
            for (start, end, lineno, line_text, tag_present, matched_variant) in occurrences:
                if not tag_present:
                    matches_without_tag.append((lineno, line_text, matched_variant))
            
            # Se ci sono occorrenze senza TAG, registrale
            if matches_without_tag:
                terms_with_missing_tag[phrase] = {
                    "count": len(occurrences),
                    "matches_without_tag": matches_without_tag
                }
    
    if progress_callback:
        progress_callback(100, "Analisi completata!")
    
    return terms_with_missing_tag, terms_not_found

def find_latex_files(path):
    """Trova tutti i file .tex/.latex in una directory e sottodirectory"""
    latex_files = []
    path_obj = Path(path)
    
    if path_obj.is_file():
        if path_obj.suffix in ['.tex', '.latex']:
            latex_files.append(str(path_obj))
    elif path_obj.is_dir():
        for ext in ['*.tex', '*.latex']:
            latex_files.extend([str(f) for f in path_obj.rglob(ext)])
    
    return sorted(latex_files)

# ----------------------------- GUI -----------------------------------

class GlossaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Scanner Glossario Automatico (Migliorato)")
        self.root.geometry("1100x750")
        self.root.minsize(900, 650)
        
        # Variabili
        self.glossary_path_var = tk.StringVar()
        self.doc_path_var = tk.StringVar()
        self.analyze_mode_var = tk.StringVar(value="single")  # single o folder
        self.terms_with_missing_tag = None
        self.terms_not_found = None
        self.terms = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Crea l'interfaccia utente"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(header_frame, text="🔍 Scanner Glossario Automatico (v2.0)", 
                              font=("Arial", 14, "bold"), foreground="#2c3e50")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(header_frame, 
                                 text="Gestisce acronimi, traduzioni e termini speciali • Case-insensitive",
                                 font=("Arial", 9), foreground="#7f8c8d")
        subtitle_label.pack(anchor=tk.W)
        
        # Controlli
        controls_frame = ttk.LabelFrame(main_frame, text="Configurazione", padding="8")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Selezione glossario
        glossary_frame = ttk.Frame(controls_frame)
        glossary_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(glossary_frame, text="File Glossario:").pack(side=tk.LEFT)
        
        self.glossary_entry = ttk.Entry(glossary_frame, textvariable=self.glossary_path_var, width=50)
        self.glossary_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(glossary_frame, text="Sfoglia...", 
                  command=self.choose_glossary).pack(side=tk.LEFT, padx=2)
        ttk.Button(glossary_frame, text="Carica Termini", 
                  command=self.load_terms).pack(side=tk.LEFT, padx=2)
        
        # Progress bar per caricamento glossario
        self.glossary_progress_frame = ttk.Frame(controls_frame)
        self.glossary_progress_frame.pack(fill=tk.X, pady=2)
        
        self.glossary_progress = ttk.Progressbar(
            self.glossary_progress_frame, mode='determinate', length=400
        )
        self.glossary_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.glossary_progress_label = tk.Label(
            self.glossary_progress_frame, text="", 
            font=("Arial", 8), foreground="#7f8c8d"
        )
        self.glossary_progress_label.pack(side=tk.LEFT, padx=5)
        
        # Info termini caricati
        self.terms_info_label = tk.Label(controls_frame, 
                                        text="Termini caricati: 0",
                                        font=("Arial", 9), foreground="#27ae60")
        self.terms_info_label.pack(anchor=tk.W, pady=5)
        
        # Modalità analisi
        mode_frame = ttk.Frame(controls_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="Modalità:").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Radiobutton(mode_frame, text="File singolo", 
                       variable=self.analyze_mode_var, 
                       value="single",
                       command=self.update_doc_label).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(mode_frame, text="Cartella (incluse sottocartelle)", 
                       variable=self.analyze_mode_var, 
                       value="folder",
                       command=self.update_doc_label).pack(side=tk.LEFT, padx=5)
        
        # Selezione documento/cartella
        doc_frame = ttk.Frame(controls_frame)
        doc_frame.pack(fill=tk.X, pady=5)
        
        self.doc_label = tk.Label(doc_frame, text="File LaTeX:")
        self.doc_label.pack(side=tk.LEFT)
        
        self.doc_entry = ttk.Entry(doc_frame, textvariable=self.doc_path_var, width=50)
        self.doc_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(doc_frame, text="Sfoglia...", 
                  command=self.choose_document).pack(side=tk.LEFT, padx=2)
        ttk.Button(doc_frame, text="Analizza", 
                  command=self.run_analysis).pack(side=tk.LEFT, padx=2)
        
        # Progress bar per analisi
        self.analysis_progress_frame = ttk.Frame(controls_frame)
        self.analysis_progress_frame.pack(fill=tk.X, pady=2)
        
        self.analysis_progress = ttk.Progressbar(
            self.analysis_progress_frame, mode='determinate', length=400
        )
        self.analysis_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.analysis_progress_label = tk.Label(
            self.analysis_progress_frame, text="", 
            font=("Arial", 8), foreground="#7f8c8d"
        )
        self.analysis_progress_label.pack(side=tk.LEFT, padx=5)
        
        # Risultati
        results_frame = ttk.LabelFrame(main_frame, text="Risultati", padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = scrolledtext.ScrolledText(
            results_frame, wrap=tk.WORD, font=("Consolas", 10), 
            background="#f8f9fa", padx=10, pady=10
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Footer
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(footer_frame, text="Esporta Risultati", 
                  command=self.export_results).pack(side=tk.RIGHT, padx=2)
        ttk.Button(footer_frame, text="Pulisci", 
                  command=self.clear_results).pack(side=tk.RIGHT, padx=2)
    
    def update_doc_label(self):
        """Aggiorna l'etichetta in base alla modalità selezionata"""
        if self.analyze_mode_var.get() == "single":
            self.doc_label.config(text="File LaTeX:")
        else:
            self.doc_label.config(text="Cartella:")
    
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
        
    def choose_glossary(self):
        """Seleziona il file glossario"""
        path = filedialog.askopenfilename(
            title="Seleziona file Glossario",
            filetypes=[("File Glossario", "*.tex *.latex *.json"), ("Tutti i file", "*.*")]
        )
        if path:
            self.glossary_path_var.set(path)
            
    def choose_document(self):
        """Seleziona il documento o la cartella da analizzare"""
        if self.analyze_mode_var.get() == "single":
            path = filedialog.askopenfilename(
                title="Seleziona documento LaTeX",
                filetypes=[("File LaTeX", "*.latex *.tex"), ("Tutti i file", "*.*")]
            )
        else:
            path = filedialog.askdirectory(
                title="Seleziona cartella contenente file LaTeX"
            )
        
        if path:
            self.doc_path_var.set(path)
            
    def load_terms(self):
        """Carica i termini dal glossario"""
        path = self.glossary_path_var.get().strip()
        if not path:
            messagebox.showwarning("Attenzione", "Seleziona prima un file glossario.")
            return
        
        self.root.config(cursor="watch")
        self.glossary_progress['value'] = 0
        self.glossary_progress_label.config(text="Inizializzazione...")
        
        try:
            terms, error = load_glossary_terms(path, self.update_glossary_progress)
            if error:
                messagebox.showerror("Errore", error)
                return
            
            self.terms = terms
            self.terms_info_label.config(
                text=f"✓ Termini caricati: {len(self.terms)}",
                foreground="#27ae60"
            )
            
            # Reset progress bar
            self.glossary_progress['value'] = 0
            self.glossary_progress_label.config(text="")
            
            # Mostra anteprima termini con varianti
            preview_lines = []
            for i, term in enumerate(self.terms[:5]):
                variants = generate_term_variants(term)
                if len(variants) > 1:
                    preview_lines.append(f"• {term} → {variants}")
                else:
                    preview_lines.append(f"• {term}")
            
            preview = "\n".join(preview_lines)
            if len(self.terms) > 5:
                preview += f"\n... (+{len(self.terms)-5} altri)"
            
            messagebox.showinfo(
                "Termini Caricati", 
                f"✓ Caricati {len(self.terms)} termini dal glossario.\n\n"
                f"Primi termini (con varianti):\n{preview}"
            )
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il caricamento:\n{e}")
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
                    f.write("=== SCANNER GLOSSARIO AUTOMATICO - RISULTATI (v2.0) ===\n\n")
                    f.write(f"Termini glossario: {len(self.terms)}\n")
                    f.write(f"File glossario: {self.glossary_path_var.get()}\n\n")
                    f.write("FUNZIONALITÀ:\n")
                    f.write("• Gestione acronimi: POC (Proof of Concept) → cerca POC e Proof of Concept\n")
                    f.write("• Gestione traduzioni: Affidabilità (Reliability) → cerca entrambe\n")
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