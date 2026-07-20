const fs = require('fs');
const path = require('path');
const { parseMarkdownFile, parseDateToTimestamp, estimateReadingTime, removeEmptyKeys, isDraft } = require('./utils');

const ARTICLES_DIR = path.join(__dirname, '..', 'articles');
const COVERS_DIR = path.join(__dirname, '..', 'covers');
const INDEX_FILE = path.join(__dirname, '..', 'index-articles.json');
const GITHUB_USERNAME = 'HelenoSalgado';
const REPO_NAME = 'openscimd';
const DEFAULT_WPM = 200;

function updateArticlesIndex() {
  console.log('🔄 Iniciando atualização do index-articles.json...');

  if (!fs.existsSync(ARTICLES_DIR)) {
    console.warn(`⚠️ Diretório de artigos não encontrado em: ${ARTICLES_DIR}`);
    return;
  }

  let existingIndex = { repo_name: 'OpenSciMD', type: 'articles', last_updated: Date.now(), articles: [] };
  if (fs.existsSync(INDEX_FILE)) {
    try {
      existingIndex = JSON.parse(fs.readFileSync(INDEX_FILE, 'utf8'));
    } catch (e) {
      console.warn('⚠️ Erro ao ler index-articles.json atual. Um novo será gerado do zero.');
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

  const files = fs.readdirSync(ARTICLES_DIR).filter(file => file.endsWith('.md'));
  const updatedArticles = [];

  for (const file of files) {
    const filePath = path.join(ARTICLES_DIR, file);
    
    try {
      const { metadata, body } = parseMarkdownFile(filePath);
      const baseName = path.basename(file, '.md');

      if (isDraft(metadata)) {
        console.log(`⚠️ Ignorando rascunho: ${file}`);
        continue;
      }

      console.log(`📄 Processando artigo: ${file}`);

      const existingArticle = existingArticlesMap.get(file);

      let id = existingArticle ? existingArticle.id : null;
      if (!id) {
        maxIdNum++;
        id = `art_${String(maxIdNum).padStart(3, '0')}`;
      }

      const title = metadata.title || (existingArticle && existingArticle.title) || baseName;

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

      let summary = metadata.summary || metadata.sumary || '';
      if (!summary && existingArticle) summary = existingArticle.summary;
      if (!summary) {
        const cleanBody = body.trim().replace(/^#+.*$/gm, '').trim();
        const firstParagraph = cleanBody.split(/\r?\n\r?\n/)[0] || '';
        summary = firstParagraph.substring(0, 250).trim();
        if (firstParagraph.length > 250) summary += '...';
      }

      const remoteUrl = `https://raw.githubusercontent.com/${GITHUB_USERNAME}/${REPO_NAME}/main/articles/${file}`;
      const coverUrl = `https://raw.githubusercontent.com/${GITHUB_USERNAME}/${REPO_NAME}/main/covers/mobile/${baseName}.webp`;
      
      let pdfUrl = undefined;
      const pdfFilePath = path.join(__dirname, '..', 'pdfs', `${baseName}.pdf`);
      if (fs.existsSync(pdfFilePath)) {
        pdfUrl = `https://raw.githubusercontent.com/${GITHUB_USERNAME}/${REPO_NAME}/main/pdfs/${baseName}.pdf`;
      }

      let categories = [];
      if (metadata.categories) {
        categories = Array.isArray(metadata.categories) ? metadata.categories : [metadata.categories];
      } else if (metadata.category) {
        categories = Array.isArray(metadata.category) ? metadata.category : [metadata.category];
      } else if (existingArticle && existingArticle.categories) {
        categories = existingArticle.categories;
      }

      let publishedAt = existingArticle ? existingArticle.published_at : null;
      if (metadata.date) {
        const parsedTs = parseDateToTimestamp(metadata.date);
        if (parsedTs) publishedAt = parsedTs;
      }
      if (!publishedAt) {
        const stats = fs.statSync(filePath);
        publishedAt = stats.mtimeMs || Date.now();
      }

      const estimatedReadingTime = estimateReadingTime(body, DEFAULT_WPM);

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

      updatedArticles.push(removeEmptyKeys(rawArticleEntry));
    } catch (err) {
      console.error(`❌ Erro ao processar artigo ${file}:`, err.message);
    }
  }

  existingIndex.articles = updatedArticles;
  existingIndex.last_updated = Date.now();

  fs.writeFileSync(INDEX_FILE, JSON.stringify(existingIndex, null, 2) + '\n', 'utf8');
  console.log(`✅ index-articles.json atualizado com sucesso! (${updatedArticles.length} artigos indexados)`);
}

if (require.main === module) {
  updateArticlesIndex();
}

module.exports = { updateArticlesIndex };
