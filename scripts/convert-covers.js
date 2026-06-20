const fs = require('fs');
const path = require('path');

// Carrega o sharp localmente. Se não estiver instalado, instrui o usuário a instalar.
let sharp;
try {
  sharp = require('sharp');
} catch (err) {
  console.error('\x1b[31mErro: A biblioteca "sharp" não está instalada.\x1b[0m');
  console.log('Para rodar este script de conversão de capas local, instale o sharp executando:');
  console.log('\x1b[36mnpm install sharp --save-dev\x1b[0m\n');
  process.exit(1);
}

const COVERS_DIR = path.join(__dirname, '..', 'covers');
const TARGET_WIDTH = 1696;
const TARGET_HEIGHT = 2528;
const TARGET_DPI = 72;

async function convertCovers() {
  console.log('🖼️  Iniciando a conversão de capas em:', COVERS_DIR);
  
  if (!fs.existsSync(COVERS_DIR)) {
    console.error(`Erro: Diretório ${COVERS_DIR} não encontrado.`);
    return;
  }

  const files = fs.readdirSync(COVERS_DIR);
  const imageExtensions = ['.jpg', '.jpeg', '.png'];
  let count = 0;

  for (const file of files) {
    const ext = path.extname(file).toLowerCase();
    if (imageExtensions.includes(ext)) {
      const inputPath = path.join(COVERS_DIR, file);
      const outputName = path.basename(file, ext) + '.webp';
      const outputPath = path.join(COVERS_DIR, outputName);

      console.log(`⏳ Convertendo: ${file} -> ${outputName}...`);

      try {
        await sharp(inputPath)
          .resize(TARGET_WIDTH, TARGET_HEIGHT, {
            fit: 'fill' // Força o redimensionamento exato para a proporção da capa do ebook
          })
          .webp({ quality: 85 })
          .withMetadata({ density: TARGET_DPI })
          .toFile(outputPath);

        console.log(`✅ Convertido com sucesso: ${outputName}`);
        
        // Remove a imagem original JPG/PNG após a conversão
        fs.unlinkSync(inputPath);
        console.log(`🗑️  Original removido: ${file}`);
        count++;
      } catch (error) {
        console.error(`❌ Erro ao converter ${file}:`, error.message);
      }
    }
  }

  console.log(`\n🎉 Processamento concluído! ${count} capas convertidas.`);
}

convertCovers();
