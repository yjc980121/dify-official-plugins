from .text_segmenter import TextSegmenter
from rank_bm25 import BM25Okapi
# import jieba
import thulac
import MicroTokenizer

from typing import List, Dict, Any

class Retriever:
    def __init__(self, method='bm25'):
        self.method = method
        self.segmenter = TextSegmenter()

    def set_method(self, method):
        self.method = method

    def retrieve(self, query: str, documents: List[str], top_k: int = 10) -> List[str]:
        segmented_documents = self.segmenter.split_by_paragraph(documents)
        if self.method == 'bm25':
            return self._bm25_retrieve(query, segmented_documents, top_k)
        # 可以在这里添加其他检索方法
        else:
            raise ValueError(f'Unsupported retrieval method: {self.method}')

    def _bm25_retrieve(self, query, documents, top_k=10):
        """
        :param query: 传入的问题  实际操作中 问题很短的时候可以用llm进行补全
        :param documents:  传入的文档列表 就是 当前知识库所有的数据文档  如果数据很多的时候 例如 超过10000个文档片段 可以进行分批次查询 每次查询top_k个文档   然后进行合并查询
        :param top_k:
        :return:
        """
        if not query or not documents:
            return []
        # thu1 = thulac.thulac()
        # tokenized_corpus = [list(jieba.cut(doc.content)) for doc in documents]
        # tokenized_corpus = [list(thu1.cut(doc.content)) for doc in documents]
        tokenized_corpus = [list(MicroTokenizer.cut(doc.content)) for doc in documents]
        bm25 = BM25Okapi(tokenized_corpus)
        # tokenized_query = list(jieba.cut(query))
        #tokenized_query = list(thu1.cut(query))
        tokenized_query = list(MicroTokenizer.cut(query))
        top = bm25.get_top_n(tokenized_query, [doc.content for doc in documents], n=top_k)
        return top
