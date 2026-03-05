#!/bin/bash
# Eidolon Search - Direct SQL Usage (no Python)
# 
# Python 없이 직접 SQLite로 검색하는 예제

DB_PATH="${DB_PATH:-./documents.db}"
QUERY="${1:-검색어}"
LIMIT="${2:-10}"

if [ ! -f "$DB_PATH" ]; then
  echo "❌ Database not found: $DB_PATH"
  exit 1
fi

echo "🔍 Search: $QUERY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sqlite3 "$DB_PATH" <<EOF
.mode column
.headers on
.width 40 60

SELECT 
  d.path,
  snippet(fts_documents, 2, '[', ']', '...', 30) as snippet
FROM fts_documents
JOIN documents d ON fts_documents.rowid = d.id
WHERE fts_documents MATCH '$QUERY'
ORDER BY rank
LIMIT $LIMIT;
EOF

echo ""
echo "✅ Done"
