const fs = require('fs');

// Helper to parse date to ms timestamp
function parseDateToTimestamp(dateStr) {
  if (!dateStr) return null;
  const cleaned = dateStr.toString().trim();
  
  // DD-MM-YYYY format (e.g. 20-06-2026)
  const ddMmYyyyMatch = cleaned.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/);
  if (ddMmYyyyMatch) {
    const day = parseInt(ddMmYyyyMatch[1], 10);
    const month = parseInt(ddMmYyyyMatch[2], 10);
    const year = parseInt(ddMmYyyyMatch[3], 10);
    return Date.UTC(year, month - 1, day);
  }

  // YYYY-MM-DD format (e.g. 2026-06-18)
  const yyyyMmDdMatch = cleaned.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/);
  if (yyyyMmDdMatch) {
    const year = parseInt(yyyyMmDdMatch[1], 10);
    const month = parseInt(yyyyMmDdMatch[2], 10);
    const day = parseInt(yyyyMmDdMatch[3], 10);
    return Date.UTC(year, month - 1, day);
  }

  // Fallback to standard parsing
  const parsed = Date.parse(cleaned);
  return isNaN(parsed) ? null : parsed;
}

// Helper to estimate reading time
function estimateReadingTime(body, wpm = 200) {
  let text = body.replace(/```[\s\S]*?```/g, '');
  text = text.replace(/`[^`]+`/g, '');
  text = text.replace(/<[^>]+>/g, '');
  text = text.replace(/[#*_\-~[\]()]/g, ' ');
  
  const words = text.trim().split(/\s+/).filter(w => w.length > 0).length;
  return Math.max(1, Math.ceil(words / wpm));
}

// Helper to clean quotes from string values
function cleanQuotes(val) {
  if (typeof val !== 'string') return val;
  let clean = val.trim();
  if (clean.startsWith('"')) clean = clean.substring(1);
  if (clean.endsWith('"')) clean = clean.substring(0, clean.length - 1);
  if (clean.startsWith("'")) clean = clean.substring(1);
  if (clean.endsWith("'")) clean = clean.substring(0, clean.length - 1);
  return clean.trim();
}

// Simple but robust YAML frontmatter parser
function parseMarkdownFile(filePath) {
  const fileContent = fs.readFileSync(filePath, 'utf8');
  const match = fileContent.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  
  if (!match) {
    return { metadata: {}, body: fileContent };
  }

  const yamlStr = match[1];
  const body = match[2];
  const metadata = {};
  
  const lines = yamlStr.split(/\r?\n/);
  let currentKey = null;
  let currentObject = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim() || line.trim().startsWith('#')) continue;

    const trimmedLine = line.trim();

    if (trimmedLine.startsWith('-')) {
      const itemContent = trimmedLine.replace(/^-\s*/, '').trim();
      const colonIndex = itemContent.indexOf(':');

      if (colonIndex !== -1) {
        const key = itemContent.substring(0, colonIndex).trim();
        const val = cleanQuotes(itemContent.substring(colonIndex + 1).trim());
        
        currentObject = {};
        currentObject[key] = val;

        if (currentKey) {
          if (!Array.isArray(metadata[currentKey])) {
            metadata[currentKey] = [];
          }
          metadata[currentKey].push(currentObject);
        }
      } else {
        currentObject = null;
        const val = cleanQuotes(itemContent);
        if (currentKey) {
          if (!Array.isArray(metadata[currentKey])) {
            metadata[currentKey] = [];
          }
          metadata[currentKey].push(val);
        }
      }
      continue;
    }

    const colonIndex = line.indexOf(':');
    if (colonIndex !== -1) {
      const key = line.substring(0, colonIndex).trim();
      const valStr = line.substring(colonIndex + 1).trim();
      const hasLeadingSpaces = line.startsWith(' ') || line.startsWith('\t');

      if (hasLeadingSpaces && currentObject && currentKey) {
        const cleanedVal = cleanQuotes(valStr);
        currentObject[key] = cleanedVal;
      } else {
        currentObject = null;
        currentKey = key;

        if (valStr === '' || valStr === '>' || valStr === '|') {
          metadata[currentKey] = [];
        } else {
          const cleanedVal = cleanQuotes(valStr);
          if (key === 'category' || key === 'categories') {
            if (cleanedVal.includes(',')) {
              metadata[key] = cleanedVal.split(',').map(s => s.trim());
            } else {
              metadata[key] = cleanedVal;
            }
          } else {
            metadata[key] = cleanedVal;
          }
        }
      }
    }
  }

  return { metadata, body };
}

// Helper to remove empty keys
function removeEmptyKeys(obj) {
  const clean = {};
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const val = obj[key];
      if (val === null || val === undefined) continue;
      if (typeof val === 'string' && val.trim().length === 0) continue;
      if (Array.isArray(val) && val.length === 0) continue;
      clean[key] = val;
    }
  }
  return clean;
}

function isDraft(metadata) {
  return metadata.draft === true || metadata.draft === 'true' || metadata.status === 'draft';
}

function getFilesRecursively(dir) {
  let results = [];
  if (!fs.existsSync(dir)) return results;
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    const fullPath = require('path').join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat && stat.isDirectory()) {
      results = results.concat(getFilesRecursively(fullPath));
    } else {
      if (fullPath.endsWith('.md')) results.push(fullPath);
    }
  });
  return results;
}

module.exports = {
  parseDateToTimestamp,
  estimateReadingTime,
  cleanQuotes,
  parseMarkdownFile,
  removeEmptyKeys,
  isDraft,
  getFilesRecursively
};
