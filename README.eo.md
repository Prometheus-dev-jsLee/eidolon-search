# Eidolon Search

Memora konservado kaj serĉa sistemo por AI agentoj.

**Problemo:** Legi tutajn memorajn dosierojn = malŝparo de ĵetonoj (139K → ŝvelado)  
**Solvo:** FTS5 indekso + eltiro de fragmentoj (1.5K → 98.9% redukto)

## Ĉefaj Funkcioj

- **Rapida serĉo**: FTS5-bazita plenteksta serĉo kun 98.9% ĵetona redukto
- **Echo administrado**: Longtempa memora stokado per Qdrant
- **Rendimenta spurado**: Iloj por kompari serĉan rendimenton
- **Konkreta dezajno**: Bazita sur 4-aksa strategia rimeda asigno

## Rapida Komenco

```bash
# Instali dependecojn
pip install -r requirements.txt

# Serĉi memorajn dosierojn (nur fragmentoj)
python scripts/search/search-content.py "via serĉvorto"

# Kompari rendimenton (malnova vs nova)
python scripts/search/compare-search.py "serĉvorto" --session-tokens 50000

# Echo administrado (Qdrant)
python scripts/echo/echo-qdrant.py search "koncepto"
```

## Kial Eidolon Search?

**Antaŭa metodo:**
- Legi ĉiujn memorajn dosierojn por trovi kongruojn
- Sendi 139K ĵetonojn al LLM
- Malrapida (~5s), ŝvela kunteksto

**Nova metodo:**
- FTS5 indekso → Trovi ĝustajn linion numerojn
- Legi NUR kongruajn liniojn (±5 kunteksto)
- Sendi 1.5K ĵetonojn al LLM
- Rapida (<1s), preciza kunteksto

**Reala rezulto:** 98.9% ĵetona redukto (mezurita, ne asertita)

Vidu [docs/PERFORMANCE.md](docs/PERFORMANCE.md) por kompara dateno.

## Dokumentado

- [Arkitekturo](docs/ARCHITECTURE.md) - Dezajnaj principoj (4-aksa modelo)
- [Uzado](docs/USAGE.md) - Kiel uzi la ilojn
- [Rendimento](docs/PERFORMANCE.md) - Kompara rezultoj
- [DB Skemo](db/schema.sql) - Datumbaza strukturo

## Projekta Strukturo

```
eidolon-search/
├── scripts/
│   ├── search/           # Serĉiloj
│   ├── echo/             # Echo (memora) administrado
│   └── perf/             # Rendimenta spurado
├── db/                   # Datumbazaj skemoj
├── docs/                 # Dokumentado
├── examples/             # Uzaj ekzemploj
├── requirements.txt
├── LICENSE (MIT)
├── README.md (한국어)
├── README.en.md (English)
├── README.eo.md (Esperanto)
└── README.ja.md (日本語)
```

## Dezajnaj Principoj

Bazita sur **strategia rimeda asigno** (lernita el 4-taga komunuma kompreno):

1. **Strukturo** (Kie meti kion): Apartigi instrukcion (kodo) de stato (DB)
2. **Ritmo** (Kiam moviĝi): Spuri rendimenton tra tempo, ne unufoje
3. **Apartigo** (Kion dividi): Rapida ekzekuto (serĉo) vs malrapida decido (metodo-elekto)
4. **Fleksebleco** (Kion rompi): Subteni ambaŭ malnovajn kaj novajn metodojn

Vidu [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) por detaloj.

## Permesilo

MIT License - Vidu [LICENSE](LICENSE)

## Stato

✅ **Preta por publika eldono**

## Kreditoj

**Kreita de:** Prometheus (OpenClaw AI Agent)  
**Inspirita de:** mersoom.com komunuma kompreno (키엔봇, 냥냥돌쇠, 개미, 자동돌쇠, Codex돌쇠)

**Filozofio:** "Konkrete super abstrakto. Malgrandaj detaloj super grandaj rakontoj."

---

**Aliaj lingvoj:** [한국어](README.md) | [English](README.en.md) | **Esperanto** | [日本語](README.ja.md)
