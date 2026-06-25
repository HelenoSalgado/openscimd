const fs = require('fs');
const path = require('path');

// Configuration
const ARTICLES_DIR = path.join(__dirname, '..', 'articles');
const COVERS_DIR = path.join(__dirname, '..', 'covers');
const INDEX_FILE = path.join(__dirname, '..', 'index.json');
const GITHUB_USERNAME = 'HelenoSalgado';
const REPO_NAME = 'md-academics';
const DEFAULT_WPM = 200; // Words Per Minute for academic/scientific text

// Helper to parse date to ms timestamp
function parseDateToTimestamp(dateStr) {
  if (!dateStr) return null;
  const cleaned = dateStr.trim();
  
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
function estimateReadingTime(body) {
  // Strip code blocks
  let text = body.replace(/```[\s\S]*?```/g, '');
  // Strip inline code
  text = text.replace(/`[^`]+`/g, '');
  // Strip HTML tags
  text = text.replace(/<[^>]+>/g, '');
  // Strip markdown formatting characters to isolate words
  text = text.replace(/[#*_\-~[\]()]/g, ' ');
  
  const words = text.trim().split(/\s+/).filter(w => w.length > 0).length;
  return Math.max(1, Math.ceil(words / DEFAULT_WPM));
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

// Simple but robust YAML frontmatter parser supporting strings, lists, and lists of objects
function parseMarkdownFile(filePath) {
  const fileContent = fs.readFileSync(filePath, 'utf8');
  const match = fileContent.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  
  if (!match) {
    // If no frontmatter, return empty metadata and use the whole file as body
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

    // Detect list items (lines starting with "-")
    if (trimmedLine.startsWith('-')) {
      const itemContent = trimmedLine.replace(/^-\s*/, '').trim();
      const colonIndex = itemContent.indexOf(':');

      if (colonIndex !== -1) {
        // List of objects item (e.g. "- name: Djamila")
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
        // Simple list item (e.g. "- Djamila Abdullazade")
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

    // Detect key-value lines
    const colonIndex = line.indexOf(':');
    if (colonIndex !== -1) {
      const key = line.substring(0, colonIndex).trim();
      const valStr = line.substring(colonIndex + 1).trim();
      const hasLeadingSpaces = line.startsWith(' ') || line.startsWith('\t');

      // Check if this belongs to a list of objects (nested indented key)
      if (hasLeadingSpaces && currentObject && currentKey) {
        const cleanedVal = cleanQuotes(valStr);
        currentObject[key] = cleanedVal;
      } else {
        // Top-level key
        currentObject = null;
        currentKey = key;

        if (valStr === '' || valStr === '>' || valStr === '|') {
          metadata[currentKey] = [];
        } else {
          const cleanedVal = cleanQuotes(valStr);

          // Normalize categories/category
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

// Scan cover images to find matching extension
function findCoverExtension(baseName) {
  const originalsDir = path.join(COVERS_DIR, 'originals');
  if (!fs.existsSync(originalsDir)) {
    return 'webp'; // Default fallback
  }
  const extensions = ['.webp', '.png', '.jpg', '.jpeg', '.svg'];
  for (const ext of extensions) {
    if (fs.existsSync(path.join(originalsDir, `${baseName}${ext}`))) {
      return ext.substring(1); // Return extension without the dot (e.g. 'webp')
    }
  }
  return 'webp'; // Fallback
}

// Helper to remove empty keys (undefined, null, empty strings, or empty arrays)
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

function updateIndex() {
  console.log('🔄 Iniciando atualização do index.json...');

  if (!fs.existsSync(ARTICLES_DIR)) {
    console.error(`❌ Diretório de artigos não encontrado em: ${ARTICLES_DIR}`);
    process.exit(1);
  }

  // Read existing index.json to preserve IDs and properties
  let existingIndex = { repo_name: 'Artigos Acadêmicos Licenciados', last_updated: Date.now(), articles: [] };
  if (fs.existsSync(INDEX_FILE)) {
    try {
      existingIndex = JSON.parse(fs.readFileSync(INDEX_FILE, 'utf8'));
    } catch (e) {
      console.warn('⚠️ Erro ao ler index.json atual. Um novo será gerado do zero.');
    }
  }

  const existingArticlesMap = new Map();
  let maxIdNum = 0;

  if (existingIndex.articles && Array.isArray(existingIndex.articles)) {
    existingIndex.articles.forEach(article => {
      if (article.remote_url) {
        const filename = path.basename(article.remote_url);
        existingArticlesMap.set(filename, article);
      }
      if (article.id) {
        const idMatch = article.id.match(/^art_(\d+)$/);
        if (idMatch) {
          const num = parseInt(idMatch[1], 10);
          if (num > maxIdNum) maxIdNum = num;
        }
      }
    });
  }

  // Scan articles directory
  const files = fs.readdirSync(ARTICLES_DIR).filter(file => file.endsWith('.md'));
  const updatedArticles = [];

  for (const file of files) {
    const filePath = path.join(ARTICLES_DIR, file);
    console.log(`📄 Processando: ${file}`);

    try {
      const { metadata, body } = parseMarkdownFile(filePath);
      const baseName = path.basename(file, '.md');
      const existingArticle = existingArticlesMap.get(file);

      // 1. Assign/Preserve ID
      let id = existingArticle ? existingArticle.id : null;
      if (!id) {
        maxIdNum++;
        id = `art_${String(maxIdNum).padStart(3, '0')}`;
      }

      // 2. Title
      const title = metadata.title || (existingArticle && existingArticle.title) || baseName;

      // 3. Authors selection: if authors is present, omit author key
      let author = undefined;
      let authorsList = undefined;

      if (metadata.authors && Array.isArray(metadata.authors) && metadata.authors.length > 0) {
        authorsList = metadata.authors;
      } else if (metadata.author) {
        author = metadata.author;
      } else if (existingArticle) {
        if (existingArticle.authors && existingArticle.authors.length > 0) {
          authorsList = existingArticle.authors;
        } else if (existingArticle.author) {
          author = existingArticle.author;
        }
      }

      // 4. Summary
      let summary = metadata.summary || metadata.sumary || '';
      if (!summary && existingArticle) {
        summary = existingArticle.summary;
      }
      if (!summary) {
        // Fallback: extract the first paragraph (up to 250 chars)
        const cleanBody = body.trim().replace(/^#+.*$/gm, '').trim(); // Remove headers
        const firstParagraph = cleanBody.split(/\r?\n\r?\n/)[0] || '';
        summary = firstParagraph.substring(0, 250).trim();
        if (firstParagraph.length > 250) summary += '...';
      }

      // 5. Remote, Cover and PDF URLs
      const remoteUrl = `https://raw.githubusercontent.com/${GITHUB_USERNAME}/${REPO_NAME}/main/articles/${file}`;
      
      const coverUrl = `https://raw.githubusercontent.com/${GITHUB_USERNAME}/${REPO_NAME}/main/covers/mobile/${baseName}.webp`;
      if (!fs.existsSync(path.join(COVERS_DIR, 'mobile', `${baseName}.webp`))) {
        console.warn(`  ⚠️ Imagem de capa mobile não encontrada para "${file}" no diretório covers/mobile/. URL de referência gerada: ${coverUrl}`);
      }

      // Check for corresponding PDF file in pdfs folder
      let pdfUrl = undefined;
      const pdfFilePath = path.join(__dirname, '..', 'pdfs', `${baseName}.pdf`);
      if (fs.existsSync(pdfFilePath)) {
        pdfUrl = `https://raw.githubusercontent.com/${GITHUB_USERNAME}/${REPO_NAME}/main/pdfs/${baseName}.pdf`;
      }

      // 6. Categories
      let categories = [];
      if (metadata.categories) {
        categories = Array.isArray(metadata.categories) ? metadata.categories : [metadata.categories];
      } else if (metadata.category) {
        categories = Array.isArray(metadata.category) ? metadata.category : [metadata.category];
      } else if (existingArticle && existingArticle.categories) {
        categories = existingArticle.categories;
      }

      // 7. Date / published_at
      let publishedAt = existingArticle ? existingArticle.published_at : null;
      if (metadata.date) {
        const parsedTs = parseDateToTimestamp(metadata.date);
        if (parsedTs) publishedAt = parsedTs;
      }
      if (!publishedAt) {
        // Default to file creation/modification time if no date is found
        const stats = fs.statSync(filePath);
        publishedAt = stats.mtimeMs || Date.now();
      }

      // 8. Reading Time Estimation
      const estimatedReadingTime = estimateReadingTime(body);

      // 9. Build final article entry, including standard and academic-scientific metadata
      const rawArticleEntry = {
        id,
        title,
        author,
        authors: authorsList,
        summary,
        remote_url: remoteUrl,
        cover_url: coverUrl,
        pdf_url: pdfUrl,
        categories,
        published_at: publishedAt,
        estimated_reading_time_min: estimatedReadingTime,
        doi: metadata.doi || metadata.DOI,
        udc: metadata.udc || metadata.UDC,
        bbk: metadata.bbk || metadata.BBK,
        hos: metadata.hos || metadata.HoS,
        license: metadata.license || metadata.licence,
        journal: metadata.journal,
        volume: metadata.volume,
        issue: metadata.issue,
        pages: metadata.pages,
        language: metadata.language
      };

      const articleEntry = removeEmptyKeys(rawArticleEntry);
      updatedArticles.push(articleEntry);
    } catch (err) {
      console.error(`❌ Erro ao processar ${file}:`, err.message);
    }
  }

  // Update index object
  existingIndex.articles = updatedArticles;
  existingIndex.last_updated = Date.now();

  // Write back to index.json
  fs.writeFileSync(INDEX_FILE, JSON.stringify(existingIndex, null, 2) + '\n', 'utf8');
  console.log(`✅ index.json atualizado com sucesso! (${updatedArticles.length} artigos indexados)`);
}

// Run if direct execution
if (require.main === module) {
  updateIndex();
}

module.exports = {
  updateIndex,
  parseMarkdownFile,
  parseDateToTimestamp,
  estimateReadingTime
};
