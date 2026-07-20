const fs = require('fs');
const path = require('path');
const { parseMarkdownFile, parseDateToTimestamp, estimateReadingTime, removeEmptyKeys, isDraft, getFilesRecursively } = require('./utils');

const BOOKS_DIR = path.join(__dirname, '..', 'books');
const COVERS_DIR = path.join(__dirname, '..', 'covers');
const INDEX_FILE = path.join(__dirname, '..', 'index-books.json');
const GITHUB_USERNAME = 'HelenoSalgado';
const REPO_NAME = 'openscimd';
const DEFAULT_WPM = 200;

function updateBooksIndex() {
  console.log('🔄 Iniciando atualização do index-books.json...');

  if (!fs.existsSync(BOOKS_DIR)) {
    console.warn(`⚠️ Diretório de livros não encontrado em: ${BOOKS_DIR}`);
    return;
  }

  let existingIndex = { repo_name: 'OpenSciMD', type: 'books', last_updated: Date.now(), books: [] };
  if (fs.existsSync(INDEX_FILE)) {
    try {
      existingIndex = JSON.parse(fs.readFileSync(INDEX_FILE, 'utf8'));
    } catch (e) {
      console.warn('⚠️ Erro ao ler index-books.json atual. Um novo será gerado do zero.');
    }
  }

  const existingBooksMap = new Map();
  let maxIdNum = 0;

  if (existingIndex.books && Array.isArray(existingIndex.books)) {
    existingIndex.books.forEach(book => {
      if (book.remote_url) {
        // Since books are in subfolders, we use the relative path to uniquely identify
        const relPath = new URL(book.remote_url).pathname.split('/main/books/')[1];
        if (relPath) existingBooksMap.set(relPath, book);
      }
      if (book.id) {
        const idMatch = book.id.match(/^book_(\d+)$/);
        if (idMatch) {
          const num = parseInt(idMatch[1], 10);
          if (num > maxIdNum) maxIdNum = num;
        }
      }
    });
  }

  const files = getFilesRecursively(BOOKS_DIR);
  const updatedBooks = [];

  for (const filePath of files) {
    const relPath = path.relative(BOOKS_DIR, filePath).replace(/\\/g, '/'); // Normalize for Windows/Linux
    const file = path.basename(filePath);
    
    try {
      const { metadata, body } = parseMarkdownFile(filePath);
      const baseName = path.basename(file, '.md');

      if (isDraft(metadata)) {
        console.log(`⚠️ Ignorando rascunho: ${relPath}`);
        continue;
      }

      console.log(`📚 Processando livro: ${relPath}`);

      const existingBook = existingBooksMap.get(relPath);

      let id = existingBook ? existingBook.id : null;
      if (!id) {
        maxIdNum++;
        id = `book_${String(maxIdNum).padStart(3, '0')}`;
      }

      const title = metadata.title || (existingBook && existingBook.title) || baseName;

      let author = undefined;
      let authorsList = undefined;
      if (metadata.authors && Array.isArray(metadata.authors) && metadata.authors.length > 0) {
        authorsList = metadata.authors;
      } else if (metadata.author) {
        author = metadata.author;
      } else if (existingBook) {
        if (existingBook.authors && existingBook.authors.length > 0) {
          authorsList = existingBook.authors;
        } else if (existingBook.author) {
          author = existingBook.author;
        }
      }

      let summary = metadata.summary || metadata.sumary || '';
      if (!summary && existingBook) summary = existingBook.summary;
      if (!summary) {
        const cleanBody = body.trim().replace(/^#+.*$/gm, '').trim();
        const firstParagraph = cleanBody.split(/\r?\n\r?\n/)[0] || '';
        summary = firstParagraph.substring(0, 250).trim();
        if (firstParagraph.length > 250) summary += '...';
      }

      // Preserve subfolder structure in remote URL
      const remoteUrl = `https://raw.githubusercontent.com/${GITHUB_USERNAME}/${REPO_NAME}/main/books/${relPath}`;
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
      } else if (existingBook && existingBook.categories) {
        categories = existingBook.categories;
      }

      let publishedAt = existingBook ? existingBook.published_at : null;
      if (metadata.date) {
        const parsedTs = parseDateToTimestamp(metadata.date);
        if (parsedTs) publishedAt = parsedTs;
      }
      if (!publishedAt) {
        const stats = fs.statSync(filePath);
        publishedAt = stats.mtimeMs || Date.now();
      }

      const estimatedReadingTime = estimateReadingTime(body, DEFAULT_WPM);

      const rawBookEntry = {
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
        license: metadata.license || metadata.licence,
        language: metadata.language,
        originalLanguage: metadata.originalLanguage,
        translator: metadata.translator,
        edition: metadata.edition,
        isbn: metadata.isbn
      };

      updatedBooks.push(removeEmptyKeys(rawBookEntry));
    } catch (err) {
      console.error(`❌ Erro ao processar livro ${relPath}:`, err.message);
    }
  }

  existingIndex.books = updatedBooks;
  existingIndex.last_updated = Date.now();

  fs.writeFileSync(INDEX_FILE, JSON.stringify(existingIndex, null, 2) + '\n', 'utf8');
  console.log(`✅ index-books.json atualizado com sucesso! (${updatedBooks.length} livros indexados)`);
}

if (require.main === module) {
  updateBooksIndex();
}

module.exports = { updateBooksIndex };
