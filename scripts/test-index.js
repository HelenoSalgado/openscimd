const assert = require('assert');
const { parseDateToTimestamp, estimateReadingTime, parseMarkdownFile } = require('./update-index');
const fs = require('fs');
const path = require('path');

function runTests() {
  console.log('🧪 Iniciando testes de unidade para as funções de indexação...');

  // 1. Test Date Parsing
  console.log('Testing parseDateToTimestamp...');
  
  // DD-MM-YYYY format
  const t1 = parseDateToTimestamp('20-06-2026');
  assert.strictEqual(t1, Date.UTC(2026, 5, 20), 'Should parse DD-MM-YYYY dates correctly');
  
  // YYYY-MM-DD format
  const t2 = parseDateToTimestamp('2026-06-18');
  assert.strictEqual(t2, Date.UTC(2026, 5, 18), 'Should parse YYYY-MM-DD dates correctly');

  // Null/Empty cases
  assert.strictEqual(parseDateToTimestamp(''), null);
  assert.strictEqual(parseDateToTimestamp(null), null);

  // 2. Test Reading Time Estimation
  console.log('Testing estimateReadingTime...');
  
  const shortText = 'Esta é uma frase de teste simples.';
  const readingTimeShort = estimateReadingTime(shortText);
  assert.strictEqual(readingTimeShort, 1, 'Should return at least 1 minute for short texts');

  // Generate 450 words
  const longText = Array(450).fill('palavra').join(' ');
  const readingTimeLong = estimateReadingTime(longText);
  assert.strictEqual(readingTimeLong, 3, 'Should estimate 3 minutes for 450 words at 200 WPM');

  // Text with code block
  const textWithCode = 'Texto normal.\n```javascript\n' + Array(200).fill('code').join(' ') + '\n```\nMais texto.';
  const readingTimeWithCode = estimateReadingTime(textWithCode);
  assert.strictEqual(readingTimeWithCode, 1, 'Should strip code blocks before estimation');

  // 3. Test Frontmatter Parsing
  console.log('Testing parseMarkdownFile with a temporary mock file...');
  
  const mockFilePath = path.join(__dirname, 'mock-article.md');
  const mockContent = `---
title: "Artigo de Teste"
author: "Test Author"
category: Teste, Geral
date: 2026-06-20
DOI: 10.1234/test
---
# Introdução
Conteúdo do artigo.`;

  fs.writeFileSync(mockFilePath, mockContent, 'utf8');

  try {
    const { metadata, body } = parseMarkdownFile(mockFilePath);
    assert.strictEqual(metadata.title, 'Artigo de Teste');
    assert.strictEqual(metadata.author, 'Test Author');
    assert.deepStrictEqual(metadata.category, ['Teste', 'Geral']);
    assert.strictEqual(metadata.date, '2026-06-20');
    assert.strictEqual(metadata.DOI, '10.1234/test');
    assert.ok(body.includes('# Introdução'), 'Should extract body correctly');
    console.log('Frontmatter parsing assertions passed.');
  } finally {
    if (fs.existsSync(mockFilePath)) {
      fs.unlinkSync(mockFilePath);
    }
  }

  console.log('✅ Todos os testes passaram com sucesso!');
}

runTests();
