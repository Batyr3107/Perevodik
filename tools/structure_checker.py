#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка структуры строк в переводах
Сравнивает количество строк и переносов между оригиналом и переводом
"""

import sys
import os
from typing import Tuple, List, Dict, Any

def count_lines_and_breaks(text: str) -> Dict[str, Any]:
    """Подсчитывает строки и переносы в тексте"""
    lines = text.split('\n')
    
    # Общее количество строк
    total_lines = len(lines)
    
    # Пустые строки
    empty_lines = sum(1 for line in lines if not line.strip())
    
    # Строки с содержимым
    content_lines = total_lines - empty_lines
    
    # Переносы внутри предложений (строки, которые не заканчиваются точкой, восклицательным или вопросительным знаком)
    line_breaks = []
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().endswith(('.', '!', '?', '»', '"', "'")):
            # Проверяем, не является ли это последней строкой
            if i < len(lines) - 1:
                line_breaks.append(i + 1)  # Нумерация с 1
    
    # Строки с тире (разделители)
    dash_lines = [i + 1 for i, line in enumerate(lines) if line.strip() == '—']
    
    return {
        'total_lines': total_lines,
        'empty_lines': empty_lines,
        'content_lines': content_lines,
        'line_breaks': line_breaks,
        'dash_lines': dash_lines,
        'break_count': len(line_breaks)
    }

def check_structure_match(original_text: str, translated_text: str) -> Dict[str, Any]:
    """Проверяет соответствие структуры между оригиналом и переводом"""
    
    original_stats = count_lines_and_breaks(original_text)
    translated_stats = count_lines_and_breaks(translated_text)
    
    # Проверяем соответствие
    structure_match = {
        'total_lines_match': original_stats['total_lines'] == translated_stats['total_lines'],
        'empty_lines_match': original_stats['empty_lines'] == translated_stats['empty_lines'],
        'content_lines_match': original_stats['content_lines'] == translated_stats['content_lines'],
        'break_count_match': original_stats['break_count'] == translated_stats['break_count'],
        'dash_lines_match': original_stats['dash_lines'] == translated_stats['dash_lines']
    }
    
    # Общий статус
    structure_match['overall_match'] = all(structure_match.values())
    
    return {
        'original': original_stats,
        'translated': translated_stats,
        'match': structure_match
    }

def print_structure_report(result: Dict[str, Any]):
    """Выводит отчет о структуре"""
    print("🔍 ПРОВЕРКА СТРУКТУРЫ СТРОК")
    print("=" * 50)
    
    original = result['original']
    translated = result['translated']
    match = result['match']
    
    print(f"📄 Оригинал:")
    print(f"   • Всего строк: {original['total_lines']}")
    print(f"   • Пустых строк: {original['empty_lines']}")
    print(f"   • Строк с содержимым: {original['content_lines']}")
    print(f"   • Переносов внутри предложений: {original['break_count']}")
    print(f"   • Строк с тире: {len(original['dash_lines'])}")
    
    print(f"\n📄 Перевод:")
    print(f"   • Всего строк: {translated['total_lines']}")
    print(f"   • Пустых строк: {translated['empty_lines']}")
    print(f"   • Строк с содержимым: {translated['content_lines']}")
    print(f"   • Переносов внутри предложений: {translated['break_count']}")
    print(f"   • Строк с тире: {len(translated['dash_lines'])}")
    
    print(f"\n✅ СООТВЕТСТВИЕ:")
    print(f"   • Всего строк: {'✅' if match['total_lines_match'] else '❌'}")
    print(f"   • Пустых строк: {'✅' if match['empty_lines_match'] else '❌'}")
    print(f"   • Строк с содержимым: {'✅' if match['content_lines_match'] else '❌'}")
    print(f"   • Переносов внутри предложений: {'✅' if match['break_count_match'] else '❌'}")
    print(f"   • Строк с тире: {'✅' if match['dash_lines_match'] else '❌'}")
    
    print(f"\n🏆 ОБЩИЙ СТАТУС: {'✅ СТРУКТУРА СООТВЕТСТВУЕТ' if match['overall_match'] else '❌ СТРУКТУРА НЕ СООТВЕТСТВУЕТ'}")
    
    # Показываем детали несоответствий
    if not match['overall_match']:
        print(f"\n⚠️ ДЕТАЛИ НЕСООТВЕТСТВИЙ:")
        
        if not match['total_lines_match']:
            print(f"   • Количество строк: {original['total_lines']} ≠ {translated['total_lines']}")
        
        if not match['empty_lines_match']:
            print(f"   • Пустых строк: {original['empty_lines']} ≠ {translated['empty_lines']}")
        
        if not match['content_lines_match']:
            print(f"   • Строк с содержимым: {original['content_lines']} ≠ {translated['content_lines']}")
        
        if not match['break_count_match']:
            print(f"   • Переносов внутри предложений: {original['break_count']} ≠ {translated['break_count']}")
        
        if not match['dash_lines_match']:
            print(f"   • Строк с тире: {len(original['dash_lines'])} ≠ {len(translated['dash_lines'])}")
    
    # Показываем переносы внутри предложений
    if original['line_breaks'] or translated['line_breaks']:
        print(f"\n📋 ПЕРЕНОСЫ ВНУТРИ ПРЕДЛОЖЕНИЙ:")
        print(f"   • Оригинал: строки {original['line_breaks']}")
        print(f"   • Перевод: строки {translated['line_breaks']}")
    
    # Показываем строки с тире
    if original['dash_lines'] or translated['dash_lines']:
        print(f"\n📋 СТРОКИ С ТИРЕ:")
        print(f"   • Оригинал: строки {original['dash_lines']}")
        print(f"   • Перевод: строки {translated['dash_lines']}")

def main():
    """Главная функция"""
    if len(sys.argv) != 3:
        print("Использование: python structure_checker.py <оригинал> <перевод>")
        print("Пример: python structure_checker.py original/Глава\\ 10 translated/Глава\\ 10-ru.txt")
        return
    
    original_file = sys.argv[1]
    translated_file = sys.argv[2]
    
    if not os.path.exists(original_file):
        print(f"❌ Файл оригинала не найден: {original_file}")
        return
    
    if not os.path.exists(translated_file):
        print(f"❌ Файл перевода не найден: {translated_file}")
        return
    
    try:
        # Читаем файлы
        with open(original_file, 'r', encoding='utf-8') as f:
            original_text = f.read()
        
        with open(translated_file, 'r', encoding='utf-8') as f:
            translated_text = f.read()
        
        # Проверяем структуру
        result = check_structure_match(original_text, translated_text)
        
        # Выводим отчет
        print_structure_report(result)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
