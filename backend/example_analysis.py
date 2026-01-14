#!/usr/bin/env python3
# example_analysis.py - Beispiel-Analysen der gescrapten Daten
"""
Beispiele für Datenanalyse nach dem Scraping.
Demonstriert verschiedene Use-Cases für das Umweltfrieden-Projekt.
"""

import pandas as pd
from pathlib import Path
from collections import Counter
import re


def load_all_data(data_dir: str = './data') -> pd.DataFrame:
    """Lädt alle Parquet-Dateien und merged sie"""
    parquet_dir = Path(data_dir) / 'parquet'
    
    # Suche merged_all.parquet
    merged_file = parquet_dir / 'merged_all.parquet'
    if merged_file.exists():
        print(f"📂 Lade Merged File: {merged_file}")
        return pd.read_parquet(merged_file)
    
    # Falls nicht vorhanden: Alle einzelnen Files laden
    parquet_files = list(parquet_dir.glob('*.parquet'))
    if not parquet_files:
        print("❌ Keine Parquet-Dateien gefunden!")
        return pd.DataFrame()
    
    print(f"📂 Lade {len(parquet_files)} Parquet-Dateien...")
    dfs = [pd.read_parquet(f) for f in parquet_files]
    df = pd.concat(dfs, ignore_index=True)
    
    # Duplikate entfernen
    if 'url' in df.columns:
        df = df.drop_duplicates(subset=['url'], keep='last')
    
    return df


def basic_stats(df: pd.DataFrame):
    """Zeigt Basis-Statistiken"""
    print("\n" + "="*60)
    print("📊 BASIS-STATISTIKEN")
    print("="*60)
    
    print(f"\nGesamt Records: {len(df)}")
    print(f"Zeitraum: {df['publish_date'].min()} bis {df['publish_date'].max()}")
    
    print("\n📌 Records pro Quelle:")
    print(df['source_name'].value_counts())
    
    print("\n🌍 Top 10 Regionen:")
    if 'region' in df.columns:
        print(df['region'].value_counts().head(10))
    
    print("\n📅 Records pro Monat:")
    if 'publish_date' in df.columns:
        df['month'] = pd.to_datetime(df['publish_date'], errors='coerce').dt.to_period('M')
        print(df['month'].value_counts().sort_index().tail(12))


def topic_analysis(df: pd.DataFrame):
    """Analysiert Topics/Themen"""
    print("\n" + "="*60)
    print("🏷️  TOPIC-ANALYSE")
    print("="*60)
    
    # Alle Topics sammeln
    all_topics = []
    for topics in df['topics']:
        if isinstance(topics, list):
            all_topics.extend(topics)
    
    topic_counts = Counter(all_topics)
    
    print("\n📈 Top 20 Topics:")
    for topic, count in topic_counts.most_common(20):
        print(f"  {topic:30} {count:4} ×")


def climate_keywords_analysis(df: pd.DataFrame):
    """Analysiert klimabezogene Keywords"""
    print("\n" + "="*60)
    print("🌡️  KLIMA-KEYWORDS")
    print("="*60)
    
    climate_keywords = [
        'drought', 'flood', 'climate change', 'temperature',
        'rainfall', 'sea level', 'wildfire', 'hurricane',
        'cyclone', 'heatwave', 'water scarcity', 'deforestation'
    ]
    
    # Zähle Keywords im Volltext
    keyword_counts = {kw: 0 for kw in climate_keywords}
    
    for text in df['full_text'].dropna():
        text_lower = text.lower()
        for kw in climate_keywords:
            keyword_counts[kw] += text_lower.count(kw)
    
    # Sortiere nach Häufigkeit
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    
    print("\n📊 Häufigste Klima-Keywords:")
    for kw, count in sorted_keywords:
        if count > 0:
            print(f"  {kw:20} {count:5} ×")


def conflict_indicators(df: pd.DataFrame):
    """Sucht nach Konflikt-Indikatoren"""
    print("\n" + "="*60)
    print("⚠️  KONFLIKT-INDIKATOREN")
    print("="*60)
    
    conflict_keywords = [
        'conflict', 'war', 'violence', 'displacement',
        'refugees', 'migration', 'unrest', 'crisis',
        'tension', 'dispute', 'protest', 'humanitarian'
    ]
    
    # Artikel mit Konflikt-Bezug
    conflict_articles = []
    
    for idx, row in df.iterrows():
        text = str(row.get('full_text', '')) + str(row.get('title', ''))
        text_lower = text.lower()
        
        matches = [kw for kw in conflict_keywords if kw in text_lower]
        
        if matches:
            conflict_articles.append({
                'url': row['url'],
                'title': row['title'],
                'source': row['source_name'],
                'region': row.get('region'),
                'keywords': matches
            })
    
    print(f"\n⚠️  {len(conflict_articles)} Artikel mit Konflikt-Bezug gefunden")
    
    if conflict_articles:
        print("\n🔍 Beispiele:")
        for article in conflict_articles[:5]:
            print(f"\n  📰 {article['title']}")
            print(f"     Quelle: {article['source']} | Region: {article['region']}")
            print(f"     Keywords: {', '.join(article['keywords'])}")


def environmental_stress_regions(df: pd.DataFrame):
    """Identifiziert Regionen mit Umweltstress"""
    print("\n" + "="*60)
    print("🌍 REGIONEN MIT UMWELTSTRESS")
    print("="*60)
    
    env_keywords = ['drought', 'water scarcity', 'flood', 'deforestation']
    
    region_stress = {}
    
    for idx, row in df.iterrows():
        region = row.get('region')
        if not region or pd.isna(region):
            continue
        
        text = str(row.get('full_text', '')) + str(row.get('title', ''))
        text_lower = text.lower()
        
        stress_count = sum(1 for kw in env_keywords if kw in text_lower)
        
        if stress_count > 0:
            if region not in region_stress:
                region_stress[region] = 0
            region_stress[region] += stress_count
    
    # Sortiere nach Stress-Level
    sorted_regions = sorted(region_stress.items(), key=lambda x: x[1], reverse=True)
    
    print("\n📊 Top 10 Regionen mit Umweltstress:")
    for region, score in sorted_regions[:10]:
        print(f"  {region:30} Score: {score:3}")


def export_summary(df: pd.DataFrame, output_file: str = './data/analysis_summary.txt'):
    """Exportiert Zusammenfassung als Text"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("UMWELTFRIEDEN - DATEN-ZUSAMMENFASSUNG\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Gesamt Records: {len(df)}\n")
        f.write(f"Zeitraum: {df['publish_date'].min()} - {df['publish_date'].max()}\n\n")
        
        f.write("Records pro Quelle:\n")
        for source, count in df['source_name'].value_counts().items():
            f.write(f"  {source}: {count}\n")
        
        f.write("\n" + "="*60 + "\n")
    
    print(f"\n💾 Zusammenfassung exportiert: {output_file}")


def main():
    """Hauptfunktion"""
    print("\n🌍 UMWELTFRIEDEN - DATENANALYSE")
    print("="*60)
    
    # Daten laden
    df = load_all_data()
    
    if df.empty:
        print("❌ Keine Daten gefunden. Führe zuerst den Scraper aus:")
        print("   python cli.py")
        return
    
    # Analysen durchführen
    basic_stats(df)
    topic_analysis(df)
    climate_keywords_analysis(df)
    conflict_indicators(df)
    environmental_stress_regions(df)
    
    # Export
    export_summary(df)
    
    print("\n" + "="*60)
    print("✅ Analyse abgeschlossen!")
    print("="*60)


if __name__ == '__main__':
    main()

