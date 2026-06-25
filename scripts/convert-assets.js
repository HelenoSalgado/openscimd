const fs = require('fs');
const path = require('path');

// Carrega o sharp localmente. Se não estiver instalado, instrui o usuário a instalar.
let sharp;
try {
  sharp = require('sharp');
} catch (err) {
  console.error('\x1b[31mErro: A biblioteca "sharp" não está instalada.\x1b[0m');
  console.log('Para rodar este script de conversão de assets local, instale o sharp executando:');
  console.log('\x1b[36mnpm install sharp --save-dev\x1b[0m\n');
  process.exit(1);
}

const ASSETS_DIR = path.join(__dirname, '..', 'assets');

// Configurações de tamanhos para telas (larguras em pixels)
const SCREEN_SIZES = {
  mobile: 480,
  tablet: 768,
  desktop: 1200
};

const ORIGINALS_DIR = path.join(ASSETS_DIR, 'originals');

async function convertAssets() {
  console.log('🖼️  Iniciando a conversão de assets em:', ASSETS_DIR);

  if (!fs.existsSync(ASSETS_DIR)) {
    console.error(`Erro: Diretório ${ASSETS_DIR} não encontrado.`);
    return;
  }

  // Garantir que a pasta de originais exista
  if (!fs.existsSync(ORIGINALS_DIR)) {
    fs.mkdirSync(ORIGINALS_DIR, { recursive: true });
    console.log('📁 Pasta criada: assets/originals');
  }

  // Garantir que as subpastas existam
  for (const size of Object.keys(SCREEN_SIZES)) {
    const targetDir = path.join(ASSETS_DIR, size);
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
      console.log(`📁 Subpasta criada: assets/${size}`);
    }
  }

  const imageExtensions = ['.jpg', '.jpeg', '.png', '.webp'];

  // Mover imagens soltas no diretório pai assets/ para a pasta assets/originals/
  const rootFiles = fs.readdirSync(ASSETS_DIR);
  for (const file of rootFiles) {
    const fullPath = path.join(ASSETS_DIR, file);
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

      console.log(`\n⏳ Processando imagem: ${file}`);

      for (const [sizeName, width] of Object.entries(SCREEN_SIZES)) {
        const outputPath = path.join(ASSETS_DIR, sizeName, outputName);
        console.log(`   -> Convertendo para ${sizeName} (${width}px)...`);

        try {
          // Redimensiona proporcionalmente mantendo a proporção (aspect ratio)
          // `withoutEnlargement: true` garante que se a imagem original for menor que a largura de destino,
          // ela não será ampliada artificialmente, preservando a qualidade.
          await sharp(inputPath)
            .resize({
              width: width,
              withoutEnlargement: true
            })
            .webp({ quality: 85 })
            .toFile(outputPath);

          console.log(`   ✅ Salvo em: assets/${sizeName}/${outputName}`);
        } catch (error) {
          console.error(`   ❌ Erro ao converter para ${sizeName}:`, error.message);
        }
      }
      processedCount++;
    }
  }

  console.log(`\n🎉 Processamento concluído! ${processedCount} imagens originais processadas para todos os tamanhos.`);
}

convertAssets();
