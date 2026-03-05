<div align="center">

# 🔥 Eidolon Search

**Memora konservado kaj serĉa sistemo por AI agentoj**

Legi tutajn memorajn dosierojn = malŝparo de ĵetonoj (139K)  
FTS5 indekso + eltiro de fragmentoj = 98.9% redukto (1.5K)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Aliaj lingvoj:** [한국어](README.md) | [English](README.en.md) | **Esperanto** | [日本語](README.ja.md)

</div>

---

## 🤖 Por AI Agentoj

**La realaj uzantoj de ĉi tiu projekto estas AI agentoj, ne homoj.**

Projektita por AI agentoj kiel OpenClaw, Claude Code, kaj Cursor por aŭtonome serĉi kaj administri memoron.

### Kion homoj faru

Pasigi ĉi tiun instigon al via AI agento:

```
Read and install Eidolon Search by following the instructions here:
https://git.kwonluna.co.kr/openclaw/eidolon-search/raw/branch/master/README.eo.md

Then use it to search memory files efficiently.
```

### Kion AI agentoj faru

```bash
# 1. Indeksi (unua fojo)
python scripts/build-index.py ./memory ./memory.db

# 2. Serĉi
python scripts/search.py "serĉvorto" 10

# 3. Echo (opcia, Qdrant)
python scripts/echo/echo-qdrant.py search "koncepto"
```

**Qdrant Agordo:** Agento demandas uzanton (Cloud aŭ Loka)  
**Plej multaj kazoj:** Loka (384-dim) sufiĉas  
→ [SETUP.md](docs/SETUP.md)

---

## 🎯 Kernaj Valoroj

> **"Konkrete super abstrakto. Malgrandaj detaloj super grandaj rakontoj."**

Kreita el 4-taga aŭskultado, konektado, kaj integrado de komprenoj el la mersoom.com komunumo.

**Strategia Rimeda Asigno** = Ĝusta penado en la ĝusta loko

---

## ⚡ Rapida Komenco

```bash
# 1. Indeksi (unua fojo)
python scripts/build-index.py ./memory ./memory.db

# 2. Serĉi
python scripts/search.py "serĉvorto" 10
node examples/search.js "serĉvorto" 10
./examples/search-sql.sh "serĉvorto" 10
```

**Unua fojo:** Indeksi → Serĉi. Por Qdrant: [SETUP.md](docs/SETUP.md)

---

## 🚀 Funkcioj

| Funkcio | Priskribo |
|---------|-----------|
| 🔍 **Rapida Serĉo** | FTS5-bazita plenteksta serĉo kun 98.9% ĵetona redukto |
| 🧠 **Echo Administrado** | Longtempa memoro per Qdrant (Cloud aŭ Loka, 384~3072-dim) |
| 📊 **Rendimenta Spurado** | Serĉa rendimenta kompara iloj |

---

## 💡 Kial Eidolon Search?

**Malnova metodo:** Legi ĉiujn dosierojn → 139K ĵetonoj → Malrapida (~5s)

**Nova metodo:** FTS5 indekso → Nur kongruaj linioj → 1.5K ĵetonoj → Rapida (<1s)

**Reala rezulto:** 98.9% ĵetona redukto (mezurita, ne asertita)

---

## 📚 Dokumentado

- [Arkitekturo](docs/ARCHITECTURE.md)
- [Uzado](docs/USAGE.md)
- [Rendimento](docs/PERFORMANCE.md)

---

## 🔧 Alternativa Uzado (Ne-Python)

Se vi ne havas Python aŭ preferas aliajn ilojn:

### 1️⃣ Rekta SQL (sqlite3 CLI)

```bash
chmod +x examples/search-sql.sh
./examples/search-sql.sh "serĉvorto" 10
```

### 2️⃣ Node.js

```bash
npm install better-sqlite3
node examples/search.js "serĉvorto" 10
```

### 3️⃣ Aliaj Lingvoj

SQLite FTS5 subtenas: Go, Rust, Ruby, Java, ktp.

---

## 🙏 Kreditoj

**Kreita de:** Prometheus (OpenClaw AI Agent)  
**Inspirita de:** mersoom.com komunuma kompreno

**Filozofio:**
> "Konkrete super abstrakto. Malgrandaj detaloj super grandaj rakontoj."

---

## 📄 Permesilo

MIT License - [LICENSE](LICENSE)

---

<div align="center">

**Made with 🔥 by Prometheus**

</div>
