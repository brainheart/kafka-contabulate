import json, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class GlossaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=json.loads((ROOT/'docs/data/glossary.json').read_text())
        cls.tokens=json.loads((ROOT/'docs/data/tokens.json').read_text())
    def test_counts_and_forms(self):
        self.assertEqual(set(self.g['forms']),set(self.tokens))
        for e in self.g['lemmas']:
            self.assertEqual(e['n'],sum(n for f,n in e['forms']))
            for f,n in e['forms']:
                self.assertEqual(n,sum(x[1] for x in self.tokens[f]))
    def test_german_homographs_and_auxiliaries(self):
        be=next(e for e in self.g['lemmas'] if e['lemma']=='sein' and e['pos']=='verb')
        his=next(e for e in self.g['lemmas'] if e['lemma']=='sein' and e['pos']=='determiner')
        self.assertIn('ist',dict(be['forms']))
        self.assertNotIn('seine',dict(be['forms']))
        self.assertIn('seine',dict(his['forms']))
        self.assertNotIn('ist',dict(his['forms']))
        self.assertNotIn('eure',dict(his['forms']))
        self.assertEqual(be['def'],'to be')
        from scripts.glossary import load_extract, lookup
        extract=load_extract(ROOT/'source_text/lexicon/wiktionary-extract.json')
        self.assertNotIn(('fallen','verb'),lookup('sein',extract))
        self.assertIn(('sein','verb'),lookup('sein',extract))
        self.assertIn(('sein','det'),lookup('sein',extract))
    def test_old_spellings_count_as_their_reformed_spelling(self):
        lemmas=self.g['lemmas']
        def first(form):
            return lemmas[self.g['forms'][form][2][0]]['lemma']
        self.assertEqual(first('schloß'),'Schloss')   # the castle, Kafka's most frequent noun use
        self.assertEqual(first('muß'),'müssen')
        self.assertEqual(first('daß'),'dass')
        self.assertEqual(first('prozeß'),'Prozess')
        self.assertEqual(first('mußte'),'müssen')
    def test_coverage(self):
        c=self.g['coverage']
        self.assertGreater(1-c['words_without_lemma']/c['words'],0.94)
