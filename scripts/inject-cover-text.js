const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

// Simple function to wrap text for SVG
function wrapText(text, maxCharsPerLine) {
  const words = text.split(' ');
  const lines = [];
  let currentLine = '';

  for (const word of words) {
    if ((currentLine + ' ' + word).length > maxCharsPerLine) {
      lines.push(currentLine.trim());
      currentLine = word;
    } else {
      currentLine = currentLine ? currentLine + ' ' + word : word;
    }
  }
  if (currentLine) lines.push(currentLine.trim());
  return lines;
}

async function injectTextToCover() {
  const inputImage = process.argv[2];
  const outputImage = process.argv[3];
  
  if (!inputImage || !outputImage) {
    console.error('Uso: node inject-cover-text.js <caminho-input> <caminho-output>');
    process.exit(1);
  }

  // Metadados extraídos do arquivo Markdown do experimento
  const title = "Induções Estruturais para Alucinações em Grandes Modelos de Linguagem: Um Estudo de Caso Apenas de Saída e a Descoberta do Loop de Correção Falsa";
  const author = "Hiroko Konishi";
  const dateStr = "2025";
  const collectionName = "OpenSciMD Collection";

  const width = 1696;
  const height = 2528;

  // Envolver o título (aprox 35 caracteres por linha para esse tamanho de fonte)
  const titleLines = wrapText(title.toUpperCase(), 35);
  
  // Construir o SVG com a tipografia
  // O SVG precisa ter o mesmo tamanho da imagem base
  let svgText = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;

  // Textos Injetados com atributos inline para garantir suporte no Sharp
  svgText += `<text x="${width/2}" y="200" font-family="sans-serif" font-size="32" fill="#D4AF37" letter-spacing="6" text-anchor="middle" font-weight="normal">${collectionName}</text>`;

  let startY = 350;
  for(let i=0; i<titleLines.length; i++) {
    svgText += `<text x="${width/2}" y="${startY + (i * 80)}" font-family="sans-serif" font-size="64" fill="#FFFFFF" font-weight="bold" text-anchor="middle" letter-spacing="2">${titleLines[i]}</text>`;
  }

  svgText += `<text x="${width/2}" y="${height - 250}" font-family="serif" font-size="48" fill="#E0E0E0" text-anchor="middle" letter-spacing="4">${author.toUpperCase()}</text>`;
  svgText += `<text x="${width/2}" y="${height - 150}" font-family="sans-serif" font-size="36" fill="#888888" text-anchor="middle" letter-spacing="8">${dateStr}</text>`;
  
  svgText += `</svg>`;

  console.log('Aplicando tipografia...');

  try {
    // Redimensionar imagem de fundo para o grid exato
    const background = await sharp(inputImage)
      .resize(width, height, { fit: 'cover' })
      .toBuffer();

    // Compor o SVG em cima do fundo
    await sharp(background)
      .composite([{
        input: Buffer.from(svgText),
        top: 0,
        left: 0
      }])
      .webp({ quality: 90 })
      .toFile(outputImage);

    console.log('✅ Capa gerada com sucesso em: ' + outputImage);
  } catch (error) {
    console.error('❌ Erro na geração:', error);
  }
}

injectTextToCover();
