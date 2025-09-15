#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система управления переводами глав новеллы
Интеграция с DeepL API и обработка результатов
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Добавляем путь к нашему модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from deepl_translator import translate_chapter_with_deepl, DeepLFileTranslator
except ImportError:
    print("❌ Не удалось импортировать deepl_translator")
    print("💡 Убедитесь, что установлены зависимости: pip install requests")
    sys.exit(1)


class ChapterTranslationManager:
    """Менеджер для обработки переводов глав"""
    
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = Path(workspace_path)
        self.journal_file = self.workspace_path / "журнал-переводов.txt"
        self.glossary_file = self.workspace_path / "глоссарий.txt"
        
    def translate_chapter_deepl(self, chapter_file: str, chapter_number: int) -> dict:
        """
        Переводит главу через DeepL API
        
        Args:
            chapter_file: Путь к файлу с английской главой
            chapter_number: Номер главы
            
        Returns:
            Результат перевода с метаданными
        """
        chapter_path = Path(chapter_file)
        
        if not chapter_path.exists():
            raise FileNotFoundError(f"Файл главы не найден: {chapter_file}")
        
        # Определяем выходной файл
        output_file = chapter_path.parent / f"{chapter_path.stem}-ru.txt"
        
        print(f"🚀 Начинаю перевод Главы {chapter_number} через DeepL...")
        
        try:
            # Отправляем на перевод через DeepL
            result = translate_chapter_with_deepl(
                english_file=str(chapter_path),
                output_file=str(output_file)
            )
            
            # Обрабатываем результат согласно нашим правилам
            processed_result = self._process_deepl_result(result, chapter_number)
            
            # Записываем в журнал
            self._update_journal(chapter_number, "DeepL API", processed_result['quality_score'])
            
            print(f"✅ Глава {chapter_number} переведена успешно!")
            print(f"📄 Сохранено в: {output_file}")
            print(f"📊 Оценка качества: {processed_result['quality_score']}/100")
            
            return processed_result
            
        except Exception as e:
            print(f"❌ Ошибка при переводе Главы {chapter_number}: {e}")
            raise
    
    def _process_deepl_result(self, deepl_result: dict, chapter_number: int) -> dict:
        """
        Обрабатывает результат DeepL согласно нашим правилам
        
        Args:
            deepl_result: Результат от DeepL API
            chapter_number: Номер главы
            
        Returns:
            Обработанный результат с оценкой качества
        """
        translated_text = deepl_result['translated']
        
        # Применяем пост-обработку согласно нашим правилам
        processed_text = self._apply_cursorrules_processing(translated_text)
        
        # Оценка качества (базовая для DeepL)
        quality_score = self._estimate_quality(processed_text, deepl_result['original'])
        
        # Проверяем на соответствие структуре
        structure_check = self._check_structure_match(
            deepl_result['original'], 
            processed_text
        )
        
        result = {
            'chapter_number': chapter_number,
            'translator': 'DeepL API',
            'translation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'original_text': deepl_result['original'],
            'raw_translation': translated_text,
            'processed_translation': processed_text,
            'quality_score': quality_score,
            'structure_match': structure_check,
            'metadata': deepl_result.get('metadata', {}),
            'needs_human_review': quality_score < 80
        }
        
        return result
    
    def _apply_cursorrules_processing(self, text) -> str:
        """
        Применяет обработку согласно правилам .cursorrules
        
        Args:
            text: Исходный перевод от DeepL (может быть строкой или списком)
            
        Returns:
            Обработанный текст
        """
        # Конвертируем в строку если пришел список
        if isinstance(text, list):
            processed = '\n'.join(text)
        else:
            processed = text
        
        # 1. Нормализация пустых строк (убираем множественные)
        lines = processed.split('\n')
        normalized_lines = []
        prev_empty = False
        
        for line in lines:
            if line.strip() == '':
                if not prev_empty:
                    normalized_lines.append('')
                prev_empty = True
            else:
                normalized_lines.append(line)
                prev_empty = False
        
        processed = '\n'.join(normalized_lines)
        
        # 2. Применяем антипаттерны из ошибки-перевода.txt
        processed = self._apply_antipatterns(processed)
        
        # 3. Проверяем терминологию из глоссария
        processed = self._apply_glossary_terms(processed)
        
        return processed
    
    def _apply_antipatterns(self, text: str) -> str:
        """
        Применяет исправления антипаттернов
        
        Args:
            text: Текст для обработки
            
        Returns:
            Исправленный текст
        """
        # Загружаем антипаттерны (можно расширить чтением из файла)
        antipatterns = {
            'крайне': 'чрезвычайно',
            'слева и справа': 'направо и налево',
            'совершенна': 'идеальна',
            'На его взгляд': 'С его точки зрения',
            'резюмировал': 'размышлял',
        }
        
        processed = text
        for wrong, correct in antipatterns.items():
            processed = processed.replace(wrong, correct)
        
        return processed
    
    def _apply_glossary_terms(self, text: str) -> str:
        """
        Применяет терминологию из глоссария
        
        Args:
            text: Текст для обработки
            
        Returns:
            Текст с исправленной терминологией
        """
        # Основные термины из нашего глоссария
        glossary_terms = {
            'Slack-Off System': 'Система Безделья',
            'Slack Off System': 'Система Безделья',
            'Holy Son': 'Святой Сын',
            'Banished Immortal Peak': 'Пик Изгнанного Бессмертного',
            'Primordial Holy Land': 'Изначальная Святая Земля',
            'Nine Heavens Realm': 'Царство Девяти Небес',
            'dog licker': 'подхалим',
            'slack off': 'бездельничать',
            'slacking': 'безделье',
        }
        
        processed = text
        for en_term, ru_term in glossary_terms.items():
            processed = processed.replace(en_term, ru_term)
        
        return processed
    
    def _estimate_quality(self, translation, original) -> int:
        """
        Базовая оценка качества перевода
        
        Args:
            translation: Переведенный текст (строка)
            original: Оригинальный текст (может быть строкой или списком)
            
        Returns:
            Оценка качества от 0 до 100
        """
        score = 70  # Базовая оценка для DeepL
        
        # Конвертируем оригинал в строку если нужно
        if isinstance(original, list):
            original_text = '\n'.join(original)
        else:
            original_text = original
        
        # Проверяем количество строк
        orig_lines = len([l for l in original_text.split('\n') if l.strip()])
        trans_lines = len([l for l in translation.split('\n') if l.strip()])
        
        if abs(orig_lines - trans_lines) <= 2:
            score += 10  # Структура сохранена
        
        # Проверяем на наличие кавычек (диалоги)
        if '"' in original_text and '"' in translation:
            score += 5  # Диалоги переведены
        
        # Проверяем длину (не должна сильно отличаться)
        length_ratio = len(translation) / len(original_text) if len(original_text) > 0 else 1
        if 0.8 <= length_ratio <= 1.5:
            score += 10  # Длина адекватная
        
        # Проверяем на наличие запрещенных слов
        forbidden_words = ['крайне', 'слева и справа', 'совершенна']
        for word in forbidden_words:
            if word in translation:
                score -= 5
        
        return min(100, max(0, score))
    
    def _check_structure_match(self, original, translation: str) -> dict:
        """
        Проверяет соответствие структуры перевода оригиналу
        
        Args:
            original: Оригинальный текст (может быть строкой или списком)
            translation: Переведенный текст
            
        Returns:
            Словарь с результатами проверки
        """
        # Конвертируем оригинал в строку если нужно
        if isinstance(original, list):
            original_text = '\n'.join(original)
        else:
            original_text = original
            
        orig_lines = original_text.split('\n')
        trans_lines = translation.split('\n')
        
        return {
            'original_lines': len(orig_lines),
            'translation_lines': len(trans_lines),
            'lines_match': len(orig_lines) == len(trans_lines),
            'empty_lines_original': len([l for l in orig_lines if l.strip() == '']),
            'empty_lines_translation': len([l for l in trans_lines if l.strip() == '']),
            'structure_score': 100 if len(orig_lines) == len(trans_lines) else max(0, 100 - abs(len(orig_lines) - len(trans_lines)) * 10)
        }
    
    def _update_journal(self, chapter_number: int, translator: str, quality_score: int):
        """
        Обновляет журнал переводов
        
        Args:
            chapter_number: Номер главы
            translator: Название переводчика
            quality_score: Оценка качества
        """
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            entry = f"Глава {chapter_number} — перевёл: {translator} — дата: {date_str} — качество: {quality_score}/100\n"
            
            with open(self.journal_file, 'a', encoding='utf-8') as f:
                f.write(entry)
                
        except Exception as e:
            print(f"⚠️ Не удалось обновить журнал: {e}")
    
    def translate_fragments_deepl(self, fragments: list) -> dict:
        """
        Переводит отдельные фрагменты через DeepL для консультации
        
        Args:
            fragments: Список английских фрагментов для перевода
            
        Returns:
            Результат консультации с переводами
        """
        try:
            from fragment_translator import FragmentConsultant
            consultant = FragmentConsultant()
            
            print(f"🤖 Консультация с DeepL по {len(fragments)} фрагментам...")
            full_results = consultant.consult_fragments(fragments)
            
            # Извлекаем только переведенные тексты
            translated_fragments = [f['deepl_translation'] for f in full_results['fragments']]
            return translated_fragments
            
        except Exception as e:
            print(f"❌ Ошибка консультации с DeepL: {e}")
            raise


def main():
    """Главная функция для тестирования"""
    print("🧪 Тестирование системы перевода через DeepL...")
    
    # Проверяем API ключ
    api_key = os.getenv('DEEPL_API_KEY')
    if not api_key:
        print("❌ Не найден API ключ DeepL!")
        print("💡 Установите переменную окружения:")
        print("   export DEEPL_API_KEY='your-key:fx'")
        return
    
    # Инициализируем менеджер
    manager = ChapterTranslationManager()
    
    # Ищем файлы глав для перевода
    workspace = Path(".")
    chapter_files = list(workspace.glob("Глава *.txt")) + list(workspace.glob("глава *.txt"))
    
    if not chapter_files:
        print("📄 Файлы глав не найдены. Создаю тестовый файл...")
        
        # Создаем тестовую главу
        test_chapter = workspace / "Тест Глава.txt"
        with open(test_chapter, 'w', encoding='utf-8') as f:
            f.write("""Chapter Test: DeepL Integration

"Finally, she's gone!" Jiang Chen exhaled with relief.

From his perspective, apart from being brainless, Ye Qingcheng was like bad luck - better to stay as far away from her as possible.

"But how does Ye Qingcheng know about Du Guyun?" Jiang Chen stroked his chin, puzzled. According to the plot trajectory, Ye Qingcheng shouldn't know Du Guyun at this point!

"System, would it count as interfering with slacking off if I take action against Du Guyun?" Jiang Chen inquired.

"It counts!" the cold voice replied.""")
        
        chapter_files = [test_chapter]
    
    # Переводим найденные главы
    for chapter_file in chapter_files[:1]:  # Только первую для теста
        try:
            chapter_number = 999  # Тестовый номер
            print(f"\n📖 Обрабатываю файл: {chapter_file}")
            
            result = manager.translate_chapter_deepl(str(chapter_file), chapter_number)
            
            print(f"📊 Результаты перевода:")
            print(f"   Качество: {result['quality_score']}/100")
            print(f"   Соответствие структуре: {result['structure_match']['structure_score']}/100")
            print(f"   Требует проверки: {'Да' if result['needs_human_review'] else 'Нет'}")
            
        except Exception as e:
            print(f"❌ Ошибка при обработке {chapter_file}: {e}")


if __name__ == "__main__":
    main()
