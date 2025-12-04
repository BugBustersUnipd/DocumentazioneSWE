#!/usr/bin/env python3
"""
Script sincronizzazione glossario - versione compatta
"""

import re, json, sys
from pathlib import Path

# Configurazione
BASE = Path("E:/TERZO ANNO/PRIMO TRIMESTRE/INGERNERIA DEL SOFTWARE/PROGETTO")
LATEX = BASE / "RTB" / "GLOSSARIO" / "Glossario.tex"
JSON = BASE / "SITO" / "glossario.json"

def main():
    print("="*50)
    print("SINCRONIZZAZIONE GLOSSARIO")
    print("="*50)
    
    # Leggi LaTeX
    print(f"\n📄 Leggo LaTeX: {LATEX.name}")
    if not LATEX.exists():
        print("❌ File LaTeX non trovato!")
        return 1
    
    with open(LATEX, 'r', encoding='utf-8') as f:
        tex = f.read()
    
    # Estrai termini da LaTeX
    tex_termini = {}
    matches = re.findall(r'\\subsection\{([^}]+)\}(.*?)(?=\\subsection|\\newpage|\\section|$)', tex, re.DOTALL)
    for nome, defn in matches:
        defn = re.sub(r'\s+', ' ', defn.strip())
        defn = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', defn)
        tex_termini[nome.strip()] = defn
    
    print(f"   ✅ Termini nel LaTeX: {len(tex_termini)}")
    
    # Leggi JSON
    print(f"\n📄 Leggo JSON: {JSON.name}")
    json_termini = {}
    if JSON.exists():
        with open(JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data.get('terms', []):
            json_termini[item['term']] = item['definition']
        print(f"   ✅ Termini nel JSON: {len(json_termini)}")
    else:
        print("   ⚠️  File JSON non trovato (sarà creato)")
    
    # Confronta
    aggiungere = [t for t in tex_termini if t not in json_termini]
    rimuovere = [t for t in json_termini if t not in tex_termini]
    modificare = []
    
    for t in tex_termini:
        if t in json_termini:
            if tex_termini[t].lower() != json_termini[t].lower():
                modificare.append(t)
    
    # Statistiche
    print("\n" + "="*50)
    print("📊 STATISTICHE")
    print("="*50)
    print(f"LaTeX: {len(tex_termini)} termini")
    print(f"JSON:  {len(json_termini)} termini")
    print(f"\n➕ Da aggiungere: {len(aggiungere)}")
    print(f"➖ Da rimuovere:  {len(rimuovere)}")
    print(f"✏️  Da modificare: {len(modificare)}")
    
    # Mostra dettagli
    if aggiungere:
        print(f"\n📋 TERMINI DA AGGIUNGERE:")
        for i, t in enumerate(aggiungere, 1):
            print(f"  {i}. {t}")
    
    if rimuovere:
        print(f"\n📋 TERMINI DA RIMUOVERE:")
        for i, t in enumerate(rimuovere, 1):
            print(f"  {i}. {t}")
    
    if modificare:
        print(f"\n📋 TERMINI DA MODIFICARE:")
        for i, t in enumerate(modificare, 1):
            print(f"  {i}. {t}")
            print(f"     Vecchio: {json_termini[t][:60]}..." if len(json_termini[t]) > 60 else f"     Vecchio: {json_termini[t]}")
            print(f"     Nuovo:   {tex_termini[t][:60]}..." if len(tex_termini[t]) > 60 else f"     Nuovo:   {tex_termini[t]}")
    
    if not (aggiungere or rimuovere or modificare):
        print("\n🎉 File già sincronizzati!")
        return 0
    
    # Chiedi conferma
    print("\n" + "="*50)
    risp = input("Procedere con la sincronizzazione? (s/n): ").strip().lower()
    if risp not in ['s', 'si', 'y', 'yes']:
        print("⏹️  Annullato")
        return 0
    
    # Backup
    if JSON.exists():
        import shutil
        backup = JSON.with_suffix('.json.bak')
        shutil.copy2(JSON, backup)
        print(f"\n📦 Backup: {backup}")
    
    # Crea nuovo JSON
    nuovi_termini = []
    for nome in sorted(tex_termini.keys()):
        # Se esiste in JSON e la definizione tex è vuota, mantieni la vecchia
        if nome in json_termini and (not tex_termini[nome] or tex_termini[nome].isspace()):
            defn = json_termini[nome]
        else:
            defn = tex_termini[nome] if tex_termini[nome] else f"[Definizione mancante per {nome}]"
        
        nuovi_termini.append({'term': nome, 'definition': defn})
    
    # Salva
    with open(JSON, 'w', encoding='utf-8') as f:
        json.dump({'terms': nuovi_termini}, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ JSON aggiornato: {len(nuovi_termini)} termini")
    print("="*50)
    return 0

if __name__ == "__main__":
    sys.exit(main())

    # prova prova