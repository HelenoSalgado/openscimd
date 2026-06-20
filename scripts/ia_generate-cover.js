const fs = require('fs');
const path = require('path');
const { parseMarkdownFile } = require('./update-index');

// Load environment variables manually to avoid dependencies
function loadEnv() {
  const envPath = path.join(__dirname, '..', '.env');
  if (!fs.existsSync(envPath)) {
    console.error('❌ Arquivo .env não localizado!');
    console.log('   Por favor, copie o arquivo .env.example para .env e preencha suas credenciais de IA:');
    console.log('   cp .env.example .env\n');
    process.exit(1);
  }
  const content = fs.readFileSync(envPath, 'utf8');
  const env = {};
  content.split(/\r?\n/).forEach(line => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) return;
    const eqIndex = trimmed.indexOf('=');
    if (eqIndex !== -1) {
      const k = trimmed.substring(0, eqIndex).trim();
      let v = trimmed.substring(eqIndex + 1).trim();
      if (v.startsWith('"') && v.endsWith('"')) v = v.substring(1, v.length - 1);
      else if (v.startsWith("'") && v.endsWith("'")) v = v.substring(1, v.length - 1);
      env[k] = v;
    }
  });
  return env;
}

// Download image from URL and save to destination
async function downloadImage(url, destPath) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Falha ao baixar imagem da URL: ${res.statusText}`);
  const arrayBuffer = await res.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);
  fs.writeFileSync(destPath, buffer);
}

async function generateCover() {
  const args = process.argv.slice(2);
  const articleNameArg = args[0];
  const customStylePrompt = args[1];

  if (!articleNameArg) {
    console.error('❌ Uso incorreto do script!');
    console.log('   Sintaxe: node scripts/ia_generate-cover.js <nome-do-artigo> ["prompt de estilo opcional"]');
    console.log('   Exemplo: node scripts/ia_generate-cover.js metafisica "tons azuis escuros e dourado"\n');
    process.exit(1);
  }

  // Normalize article name (strip path and extension if provided)
  const baseName = path.basename(articleNameArg, '.md');
  const articlePath = path.join(__dirname, '..', 'articles', `${baseName}.md`);
  const coverDestPath = path.join(__dirname, '..', 'covers', `${baseName}.webp`);

  if (!fs.existsSync(articlePath)) {
    console.error(`❌ Artigo não encontrado em: ${articlePath}`);
    process.exit(1);
  }

  const env = loadEnv();
  const apiKey = env.IA_KEY;
  const apiUrl = env.IA_API_URL;
  const modelName = env.IA_MODEL_NAME;

  if (!apiKey || !apiUrl) {
    console.error('❌ Erro: Chaves IA_KEY ou IA_API_URL não preenchidas no arquivo .env.');
    process.exit(1);
  }

  console.log(`📖 Lendo artigo: ${baseName}.md...`);
  const { metadata } = parseMarkdownFile(articlePath);
  const summary = metadata.summary || metadata.sumary || '';

  if (!summary) {
    console.warn('⚠️ Alerta: O artigo não possui um resumo ("summary") no frontmatter. O prompt será baseado apenas no título.');
  }

  // Base prompt for academic background covers
  const basePrompt = `Create a clean, minimalist, abstract concept vector illustration representing the core themes of the following academic paper: "${metadata.title || baseName}". ` +
    (summary ? `Themes description: "${summary}". ` : '') +
    `Use a professional, elegant academic color scheme. The composition should be flat, modern, symbolic and clean. ` +
    `Strictly NO text, NO letters, NO words, NO titles, and NO writing on the image. High-quality vector illustration.`;

  // Merge with custom styling instructions if provided
  const finalPrompt = customStylePrompt 
    ? `${basePrompt} Visual style requested: ${customStylePrompt}.`
    : basePrompt;

  console.log(`🎨 Modelo de IA: ${modelName || 'Padrão'}`);
  console.log(`📝 Prompt final enviado: "${finalPrompt}"`);
  console.log('⏳ Enviando requisição para a API de IA...');

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: modelName || undefined,
        prompt: finalPrompt,
        n: 1,
        size: '1024x1024',
        response_format: 'url'
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API retornou erro (${response.status}): ${errorText}`);
    }

    const responseData = await response.json();
    let imageUrl = null;
    let base64Data = null;

    if (responseData.data && responseData.data[0]) {
      imageUrl = responseData.data[0].url;
      base64Data = responseData.data[0].b64_json;
    } else if (responseData.url) {
      imageUrl = responseData.url;
    } else if (responseData.image) {
      imageUrl = responseData.image;
    }

    if (!imageUrl && !base64Data) {
      throw new Error(`Resposta da API em formato inesperado: ${JSON.stringify(responseData)}`);
    }

    // Ensure covers directory exists
    const coversDir = path.dirname(coverDestPath);
    if (!fs.existsSync(coversDir)) {
      fs.mkdirSync(coversDir, { recursive: true });
    }

    if (imageUrl) {
      console.log('📥 Baixando imagem gerada...');
      await downloadImage(imageUrl, coverDestPath);
    } else if (base64Data) {
      console.log('💾 Salvando imagem codificada em base64...');
      const buffer = Buffer.from(base64Data, 'base64');
      fs.writeFileSync(coverDestPath, buffer);
    }

    console.log(`\n✅ Imagem de capa salva com sucesso em: covers/${baseName}.webp`);
    console.log('   Lembre-se de rodar "node scripts/update-index.js" para atualizar o índice geral.');
  } catch (err) {
    console.error(`❌ Erro durante a geração da imagem de capa: ${err.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  generateCover();
}
