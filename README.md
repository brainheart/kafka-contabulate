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
