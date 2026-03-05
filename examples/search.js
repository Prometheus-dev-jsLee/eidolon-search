#!/usr/bin/env node
/**
 * Eidolon Search - Node.js Example
 * 
 * Usage:
 *   node examples/search.js "검색어"
 *   DB_PATH=./documents.db node examples/search.js "query"
 */

const sqlite3 = require('better-sqlite3');
const path = require('path');

const DB_PATH = process.env.DB_PATH || path.join(__dirname, '..', 'memory.db');
const query = process.argv[2] || '검색어';
const limit = parseInt(process.argv[3] || '10', 10);

if (!require('fs').existsSync(DB_PATH)) {
  console.error('❌ Database not found:', DB_PATH);
  process.exit(1);
}

const db = sqlite3(DB_PATH, { readonly: true });

console.log('🔍 Search:', query);
console.log('━'.repeat(60));

const results = db.prepare(`
  SELECT 
    path,
    snippet(memory_fts, 1, '[', ']', '...', 30) as snippet,
    rank
  FROM memory_fts
  WHERE memory_fts MATCH ?
  ORDER BY rank
  LIMIT ?
`).all(query, limit);

if (results.length === 0) {
  console.log('No results found.');
} else {
  results.forEach((row, i) => {
    console.log(`\n${i + 1}. ${row.path}`);
    console.log(`   ${row.snippet}`);
  });
}

console.log('\n✅ Done');
db.close();
