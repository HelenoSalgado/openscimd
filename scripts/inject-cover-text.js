const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const { parseMarkdownFile } = require('./utils');

/**
 * Normaliza lista de autores a partir dos metadados do artigo
 */
function extractAuthors(metadata) {
  if (metadata.authors) {
    if (Array.isArray(metadata.authors)) {
      return metadata.authors.map(a => (typeof a === 'object' && a.name ? a.name : a)).join(', ');
    }
    return String(metadata.authors);
  }
  if (metadata.author) {
    if (Array.isArray(metadata.author)) {
      return metadata.author.map(a => (typeof a === 'object' && a.name ? a.name : a)).join(', ');
    }
    return String(metadata.author);
  }
  return '';
}

/**
 * Formata data de maneira humanizada no formato brasileiro (ex: Julho de 2026 ou 29 de Julho de 2026)
 */
function formatDate(dateStr) {
  if (!dateStr) return '';
  const str = String(dateStr).trim();

  const monthsBR = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];

  // Regex para MM-DD-YYYY ou DD-MM-YYYY
  const match = str.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/);
  if (match) {
    let p1 = parseInt(match[1], 10);
    let p2 = parseInt(match[2], 10);
    const year = match[3];

    // Trata se p1 for mês (>12 significa que é dia, portanto DD-MM-YYYY)
    if (p1 > 12) {
      const day = p1;
      const month = p2;
      if (month >= 1 && month <= 12) {
        return `${day} de ${monthsBR[month - 1]} de ${year}`;
      }
    } else if (p2 > 12) {
      // MM-DD-YYYY
      const month = p1;
      const day = p2;
      if (month >= 1 && month <= 12) {
        return `${day} de ${monthsBR[month - 1]} de ${year}`;
      }
    } else {
      // Se ambos <= 12, assume formato MM-DD-YYYY por padrão dos artigos (ex: 07-29-2026)
      const month = p1;
      const day = p2;
      return `${day} de ${monthsBR[month - 1]} de ${year}`;
    }
  }

  // Apenas Ano e Mês (YYYY-MM ou MM-YYYY)
  const monthYearMatch = str.match(/^(\d{4})[-/](\d{1,2})$/) || str.match(/^(\d{1,2})[-/](\d{4})$/);
  if (monthYearMatch) {
    let m = parseInt(monthYearMatch[1], 10);
    let y = monthYearMatch[2];
    if (m > 12) { y = monthYearMatch[1]; m = parseInt(monthYearMatch[2], 10); }
    if (m >= 1 && m <= 12) {
      return `${monthsBR[m - 1]} de ${y}`;
    }
  }

  return str;
}

/**
 * Quebra o título em várias linhas com base na largura máxima
 */
function wrapText(text, maxCharsPerLine = 32) {
  if (!text) return [];
  const words = text.split(/\s+/);
  const lines = [];
  let currentLine = '';

  for (const word of words) {
    if ((currentLine + (currentLine ? ' ' : '') + word).length <= maxCharsPerLine) {
      currentLine += (currentLine ? ' ' : '') + word;
    } else {
      if (currentLine) lines.push(currentLine);
      currentLine = word;
    }
  }
  if (currentLine) lines.push(currentLine);
  return lines;
}

/**
 * Escapa caracteres especiais para SVG
 */
function escapeXml(unsafe) {
  if (!unsafe) return '';
  return String(unsafe)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

async function injectCoverText() {
  const args = process.argv.slice(2);
  const rawImagePath = args[0];
  const customTextArg = args[1]; // Opcional: "Título | Autor | Data"

  if (!rawImagePath) {
    console.error('❌ Uso incorreto do script!');
    console.log('   Sintaxe: node scripts/inject-cover-text.js <caminho-da-imagem> ["Título | Autores | Data"]');
    process.exit(1);
  }

  const resolvedImagePath = path.resolve(rawImagePath);
  if (!fs.existsSync(resolvedImagePath)) {
    console.error(`❌ Erro: Arquivo de imagem não encontrado em: ${resolvedImagePath}`);
    process.exit(1);
  }

  const fileExt = path.extname(resolvedImagePath);
  const fileName = path.basename(resolvedImagePath);
  const baseName = path.basename(resolvedImagePath, fileExt);

  let title = '';
  let authors = '';
  let date = '';
  const collectionName = 'COLEÇÃO OPENSCIMD';

  // Se o texto customizado foi informado no argumento
  if (customTextArg) {
    const parts = customTextArg.split('|').map(s => s.trim());
    title = parts[0] || '';
    authors = parts[1] || '';
    date = parts[2] || '';
  } else {
    // Tenta encontrar o artigo correspondente em articles/<baseName>.md
    const articlePath = path.join(__dirname, '..', 'articles', `${baseName}.md`);
    if (fs.existsSync(articlePath)) {
      console.log(`📖 Extraindo metadados de: articles/${baseName}.md...`);
      const { metadata } = parseMarkdownFile(articlePath);
      title = metadata.title || baseName;
      authors = extractAuthors(metadata);
      date = formatDate(metadata.date);
    } else {
      console.warn(`⚠️ Aviso: Artigo não encontrado em articles/${baseName}.md. Usando o nome da imagem como título.`);
      title = baseName.replace(/-/g, ' ').toUpperCase();
    }
  }

  console.log(`🎨 Injetando texto na capa:`);
  console.log(`   Coleção: ${collectionName}`);
  console.log(`   Título : ${title}`);
  console.log(`   Autores: ${authors}`);
  console.log(`   Data   : ${date}`);

  // Dimensões do grid de capa (1696 x 2528 px, proporção 2:3)
  const width = 1696;
  const height = 2528;

  // Configurações tipográficas de alto impacto (tamanho de fonte maior e entrelinha justa)
  const headerFontSize = 42;
  let titleFontSize = 64;
  let titleLineHeight = 80;
  let maxChars = 28;

  if (title.length > 70) {
    titleFontSize = 56;
    titleLineHeight = 70;
    maxChars = 32;
  }
  const authorFontSize = 48;
  const dateFontSize = 36;

  const titleLines = wrapText(title, maxChars);

  // Garantir diretório covers/originals
  const originalsDir = path.join(__dirname, '..', 'covers', 'originals');
  if (!fs.existsSync(originalsDir)) {
    fs.mkdirSync(originalsDir, { recursive: true });
  }

  // Define caminho de saída em covers/originals/<baseName>.png
  const destOriginalPath = path.join(originalsDir, `${baseName}.png`);

  try {
    console.log('⏳ Renderizando tipografia e aplicando overlay de alta definição...');

    // 1. Redimensiona imagem base primeiro
    const resizedBase = path.join(__dirname, '..', 'covers', `.tmp_base_${baseName}.png`);
    await sharp(resolvedImagePath)
      .resize(width, height, { fit: 'cover', position: 'center' })
      .toFile(resizedBase);

    // 2. Composição tipográfica direta via ImageMagick (magick)
    const { execSync } = require('child_process');
    let drawCommands = ``;

    // Cabeçalho da coleção
    drawCommands += ` -font "Adwaita-Sans" -pointsize ${headerFontSize} -weight Bold -fill "#334155" -gravity North -annotate +0+160 "${collectionName}" `;
    // Linha divisória topo
    drawCommands += ` -stroke "#CBD5E1" -strokewidth 2 -draw "line 648,215 1048,215" -stroke none `;

    // Linhas do Título (cálculo rígido de Y por linha)
    let startY = 310;
    for (let i = 0; i < titleLines.length; i++) {
      const lineUpper = titleLines[i].toUpperCase();
      const lineY = startY + (i * titleLineHeight);
      drawCommands += ` -font "C059-Bold" -pointsize ${titleFontSize} -weight Bold -fill "#0F172A" -gravity North -annotate +0+${lineY} "${lineUpper}" `;
    }

    // Rodapé: Linha divisória, Autores e Data
    if (authors) {
      drawCommands += ` -stroke "#94A3B8" -strokewidth 3 -draw "line 748,2220 948,2220" -stroke none `;
      drawCommands += ` -font "Adwaita-Sans" -pointsize ${authorFontSize} -weight Bold -fill "#0F172A" -gravity South -annotate +0+210 "${authors}" `;
    }
    if (date) {
      drawCommands += ` -font "Adwaita-Sans" -pointsize ${dateFontSize} -fill "#475569" -gravity South -annotate +0+150 "${date}" `;
    }

    // Executa o ImageMagick para gerar a imagem final em covers/originals
    const cmd = `magick "${resizedBase}" ${drawCommands} "${destOriginalPath}"`;
    execSync(cmd, { stdio: 'inherit' });

    // Limpa imagem temporária
    if (fs.existsSync(resizedBase)) fs.unlinkSync(resizedBase);

    console.log(`\n✅ Capa final com tipografia salva em: covers/originals/${baseName}.png`);

    if (resolvedImagePath !== destOriginalPath && fs.existsSync(resolvedImagePath) && path.dirname(resolvedImagePath) === path.join(__dirname, '..', 'covers')) {
      fs.unlinkSync(resolvedImagePath);
      console.log(`🧹 Imagem temporária sem texto removida de: covers/${fileName}`);
    }

    console.log('💡 Dica: Agora você pode rodar "npm run convert-covers" para gerar as versões responsivas (mobile, tablet, desktop).');

  } catch (err) {
    console.error('❌ Erro ao injetar texto na capa:', err.message);
    process.exit(1);
  }
}

if (require.main === module) {
  injectCoverText();
}
