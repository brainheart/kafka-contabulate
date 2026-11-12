# Kafka Contabulate

Static Contabulate corpus site for selected German works by Franz Kafka, built from public-domain German texts.

## Corpus

The corpus includes 11 public-domain texts:

- Betrachtung
- Das Urteil
- Amerika
- Die Verwandlung
- In der Strafkolonie
- Ein Landarzt
- Ein Hungerkünstler
- Der Mord
- Richard und Samuel
- Der Prozess
- Das Schloss

Most source texts are Project Gutenberg eTexts. Amerika and Das Schloss are imported from Sternchenland public-domain EPUBs at https://sternchenland.com/romane/franz-kafka/amerika and https://sternchenland.com/romane/franz-kafka/das-schloss. Amerika includes Der Heizer as its first chapter, so Der Heizer is not counted separately.

Build generated data with:

```bash
python3 build_kafka.py
```

## English dictionary reading aids

For readers without German, a lookup box above the term field finds German words by English meaning and inserts them as search terms; the word views add English and Dictionary form columns. Long pattern headers have hover text and a more/less toggle. Nothing here is searched or counted, and the page works without the data.

Definitions and inflections: English Wiktionary via Kaikki (2026-10-30), CC BY-SA 3.0 / GFDL; see `docs/sources.html`. The pinned extract in `source_text/lexicon/` permits offline builds (`build_kafka.py` writes `docs/data/glossary.json` through `scripts/glossary.py`); regenerate it with `python3 scripts/kaikki_extract.py DICTIONARY.jsonl docs/data/tokens.json source_text/lexicon/wiktionary-extract.json --language de --url https://kaikki.org/dictionary/German/kaikki.org-dictionary-German.jsonl --published 2026-10-30` and update `EXTRACT_SHA256`. Old ß spellings are analysed as their reformed spelling. `docs/js/glossary.js` is shared verbatim with the other non-English Contabulate instances.

