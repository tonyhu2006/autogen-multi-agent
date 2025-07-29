#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终端Markdown渲染器
为AI响应提供美观的终端输出格式
"""

import re
import os
from typing import Dict, Any, Optional
from colorama import init, Fore, Back, Style

# 初始化colorama
init(autoreset=True)

class TerminalMarkdownRenderer:
    """终端Markdown渲染器"""
    
    def __init__(self):
        self.colors = {
            'header': Fore.CYAN + Style.BRIGHT,
            'subheader': Fore.BLUE + Style.BRIGHT,
            'bold': Style.BRIGHT,
            'italic': Style.DIM,
            'code': Fore.GREEN + Back.BLACK,
            'code_block': Fore.GREEN,
            'quote': Fore.YELLOW + Style.DIM,
            'list': Fore.WHITE,
            'link': Fore.BLUE + Style.BRIGHT,
            'error': Fore.RED + Style.BRIGHT,
            'success': Fore.GREEN + Style.BRIGHT,
            'warning': Fore.YELLOW + Style.BRIGHT,
            'info': Fore.CYAN,
            'reset': Style.RESET_ALL
        }
    
    def render(self, text: str) -> str:
        """渲染Markdown文本为终端格式"""
        if not text:
            return ""
        
        # 处理各种Markdown元素
        rendered = text
        
        # 1. 处理标题
        rendered = self._render_headers(rendered)
        
        # 2. 处理代码块
        rendered = self._render_code_blocks(rendered)
        
        # 3. 处理行内代码
        rendered = self._render_inline_code(rendered)
        
        # 4. 处理粗体和斜体
        rendered = self._render_bold_italic(rendered)
        
        # 5. 处理引用
        rendered = self._render_quotes(rendered)
        
        # 6. 处理列表
        rendered = self._render_lists(rendered)
        
        # 7. 处理链接
        rendered = self._render_links(rendered)
        
        # 8. 处理特殊标记（如表情符号增强）
        rendered = self._render_special_markers(rendered)
        
        return rendered + self.colors['reset']
    
    def _render_headers(self, text: str) -> str:
        """渲染标题"""
        lines = text.split('\n')
        rendered_lines = []
        
        for line in lines:
            # H1 标题
            if line.startswith('# '):
                content = line[2:].strip()
                rendered_lines.append(f"\n{self.colors['header']}{'='*60}")
                rendered_lines.append(f"{self.colors['header']}🎯 {content}")
                rendered_lines.append(f"{self.colors['header']}{'='*60}{self.colors['reset']}")
            
            # H2 标题
            elif line.startswith('## '):
                content = line[3:].strip()
                rendered_lines.append(f"\n{self.colors['subheader']}📋 {content}")
                rendered_lines.append(f"{self.colors['subheader']}{'-'*40}{self.colors['reset']}")
            
            # H3 标题
            elif line.startswith('### '):
                content = line[4:].strip()
                rendered_lines.append(f"\n{self.colors['subheader']}🔸 {content}{self.colors['reset']}")
            
            # H4+ 标题
            elif line.startswith('#### '):
                content = line[5:].strip()
                rendered_lines.append(f"\n{self.colors['info']}• {content}{self.colors['reset']}")
            
            else:
                rendered_lines.append(line)
        
        return '\n'.join(rendered_lines)
    
    def _render_code_blocks(self, text: str) -> str:
        """渲染代码块"""
        # 处理三重反引号代码块
        pattern = r'```(\w+)?\n(.*?)\n```'
        
        def replace_code_block(match):
            language = match.group(1) or 'text'
            code = match.group(2)
            
            lines = code.split('\n')
            rendered_lines = []
            
            # 代码块头部
            rendered_lines.append(f"{self.colors['code_block']}┌─ {language.upper()} ─{'─'*(50-len(language))}")
            
            # 代码内容
            for line in lines:
                rendered_lines.append(f"{self.colors['code_block']}│ {line}")
            
            # 代码块底部
            rendered_lines.append(f"{self.colors['code_block']}└─{'─'*58}{self.colors['reset']}")
            
            return '\n'.join(rendered_lines)
        
        return re.sub(pattern, replace_code_block, text, flags=re.DOTALL)
    
    def _render_inline_code(self, text: str) -> str:
        """渲染行内代码"""
        pattern = r'`([^`]+)`'
        return re.sub(pattern, f"{self.colors['code']} \\1 {self.colors['reset']}", text)
    
    def _render_bold_italic(self, text: str) -> str:
        """渲染粗体和斜体"""
        # 粗体
        text = re.sub(r'\*\*([^*]+)\*\*', f"{self.colors['bold']}\\1{self.colors['reset']}", text)
        text = re.sub(r'__([^_]+)__', f"{self.colors['bold']}\\1{self.colors['reset']}", text)
        
        # 斜体
        text = re.sub(r'\*([^*]+)\*', f"{self.colors['italic']}\\1{self.colors['reset']}", text)
        text = re.sub(r'_([^_]+)_', f"{self.colors['italic']}\\1{self.colors['reset']}", text)
        
        return text
    
    def _render_quotes(self, text: str) -> str:
        """渲染引用"""
        lines = text.split('\n')
        rendered_lines = []
        
        for line in lines:
            if line.startswith('> '):
                content = line[2:]
                rendered_lines.append(f"{self.colors['quote']}│ {content}{self.colors['reset']}")
            else:
                rendered_lines.append(line)
        
        return '\n'.join(rendered_lines)
    
    def _render_lists(self, text: str) -> str:
        """渲染列表"""
        lines = text.split('\n')
        rendered_lines = []
        
        for line in lines:
            # 无序列表
            if re.match(r'^[\s]*[-*+]\s', line):
                indent = len(line) - len(line.lstrip())
                content = re.sub(r'^[\s]*[-*+]\s', '', line)
                bullet = "•" if indent == 0 else "◦"
                rendered_lines.append(f"{' ' * indent}{self.colors['list']}{bullet} {content}{self.colors['reset']}")
            
            # 有序列表
            elif re.match(r'^[\s]*\d+\.\s', line):
                indent = len(line) - len(line.lstrip())
                content = re.sub(r'^[\s]*\d+\.\s', '', line)
                number = re.match(r'^[\s]*(\d+)\.', line).group(1)
                rendered_lines.append(f"{' ' * indent}{self.colors['list']}{number}. {content}{self.colors['reset']}")
            
            else:
                rendered_lines.append(line)
        
        return '\n'.join(rendered_lines)
    
    def _render_links(self, text: str) -> str:
        """渲染链接"""
        # Markdown链接格式 [text](url)
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        return re.sub(pattern, f"{self.colors['link']}\\1{self.colors['reset']} ({self.colors['info']}\\2{self.colors['reset']})", text)
    
    def _render_special_markers(self, text: str) -> str:
        """渲染特殊标记"""
        # 增强表情符号和状态标记
        replacements = {
            '✅': f"{self.colors['success']}✅{self.colors['reset']}",
            '❌': f"{self.colors['error']}❌{self.colors['reset']}",
            '⚠️': f"{self.colors['warning']}⚠️{self.colors['reset']}",
            '🔍': f"{self.colors['info']}🔍{self.colors['reset']}",
            '🎯': f"{self.colors['header']}🎯{self.colors['reset']}",
            '📋': f"{self.colors['subheader']}📋{self.colors['reset']}",
            '🚀': f"{self.colors['success']}🚀{self.colors['reset']}",
            '💡': f"{self.colors['warning']}💡{self.colors['reset']}",
            '🔧': f"{self.colors['info']}🔧{self.colors['reset']}",
        }
        
        for marker, replacement in replacements.items():
            text = text.replace(marker, replacement)
        
        return text
    
    def render_ai_response(self, response: str, agent_name: str = "AI") -> str:
        """专门渲染AI响应"""
        # 添加AI响应头部
        header = f"\n{self.colors['header']}🤖 {agent_name} 回复:{self.colors['reset']}\n"
        
        # 渲染响应内容
        rendered_content = self.render(response)
        
        # 添加分隔线
        separator = f"\n{self.colors['info']}{'─'*60}{self.colors['reset']}\n"
        
        return header + rendered_content + separator

# 延迟初始化的全局渲染器实例
_markdown_renderer = None

def _get_renderer():
    """获取渲染器实例（延迟初始化）"""
    global _markdown_renderer
    if _markdown_renderer is None:
        try:
            _markdown_renderer = TerminalMarkdownRenderer()
        except Exception as e:
            # 如果初始化失败，返回None
            print(f"警告：Markdown渲染器初始化失败: {e}")
            _markdown_renderer = False  # 标记为失败，避免重复尝试
    return _markdown_renderer if _markdown_renderer is not False else None

def render_markdown(text: str) -> str:
    """便捷函数：渲染Markdown文本"""
    renderer = _get_renderer()
    if renderer:
        return renderer.render(text)
    else:
        return text  # 回退到原始文本

def render_ai_response(response: str, agent_name: str = "AI") -> str:
    """便捷函数：渲染AI响应"""
    renderer = _get_renderer()
    if renderer:
        return renderer.render_ai_response(response, agent_name)
    else:
        return f"🤖 {agent_name}: {response}"  # 回退到简单格式

def print_markdown(text: str):
    """便捷函数：打印Markdown文本"""
    print(render_markdown(text))

def print_ai_response(response: str, agent_name: str = "AI"):
    """便捷函数：打印AI响应"""
    print(render_ai_response(response, agent_name))
