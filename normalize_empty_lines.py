#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для нормализации пустых строк в файлах проекта
Удаляет множественные пустые строки, оставляя только одинарные
"""

import os
import re
import glob
from typing import List, Tuple

def normalize_empty_lines(content: str) -> str:
    """
    Нормализует пустые строки в тексте
    
    Args:
        content: Исходный текст
        
    Returns:
        Текст с нормализованными пустыми строками
    """
    # Заменяем 2 и более подряд идущих пустых строк на 2 (одна пустая строка)
    # Сначала обрабатываем Unix окончания строк (\n)
    normalized = re.sub(r'\n{3,}', '\n\n', content)
    
    # Затем обрабатываем Windows окончания строк (\r\n)
    normalized = re.sub(r'(\r\n){3,}', '\r\n\r\n', normalized)
    
    # Дополнительно убираем лишние пробелы в пустых строках
    normalized = re.sub(r'\n\s+\n', '\n\n', normalized)
    normalized = re.sub(r'(\r\n)\s+(\r\n)', r'\1\2', normalized)
    
    return normalized

def process_file(file_path: str) -> Tuple[bool, str]:
    """
    Обрабатывает один файл
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        (успех, сообщение)
    """
    try:
        # Читаем файл
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Нормализуем пустые строки
        normalized_content = normalize_empty_lines(original_content)
        
        # Проверяем, были ли изменения
        if original_content == normalized_content:
            return True, "Файл уже нормализован"
        
        # Записываем обратно
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(normalized_content)
        
        # Подсчитываем изменения
        original_lines = len(original_content.splitlines())
        normalized_lines = len(normalized_content.splitlines())
        lines_removed = original_lines - normalized_lines
        
        return True, f"Удалено {lines_removed} лишних строк"
        
    except Exception as e:
        return False, f"Ошибка: {e}"

def find_files_to_process() -> List[str]:
    """
    Находит все файлы для обработки
    
    Returns:
        Список путей к файлам
    """
    # Паттерны файлов для обработки (с учетом новой структуры папок)
    patterns = [
        "original/Глава *.txt",     # Оригинальные главы с расширением
        "original/глава *.txt",     # Строчные оригиналы с расширением
        "original/Глава *",         # Оригинальные главы без расширения
        "original/глава *",         # Строчные оригиналы без расширения
        "translated/Глава *-ru.txt", # Переведенные главы
        "translated/глава *-ru.txt"  # Строчные переводы
    ]
    
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    
    # Убираем дубликаты и сортируем
    files = sorted(list(set(files)))
    
    return files

def main():
    """Главная функция"""
    print("🧹 НОРМАЛИЗАЦИЯ ПУСТЫХ СТРОК В ПРОЕКТЕ")
    print("="*50)
    
    # Находим файлы для обработки
    files = find_files_to_process()
    
    if not files:
        print("❌ Файлы для обработки не найдены")
        return
    
    print(f"📁 Найдено файлов для обработки: {len(files)}")
    print()
    
    # Обрабатываем каждый файл
    success_count = 0
    total_lines_removed = 0
    
    for file_path in files:
        print(f"📄 Обрабатываю: {file_path}")
        
        success, message = process_file(file_path)
        
        if success:
            print(f"   ✅ {message}")
            success_count += 1
            
            # Извлекаем количество удаленных строк из сообщения
            if "Удалено" in message:
                try:
                    lines_removed = int(re.search(r'Удалено (\d+)', message).group(1))
                    total_lines_removed += lines_removed
                except:
                    pass
        else:
            print(f"   ❌ {message}")
        
        print()
    
    # Итоговая статистика
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("="*30)
    print(f"✅ Успешно обработано: {success_count}/{len(files)} файлов")
    print(f"🗑️  Всего удалено строк: {total_lines_removed}")
    
    if success_count == len(files):
        print("🎉 Все файлы успешно нормализованы!")
    else:
        print("⚠️  Некоторые файлы не удалось обработать")

def preview_changes():
    """Предварительный просмотр изменений без их применения"""
    print("👀 ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР ИЗМЕНЕНИЙ")
    print("="*50)
    
    files = find_files_to_process()
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            normalized_content = normalize_empty_lines(original_content)
            
            if original_content != normalized_content:
                original_lines = len(original_content.splitlines())
                normalized_lines = len(normalized_content.splitlines())
                lines_to_remove = original_lines - normalized_lines
                
                print(f"📄 {file_path}: будет удалено {lines_to_remove} строк")
            else:
                print(f"📄 {file_path}: изменений не требуется")
                
        except Exception as e:
            print(f"📄 {file_path}: ошибка чтения - {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_changes()
    else:
        main()
