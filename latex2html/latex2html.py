import re
import html


class Latex2Html:
    def __init__(self):
        self.text = ''
        self.protected_equations = {}
        self.script = """
    <script type='text/javascript' async src='https://polyfill.io/v3/polyfill.min.js?features=es6'></script>
    <script type='text/javascript' id='MathJax-script' async src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'></script>"""
        
        self.command_handlers = {
            'textbf': self.handle_bold,
            'textit': self.handle_italic,
            'section': self.handle_section,
            'subsection': self.handle_subsection,
            'subsubsection': self.handle_subsubsection,
            'cite': self.handle_cite,
            'label': self.handle_label,
            'ref': self.handle_ref,
        }
        
        self.environment_handlers = {
            'enumerate': self.handle_enumerate,
            'itemize': self.handle_itemize,
            'abstract': self.handle_abstract,
            'figure': self.handle_figure,
            'algorithm': self.handle_algorithm,
            #'table': self.handle_tables,
        }
        
        self.idle_handlers = [
            'maketitle',
            'centering',
            'hline',
        ]

    def convert(self, latex_content):
        self.text = latex_content
        self.process_comments()
        self.protect_equations()
        self.parse_latex()
        self.restore_equations()
        self.process_inline_math()
        self.process_block_math()
        return self.text

    def parse_latex(self):
        document_match = re.search(r'\\begin{document}(.*)\\end{document}', self.text, flags=re.DOTALL)
        if document_match:
            self.text = document_match.group(1)
            self.process_document_content()
            self.wrap_html()

    def wrap_html(self):
        self.text = f"""<!DOCTYPE html>
<html>
  <head>
    <title>Converted Document</title>
    {self.script}
  </head>
<body>
{self.text}
</body>
</html>"""

    def process_document_content(self):
        
        self.process_environments()
        self.process_commands()
        self.handle_tables()
        
        self.handle_paragraphs()
        #self.escape_remaining_text()
        self.process_idle_conmmands()
        self.replace_special_chars()
        self.cleanup()
        
    def process_inline_math(self):
        self.text = re.sub(r'\\\((.*?)\\\)', r'<span class="math">\\(\1\\)</span>', self.text)
        self.text = re.sub(r'\$(.*?)\$', r'<span class="math">\\(\1\\)</span>', self.text)


    def process_block_math(self):
        self.text = re.sub(r'\\\[(.*?)\\\]', r'<div class="math">\\[\1\\]</div>', self.text, flags=re.DOTALL)
        self.text = re.sub(r'\$\$(.*?)\$\$', r'<div class="math">\\[\1\\]</div>', self.text, flags=re.DOTALL)


    # 主要功能方法
    def protect_equations(self):
        equation_patterns = [
            (r'\\begin{(equation\*?|align\*?|gather\*?|multline\*?)}.*?\\end{\1}', re.DOTALL),
            (r'\$\$(.*?)\$\$', re.DOTALL),
            (r'\$(.*?)\$', re.DOTALL)
        ]
        
        def replacer(match):
            key = f'__EQUATION_{len(self.protected_equations)}__'
            self.protected_equations[key] = match.group(0)
            return key
            
        for pattern, flags in equation_patterns:
            self.text = re.sub(pattern, replacer, self.text, flags=flags)

    def restore_equations(self):
        for key, value in self.protected_equations.items():
            self.text = self.text.replace(key, value)
            
    def process_comments(self):
        self.text = re.sub(r'(?<!\\)%.*', '\n', self.text)
        self.text = self.text.replace('\\%', '%')

    
    def process_environments(self):
        for environment, handler in self.environment_handlers.items():
            env_pattern = re.compile(
                rf'\\begin{{{environment}\*?}}(.*?)\\end{{{environment}\*?}}',
                re.DOTALL
            )
            while True:
                match = env_pattern.search(self.text)
                if not match:
                    break
                full_match = match.group(0)
                content = html.escape(match.group(1).strip())
                replacement = handler(content, starred='*' in full_match)
                self.text = self.text.replace(full_match, replacement)
                
    def handle_enumerate(self, content, starred=False):
        items = re.split(r'\\item\s+', content.strip())
        items = [html.escape(item.strip()) for item in items if item.strip()]
        content = ''.join(f"<li>{item}</li>\n" for item in items)
        return f'\n<ol>{content}</ol>'
    
    def handle_itemize(self, content, starred=False):
        items = re.split(r'\\item\s+', content.strip())
        items = [html.escape(item.strip()) for item in items if item.strip()]
        content = ''.join(f"<li>{item}</li>\n" for item in items)
        return f'\n<ul>{content}</ul>'
    
    def handle_abstract(self, content, starred=False):
        return f'<strong>Abstract:</strong> {content}'
    
    def handle_figure(self, content, starred=False):
        return f'\n'  # 处理图片暂未设置
    
    def handle_algorithm(self, content, starred=False):
        return f'\n'  # 处理算法暂未设置
    
    def handle_tables(self):
        """ 提取 LaTeX 表格的关键信息 """
        table_pattern = re.compile(r'\\begin{table}.*?\\caption{(.*?)}(.*?)\\end{table}', re.DOTALL)
        
        for match in table_pattern.finditer(self.text):
            caption = match.group(1).strip()  # 提取标题
            table_content = match.group(2).strip()  # 提取表格内容
            table_html = self.extract_table_info(table_content)
            # 组合完整 HTML 表格
            final_table = f'''
            <table style="margin:auto; border-collapse: collapse; border: 1px solid black;">
                <caption>{caption}</caption>
                {table_html}
            </table>'''

            self.text = self.text.replace(match.group(0), final_table)


    def extract_table_info(self, content):
        """ 解析表格中的 tabular 结构并提取数据 """
        tabular_pattern = re.compile(r'\\begin{tabular}{.*?}(.*?)\\end{tabular}', re.DOTALL)
        label_pattern = re.compile(r'\\label{(.*?)}')

        # 处理 \label{}
        label_match = label_pattern.search(content)
        table_id = label_match.group(1) if label_match else None
        table_anchor = f'<a id="{table_id}"></a>' if table_id else ''

        # 解析表格数据
        tabular_match = tabular_pattern.search(content)
        if not tabular_match:
            return table_anchor  # 没有表格数据，返回 ID

        table_body = tabular_match.group(1).strip()
        rows = table_body.split('\\\\')  # 按行拆分

        table_html = [table_anchor]  # 存储表格内容
        column_count = None  # 记录列数

        for row in rows:
            row = row.strip()
            if not row:
                continue

            # 处理 \hline
            if row == r'\hline':
                if column_count:
                    table_html.append(f'<tr><td colspan="{column_count}" class="solid-line"></td></tr>')
                continue

            # 处理 \textbf{}
            row = re.sub(r'\\textbf{(.*?)}', r'<b>\1</b>', row)

            # 处理列 & 计算列数
            row = html.unescape(row)  # 先还原 &amp; → &
            cols = [col.strip() for col in row.split('&')]

            if column_count is None:
                column_count = len(cols)  # 记录列数

            table_html.append('<tr>' + ''.join(f'<td>{col}</td>' for col in cols) + '</tr>')

        return '\n'.join(table_html)


    def handle_table(self, content, starred=False):
        content = html.unescape(content)
        content = re.sub(r'\[.*?\]', '\n', content)
        content = re.sub(r'\{.*?\}', '\n', content)
        content = re.sub(r'\\begin', '\n', content)
        content = re.sub(r'\\end', '\n', content)
        content = re.sub(r'\\hline', '\n', content)
        content = re.sub(r'\\caption', '\n', content)
        rows = content.split("\\\\")
        table_html = ['<table style="margin:auto;">']
        column_count = None
        for row in rows:
            print(row)
            row = row.strip()
            if not row:
                continue
            elif row == r'\hline':
                if column_count:
                    table_html.append(f'<tr><td colspan="{column_count}" class="solid-line"></td></tr>')
                continue
            row = re.sub(r'\\textbf{(.*?)}', r'<strong>\1</strong>', row)
            cols = [col.strip().replace("amp;", "") for col in row.split('&')]
            
            if column_count is None:
                column_count = len(cols)
            
            table_html.append('<tr>' + ''.join(f'<td>{col}</td>' for col in cols) + '</tr>')
            
        table_html.append('</table>')
        return '\n'.join(table_html)
        
    def process_commands(self):
        # 处理注册的命令
        for command, handler in self.command_handlers.items():
            star_pattern = re.compile(rf'~?\\{command}\*?{{(.*?)}}', re.DOTALL)

            while True:
                match = star_pattern.search(self.text)
                if not match:
                    break
                full_match = match.group(0)
                content = html.escape(match.group(1).strip())
                replacement = handler(content, starred='*' in full_match)
                self.text = self.text.replace(full_match, replacement)
                

    def handle_bold(self, content, starred=False):
        return f'<strong>{content}</strong>'

    def handle_italic(self, content, starred=False):
        return f'<i>{content}</i>'

    def handle_section(self, content, starred=False):
        return f'\n<h2 class="{"unnumbered" if starred else ""}">{content}</h2>\n'

    def handle_subsection(self, content, starred=False):
        return f'\n<h3 class="{"unnumbered" if starred else ""}">{content}</h3>\n'

    def handle_subsubsection(self, content, starred=False):
        return f'\n<h4 class="{"unnumbered" if starred else ""}">{content}</h4>\n'
    
    def handle_cite(self, content, starred=False):
        return f'' # 处理引用暂未设置
    
    def handle_label(self, content, starred=False):
        return f'<a id="{content}"></a>'
    
    def handle_ref(self, content, starred=False):
        return f'<a href="#{content}">{content}</a>'

    
    def process_idle_conmmands(self):
        # 处理注册的命令
        for idle in self.idle_handlers:
            self.text = re.sub(rf'\\{idle}', '', self.text)
                

    def replace_special_chars(self):
        replacements = [
            (r'``', '“'), (r"''", '”'), 
            (r'---', '—'), (r'--', '-')
        ]
        for pattern, repl in replacements:
            self.text = re.sub(pattern, repl, self.text)

    def handle_paragraphs(self):
        paragraphs = self.text.split('\n\n')
        processed_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if not re.match(r'<h[1-6]([^>]*)>|<ul>|<ol>|<li>|<table([^>]*)>', para):  
                para = f'<p>{para}</p>'
            processed_paragraphs.append(para)
        self.text = '\n\n'.join(processed_paragraphs).replace('<p></p>', '\n')

    def escape_remaining_text(self):
        parts = []
        for part in re.split(r'(<[^>]*>)', self.text):
            if re.match(r'<[^>]*>', part):
                parts.append(part)
            else:
                parts.append(html.escape(part))
        self.text = ''.join(parts)

    def cleanup(self):
        self.text = re.sub(r'\\[a-zA-Z]+{.*?}', '', self.text)
        self.text = re.sub(r'\n\s*\n', '\n', self.text)
        self.text = re.sub(r'<p>\s*</p>', '\n', self.text)
        



def convert_latex_to_html(latex_content):
    converter = Latex2Html()
    return converter.convert(latex_content)