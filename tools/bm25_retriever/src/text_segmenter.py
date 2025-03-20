from typing import List, Dict, Any
import re
from io import StringIO
import csv

class DocumentChunk:
    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}

class TextSegmenter:
    def __init__(self):
        # 句子分割
        self.sentence_pattern = re.compile(r'(?<=[。！？]) +|(?<=[.!?]) +')
        # 章节分割
        self.chapter_pattern = re.compile(
            r"""(?mx)^[\u3000\s]*  # 匹配行首可能存在的空格或全角空格
            (?:  # 非捕获组开始
                # 中文章节格式（支持更多单位词）
                (?:第\s*[一二三四五六七八九十百千万零〇]+?\s*[章节卷集部篇回]) |
                (?:第\s*\d+\s*[章节卷集部篇回]) |
                # 英文章节格式（支持罗马数字）
                (?:Chapter\s+[IVXLCDMivxlcdm]+\b) |
                (?:Chapter\s+\d+) |
                # 法律条文格式
                (?:§\s*\d+\.\d+) |
                # 特殊章节标识（如楔子、尾声）
                (?:[【〖]?(?:序幕|楔子|终章|尾声|后记)[】〗]?) |
                # 带修饰符的章节（如★第一章★）
                (?:[★☆◆■]?\s*第\s*[\d〇一二三四五六七八九十百千万]+\s*章\s*[★☆◆■]?) |
                # 多级标题（如第二卷 第三章）
                (?:(?:第\s*[一二三四五六七八九十百千万]+\s*[卷部])\s*第\s*[一二三四五六七八九十百千万]+\s*章)
            )  # 非捕获组结束
            [\u3000\s]*  # 标题后的空白
            [：:.、\-—]?  # 允许存在的分隔符
            [\u3000\s]*  # 分隔符后的空白
            .+?  # 章节标题内容
            (?=\n|$)  # 章节标题结束位置
            """,
            flags=re.MULTILINE
        )
        self.chapter_pattern = re.compile(
            r'(?m)^\s*(?:(?:第\s*[一二三四五六七八九十百千万零〇]+\s*[章节卷集部篇回])|(?:第\s*\d+\s*[章节卷集部篇回])|(?:Chapter\s+[IVXLCDMivxlcdm]+\b)|(?:Chapter\s+\d+)|(?:§\s*\d+\.\d+)|(?:[【〖]?(?:序幕|楔子|终章|尾声|后记)[】〗]?)|(?:[★☆◆■]?\s*第\s*[\d〇一二三四五六七八九十百千万]+\s*章\s*[★☆◆■]?)|(?:(?:第\s*[一二三四五六七八九十百千万]+\s*[卷部])\s*第\s*[一二三四五六七八九十百千万]+\s*章))\s*[：:.、\-—]?\s*.+?(?=\n|$)',
            flags=re.MULTILINE
        )
        # Markdown标题分割
        self.markdown_header_pattern = re.compile(r'^#{1,6}\s+.+', re.MULTILINE)
        # 电子邮件分割
        self.email_pattern = re.compile(
            r'(From:.+?\nTo:.+?\nSubject:.+?)\n{2,}(.*)',
            re.DOTALL
        )
        # 社交媒体内容分割
        self.social_media_pattern = re.compile(
            r'(#\w+|@\w+|https?://\S+|[\U0001F600-\U0001F64F])'
        )
        # 数学公式分割
        self.equation_pattern = re.compile(
            r'\$(.*?)\$|\\begin{equation}(.*?)\\end{equation}',
            re.DOTALL
        )
    
    def _handle_overlap(self, chunks: List[DocumentChunk], overlap: int, overlap_seg: str = "") -> List[DocumentChunk]:
        if overlap > 0 and chunks:
            # 获取最后一段的内容
            last_chunk = chunks[-1]
            # 获取重叠部分
            overlap_chunk = chunks[-overlap-1:-1] if len(chunks) > overlap else chunks[:-1]
            # 将重叠部分的内容添加到当前段落的开头
            for overlap_row in overlap_chunk:
                last_chunk.content = overlap_row.content + overlap_seg + last_chunk.content
        return chunks
    
    # 细粒度检索
    def split_text(self, texts: List[str], max_len: int = 61, overlap: int = 0) -> List[DocumentChunk]:
        result = []
        for text in texts:
            punctuation_pattern = re.compile(r'[,.!?/#$%^&*()_+{}~。|:"！？｡＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～]+')
            words = text.split()
            current_chunk = []
            current_length = 0

            for word in words:
                if current_length + len(word) + len(punctuation_pattern.findall(word)) > max_len:
                    result.append(''.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                current_chunk.append(word)
                current_length += len(word) + len(punctuation_pattern.findall(word))
            if current_chunk:
                result.append(''.join(current_chunk))
        return [DocumentChunk(content=chunk) for chunk in result]

    def split_by_paragraph(self, texts: List[str], max_len: int = 500, overlap: int = 0) -> List[DocumentChunk]:
        """段落分割"""
        chunks = []
        for text in texts:
            paragraphs = text.split('\n')
            for paragraph in paragraphs:
                if len(paragraph) > max_len:
                    # 使用 split_text 方法进行分割
                    sub_chunks = self.split_text([paragraph], max_len)
                    chunks.extend(sub_chunks)
                else:
                    # 细粒度检索
                    if paragraph.strip():
                        chunks.append(DocumentChunk(content=paragraph.strip(), metadata={"type": "paragraph"}))
            # 每个chunk应该和迁移个chunk重叠
            self._handle_overlap(chunks, overlap, overlap_seg="\n")
        return chunks

    def split_by_sentence(self, texts: List[str], max_len: int = 500, overlap: int = 0) -> List[DocumentChunk]:
        """句子分割"""
        chunks = []
        for text in texts:
            sentences = self.sentence_pattern.split(text)
            current_chunk = []
            for sentence in sentences:
                if current_chunk and len(' '.join(current_chunk)) + len(sentence) > max_len:
                    chunks.append(DocumentChunk(content=' '.join(current_chunk)))
                    current_chunk = current_chunk[-overlap:]  # 保留重叠部分
                current_chunk.append(sentence.strip())
            # 每个chunk应该和迁移个chunk重叠
            self._handle_overlap(chunks, overlap, overlap_seg="")
        return chunks

    def split_by_chapter(self, texts: List[str], max_len: int = 500, overlap: int = 0) -> List[DocumentChunk]:
        """章节分割"""
        chunks = []
        for text in texts:
            last_pos = 0
            for match in self.chapter_pattern.finditer(text):
                start = match.start()
                if start > last_pos:
                    chapter_content = text[last_pos:start]
                    # 检查章节内容长度，如果超过 max_len 则进行分割
                    if len(chapter_content) > max_len:
                        sub_chunks = self.split_text([chapter_content], max_len)
                        chunks.extend(sub_chunks)
                    else:
                        chunks.append(DocumentChunk(content=chapter_content, metadata={"type": "chapter_content"}))
                chapter_title = match.group().strip()
                chunks.append(DocumentChunk(content=chapter_title, metadata={"type": "chapter_title"}))
                last_pos = match.end()
            if last_pos < len(text):
                chapter_content = text[last_pos:]
                # 检查最后一部分的长度
                if len(chapter_content) > max_len:
                    sub_chunks = self.split_text([chapter_content], max_len)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(DocumentChunk(content=chapter_content, metadata={"type": "chapter_content"}))
            # 每个chunk应该和迁移个chunk重叠
            self._handle_overlap(chunks, overlap, overlap_seg="\n")
        return chunks

    def split_by_markdown(self, texts: List[str], max_len: int = 500, overlap: int = 0) -> List[DocumentChunk]:
        """Markdown标题层级分割"""
        chunks = []
        for text in texts:
            lines = text.split('\n')
            for line in lines:
                if self.markdown_header_pattern.match(line):
                    chunks.append(DocumentChunk(content=line.strip(), metadata={"type": "markdown_header"}))
                else:
                    # 检查文本长度，如果超过 max_len 则进行分割
                    if len(line.strip()) > max_len:
                        sub_chunks = self.split_text([line], max_len)
                        chunks.extend(sub_chunks)
                    else:
                        chunks.append(DocumentChunk(content=line.strip(), metadata={"type": "text"}))
            # 每个chunk应该和迁移个chunk重叠
            self._handle_overlap(chunks, overlap, overlap_seg="\n\n")
        return chunks

    def split_emails(self, texts: List[str], max_len: int = 500, overlap: int = 0) -> List[DocumentChunk]:
        """电子邮件分割（支持MIME格式）"""
        chunks = []
        for text in texts:
            for match in self.email_pattern.finditer(text):
                header, body = match.groups()
                # 检查标题长度，如果超过 max_len 则进行分割
                if len(header) > max_len:
                    sub_chunks = self.split_text([header], max_len)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(DocumentChunk(content=header, metadata={"type": "email_header"}))
                # 检查正文长度，如果超过 max_len 则进行分割
                if len(body) > max_len:
                    sub_chunks = self.split_text([body], max_len)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(DocumentChunk(content=body, metadata={"type": "email_body"}))
            # 每个chunk应该和迁移个chunk重叠
            self._handle_overlap(chunks, overlap, overlap_seg="\n")
        return chunks

    def split_social_media(self, texts: List[str], max_len: int = 500, overlap: int = 0) -> List[DocumentChunk]:
        """社交媒体内容分割（识别话题标签、表情符号等）"""
        chunks = []
        for text in texts:
            last_end = 0
            for match in self.social_media_pattern.finditer(text):
                start = match.start()
                if start > last_end:
                    social_media_content = text[last_end:start]
                    # 检查社交媒体内容长度，如果超过 max_len 则进行分割
                    if len(social_media_content) > max_len:
                        sub_chunks = self.split_text([social_media_content], max_len)
                        chunks.extend(sub_chunks)
                    else:
                        chunks.append(DocumentChunk(content=social_media_content, metadata={"type": "text"}))
                entity = match.group()
                entity_type = "hashtag" if entity.startswith('#') else \
                            "mention" if entity.startswith('@') else \
                            "emoji" if re.match(r'[\U0001F600-\U0001F64F]', entity) else \
                            "link"
                chunks.append(DocumentChunk(content=entity, metadata={"type": entity_type}))
                last_end = match.end()
            if last_end < len(text):
                remaining_content = text[last_end:]
                # 检查剩余内容长度
                if len(remaining_content) > max_len:
                    sub_chunks = self.split_text([remaining_content], max_len)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(DocumentChunk(content=remaining_content, metadata={"type": "text"}))
            # 每个chunk应该和迁移个chunk重叠
            self._handle_overlap(chunks, overlap, overlap_seg="\n")
        return chunks


    def split_equations(self, texts: List[str], max_len: int = 500, overlap: int = 0) -> List[DocumentChunk]:
        """数学公式分割（支持LaTeX和行内公式）"""
        chunks = []
        for text in texts:
            last_end = 0
            for match in self.equation_pattern.finditer(text):
                start = match.start()
                if start > last_end:
                    equation_content = text[last_end:start]
                    # 检查公式内容长度，如果超过 max_len 则进行分割
                    if len(equation_content) > max_len:
                        sub_chunks = self.split_text([equation_content], max_len)
                        chunks.extend(sub_chunks)
                    else:
                        chunks.append(DocumentChunk(content=equation_content, metadata={"type": "text"}))
                equation = match.group(1) or match.group(2)
                chunks.append(DocumentChunk(content=equation, metadata={"type": "equation"}))
                last_end = match.end()
            if last_end < len(text):
                remaining_content = text[last_end:]
                # 检查剩余内容长度
                if len(remaining_content) > max_len:
                    sub_chunks = self.split_text([remaining_content], max_len)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(DocumentChunk(content=remaining_content, metadata={"type": "text"}))
            # 每个chunk应该和迁移个chunk重叠
            self._handle_overlap(chunks, overlap, overlap_seg="")
        return chunks

    def split_csv(self, texts: List[str], max_len: int = 500, overlap: int = 0, has_header: bool = False) -> List[DocumentChunk]:
        """CSV内容分割，确保正确处理标题和数据行"""
        # 对于表格处理困难,可能需要更复杂的逻辑
        chunks = []
        for text in texts:
            # 使用 StringIO 将文本转换为文件对象
            f = StringIO(text)
            reader = csv.reader(f)
            # 读取标题行
            if has_header:
                headers = next(reader, None)
                if headers:
                    # 将标题行作为一个 DocumentChunk
                    chunks.append(DocumentChunk(content=','.join(headers), metadata={"type": "csv_header"}))
            # 读取数据行
            for row in reader:
                if row:  # 确保行不为空
                    chunks.append(DocumentChunk(content=','.join(row), metadata={"type": "csv_row"}))
            # 每个chunk应该和迁移个chunk重叠
            self._handle_overlap(chunks, overlap, overlap_seg="\n")
        return chunks

    def split_html(self, texts: List[str], max_len: int = 500, overlap: int = 0) -> List[DocumentChunk]:
        def __handle_overlap_html(chunks: List[DocumentChunk], overlap: int, overlap_seg: str = "") -> List[DocumentChunk]:
            if overlap > 0 and chunks:
                last_chunk = chunks[-1]
                # 获取重叠部分
                overlap_chunk = chunks[-overlap-1:-1] if len(chunks) > overlap else chunks[:-1]
                # 将重叠部分的内容添加到当前段落的开头
                overlap_content = overlap_seg.join(chunk.content for chunk in overlap_chunk)
                last_chunk.content = overlap_content + overlap_seg + last_chunk.content
                return chunks
        """HTML内容分割"""
        from bs4 import BeautifulSoup
        chunks = []
        for text in texts:
            soup = BeautifulSoup(text, 'html.parser')
            for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'table']):
                # 检查内容长度，如果超过 max_len 则进行分割
                content = element.get_text(strip=True)
                if len(content) > max_len:
                    sub_chunks = self.split_text([content], max_len)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(DocumentChunk(content=content, metadata={"type": "html"}))
            # 每个chunk应该和迁移个chunk重叠
            self._handle_overlap(chunks, overlap, overlap_seg="\n")
        return chunks

    def split_xml(self, texts: List[str], max_len: int = 500, overlap: int = 0) -> List[DocumentChunk]:
        """XML内容分割"""
        import xml.etree.ElementTree as ET
        chunks = []
        for text in texts:
            root = ET.fromstring(text)
            for elem in root.iter():
                # 检查内容长度，如果超过 max_len 则进行分割
                content = elem.text.strip() if elem.text else ''
                if len(content) > max_len:
                    sub_chunks = self.split_text([content], max_len)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(DocumentChunk(content=content, metadata={"type": "xml"}))
            # 每个chunk应该和迁移个chunk重叠
            self._handle_overlap(chunks, overlap, overlap_seg="\n")
        return chunks

    def split_code(self, texts: List[str], max_len: int = 500, overlap: int = 0) -> List[DocumentChunk]:
        """代码块分割，支持可选语言标识"""
        chunks = []
        for text in texts:
            # 使用正则表达式匹配代码块，假设代码块用 ``` 包裹，支持可选语言标识
            code_blocks = re.findall(r'```(\w+)?\n(.*?)```', text, re.DOTALL)
            for lang, code in code_blocks:
                # 如果有语言标识，可以将其包含在元数据中
                lang = lang if lang else "plaintext"  # 默认语言为 plaintext
                # 检查内容长度，如果超过 max_len 则进行分割
                if len(code) > max_len:
                    sub_chunks = self.split_text([code], max_len)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(DocumentChunk(content=code.strip(), metadata={"type": "code", "language": lang}))
            # 每个chunk应该和迁移个chunk重叠
            self._handle_overlap(chunks, overlap, overlap_seg="\n")
        return chunks

    def segment(self, texts: List[str], mode: str = 'auto', overlap: int = 0) -> List[DocumentChunk]:
        """
        智能分段入口
        :param texts: 输入文本列表
        :param mode: 分割模式 (auto/para/sentence/chapter/md/email/social/equation/code/csv/html/xml)
        :param overlap: 重叠度
        """
        if mode == 'paragraph':
            return self.split_by_paragraph(texts, overlap)
        elif mode == 'sentence':
            return self.split_by_sentence(texts, overlap)
        elif mode == 'chapter':
            return self.split_by_chapter(texts, overlap)
        elif mode == 'markdown':
            return self.split_by_markdown(texts, overlap)
        elif mode == 'email':
            return self.split_emails(texts, overlap)
        elif mode == 'social':
            return self.split_social_media(texts, overlap)
        elif mode == 'equation':
            return self.split_equations(texts, overlap)
        elif mode == 'code':
            return self.split_code(texts, overlap)
        elif mode == 'csv':
            return self.split_csv(texts, overlap)
        elif mode == 'html':
            return self.split_html(texts, overlap)
        elif mode == 'xml':
            return self.split_xml(texts, overlap)
        else:
            # 默认使用段落分割
            return self.split_by_paragraph(texts, overlap)

if __name__ == '__main__':
    segmenter = TextSegmenter()
    documents = [
        "第一段文本。\n第二段文本。\n第三段文本。",
        "第1章 引言\n本章介绍研究背景...\n第2章 相关工作\n介绍相关研究。",
        "# 标题1\n内容1\n## 标题2\n内容2",
        "From: example@example.com\nTo: recipient@example.com\nSubject: Test Email\n\n这是邮件正文。",
        "这是社交媒体内容 #话题 @用户 https://example.com",
        "这是一个数学公式：$E=mc^2$ 和 \\begin{equation} a^2 + b^2 = c^2 \\end{equation}",
        "name,age\nAlice,30\nBob,25",
        "<p>这是一个段落。</p><h1>标题</h1>",
        "<root><item>内容1</item><item>内容2</item></root>",
        "```python\nprint('Hello, World!')\n```"
    ]
    
    # 段落分割示例
    paragraph_chunks = segmenter.segment(documents, mode='paragraph', overlap=1)
    for chunk in paragraph_chunks:
        print(f"Paragraph: {chunk.content}")

    # 句子分割示例
    sentence_chunks = segmenter.segment(documents, mode='sentence', overlap=1)
    for chunk in sentence_chunks:
        print(f"Sentence: {chunk.content}")

    # 章节分割示例
    chapter_chunks = segmenter.segment(documents, mode='chapter', overlap=1)
    for chunk in chapter_chunks:
        print(f"Chapter: {chunk.content}")

    # Markdown分割示例
    markdown_chunks = segmenter.segment(documents, mode='markdown', overlap=1)
    for chunk in markdown_chunks:
        print(f"Markdown: {chunk.content}")

    # 电子邮件分割示例
    email_chunks = segmenter.segment(documents, mode='email', overlap=1)
    for chunk in email_chunks:
        print(f"Email: {chunk.content}")

    # 社交媒体分割示例
    social_chunks = segmenter.segment(documents, mode='social', overlap=1)
    for chunk in social_chunks:
        print(f"Social Media: {chunk.content}")

    # 数学公式分割示例
    equation_chunks = segmenter.segment(documents, mode='equation', overlap=1)
    for chunk in equation_chunks:
        print(f"Equation: {chunk.content}")
