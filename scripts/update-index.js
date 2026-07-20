const { updateArticlesIndex } = require('./update-articles-index');
const { updateBooksIndex } = require('./update-books-index');
const fs = require('fs');
const path = require('path');

function updateAll() {
  console.log('🔄 Iniciando atualização geral de índices...');
  try {
    updateArticlesIndex();
    updateBooksIndex();
    console.log('✅ Todos os índices atualizados com sucesso!');
  } catch (error) {
    console.error('❌ Erro durante a atualização:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  updateAll();
}

// For compatibility with previous exports in case they are used elsewhere
// Note: Some of these were moved to utils.js
const utils = require('./utils');
module.exports = {
  updateIndex: updateAll,
  parseMarkdownFile: utils.parseMarkdownFile,
  parseDateToTimestamp: utils.parseDateToTimestamp,
  estimateReadingTime: utils.estimateReadingTime
};
