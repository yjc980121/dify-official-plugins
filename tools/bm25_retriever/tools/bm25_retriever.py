from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from src.retriever import Retriever
from src.text_segmenter import TextSegmenter

 

class Bm25RetrieverTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        query = tool_parameters.get("query", "")
        if not query:
            yield self.create_text_message("Please input query")
        text = tool_parameters.get("text", "")
        if not text:
            yield self.create_text_message("Please input text")
        segment_method = tool_parameters.get("segment_method", "paragraph")
        if segment_method not in ["paragraph", "sentence", "chapter", "markdown", "email", "social", "equation", "code", "csv", "html", "xml"]:
            yield self.create_text_message("Invalid segment method")
        overlap = tool_parameters.get("overlap", 0)
        if overlap < 0:
            yield self.create_text_message("Invalid overlap")
        top_k = tool_parameters.get("top_k", 10)
        if top_k < 0:
            yield self.create_text_message("Invalid top_k")
        
        segmenter = TextSegmenter()
        retriever = Retriever()
        retriever.set_method('bm25')
        
        segmented_documents = segmenter.segment([text], mode=segment_method, overlap=overlap)
        retrieved_results = retriever.retrieve(query, [doc.content for doc in segmented_documents], top_k=top_k)
        yield self.create_json_message({
            "result": retrieved_results,
            "segmented_documents": [doc.content for doc in segmented_documents]
        })
