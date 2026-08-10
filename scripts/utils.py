import os
import re
import yaml
from datetime import datetime, timezone
from pathlib import Path

def parse_date_to_timestamp(date_str):
    if not date_str:
        return None
    date_str = str(date_str).strip()
    
    # DD-MM-YYYY
    m = re.match(r'^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$', date_str)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if day > 12 and month <= 12:
            pass
        elif month > 12 and day <= 12:
            day, month = month, day
        try:
            return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp() * 1000)
        except ValueError:
            return None
            
    # YYYY-MM-DD
    m = re.match(r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$', date_str)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp() * 1000)
        except ValueError:
            return None
            
    try:
        dt = datetime.fromisoformat(date_str)
        return int(dt.timestamp() * 1000)
    except ValueError:
        return None

def estimate_reading_time(body, wpm=200):
    text = re.sub(r'```[\s\S]*?```', '', body)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[#*_\-~\[\]()]', ' ', text)
    words = len([w for w in text.split() if w.strip()])
    return max(1, (words + wpm - 1) // wpm)

def parse_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.match(r'^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$', content)
    if not match:
        return {"metadata": {}, "body": content}
    
    yaml_str = match.group(1)
    body = match.group(2)
    
    try:
        metadata = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError:
        metadata = {}
        
    return {"metadata": metadata, "body": body}

def is_draft(metadata):
    draft = metadata.get('draft')
    status = metadata.get('status')
    return draft is True or str(draft).lower() == 'true' or status == 'draft'

def remove_empty_keys(d):
    clean = {}
    for k, v in d.items():
        if v is None: continue
        if isinstance(v, str) and not v.strip(): continue
        if isinstance(v, list) and not v: continue
        clean[k] = v
    return clean

def get_files_recursively(directory, extension='.md'):
    results = []
    path = Path(directory)
    if not path.exists():
        return results
    for p in path.rglob(f'*{extension}'):
        if p.is_file():
            results.append(str(p))
    return results
