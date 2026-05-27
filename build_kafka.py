#!/usr/bin/env python3
"""Build Contabulate JSON data files for a German Franz Kafka corpus."""

import json
import os
import re
import unicodedata
from collections import Counter, defaultdict


CATALOG_PATH = "CATALOG.json"
OUT_DIR = os.path.join("docs", "data")
LINES_DIR = os.path.join("docs", "lines")

START_RE = re.compile(r"\*\*\*\s*START OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I)
END_RE = re.compile(r"\*\*\*\s*END OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I)

WORK_ABBRS = {
    "betrachtung": "BETR",
    "das-urteil": "URT",
    "amerika": "AMER",
    "die-verwandlung": "VERW",
    "in-der-strafkolonie": "STRAF",
    "ein-landarzt": "LAND",
    "ein-hungerkuenstler": "HUNG",
    "der-mord": "MORD",
    "richard-und-samuel": "RICH",
    "der-prozess": "PROZ",
    "das-schloss": "SCHL",
}

ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
GERMAN_ORDINALS = {
    "ERSTE": 1,
    "ERSTES": 1,
    "ZWEITE": 2,
    "ZWEITES": 2,
    "DRITTE": 3,
    "DRITTES": 3,
    "VIERTE": 4,
    "VIERTES": 4,
    "FÜNFTE": 5,
    "FUENFTE": 5,
    "FÜNFTES": 5,
    "FUENFTES": 5,
    "SECHSTE": 6,
    "SECHSTES": 6,
    "SIEBENTE": 7,
    "SIEBENTES": 7,
    "SIEBTE": 7,
    "SIEBTES": 7,
    "ACHTE": 8,
    "ACHTES": 8,
    "NEUNTE": 9,
    "NEUNTES": 9,
    "ZEHNTE": 10,
    "ZEHNTES": 10,
    "ELFTE": 11,
    "ELFTES": 11,
    "ZWÖLFTE": 12,
    "ZWOELFTE": 12,
    "ZWÖLFTES": 12,
    "ZWOELFTES": 12,
    "DREIZEHNTE": 13,
    "DREIZEHNTES": 13,
    "VIERZEHNTE": 14,
    "VIERZEHNTES": 14,
    "FÜNFZEHNTE": 15,
    "FUENFZEHNTE": 15,
    "FÜNFZEHNTES": 15,
    "FUENFZEHNTES": 15,
    "SECHZEHNTE": 16,
    "SECHZEHNTES": 16,
    "SIEBZEHNTE": 17,
    "SIEBZEHNTES": 17,
    "ACHTZEHNTE": 18,
    "ACHTZEHNTES": 18,
    "NEUNZEHNTE": 19,
    "NEUNZEHNTES": 19,
    "ZWANZIGSTE": 20,
    "ZWANZIGSTES": 20,
}


def load_catalog():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def read_file(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def strip_gutenberg(text):
    start_match = START_RE.search(text)
    start = start_match.end() if start_match else 0
    end_match = END_RE.search(text, start)
    end = end_match.start() if end_match else len(text)
    return text[start:end].strip()


def clean_paragraph(text):
    return re.sub(r"\s+", " ", text).strip()


def paragraphs_from_text(text):
    return [clean_paragraph(p) for p in re.split(r"\n\s*\n", text) if clean_paragraph(p)]


def normalize_token(text):
    return unicodedata.normalize("NFC", text).lower()


def tokenize(text):
    return re.findall(r"[^\W\d_]+(?:[-'][^\W\d_]+)*", normalize_token(text), flags=re.UNICODE)


def build_ngrams(tokens, n):
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def roman_to_int(value):
    total = 0
    previous = 0
    for char in reversed(value.upper().strip(".")):
        current = ROMAN_VALUES[char]
        total = total - current if current < previous else total + current
        previous = max(previous, current)
    return total


def is_mostly_heading(text):
    letters = re.findall(r"[^\W\d_]", text, flags=re.UNICODE)
    if not letters:
        return False
    upper = [ch for ch in letters if ch.upper() == ch and ch.lower() != ch]
    return len(upper) / len(letters) > 0.75


def trim_front_matter(paragraphs):
    skip_patterns = (
        "Produced by",
        "Copyright",
        "Gedruckt",
        "FRANZ KAFKA",
        "KURT WOLFF",
        "ERNST ROWOHLT",
        "VERLAG",
        "Anmerkungen zur Transkription",
    )
    for idx, para in enumerate(paragraphs):
        if any(pattern in para for pattern in skip_patterns):
            continue
        letters = re.findall(r"[^\W\d_]", para, flags=re.UNICODE)
        if len(letters) < 40:
            continue
        if is_mostly_heading(para):
            continue
        return paragraphs[idx:]
    return paragraphs


def make_section(number, label, title, body):
    paragraphs = trim_front_matter(paragraphs_from_text(body))
    return {"number": number, "label": label, "title": title, "paragraphs": paragraphs}


def parse_whole(text, title):
    section = make_section(1, "Text 1", title, text)
    return [section] if section["paragraphs"] else []


def normalize_title_line(text):
    value = clean_paragraph(text)
    value = re.sub(r"\s+\d+\s*$", "", value)
    return value.rstrip(".")


def collect_toc_titles(lines):
    titles = []
    in_toc = False
    for raw in lines[:250]:
        line = raw.strip()
        if line == "INHALT":
            in_toc = True
            continue
        if not in_toc:
            continue
        if not line:
            continue
        if line.startswith("Meinem ") or line.startswith("Für "):
            break
        if titles and not re.search(r"\s+\d+\s*$", line):
            break
        if not re.search(r"\s+\d+\s*$", line):
            continue
        title = normalize_title_line(line)
        if title and re.search(r"[^\W\d_]", title, flags=re.UNICODE):
            titles.append(title)
    return titles


def parse_collection(text, fallback_title):
    lines = text.splitlines()
    titles = collect_toc_titles(lines)
    if not titles:
        return parse_whole(text, fallback_title)

    title_map = {normalize_title_line(title).casefold(): title for title in titles}
    starts = []
    for idx, raw in enumerate(lines):
        key = normalize_title_line(raw.strip()).casefold()
        if key in title_map:
            starts.append((idx, title_map[key]))

    body_starts = []
    seen = set()
    for idx, title in reversed(starts):
        if title not in seen:
            body_starts.append((idx, title))
            seen.add(title)
    starts = sorted(body_starts)

    sections = []
    for pos, (start_idx, title) in enumerate(starts):
        end_idx = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        body = "\n".join(lines[start_idx + 1:end_idx])
        section = make_section(len(sections) + 1, f"Story {len(sections) + 1}", title, body)
        if section["paragraphs"]:
            sections.append(section)
    return sections or parse_whole(text, fallback_title)


def parse_roman_sections(text):
    lines = text.splitlines()
    starts = []
    for idx, raw in enumerate(lines):
        line = raw.strip()
        if re.fullmatch(r"[IVXLCDM]+\.", line):
            starts.append((idx, roman_to_int(line), f"Part {roman_to_int(line)}", ""))
    return build_sections(lines, starts)


def parse_prozess(text):
    lines = text.splitlines()
    starts = []
    for idx, raw in enumerate(lines):
        line = raw.strip().upper()
        match = re.fullmatch(r"([A-ZÄÖÜ]+)\s+KAPITEL", line)
        if not match:
            continue
        number = GERMAN_ORDINALS.get(match.group(1))
        if number:
            starts.append((idx, number, f"Chapter {number}", ""))
    return build_sections(lines, starts)


def parse_german_chapters(text):
    lines = text.splitlines()
    starts = []
    for idx, raw in enumerate(lines):
        line = raw.strip().upper()
        match = re.fullmatch(r"DAS\s+([A-ZÄÖÜ]+)\s+KAPITEL", line)
        if not match:
            continue
        number = GERMAN_ORDINALS.get(match.group(1))
        if number:
            starts.append((idx, number, f"Chapter {number}", ""))
    return build_sections(lines, starts)


def parse_source_chapters(text):
    lines = text.splitlines()
    starts = []
    for idx, raw in enumerate(lines):
        match = re.fullmatch(r"###\s+Chapter\s+(\d+)(?::\s*(.*))?", raw.strip())
        if match:
            number = int(match.group(1))
            title = match.group(2) or ""
            starts.append((idx, number, f"Chapter {number}", title))
    return build_sections(lines, starts)


def build_sections(lines, starts):
    sections = []
    for pos, (start_idx, number, label, inline_title) in enumerate(starts):
        end_idx = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        body_start = start_idx + 1
        title_lines = []
        for idx in range(body_start, min(body_start + 8, end_idx)):
            line = lines[idx].strip()
            if not line:
                if title_lines:
                    body_start = idx + 1
                    break
                continue
            if is_mostly_heading(line):
                title_lines.append(line.title())
                body_start = idx + 1
            else:
                break
        title = inline_title or " · ".join(title_lines)
        body = "\n".join(lines[body_start:end_idx])
        section = make_section(number, label, title, body)
        if section["paragraphs"]:
            sections.append(section)
    return sections


def parse_work_sections(work):
    body = strip_gutenberg(read_file(work["file"]))
    mode = work.get("parse")
    if mode == "collection":
        return parse_collection(body, work["title"])
    if mode == "roman":
        return parse_roman_sections(body) or parse_whole(body, work["title"])
    if mode == "prosecuted":
        return parse_prozess(body) or parse_whole(body, work["title"])
    if mode == "german_chapters":
        return parse_german_chapters(body) or parse_whole(body, work["title"])
    if mode == "source_chapters":
        return parse_source_chapters(body) or parse_whole(body, work["title"])
    return parse_whole(body, work["title"])


def dump_json(path, value):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, separators=(",", ":"))


def build_json_corpus(catalog):
    plays = []
    chunks = []
    lines = []
    tokens1 = defaultdict(list)
    tokens2 = defaultdict(list)
    tokens3 = defaultdict(list)
    per_work_stats = []
    total_words = 0
    total_paragraphs = 0
    unique_unigrams = set()
    unique_bigrams = set()
    unique_trigrams = set()
    scene_id = 0

    for play_id, work in enumerate(catalog, start=1):
        sections = parse_work_sections(work)
        if not sections:
            raise ValueError(f"No sections found for {work['title']}")

        play_abbr = WORK_ABBRS.get(work["id"], re.sub(r"[^A-ZÄÖÜ]", "", work["title"].upper())[:6] or f"W{play_id}")
        play_location = f"{play_id:02d}.{play_abbr}"
        work_total_words = 0
        work_total_lines = 0

        for section in sections:
            section_num = section["number"]
            act_label = section["title"] or section["label"]
            for para_idx, para in enumerate(section["paragraphs"], start=1):
                scene_id += 1
                words = tokenize(para)
                unigram_counts = Counter(words)
                bigram_counts = Counter(build_ngrams(words, 2))
                trigram_counts = Counter(build_ngrams(words, 3))
                word_count = len(words)
                canonical_id = f"{play_abbr}.{section_num}.{para_idx}"
                location = f"{play_location}.{section_num:03d}.{para_idx:04d}"

                chunks.append({
                    "scene_id": scene_id,
                    "canonical_id": canonical_id,
                    "location": location,
                    "play_id": play_id,
                    "play_title": work["title"],
                    "play_abbr": play_abbr,
                    "genre": work["genre"],
                    "act": section_num,
                    "scene": para_idx,
                    "heading": f"{act_label}, {para_idx}",
                    "total_words": word_count,
                    "unique_words": len(unigram_counts),
                    "num_speeches": 0,
                    "num_lines": 1,
                    "characters_present_count": 0,
                    "act_label": act_label,
                    "scene_label": str(para_idx),
                })
                lines.append({
                    "play_id": play_id,
                    "canonical_id": canonical_id,
                    "location": location,
                    "act": section_num,
                    "scene": para_idx,
                    "line_num": para_idx,
                    "speaker": "",
                    "text": para,
                    "act_label": act_label,
                    "scene_label": str(para_idx),
                })

                for token, count in unigram_counts.items():
                    tokens1[token].append([scene_id, count])
                for token, count in bigram_counts.items():
                    tokens2[token].append([scene_id, count])
                for token, count in trigram_counts.items():
                    tokens3[token].append([scene_id, count])

                unique_unigrams.update(unigram_counts)
                unique_bigrams.update(bigram_counts)
                unique_trigrams.update(trigram_counts)
                work_total_words += word_count
                work_total_lines += 1
                total_words += word_count
                total_paragraphs += 1

        plays.append({
            "play_id": play_id,
            "location": play_location,
            "title": work["title"],
            "abbr": play_abbr,
            "genre": work["genre"],
            "first_performance_year": work["year"],
            "num_acts": len(sections),
            "num_scenes": work_total_lines,
            "num_speeches": 0,
            "total_words": work_total_words,
            "total_lines": work_total_lines,
        })
        per_work_stats.append({
            "title": work["title"],
            "year": work["year"],
            "sections": len(sections),
            "paragraphs": work_total_lines,
            "words": work_total_words,
        })

    return {
        "plays": plays,
        "chunks": chunks,
        "lines": lines,
        "tokens": dict(tokens1),
        "tokens2": dict(tokens2),
        "tokens3": dict(tokens3),
        "per_work_stats": per_work_stats,
        "totals": {
            "works": len(plays),
            "paragraphs": total_paragraphs,
            "lines": len(lines),
            "words": total_words,
            "unique_unigrams": len(unique_unigrams),
            "unique_bigrams": len(unique_bigrams),
            "unique_trigrams": len(unique_trigrams),
        },
    }


def write_outputs(data):
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(LINES_DIR, exist_ok=True)
    dump_json(os.path.join(OUT_DIR, "plays.json"), data["plays"])
    dump_json(os.path.join(OUT_DIR, "chunks.json"), data["chunks"])
    dump_json(os.path.join(OUT_DIR, "tokens.json"), data["tokens"])
    dump_json(os.path.join(OUT_DIR, "tokens2.json"), data["tokens2"])
    dump_json(os.path.join(OUT_DIR, "tokens3.json"), data["tokens3"])
    dump_json(os.path.join(OUT_DIR, "characters.json"), [])
    dump_json(os.path.join(OUT_DIR, "tokens_char.json"), {})
    dump_json(os.path.join(OUT_DIR, "tokens_char2.json"), {})
    dump_json(os.path.join(OUT_DIR, "tokens_char3.json"), {})
    dump_json(os.path.join(OUT_DIR, "character_name_filter_config.json"), {"plays": {}})
    dump_json(os.path.join(LINES_DIR, "all_lines.json"), data["lines"])


def main():
    data = build_json_corpus(load_catalog())
    write_outputs(data)
    for work in data["per_work_stats"]:
        print(f"{work['title']} ({work['year']}): {work['sections']} sections, {work['paragraphs']} paragraphs, {work['words']:,} words")
    totals = data["totals"]
    print(f"Works: {totals['works']}")
    print(f"Paragraphs: {totals['paragraphs']}")
    print(f"Lines: {totals['lines']}")
    print(f"Total words: {totals['words']:,}")
    print(f"Unique unigrams: {totals['unique_unigrams']:,}")
    print(f"Unique bigrams: {totals['unique_bigrams']:,}")
    print(f"Unique trigrams: {totals['unique_trigrams']:,}")


if __name__ == "__main__":
    main()
