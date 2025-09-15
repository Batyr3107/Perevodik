#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Разделитель глав на параграфы и сегменты
Отвечает за правильную разбивку текста для перевода
"""

import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class TextSegment:
    """Сегмент текста с метаданными"""
    content: str
    segment_type: str  # 'paragraph', 'dialogue', 'description', 'system'
    line_number: int
    character: str = None
    is_dialogue: bool = False
    is_system: bool = False

class ChapterSplitter:
    """Разделитель глав на логические сегменты"""
    
    def __init__(self):
        # Паттерны для определения типов сегментов
        self.dialogue_patterns = [
            r'"[^"]*"',  # Обычные кавычки
            r'«[^»]*»',  # Ёлочки
            r'—[^—]*—',  # Тире
        ]
        
        self.system_patterns = [
            r'Динь!.*',
            r'Система.*',
            r'Оповещение.*',
            r'Получено.*',
            r'Награда.*'
        ]
        
        self.character_indicators = [
            'Цзян Чэнь', 'Jiang Chen',
            'Е Цинчэн', 'Ye Qingcheng', 
            'Ду Гуюнь', 'Du Guyun',
            'Старейшина', 'Elder'
        ]
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """Разбить текст на параграфы по двойным переносам"""
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    def split_by_lines(self, text: str) -> List[TextSegment]:
        """Разбить текст построчно с сохранением структуры"""
        lines = text.split('\n')
        segments = []
        
        for i, line in enumerate(lines, 1):
            # Убираем только \r, оставляем \n для сохранения структуры
            original_line = line
            line = line.rstrip('\r')
            
            # Пустая строка - это строка, которая содержит только пробелы и \n
            if not line.strip() or line == '\n':
                segments.append(TextSegment(
                    content='',
                    segment_type='empty_line',
                    line_number=i
                ))
            else:
                # Определяем тип сегмента
                segment_type = self._detect_segment_type(line)
                character = self._detect_character(line)
                is_dialogue = self._is_dialogue(line)
                is_system = self._is_system(line)
                
                segments.append(TextSegment(
                    content=line,
                    segment_type=segment_type,
                    line_number=i,
                    character=character,
                    is_dialogue=is_dialogue,
                    is_system=is_system
                ))
        
        return segments
    
    def _detect_segment_type(self, line: str) -> str:
        """Определить тип сегмента"""
        if not line.strip():
            return 'empty_line'
        elif any(re.search(pattern, line) for pattern in self.dialogue_patterns):
            return 'dialogue'
        elif any(re.search(pattern, line) for pattern in self.system_patterns):
            return 'system'
        else:
            return 'description'
    
    def _detect_character(self, line: str) -> str:
        """Определить персонажа в строке"""
        for indicator in self.character_indicators:
            if indicator in line:
                return indicator
        return None
    
    def _is_dialogue(self, line: str) -> bool:
        """Проверить, является ли строка диалогом"""
        return any(re.search(pattern, line) for pattern in self.dialogue_patterns)
    
    def _is_system(self, line: str) -> bool:
        """Проверить, является ли строка системным сообщением"""
        return any(re.search(pattern, line) for pattern in self.system_patterns)
    
    def split_by_sentences(self, text: str) -> List[str]:
        """Разбить текст на предложения"""
        # Улучшенное разделение предложений
        sentences = re.split(r'(?<=[.!?])\s+(?=[А-ЯA-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def create_segments(self, text: str) -> List[TextSegment]:
        """Создать структурированные сегменты из текста"""
        segments = []
        lines = text.split('\n')
        
        current_paragraph = []
        paragraph_start_line = 1
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line:
                # Пустая строка - завершаем параграф
                if current_paragraph:
                    paragraph_text = '\n'.join(current_paragraph)
                    segment = self._analyze_segment(paragraph_text, paragraph_start_line)
                    segments.append(segment)
                    current_paragraph = []
                continue
            
            if not current_paragraph:
                paragraph_start_line = i
            
            current_paragraph.append(line)
        
        # Обрабатываем последний параграф
        if current_paragraph:
            paragraph_text = '\n'.join(current_paragraph)
            segment = self._analyze_segment(paragraph_text, paragraph_start_line)
            segments.append(segment)
        
        return segments
    
    def _analyze_segment(self, text: str, line_number: int) -> TextSegment:
        """Анализировать сегмент и определить его тип"""
        segment_type = 'description'
        character = None
        is_dialogue = False
        is_system = False
        
        # Проверяем на диалог
        for pattern in self.dialogue_patterns:
            if re.search(pattern, text):
                segment_type = 'dialogue'
                is_dialogue = True
                break
        
        # Проверяем на системные уведомления
        for pattern in self.system_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                segment_type = 'system'
                is_system = True
                break
        
        # Определяем персонажа
        for indicator in self.character_indicators:
            if indicator in text:
                character = indicator
                break
        
        return TextSegment(
            content=text,
            segment_type=segment_type,
            line_number=line_number,
            character=character,
            is_dialogue=is_dialogue,
            is_system=is_system
        )
    
    def split_for_translation(self, text: str, max_length: int = 1000) -> List[Dict[str, Any]]:
        """Разбить текст на части для перевода с учетом лимитов"""
        segments = self.create_segments(text)
        translation_units = []
        current_unit = []
        current_length = 0
        
        for segment in segments:
            segment_length = len(segment.content)
            
            # Если добавление сегмента превысит лимит, завершаем текущую единицу
            if current_length + segment_length > max_length and current_unit:
                translation_units.append({
                    'segments': current_unit,
                    'total_length': current_length,
                    'text': '\n\n'.join([s.content for s in current_unit])
                })
                current_unit = []
                current_length = 0
            
            current_unit.append(segment)
            current_length += segment_length
        
        # Добавляем последнюю единицу
        if current_unit:
            translation_units.append({
                'segments': current_unit,
                'total_length': current_length,
                'text': '\n\n'.join([s.content for s in current_unit])
            })
        
        return translation_units
    
    def get_dialogue_segments(self, text: str) -> List[TextSegment]:
        """Получить только диалоговые сегменты"""
        segments = self.create_segments(text)
        return [s for s in segments if s.is_dialogue]
    
    def get_system_segments(self, text: str) -> List[TextSegment]:
        """Получить только системные сегменты"""
        segments = self.create_segments(text)
        return [s for s in segments if s.is_system]
    
    def get_character_segments(self, text: str, character: str) -> List[TextSegment]:
        """Получить сегменты конкретного персонажа"""
        segments = self.create_segments(text)
        return [s for s in segments if s.character == character]
    
    def validate_structure(self, original_text: str, translated_text: str) -> Dict[str, Any]:
        """Проверить соответствие структуры перевода оригиналу"""
        original_segments = self.create_segments(original_text)
        translated_segments = self.create_segments(translated_text)
        
        return {
            'original_segments': len(original_segments),
            'translated_segments': len(translated_segments),
            'structure_match': len(original_segments) == len(translated_segments),
            'missing_segments': len(original_segments) - len(translated_segments),
            'extra_segments': len(translated_segments) - len(original_segments),
            'match_percentage': (min(len(original_segments), len(translated_segments)) / 
                              max(len(original_segments), len(translated_segments)) * 100) if max(len(original_segments), len(translated_segments)) > 0 else 100
        }

def test_chapter_splitter():
    """Тестирование разделителя глав"""
    print("🧪 ТЕСТИРОВАНИЕ РАЗДЕЛИТЕЛЯ ГЛАВ")
    print("=" * 50)
    
    splitter = ChapterSplitter()
    
    # Тестовый текст
    test_text = """Глава 1: Начало

"Наконец-то она ушла!" Цзян Чэнь с облегчением выдохнул.

С его точки зрения, помимо безмозглости, Е Цинчэн была как невезение - лучше держаться от неё подальше.

"Система, будет ли считаться вмешательством в безделье, если я предприму действия?" Цзян Чэнь спросил.

Динь! За успешное безделье получено: Императорское оружие «Всенебесное Зеркало»!

Старейшина посмотрел на него с удивлением."""
    
    # Тест разбивки на параграфы
    paragraphs = splitter.split_by_paragraphs(test_text)
    print(f"📝 Параграфов: {len(paragraphs)}")
    
    # Тест создания сегментов
    segments = splitter.create_segments(test_text)
    print(f"🔍 Сегментов: {len(segments)}")
    
    for i, segment in enumerate(segments, 1):
        print(f"  {i}. {segment.segment_type} (строка {segment.line_number}): {segment.content[:50]}...")
        if segment.character:
            print(f"     Персонаж: {segment.character}")
    
    # Тест диалогов
    dialogue_segments = splitter.get_dialogue_segments(test_text)
    print(f"💬 Диалоговых сегментов: {len(dialogue_segments)}")
    
    # Тест системных уведомлений
    system_segments = splitter.get_system_segments(test_text)
    print(f"🔔 Системных сегментов: {len(system_segments)}")
    
    # Тест разбивки для перевода
    translation_units = splitter.split_for_translation(test_text, max_length=200)
    print(f"📦 Единиц для перевода: {len(translation_units)}")
    
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    test_chapter_splitter()
