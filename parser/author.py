import re
import datetime

class AuthorParser:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.authors = []
        self.current_author = None
        self.patterns = {
            'author': re.compile(r'\\author(\[[^\]]*\])?{(.*?)}', re.DOTALL),
            'affil': re.compile(r'\\affil{((?:[^{}]|\{[^{}]*\})*)}', re.DOTALL),
            'date': re.compile(r'\\date{(.*?)}', re.DOTALL)
        }
    
    def parse_line(self, line):
        # 处理作者信息
        author_match = self.patterns['author'].search(line)
        if author_match:
            if self.current_author:
                self.authors.append(self.current_author)
            self.current_author = {
                'name': self._clean_content(author_match.group(2)),
                'affils': []
            }
            return True

        # 处理机构信息
        affil_match = self.patterns['affil'].search(line)
        if affil_match and self.current_author:
            affil = self._clean_content(affil_match.group(1))
            self.current_author['affils'].append(affil)
            return True

        # 处理日期信息
        date_match = self.patterns['date'].search(line)
        if date_match:
            self.date = self._clean_content(date_match.group(1))
            return True

        return False

    def finalize(self):
        if self.current_author:
            self.authors.append(self.current_author)
        return self.authors, getattr(self, 'date', None)

    def _clean_content(self, text):
        # 处理顺序优化（从内到外）
        patterns = [
            (r'\\small\s*', ''),         # 先处理内部命令
            (r'\\textit{(.*?)}', r'\1'), # 非贪婪匹配内容
            (r'\\today', self._get_date),# 动态处理日期
            (r'\s+', ' ')                # 压缩多余空格
        ]
        
        for pattern, repl in patterns:
            if callable(repl):
                text = re.sub(pattern, repl, text, flags=re.DOTALL)
            else:
                text = re.sub(pattern, repl, text)
        
        return text.strip()

    def _get_date(self, match):
        return datetime.date.today().strftime('%Y-%m-%d')