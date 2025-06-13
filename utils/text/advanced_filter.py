# utils/advanced_filter.py

import re
import string
from nltk.stem.snowball import PortugueseStemmer
from nltk.corpus import stopwords
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import difflib

class FiltroAvancado:
    def __init__(self, palavras_globais=None, top_n=5):
        self.palavras_globais = palavras_globais or {}
        self.stemmer = PortugueseStemmer()
        self.indices = {}           # seções: {id: texto}
        self.tfidf = None           # TF-IDF vectorizer
        self.tfidf_matrix = None    # matriz de representações
        self.section_ids = []
        self.top_n = top_n
        # Carrega stop words em português do NLTK
        try:
            self.portuguese_stopwords = stopwords.words('portuguese')
        except LookupError:
            import nltk
            nltk.download('stopwords')
            self.portuguese_stopwords = stopwords.words('portuguese')

    def limpar_texto(self, texto):
        txt = texto.lower()
        return txt.translate(str.maketrans('', '', string.punctuation))

    def stem_palavras(self, texto):
        palavras = self.limpar_texto(texto).split()
        return [self.stemmer.stem(p) for p in palavras]

    def expandir_termos(self, termos):
        expandidos = set(termos)
        for termo in termos:
            if termo in self.palavras_globais:
                definicao = self.palavras_globais[termo]
                for w in self.limpar_texto(definicao).split():
                    expandidos.add(w)
        return list(expandidos)

    def indexar_texto(self, markdown_text):
        # separa por headings (#...)
        self.indices.clear()
        self.section_ids.clear()
        lines = markdown_text.splitlines()
        current_id = 'GLOBAL'
        buffer = []
        def flush_section(sec_id):
            if sec_id and buffer:
                content = '\n'.join(buffer).strip()
                self.indices[sec_id] = content
                self.section_ids.append(sec_id)
        for line in lines:
            m = re.match(r'^(#{1,6})\s*(.+)', line)
            if m:
                flush_section(current_id)
                current_id = m.group(2).strip()
                buffer = []
            else:
                buffer.append(line)
        flush_section(current_id)
        # cria TF-IDF com stop words em português
        texts = [self.indices[sid] for sid in self.section_ids]
        self.tfidf = TfidfVectorizer(stop_words=self.portuguese_stopwords)
        self.tfidf_matrix = self.tfidf.fit_transform(texts)

    def calcula_score(self, texto, termos_query):
        stems = set(self.stem_palavras(texto))
        score = sum(1 for t in termos_query if t in stems)
        interrog = {'quem','quando','onde','como','qual','porquê','porque'}
        score += len(stems & interrog)
        for t in termos_query:
            for word in self.limpar_texto(texto).split():
                if difflib.SequenceMatcher(None, t, word).ratio() > 0.8:
                    score += 0.5
        return score

    def busca_avancada(self, texto_completo, query):
        if not self.indices or not self.tfidf:
            self.indexar_texto(texto_completo)
        stems = self.stem_palavras(query)
        termos = self.expandir_termos(stems)
        q_vec = self.tfidf.transform([query])
        sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        combined = []
        for idx, sid in enumerate(self.section_ids):
            text = self.indices[sid]
            scr = self.calcula_score(text, termos)
            tfidf_scr = sims[idx]
            total = scr + tfidf_scr
            combined.append((sid, total))
        top = sorted(combined, key=lambda x: x[1], reverse=True)[:self.top_n]
        resultados = []
        for sid, _ in top:
            txt = self.indices[sid]
            for t in termos:
                regex = re.compile(re.escape(t), re.IGNORECASE)
                txt = regex.sub(lambda m: f'<mark>{m.group(0)}</mark>', txt)
            resultados.append(f"## {sid}\n\n{txt}")
        return resultados
