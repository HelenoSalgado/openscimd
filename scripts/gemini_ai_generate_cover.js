const fs = require('node:fs');
const path = require('node:path');
const { parseMarkdownFile } = require('./update-index');

// Load environment variables manually
function loadEnv() {
  const envPath = path.join(__dirname, '..', '.env');
  if (!fs.existsSync(envPath)) {
    console.error('❌ Arquivo .env não localizado!');
    console.log('   Por favor, copie o arquivo .env.example para .env e preencha suas credenciais de IA.');
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

async function main() {
  const args = process.argv.slice(2);
  const articleNameArg = args[0];
  const customStylePrompt = args[1];

  // Optional argument to list available models
  if (articleNameArg === '--list' || articleNameArg === '-l' || articleNameArg === '--list-models' || articleNameArg === 'list') {
    console.log('📋 Modelos de Geração de Imagem Google Gemini disponíveis:');
    console.log('   - gemini-3.1-flash-image          (Modelo padrão, veloz e otimizado)');
    console.log('   - imagen-3.0-generate-002         (Modelo de imagem de alta qualidade)');
    console.log('   - imagen-3.0-fast-generate-001    (Modelo de imagem rápido)');
    console.log('\n💡 Configure o modelo desejado no seu arquivo .env com a variável IA_MODEL_NAME.');
    process.exit(0);
  }

  if (!articleNameArg) {
    console.error('❌ Uso incorreto do script!');
    console.log('   Sintaxe: node scripts/gemini_ai_generate_cover.js <nome-do-artigo> ["prompt de estilo opcional"]');
    console.log('   Sintaxe (listar modelos): node scripts/gemini_ai_generate_cover.js --list');
    console.log('   Exemplo: node scripts/gemini_ai_generate_cover.js metafisica "estilo barroco em tons de azul"\n');
    process.exit(1);
  }

  const baseName = path.basename(articleNameArg, '.md');
  const articlePath = path.join(__dirname, '..', 'articles', `${baseName}.md`);
  const coverDestPath = path.join(__dirname, '..', 'covers', `${baseName}.png`);

  if (!fs.existsSync(articlePath)) {
    console.error(`❌ Artigo não encontrado em: ${articlePath}`);
    process.exit(1);
  }

  const env = loadEnv();
  const apiKey = env.IA_KEY;
  const modelName = env.IA_MODEL_NAME || 'gemini-3.1-flash-image';

  if (!apiKey) {
    console.error('❌ Erro: Chave IA_KEY não preenchidas no arquivo .env.');
    process.exit(1);
  }

  // Import @google/genai dynamically to support ESM inside CommonJS
  let GoogleGenAI;
  try {
    const sdk = await import('@google/genai');
    GoogleGenAI = sdk.GoogleGenAI;
  } catch (err) {
    console.error('❌ Erro ao carregar o SDK da Google Gen AI. Certifique-se de que rodou "npm install".');
    console.error(err.message);
    process.exit(1);
  }

  console.log(`📖 Lendo artigo: ${baseName}.md...`);
  const { metadata } = parseMarkdownFile(articlePath);
  const summary = metadata.summary || '';

  if (!summary) {
    console.warn('⚠️ Alerta: O artigo não possui um resumo ("summary") no frontmatter. O prompt será baseado apenas no título.');
  }

  // Base prompt for academic background covers (book cover ratio, centered solid illustration, negative space)
  const basePrompt = `Create a clean, minimalist book cover background artwork with vertical 2:3 aspect ratio (portrait orientation). ` +
    `The illustration must NOT be abstract; instead, depict a clear, solid, recognizable minimalist object or symbol representing the single strongest central element of the following academic paper: "${metadata.title || baseName}". ` +
    (summary ? `Themes description: "${summary}". ` : '') +
    `The main subject must be perfectly centered in the middle of the composition. ` +
    `Keep ample clean negative space at the top and bottom of the image for editorial text placement. ` +
    `Use a professional, elegant academic color scheme with 2D flat vector aesthetic. ` +
    `Strictly NO text, NO letters, NO words, NO titles, NO borders, and NO writing anywhere on the image. High-quality cover illustration.`;

  const finalPrompt = customStylePrompt 
    ? `${basePrompt} Visual style requested: ${customStylePrompt}.`
    : basePrompt;

  console.log(`🎨 Modelo de IA: ${modelName}`);
  console.log(`📝 Prompt final enviado: "${finalPrompt}"`);
  console.log('⏳ Enviando requisição para o Google Gemini...');

  try {
    const ai = new GoogleGenAI({ apiKey: apiKey });
    const interaction = await ai.interactions.create({
      model: modelName,
      input: finalPrompt,
    });

    const generatedImage = interaction.output_image;
    if (!generatedImage || !generatedImage.data) {
      throw new Error('Nenhuma imagem foi retornada pelo modelo Gemini.');
    }

    // Ensure covers directory exists
    const coversDir = path.dirname(coverDestPath);
    if (!fs.existsSync(coversDir)) {
      fs.mkdirSync(coversDir, { recursive: true });
    }

    console.log('💾 Salvando imagem gerada de fundo temporária...');
    const tempRawPath = path.join(coversDir, `${baseName}.png`);
    const buffer = Buffer.from(generatedImage.data, 'base64');
    fs.writeFileSync(tempRawPath, buffer);

    console.log('🎨 Aplicando overlay de tipografia editorial e salvando em covers/originals...');
    const { execSync } = require('child_process');
    const injectScript = path.join(__dirname, 'inject-cover-text.js');
    execSync(`node "${injectScript}" "${tempRawPath}"`, { stdio: 'inherit' });

    console.log(`\n✅ Processo concluído! Capa gerada e formatada em: covers/originals/${baseName}.png`);
    console.log('   Lembre-se de rodar "npm run convert-covers" e "node scripts/update-index.js".');
  } catch (err) {
    console.error(`❌ Erro durante a geração da imagem de capa via Gemini: ${err.message}`);
    process.exit(1);
  }
}

main();
