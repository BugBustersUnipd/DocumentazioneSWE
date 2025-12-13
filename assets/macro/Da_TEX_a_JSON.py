#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
glossary_sync_tool.py - Sincronizzatore Glossario LaTeX/JSON

Sincronizza automaticamente il glossario LaTeX con il file JSON:
- Estrae termini e definizioni dal LaTeX
- Aggiorna il JSON in ordine alfabetico
- Supporta aggiunta, modifica e rimozione automatica
- Interfaccia grafica con progress bar
- Il file JSON finale si chiama SEMPRE "glossario.json"
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import re
import json
from datetime import datetime
import threading
from queue import Queue
import shutil

# --------------------------- COSTANTI --------------------------------
SUPPORTED_EXTS = {'.tex', '.latex', '.json'}
REQUIRED_JSON_NAME = "glossario.json"

# ------------------------- FUNZIONI UTILI -----------------------------

def extract_sections_from_latex(latex_content):
    """Estrae tutte le sezioni dal file LaTeX"""
    sections = {}
    
    # Pattern per sezioni e sottosezioni
    section_pattern = re.compile(r'\\section\{([A-Z])\}.*?(?=\\section\{|\Z)', re.DOTALL | re.IGNORECASE)
    subsection_pattern = re.compile(r'\\subsection\{([^}]+)\}(.*?)(?=\\subsection\{|\Z)', re.DOTALL)
    
    # Trova tutte le sezioni
    section_matches = list(section_pattern.finditer(latex_content))
    
    for i, section_match in enumerate(section_matches):
        section_letter = section_match.group(1)
        section_content = section_match.group(0)
        
        # Trova tutte le sottosezioni in questa sezione
        subsection_matches = subsection_pattern.findall(section_content)
        
        for term, definition in subsection_matches:
            # Pulisci la definizione
            definition = clean_latex_definition(definition)
            if term.strip() and definition.strip():
                sections[term.strip()] = definition.strip()
    
    return sections

def clean_latex_definition(text):
    """Pulisce il testo LaTeX rimuovendo comandi e formattazione"""
    # Rimuovi commenti LaTeX (tutto da % a fine riga)
    text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
    
    # Rimuovi comandi LaTeX comuni mantenendo il contenuto
    # Rimuovi \textbf, \textit, \texttt (mantieni il contenuto tra {})
    text = re.sub(r'\\textbf\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\textit\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\texttt\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\emph\{([^}]+)\}', r'\1', text)
    
    # Rimuovi \newpage, \pagebreak, \vspace, \hspace
    text = re.sub(r'\\newpage|\\pagebreak|\\clearpage|\\vspace\{[^}]*\}|\\hspace\{[^}]*\}', '', text)
    
    # Rimuovi comandi di formattazione vuoti
    text = re.sub(r'\\[a-zA-Z]+\{\}', '', text)
    
    # Normalizza spazi bianchi
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def load_json_glossary(json_path):
    """Carica il glossario JSON esistente"""
    try:
        if not os.path.exists(json_path):
            return {}  # File non esistente
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'terms' in data and isinstance(data['terms'], list):
            # Crea dizionario per accesso rapido
            glossary_dict = {}
            for item in data['terms']:
                if 'term' in item and 'definition' in item:
                    glossary_dict[item['term']] = item['definition']
            return glossary_dict
        else:
            # Prova formato alternativo
            if isinstance(data, dict):
                # Forse è già un dizionario term:definition
                return data
            elif isinstance(data, list):
                # Forse è una lista di dizionari con chiavi diverse
                glossary_dict = {}
                for item in data:
                    if isinstance(item, dict):
                        # Cerca chiavi comuni
                        if 'term' in item and 'definition' in item:
                            glossary_dict[item['term']] = item['definition']
                        elif 'name' in item and 'desc' in item:
                            glossary_dict[item['name']] = item['desc']
                return glossary_dict
        
        return {}
    except json.JSONDecodeError as e:
        raise Exception(f"Errore nel formato JSON: {str(e)}\nIl file potrebbe essere corrotto o non valido.")
    except Exception as e:
        raise Exception(f"Errore caricamento JSON: {str(e)}")

def ensure_correct_json_name(json_path):
    """Assicura che il percorso JSON abbia il nome corretto 'glossario.json'"""
    directory = os.path.dirname(json_path)
    correct_path = os.path.join(directory, REQUIRED_JSON_NAME)
    return correct_path

def save_json_glossary(json_path, terms_dict, progress_callback=None):
    """Salva il glossario in JSON ordinato alfabeticamente"""
    # Assicura che il file si chiami 'glossario.json'
    json_path = ensure_correct_json_name(json_path)
    
    # Converti dizionario in lista di oggetti
    terms_list = []
    
    for i, (term, definition) in enumerate(sorted(terms_dict.items(), key=lambda x: x[0].lower())):
        terms_list.append({
            "term": term,
            "definition": definition
        })
        
        if progress_callback and i % 10 == 0:
            progress = (i / len(terms_dict)) * 100 if terms_dict else 0
            progress_callback(progress)
    
    # Crea struttura JSON
    data = {
        "terms": terms_list
    }
    
    # Salva file
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    if progress_callback:
        progress_callback(100)
    
    return data, json_path

def compare_glossaries(old_dict, new_dict):
    """Confronta due glossari e restituisce differenze"""
    added = []
    modified = []
    removed = []
    unchanged = []
    
    # Termini nuovi o modificati
    for term, definition in new_dict.items():
        if term not in old_dict:
            added.append(term)
        elif old_dict[term] != definition:
            modified.append(term)
        else:
            unchanged.append(term)
    
    # Termini rimossi
    for term in old_dict:
        if term not in new_dict:
            removed.append(term)
    
    return {
        'added': sorted(added, key=str.lower),
        'modified': sorted(modified, key=str.lower),
        'removed': sorted(removed, key=str.lower),
        'unchanged': sorted(unchanged, key=str.lower)
    }

def generate_report(latex_path, json_path, diff_result, final_count):
    """Genera report dettagliato della sincronizzazione"""
    report = []
    report.append("=" * 80)
    report.append("REPORT SINCRONIZZAZIONE GLOSSARIO")
    report.append("=" * 80)
    report.append(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"File LaTeX: {os.path.basename(latex_path)}")
    report.append(f"File JSON: {os.path.basename(json_path)}")
    report.append(f"Termini totali: {final_count}")
    report.append("=" * 80)
    
    # Statistiche
    report.append("\n📊 STATISTICHE:")
    report.append(f"  • Termini aggiunti: {len(diff_result['added'])}")
    report.append(f"  • Termini modificati: {len(diff_result['modified'])}")
    report.append(f"  • Termini rimossi: {len(diff_result['removed'])}")
    report.append(f"  • Termini invariati: {len(diff_result['unchanged'])}")
    
    # Dettagli aggiunti
    if diff_result['added']:
        report.append("\n➕ TERMINI AGGIUNTI:")
        for term in diff_result['added'][:10]:  # Mostra max 10
            report.append(f"  • {term}")
        if len(diff_result['added']) > 10:
            report.append(f"  ... e altri {len(diff_result['added']) - 10}")
    
    # Dettagli modificati
    if diff_result['modified']:
        report.append("\n✏️  TERMINI MODIFICATI:")
        for term in diff_result['modified'][:10]:  # Mostra max 10
            report.append(f"  • {term}")
        if len(diff_result['modified']) > 10:
            report.append(f"  ... e altri {len(diff_result['modified']) - 10}")
    
    # Dettagli rimossi
    if diff_result['removed']:
        report.append("\n🗑️  TERMINI RIMOSSI:")
        for term in diff_result['removed'][:10]:  # Mostra max 10
            report.append(f"  • {term}")
        if len(diff_result['removed']) > 10:
            report.append(f"  ... e altri {len(diff_result['removed']) - 10}")
    
    # Riepilogo
    report.append("\n" + "=" * 80)
    if not diff_result['added'] and not diff_result['modified'] and not diff_result['removed']:
        report.append("✅ GLOSSARI GIÀ SINCRONIZZATI")
    else:
        report.append("🔄 SINCRONIZZAZIONE COMPLETATA")
    report.append("=" * 80)
    
    return "\n".join(report)

# ----------------------------- GUI -----------------------------------

class GlossarySyncTool:
    def __init__(self, root):
        self.root = root
        self.root.title("🔄 Sincronizzatore Glossario LaTeX/JSON")
        self.root.geometry("1000x700")
        
        # Variabili
        self.latex_path = tk.StringVar()
        self.json_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Pronto")
        self.progress_value = tk.IntVar(value=0)
        
        # Coda per thread
        self.message_queue = Queue()
        
        # Setup UI
        self.setup_ui()
        
        # Check per messaggi
        self.check_queue()
    
    def setup_ui(self):
        """Configura l'interfaccia utente"""
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header(main_frame)
        
        # Pannello file
        self.create_file_panel(main_frame)
        
        # Pannello progresso
        self.create_progress_panel(main_frame)
        
        # Pannello risultati
        self.create_results_panel(main_frame)
        
        # Footer
        self.create_footer(main_frame)
    
    def create_header(self, parent):
        """Crea l'intestazione"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(
            header_frame,
            text="🔄 SINCRONIZZATORE GLOSSARIO LaTeX ↔ JSON",
            font=("Arial", 16, "bold"),
            foreground="#2c3e50"
        )
        title.pack(anchor=tk.W)
        
        subtitle = tk.Label(
            header_frame,
            text=f"Sincronizza automaticamente il glossario LaTeX - Il file JSON finale si chiamerà '{REQUIRED_JSON_NAME}'",
            font=("Arial", 10),
            foreground="#7f8c8d"
        )
        subtitle.pack(anchor=tk.W, pady=(5, 0))
    
    def create_file_panel(self, parent):
        """Crea il pannello per selezionare i file"""
        file_frame = ttk.LabelFrame(parent, text="📁 File", padding="15")
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        # File LaTeX
        latex_frame = ttk.Frame(file_frame)
        latex_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(latex_frame, text="Glossario LaTeX:", width=15).pack(side=tk.LEFT)
        
        self.latex_entry = ttk.Entry(latex_frame, textvariable=self.latex_path, width=60)
        self.latex_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(
            latex_frame,
            text="Sfoglia",
            command=self.browse_latex
        ).pack(side=tk.LEFT)
        
        # File JSON
        json_frame = ttk.Frame(file_frame)
        json_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(json_frame, text="Glossario JSON:", width=15).pack(side=tk.LEFT)
        
        self.json_entry = ttk.Entry(json_frame, textvariable=self.json_path, width=60)
        self.json_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(
            json_frame,
            text="Sfoglia",
            command=self.browse_json
        ).pack(side=tk.LEFT)
        
        # Auto-detect JSON
        ttk.Button(
            file_frame,
            text=f"🔍 Trova/Crea '{REQUIRED_JSON_NAME}'",
            command=self.auto_detect_json
        ).pack(pady=(10, 0))
    
    def create_progress_panel(self, parent):
        """Crea il pannello progresso"""
        progress_frame = ttk.LabelFrame(parent, text="📊 Progresso", padding="15")
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Status label
        self.status_label = tk.Label(
            progress_frame,
            textvariable=self.status_text,
            font=("Arial", 10),
            foreground="#2c3e50"
        )
        self.status_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_value,
            length=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Pulsanti azione
        button_frame = ttk.Frame(progress_frame)
        button_frame.pack(fill=tk.X)
        
        self.sync_button = ttk.Button(
            button_frame,
            text="🔄 SINCRONIZZA",
            command=self.start_sync,
            style='Accent.TButton'
        )
        self.sync_button.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="📋 Analizza Differenze",
            command=self.analyze_differences
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="🔄 Reset",
            command=self.reset_ui
        ).pack(side=tk.RIGHT, padx=2)
    
    def create_results_panel(self, parent):
        """Crea il pannello risultati"""
        results_frame = ttk.LabelFrame(parent, text="📋 Risultati", padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Area testo risultati
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            background="#f8f9fa",
            padx=10,
            pady=10
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Configura tag per colori
        self.results_text.tag_config("success", foreground="#27ae60")
        self.results_text.tag_config("warning", foreground="#f39c12")
        self.results_text.tag_config("danger", foreground="#e74c3c")
        self.results_text.tag_config("info", foreground="#3498db")
    
    def create_footer(self, parent):
        """Crea il footer"""
        footer_frame = ttk.Frame(parent)
        footer_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Info
        info_label = tk.Label(
            footer_frame,
            text=f"Il file JSON finale si chiama '{REQUIRED_JSON_NAME}' | Termini ordinati alfabeticamente",
            font=("Arial", 9),
            foreground="#7f8c8d"
        )
        info_label.pack(side=tk.LEFT)
        
        # Pulsanti esportazione
        export_frame = ttk.Frame(footer_frame)
        export_frame.pack(side=tk.RIGHT)
        
        ttk.Button(
            export_frame,
            text="📄 Esporta Report",
            command=self.export_report
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            export_frame,
            text="📋 Copia",
            command=self.copy_results
        ).pack(side=tk.LEFT, padx=2)
    
    def browse_latex(self):
        """Seleziona file LaTeX"""
        path = filedialog.askopenfilename(
            title="Seleziona glossario LaTeX",
            filetypes=[
                ("File LaTeX", "*.tex *.latex"),
                ("Tutti i file", "*.*")
            ]
        )
        if path:
            self.latex_path.set(path)
    
    def browse_json(self):
        """Seleziona file JSON"""
        path = filedialog.askopenfilename(
            title="Seleziona glossario JSON",
            filetypes=[
                ("File JSON", "*.json"),
                ("Tutti i file", "*.*")
            ]
        )
        if path:
            self.json_path.set(path)
    
    def auto_detect_json(self):
        """Trova o crea glossario.json"""
        latex_path = self.latex_path.get().strip()
        
        if not latex_path:
            messagebox.showwarning("Attenzione", "Seleziona prima un file LaTeX.")
            return
        
        # Cerca nella cartella del file LaTeX
        latex_dir = os.path.dirname(latex_path)
        if not latex_dir:
            latex_dir = "."
        
        # Prima cerca un file JSON esistente
        json_files = []
        if os.path.exists(latex_dir):
            for file in os.listdir(latex_dir):
                if file.lower().endswith('.json'):
                    json_files.append(file)
        
        if json_files:
            # Se c'è già un glossario.json, usalo
            if REQUIRED_JSON_NAME in json_files:
                json_path = os.path.join(latex_dir, REQUIRED_JSON_NAME)
                self.json_path.set(json_path)
                messagebox.showinfo("JSON Trovato", 
                                  f"Trovato '{REQUIRED_JSON_NAME}'.\nPercorso: {json_path}")
                return
            
            # Altrimenti, chiedi all'utente quale usare
            file_list = "\n".join(f"• {f}" for f in json_files)
            response = messagebox.askyesno(
                "File JSON trovati",
                f"Nella cartella sono stati trovati questi file JSON:\n\n{file_list}\n\n"
                f"Vuoi usarne uno come base per creare '{REQUIRED_JSON_NAME}'?"
            )
            
            if response:
                # Se l'utente vuole usare un JSON esistente
                path = filedialog.askopenfilename(
                    initialdir=latex_dir,
                    title="Seleziona file JSON da usare come base",
                    filetypes=[("File JSON", "*.json")]
                )
                if path:
                    self.json_path.set(path)
                    messagebox.showinfo(
                        "File selezionato",
                        f"File JSON selezionato come base.\n"
                        f"Il risultato finale sarà salvato come '{REQUIRED_JSON_NAME}'."
                    )
                return
        
        # Se non ci sono file JSON, crea nuovo
        json_path = os.path.join(latex_dir, REQUIRED_JSON_NAME)
        
        response = messagebox.askyesno(
            "Crea nuovo file",
            f"Non sono stati trovati file JSON nella cartella.\n\n"
            f"Creare nuovo file '{REQUIRED_JSON_NAME}'?\n\n"
            f"Percorso: {json_path}"
        )
        
        if response:
            self.json_path.set(json_path)
            # Crea un file JSON vuoto
            empty_data = {"terms": []}
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(empty_data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("File creato", f"File '{REQUIRED_JSON_NAME}' creato con successo.")
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile creare il file: {str(e)}")
    
    def start_sync(self):
        """Avvia la sincronizzazione in thread separato"""
        # Verifica file
        latex_path = self.latex_path.get().strip()
        json_input_path = self.json_path.get().strip()
        
        if not latex_path:
            messagebox.showwarning("Attenzione", "Seleziona un file LaTeX.")
            return
        
        if not json_input_path:
            messagebox.showwarning("Attenzione", "Seleziona un file JSON.")
            return
        
        if not os.path.exists(latex_path):
            messagebox.showerror("Errore", f"File LaTeX non trovato:\n{latex_path}")
            return
        
        # Determina il percorso finale per glossario.json
        if os.path.basename(json_input_path).lower() != REQUIRED_JSON_NAME.lower():
            # Se l'utente ha selezionato un file con nome diverso
            directory = os.path.dirname(json_input_path)
            if not directory:
                directory = "."
            json_final_path = os.path.join(directory, REQUIRED_JSON_NAME)
            
            # Avvisa l'utente del cambio nome
            response = messagebox.askyesno(
                "Rinomina file",
                f"Il file selezionato non si chiama '{REQUIRED_JSON_NAME}'.\n\n"
                f"Input: {os.path.basename(json_input_path)}\n"
                f"Output: {REQUIRED_JSON_NAME}\n\n"
                f"Vuoi continuare? Il file sarà salvato come '{REQUIRED_JSON_NAME}'."
            )
            
            if not response:
                return
        else:
            json_final_path = json_input_path
        
        # Disabilita pulsanti durante sincronizzazione
        self.sync_button.config(state=tk.DISABLED)
        self.status_text.set(f"Sincronizzazione in corso...")
        self.progress_value.set(0)
        
        def sync_task():
            try:
                # Aggiorna progresso
                def update_progress(value):
                    self.message_queue.put(('progress', value))
                
                def update_status(message):
                    self.message_queue.put(('status', message))
                
                # 1. Carica LaTeX
                update_status("Caricamento LaTeX...")
                with open(latex_path, 'r', encoding='utf-8') as f:
                    latex_content = f.read()
                
                update_progress(20)
                
                # 2. Estrai termini da LaTeX
                update_status("Estrazione termini da LaTeX...")
                latex_terms = extract_sections_from_latex(latex_content)
                update_progress(40)
                
                # 3. Carica JSON esistente (se esiste)
                update_status("Caricamento JSON esistente...")
                json_terms = {}
                
                # Prova a caricare dal file di input (se esiste)
                if os.path.exists(json_input_path):
                    try:
                        json_terms = load_json_glossary(json_input_path)
                    except Exception as e:
                        # Se c'è un errore, avvisa ma continua con dizionario vuoto
                        self.message_queue.put(('warning', 
                            f"Attenzione: il file JSON non è stato caricato correttamente.\n"
                            f"Errore: {str(e)}\n\n"
                            f"Verrà creato un nuovo glossario."))
                        json_terms = {}
                
                update_progress(60)
                
                # 4. Confronta
                update_status("Analisi differenze...")
                diff_result = compare_glossaries(json_terms, latex_terms)
                update_progress(80)
                
                # 5. Salva nuovo JSON con nome corretto
                update_status(f"Salvataggio {REQUIRED_JSON_NAME}...")
                _, saved_json_path = save_json_glossary(json_final_path, latex_terms, update_progress)
                update_progress(90)
                
                # 6. Genera report
                update_status("Generazione report...")
                report = generate_report(latex_path, saved_json_path, diff_result, len(latex_terms))
                
                self.message_queue.put(('complete', (report, diff_result, saved_json_path)))
                
            except Exception as e:
                self.message_queue.put(('error', str(e)))
        
        # Avvia thread
        thread = threading.Thread(target=sync_task, daemon=True)
        thread.start()
    
    def analyze_differences(self):
        """Analizza solo le differenze senza salvare"""
        latex_path = self.latex_path.get().strip()
        json_path = self.json_path.get().strip()
        
        if not latex_path:
            messagebox.showwarning("Attenzione", "Seleziona un file LaTeX.")
            return
        
        if not json_path:
            messagebox.showwarning("Attenzione", "Seleziona un file JSON.")
            return
        
        try:
            # Carica LaTeX
            with open(latex_path, 'r', encoding='utf-8') as f:
                latex_content = f.read()
            
            latex_terms = extract_sections_from_latex(latex_content)
            
            # Carica JSON se esiste
            if os.path.exists(json_path):
                try:
                    json_terms = load_json_glossary(json_path)
                except Exception as e:
                    messagebox.showerror(
                        "Errore JSON",
                        f"Impossibile leggere il file JSON:\n\n{str(e)}\n\n"
                        f"Assicurati che il file sia un JSON valido."
                    )
                    return
            else:
                json_terms = {}
                messagebox.showinfo(
                    "File non trovato", 
                    f"Il file JSON non esiste.\nAnalisi basata su glossario vuoto."
                )
            
            diff_result = compare_glossaries(json_terms, latex_terms)
            
            # Determina il nome finale
            if os.path.basename(json_path).lower() != REQUIRED_JSON_NAME.lower():
                final_name = REQUIRED_JSON_NAME
            else:
                final_name = os.path.basename(json_path)
            
            # Genera report analisi
            report = []
            report.append("=" * 80)
            report.append("ANALISI DIFFERENZE (SOLO LETTURA)")
            report.append("=" * 80)
            report.append(f"File LaTeX: {os.path.basename(latex_path)}")
            report.append(f"File JSON input: {os.path.basename(json_path)}")
            report.append(f"File JSON output: {final_name}")
            report.append(f"Termini LaTeX: {len(latex_terms)}")
            report.append(f"Termini JSON: {len(json_terms)}")
            report.append("=" * 80)
            
            report.append("\n📊 DIFFERENZE:")
            report.append(f"  • Da aggiungere: {len(diff_result['added'])}")
            report.append(f"  • Da modificare: {len(diff_result['modified'])}")
            report.append(f"  • Da rimuovere: {len(diff_result['removed'])}")
            
            if diff_result['added']:
                report.append("\n➕ TERMINI NUOVI (non in JSON):")
                for term in diff_result['added'][:20]:
                    report.append(f"  • {term}")
                if len(diff_result['added']) > 20:
                    report.append(f"  ... e altri {len(diff_result['added']) - 20}")
            
            if diff_result['removed']:
                report.append("\n🗑️  TERMINI DA RIMUOVERE (non in LaTeX):")
                for term in diff_result['removed'][:20]:
                    report.append(f"  • {term}")
                if len(diff_result['removed']) > 20:
                    report.append(f"  ... e altri {len(diff_result['removed']) - 20}")
            
            report.append("\n" + "=" * 80)
            report.append(f"ℹ️  Questa è solo un'analisi. Usa 'SINCRONIZZA' per creare/aggiornare '{REQUIRED_JSON_NAME}'.")
            report.append("=" * 80)
            
            self.results_text.delete("1.0", tk.END)
            self.results_text.insert("1.0", "\n".join(report))
            
        except Exception as e:
            messagebox.showerror("Errore Analisi", f"Errore durante l'analisi:\n\n{str(e)}")
    
    def check_queue(self):
        """Controlla la coda per messaggi dai thread"""
        try:
            while not self.message_queue.empty():
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == 'progress':
                    self.progress_value.set(data)
                
                elif msg_type == 'status':
                    self.status_text.set(data)
                
                elif msg_type == 'warning':
                    messagebox.showwarning("Avviso", data)
                
                elif msg_type == 'complete':
                    report, diff_result, saved_json_path = data
                    self.show_results(report, diff_result, saved_json_path)
                    self.sync_button.config(state=tk.NORMAL)
                
                elif msg_type == 'error':
                    self.status_text.set(f"Errore: {data}")
                    self.sync_button.config(state=tk.NORMAL)
                    messagebox.showerror("Errore Sincronizzazione", 
                                       f"Errore durante la sincronizzazione:\n\n{str(data)}")
        
        except:
            pass
        
        # Ricontrolla
        self.root.after(100, self.check_queue)
    
    def show_results(self, report, diff_result, saved_json_path):
        """Mostra i risultati della sincronizzazione"""
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", report)
        
        # Evidenzia sezioni
        lines = report.split('\n')
        
        # Applica colori in base al contenuto
        for i, line in enumerate(lines):
            start_idx = f"{i+1}.0"
            
            if "✅" in line or "GIÀ SINCRONIZZATI" in line:
                self.results_text.tag_add("success", start_idx, f"{i+1}.end")
            elif "🔄" in line or "COMPLETATA" in line:
                self.results_text.tag_add("info", start_idx, f"{i+1}.end")
            elif "➕" in line or "AGGIUNTI" in line:
                self.results_text.tag_add("success", start_idx, f"{i+1}.end")
            elif "✏️" in line or "MODIFICATI" in line:
                self.results_text.tag_add("warning", start_idx, f"{i+1}.end")
            elif "🗑️" in line or "RIMOSSI" in line:
                self.results_text.tag_add("danger", start_idx, f"{i+1}.end")
        
        # Messaggio finale
        added = len(diff_result['added'])
        modified = len(diff_result['modified'])
        removed = len(diff_result['removed'])
        
        if added == 0 and modified == 0 and removed == 0:
            self.status_text.set(f"✅ Glossari già sincronizzati")
        else:
            self.status_text.set(f"🔄 Sincronizzazione completata: +{added} ✏️{modified} -{removed}")
        
        # Mostra notifica con percorso del file
        messagebox.showinfo(
            "Sincronizzazione Completata",
            f"Il file '{REQUIRED_JSON_NAME}' è stato creato/aggiornato con successo:\n\n"
            f"Percorso: {saved_json_path}\n"
            f"Termini totali: {len(diff_result['added']) + len(diff_result['modified']) + len(diff_result['unchanged'])}\n\n"
            f"File di input: {os.path.basename(self.json_path.get())}\n"
            f"File di output: {os.path.basename(saved_json_path)}"
        )
    
    def export_report(self):
        """Esporta il report"""
        content = self.results_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Nessun report", "Non ci sono risultati da esportare.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("File di testo", "*.txt"),
                ("File Markdown", "*.md"),
                ("Tutti i file", "*.*")
            ]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                messagebox.showinfo(
                    "Esportazione Completata",
                    f"Report esportato in:\n{filename}"
                )
            except Exception as e:
                messagebox.showerror("Errore Esportazione", str(e))
    
    def copy_results(self):
        """Copia risultati negli appunti"""
        content = self.results_text.get("1.0", tk.END).strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            
            # Feedback temporaneo
            original = self.status_text.get()
            self.status_text.set("✅ Risultati copiati!")
            self.root.after(2000, lambda: self.status_text.set(original))
    
    def reset_ui(self):
        """Resetta l'interfaccia"""
        self.latex_path.set("")
        self.json_path.set("")
        self.status_text.set("Pronto")
        self.progress_value.set(0)
        self.results_text.delete("1.0", tk.END)
        self.sync_button.config(state=tk.NORMAL)

# ---------------------------- MAIN ------------------------------------

def main():
    root = tk.Tk()
    
    # Configura stile
    style = ttk.Style()
    style.configure('Accent.TButton', foreground='white', background='#3498db')
    
    app = GlossarySyncTool(root)
    
    # Imposta dimensioni minime
    root.minsize(900, 600)
    
    root.mainloop()

if __name__ == "__main__":
    main()