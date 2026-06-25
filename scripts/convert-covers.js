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
const ORIGINALS_DIR = path.join(COVERS_DIR, 'originals');
const TARGET_WIDTH = 1696;
const TARGET_HEIGHT = 2528;
const TARGET_DPI = 72;

// Configurações de tamanhos para telas (larguras em pixels)
const SCREEN_SIZES = {
  mobile: 1080,
  tablet: 1200,
  desktop: 1696
};

async function convertCovers() {
  console.log('🖼️  Iniciando a conversão de capas em:', COVERS_DIR);
  
  if (!fs.existsSync(COVERS_DIR)) {
    console.error(`Erro: Diretório ${COVERS_DIR} não encontrado.`);
    return;
  }

  // Garantir que a pasta de originais exista
  if (!fs.existsSync(ORIGINALS_DIR)) {
    fs.mkdirSync(ORIGINALS_DIR, { recursive: true });
    console.log('📁 Pasta criada: covers/originals');
  }

  // Garantir que as subpastas de tamanhos existam
  for (const size of Object.keys(SCREEN_SIZES)) {
    const targetDir = path.join(COVERS_DIR, size);
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
      console.log(`📁 Subpasta criada: covers/${size}`);
    }
  }

  const imageExtensions = ['.jpg', '.jpeg', '.png', '.webp'];

  // Mover imagens soltas no diretório pai covers/ para a pasta covers/originals/
  const rootFiles = fs.readdirSync(COVERS_DIR);
  for (const file of rootFiles) {
    const fullPath = path.join(COVERS_DIR, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      continue;
    }
    const ext = path.extname(file).toLowerCase();
    if (imageExtensions.includes(ext)) {
      const destPath = path.join(ORIGINALS_DIR, file);
      fs.renameSync(fullPath, destPath);
      console.log(`📦 Mapeado original para pasta originals: ${file}`);
    }
  }

  // Listar arquivos no diretório de originais
  const files = fs.readdirSync(ORIGINALS_DIR);
  let processedCount = 0;

  for (const file of files) {
    const ext = path.extname(file).toLowerCase();
    if (imageExtensions.includes(ext)) {
      const inputPath = path.join(ORIGINALS_DIR, file);
      const baseName = path.basename(file, ext);
      const outputName = `${baseName}.webp`;

      console.log(`\n⏳ Processando capa: ${file}`);

      for (const [sizeName, width] of Object.entries(SCREEN_SIZES)) {
        const outputPath = path.join(COVERS_DIR, sizeName, outputName);
        const height = Math.round(width * (TARGET_HEIGHT / TARGET_WIDTH));
        console.log(`   -> Convertendo para ${sizeName} (${width}x${height}px)...`);

        try {
          await sharp(inputPath)
            .resize(width, height, {
              fit: 'fill' // Força o redimensionamento exato para a proporção da capa do ebook
            })
            .webp({ quality: 85 })
            .withMetadata({ density: TARGET_DPI })
            .toFile(outputPath);

          console.log(`   ✅ Salvo em: covers/${sizeName}/${outputName}`);
        } catch (error) {
          console.error(`   ❌ Erro ao converter para ${sizeName}:`, error.message);
        }
      }
      processedCount++;
    }
  }

  console.log(`\n🎉 Processamento concluído! ${processedCount} capas originais processadas para todos os tamanhos.`);
}

convertCovers();
