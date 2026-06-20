const fs = require('fs');
const path = require('path');
const { parseMarkdownFile, parseDateToTimestamp } = require('./update-index');

const ARTICLES_DIR = path.join(__dirname, '..', 'articles');
const COVERS_DIR = path.join(__dirname, '..', 'covers');
const PDFS_DIR = path.join(__dirname, '..', 'pdfs');

function validateArticles() {
  console.log('🧪 Iniciando validação de formato e metadados dos artigos...\n');

  if (!fs.existsSync(ARTICLES_DIR)) {
    console.error(`❌ Diretório de artigos não encontrado em: ${ARTICLES_DIR}`);
    process.exit(1);
  }

  const files = fs.readdirSync(ARTICLES_DIR).filter(file => file.endsWith('.md'));
  let totalErrors = 0;
  let totalWarnings = 0;
  let invalidFilesCount = 0;

  files.forEach(file => {
    const filePath = path.join(ARTICLES_DIR, file);
    const baseName = path.basename(file, '.md');
    const errors = [];
    const warnings = [];

    try {
      const fileContent = fs.readFileSync(filePath, 'utf8');
      
      // Check frontmatter delimiters
      if (!fileContent.startsWith('---')) {
        errors.push('O arquivo não inicia com delimitadores de metadados ("---").');
      }

      const match = fileContent.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
      if (!match) {
        errors.push('Estrutura de metadados inválida ou delimitador de fechamento ("---") ausente.');
      } else {
        const { metadata } = parseMarkdownFile(filePath);

        // 1. Validate Required Fields (ERRORS if missing)
        // Title
        if (!metadata.title || metadata.title.trim().length === 0) {
          errors.push('Campo obrigatório "title" está ausente ou vazio.');
        }

        // Author / Authors
        const hasAuthor = !!metadata.author && metadata.author.trim().length > 0;
        const hasAuthors = !!metadata.authors && Array.isArray(metadata.authors) && metadata.authors.length > 0;
        if (!hasAuthor && !hasAuthors) {
          errors.push('Campo de autoria obrigatório ("author" ou "authors") ausente ou vazio.');
        }

        // Summary / Sumary
        const summary = metadata.summary || metadata.sumary;
        if (!summary || summary.trim().length === 0) {
          errors.push('Resumo ("summary" ou "sumary") ausente ou vazio.');
        } else if (metadata.sumary) {
          warnings.push('Encontrado erro de digitação no campo "sumary". Recomenda-se renomear para "summary".');
        }

        // Date
        if (!metadata.date) {
          errors.push('Campo obrigatório "date" ausente.');
        } else {
          const timestamp = parseDateToTimestamp(metadata.date);
          if (!timestamp) {
            errors.push(`Formato de data inválido: "${metadata.date}". Use YYYY-MM-DD ou DD-MM-YYYY.`);
          }
        }

        // License / Licence
        const license = metadata.license || metadata.licence;
        if (!license || license.trim().length === 0) {
          errors.push('Campo de licença obrigatório ("license" ou "licence") ausente ou vazio.');
        } else if (metadata.licence) {
          warnings.push('Chave de licença escrita como "licence". Recomenda-se padronizar para "license".');
        }

        // 2. Validate Recommended / Administrative Academic Fields (WARNINGS if missing)
        if (!metadata.doi && !metadata.DOI) {
          warnings.push('Campo recomendado "DOI" (Digital Object Identifier) está ausente.');
        }
        if (!metadata.udc && !metadata.UDC) {
          warnings.push('Campo recomendado "UDC" (Classificação Decimal Universal) está ausente.');
        }
        if (!metadata.bbk && !metadata.BBK) {
          warnings.push('Campo recomendado "BBK" (Classificação Bibliográfica) está ausente.');
        }
        if (!metadata.categories && !metadata.category) {
          warnings.push('Campo recomendado "categories" ou "category" está ausente.');
        }
        if (!metadata.journal) {
          warnings.push('Campo administrativo "journal" (Revista científica de origem) está ausente.');
        }

        // 3. Check Physical File Existences (Covers & PDFs)
        // Check Cover
        const coverExtensions = ['.webp', '.png', '.jpg', '.jpeg', '.svg'];
        let coverExists = false;
        for (const ext of coverExtensions) {
          if (fs.existsSync(path.join(COVERS_DIR, `${baseName}${ext}`))) {
            coverExists = true;
            break;
          }
        }
        if (!coverExists) {
          warnings.push(`Imagem de capa correspondente não localizada em covers/${baseName}.webp (ou outras extensões).`);
        }

        // Check PDF
        const pdfExists = fs.existsSync(path.join(PDFS_DIR, `${baseName}.pdf`));
        if (!pdfExists) {
          warnings.push(`Arquivo original em PDF não localizado em pdfs/${baseName}.pdf.`);
        }
      }
    } catch (err) {
      errors.push(`Falha crítica ao ler/processar arquivo: ${err.message}`);
    }

    // Print report for the file
    if (errors.length > 0 || warnings.length > 0) {
      console.log(`📄 Artigo: ${file}`);
      
      if (errors.length > 0) {
        invalidFilesCount++;
        totalErrors += errors.length;
        errors.forEach(err => console.log(`  ❌ [ERRO] ${err}`));
      }
      
      if (warnings.length > 0) {
        totalWarnings += warnings.length;
        warnings.forEach(warn => console.log(`  ⚠️ [ALERTA] ${warn}`));
      }
      console.log('');
    }
  });

  console.log('--------------------------------------------------');
  console.log(`📊 Resumo da Validação dos Artigos:`);
  console.log(`   - Total de Artigos Verificados: ${files.length}`);
  console.log(`   - Artigos com Erros Fatais: ${invalidFilesCount}`);
  console.log(`   - Total de Erros Encontrados: ${totalErrors}`);
  console.log(`   - Total de Alertas/Recomendações: ${totalWarnings}\n`);

  if (invalidFilesCount > 0) {
    console.error('❌ Falha na validação! Corrija os erros listados nos artigos antes de prosseguir.');
    process.exit(1);
  } else {
    console.log('✅ Validação concluída com sucesso! Todos os artigos estão aptos.');
    process.exit(0);
  }
}

validateArticles();
