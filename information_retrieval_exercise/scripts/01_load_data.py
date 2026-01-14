"""
Skript zum Laden und Vorbereiten des Tagesschau-Datensatzes
"""
import pandas as pd
from datasets import load_dataset
from pathlib import Path
import json

def load_tagesschau_dataset(year=2023):
    """
    Lädt den awesome-tagesschau Datensatz von HuggingFace
    
    Args:
        year: Jahr des Datensatzes (Standard: 2023)
    
    Returns:
        Dataset-Objekt von HuggingFace
    """
    print(f"Lade Tagesschau-Datensatz für Jahr {year}...")
    # Lade direkt die JSONL-Datei für das spezifische Jahr
    try:
        # Versuche direkt die JSONL-Datei zu laden
        from huggingface_hub import hf_hub_download
        import json
        
        jsonl_path = hf_hub_download(
            repo_id="stefan-it/awesome-tagesschau",
            filename=f"{year}.jsonl",
            repo_type="dataset"
        )
        
        print(f"JSONL-Datei geladen: {jsonl_path}")
        
        # Lade die Daten manuell
        articles = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    articles.append(json.loads(line))
        
        print(f"Geladene Artikel: {len(articles)}")
        return articles
        
    except Exception as e:
        print(f"Fehler beim direkten Laden: {e}")
        print("Versuche alternativen Ansatz...")
        # Fallback: Versuche mit datasets zu laden, aber mit streaming
        try:
            from datasets import load_dataset
            dataset = load_dataset("stefan-it/awesome-tagesschau", streaming=True)
            # Konvertiere zu Liste (nur für kleine Stichproben)
            articles = []
            for item in dataset['train']:
                if 'date' in item and str(year) in str(item.get('date', '')):
                    articles.append(item)
                if len(articles) >= 1000:  # Limit für Demo
                    break
            return articles
        except Exception as e2:
            print(f"Alternativer Ansatz fehlgeschlagen: {e2}")
            raise

def explore_dataset(articles):
    """
    Erkundet die Struktur des Datensatzes
    
    Args:
        articles: Liste von Artikel-Dictionaries
    """
    print("\n=== Dataset-Struktur ===")
    print(f"Anzahl Artikel: {len(articles)}")
    
    if len(articles) > 0:
        print(f"\n  Beispiel-Eintrag:")
        example = articles[0]
        for key, value in example.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"    {key}: {value[:100]}...")
            elif isinstance(value, (dict, list)):
                print(f"    {key}: {type(value).__name__} ({len(value) if hasattr(value, '__len__') else 'N/A'})")
            else:
                print(f"    {key}: {value}")

def prepare_articles(articles):
    """
    Bereitet die Artikel für die weitere Verarbeitung vor
    
    Args:
        articles: Liste von Artikel-Dictionaries
    
    Returns:
        DataFrame mit vorbereiteten Artikeln
    """
    print(f"\n=== Vorbereitung der Artikel ===")
    
    # Konvertiere zu DataFrame
    df = pd.DataFrame(articles)
    
    # Extrahiere Text aus content-Feld (enthält verschachtelte Struktur)
    import re
    
    print("Extrahiere Text aus Artikeln...")
    texts = []
    
    for idx, row in df.iterrows():
        text_parts = []
        
        # Kombiniere verschiedene Text-Quellen
        if pd.notna(row.get('topline')):
            text_parts.append(str(row['topline']))
        if pd.notna(row.get('title')):
            text_parts.append(str(row['title']))
        if pd.notna(row.get('firstSentence')):
            text_parts.append(str(row['firstSentence']))
        
        # Extrahiere aus content-Feld
        content_val = row.get('content')
        if content_val is not None:
            try:
                # Handle verschiedene Formate
                if isinstance(content_val, str):
                    try:
                        content = json.loads(content_val)
                    except:
                        content = None
                elif isinstance(content_val, list):
                    content = content_val
                else:
                    content = None
                
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and 'value' in item:
                            value = item['value']
                            if isinstance(value, str):
                                # Entferne HTML-Tags
                                value = re.sub(r'<[^>]+>', '', value)
                                text_parts.append(value)
            except Exception:
                pass
        
        result = ' '.join(text_parts)
        texts.append(result if result.strip() else str(row.get('title', '')))
    
    df['text'] = texts
    
    # Bereinige Text
    df['text'] = df['text'].fillna('').astype(str)
    df['text'] = df['text'].str.replace(r'\s+', ' ', regex=True)  # Normalisiere Whitespace
    
    print(f"Text-Extraktion abgeschlossen. Durchschnittliche Text-Länge: {df['text'].str.len().mean():.0f} Zeichen")
    
    print(f"Anzahl Artikel: {len(df)}")
    print(f"Spalten: {df.columns.tolist()}")
    
    # Zeige erste Zeilen
    print("\nErste Zeilen:")
    print(df.head())
    
    return df

def save_prepared_data(df, output_path):
    """
    Speichert vorbereitete Daten
    
    Args:
        df: DataFrame mit Artikeln
        output_path: Pfad zum Speichern
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Speichere als CSV
    csv_path = output_path.with_suffix('.csv')
    df.to_csv(csv_path, index=False)
    print(f"\nDaten gespeichert: {csv_path}")
    
    # Speichere Metadaten als JSON
    json_path = output_path.with_suffix('.json')
    metadata = {
        'num_articles': len(df),
        'columns': df.columns.tolist(),
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"Metadaten gespeichert: {json_path}")

if __name__ == "__main__":
    # Lade Datensatz
    articles = load_tagesschau_dataset(year=2023)
    
    # Erkunde Struktur
    explore_dataset(articles)
    
    # Bereite Artikel vor
    df = prepare_articles(articles)
    
    # Speichere vorbereitete Daten
    data_dir = Path(__file__).parent.parent / "data"
    save_prepared_data(df, data_dir / "tagesschau_2023_prepared")

