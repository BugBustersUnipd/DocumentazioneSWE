#!/usr/bin/env python3
"""
Script per aggiornare automaticamente il file Glossario.tex partendo dal file Json.
leggendo i termini dal file glossario.json nella cartella SITO.
Mantiene la struttura LaTeX esistente e ordina i termini alfabeticamente.
"""

import json
import re
from pathlib import Path

def load_glossary_terms(glossary_path):
    """Carica i termini dal file JSON glossario."""
    with open(glossary_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'terms' not in data:
        raise ValueError("Il file JSON non contiene la chiave 'terms'")

    return data['terms']

def generate_latex_sections(terms):
    """Genera le sezioni LaTeX ordinate alfabeticamente."""
    # Ordina i termini alfabeticamente (case-insensitive)
    sorted_terms = sorted(terms, key=lambda x: x['term'].lower())

    sections = {}
    current_section = None

    # Raggruppa i termini per lettera iniziale
    for term_data in sorted_terms:
        term = term_data['term']
        definition = term_data['definition']

        # Ottieni la lettera iniziale (case-insensitive)
        first_letter = term[0].upper()

        if first_letter not in sections:
            sections[first_letter] = []

        sections[first_letter].append((term, definition))

    # Genera il contenuto LaTeX
    latex_content = []

    for letter in sorted(sections.keys()):
        latex_content.append(f"\\newpage\n\n\\section{{{letter}}}\n")

        for term, definition in sections[letter]:
            # Gestisci i caratteri speciali LaTeX nel termine
            safe_term = term.replace('&', '\\&').replace('%', '\\%').replace('$', '\\$').replace('#', '\\#')

            # Gestisci i caratteri speciali LaTeX nella definizione
            safe_definition = definition.replace('&', '\\&').replace('%', '\\%').replace('$', '\\$').replace('#', '\\#')

            latex_content.append(f"\n\\subsection{{{safe_term}}}")
            latex_content.append(f"{safe_definition}\n")

    return '\n'.join(latex_content)

def update_latex_file(latex_path, glossary_path):
    """Aggiorna il file LaTeX con i nuovi termini dal glossario JSON."""
    # Leggi il file LaTeX esistente
    with open(latex_path, 'r', encoding='utf-8') as f:
        latex_content = f.read()

    # Carica i termini dal glossario
    terms = load_glossary_terms(glossary_path)

    # Genera le nuove sezioni
    new_sections = generate_latex_sections(terms)

    # Trova la parte da sostituire: da dopo "\section{Introduzione}" fino a prima di "\end{document}"
    # Cerchiamo il pattern che identifica l'inizio delle sezioni dei termini
    intro_pattern = r'(\\section\{Introduzione\}.*?\\newpage\s*\\section\{[A-Z]\})'
    end_pattern = r'(\\end\{document\})'

    # Troviamo dove inizia la sezione Introduzione
    intro_match = re.search(intro_pattern, latex_content, re.DOTALL)
    if not intro_match:
        raise ValueError("Non riesco a trovare la sezione Introduzione nel file LaTeX")

    # Troviamo dove finisce il documento
    end_match = re.search(end_pattern, latex_content)
    if not end_match:
        raise ValueError("Non riesco a trovare \\end{document} nel file LaTeX")

    # Estrai la parte iniziale (fino alla fine dell'introduzione)
    intro_end = intro_match.end(1)
    start_content = latex_content[:intro_end]

    # La parte finale inizia da \end{document}
    end_start = end_match.start(1)
    end_content = latex_content[end_start:]

    # Combina tutto
    updated_content = start_content + '\n' + new_sections + '\n\n' + end_content

    # Scrivi il file aggiornato
    with open(latex_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"✅ File LaTeX aggiornato con {len(terms)} termini")
    print(f"📁 File salvato: {latex_path}")

def main():
    # Percorsi
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    glossario_json = project_root / "SITO" / "glossario.json"
    glossario_tex = project_root / "RTB" / "GLOSSARIO" / "Glossario.tex"

    print("🔄 Script per aggiornare Glossario.tex dal file JSON")
    print(f"📖 Glossario JSON: {glossario_json}")
    print(f"📝 File LaTeX: {glossario_tex}")
    print()

    # Verifica che i file esistano
    if not glossario_json.exists():
        print(f"❌ Errore: file glossario JSON non trovato: {glossario_json}")
        return 1

    if not glossario_tex.exists():
        print(f"❌ Errore: file LaTeX non trovato: {glossario_tex}")
        return 1

    try:
        # Carica e mostra info sui termini
        terms = load_glossary_terms(glossario_json)
        print(f"📊 Trovati {len(terms)} termini nel glossario JSON")

        # Chiedi conferma
        conferma = input("⚠️  Vuoi aggiornare il file LaTeX? (s/N): ").strip().lower()
        if conferma not in ['s', 'si', 'sì', 'y', 'yes']:
            print("❌ Operazione annullata.")
            return 0

        # Aggiorna il file
        update_latex_file(glossario_tex, glossario_json)

        print("✅ Aggiornamento completato!")

    except Exception as e:
        print(f"❌ Errore durante l'aggiornamento: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())