#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматизированный процессор глав для перевода
Объединяет все этапы перевода в единый pipeline
"""

import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Импорты из других модулей
from config import (
    QUALITY_METRICS, MIN_QUALITY_THRESHOLDS, DIALOGUE_IMPROVEMENTS,
    CHARACTER_VOICES_FILE, CULTIVATION_LEVELS, HONORIFICS,
    TRANSLATION_STYLE, MAX_SENTENCE_LENGTH, BANNED_ARCHAISMS,
    TARGET_READABILITY, CHARACTER_STYLES
)
from tools.context_manager import TranslationMemoryManager, TranslationMemory
from tools.consultation_base import DeepLConsultationBase
from tools.style_modernizer import StyleModernizer
from tools.chapter_splitter import ChapterSplitter
from tools.chapter_translator import ChapterTranslator, TranslationContext
from tools.chapter_validator import ChapterValidator

@dataclass
class ChapterContext:
    """Контекст главы для перевода"""
    chapter_number: str
    previous_chapters: List[str]
    main_characters: List[str]
    current_scene: str
    emotional_tone: str

class DialogueImprover:
    """Улучшитель диалогов"""
    
    def __init__(self):
        self.character_voices = self._load_character_voices()
        self.dialogue_patterns = DIALOGUE_IMPROVEMENTS
    
    def _load_character_voices(self) -> Dict:
        """Загрузить голоса персонажей"""
        try:
            if os.path.exists(CHARACTER_VOICES_FILE):
                with open(CHARACTER_VOICES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️ Ошибка загрузки голосов персонажей: {e}")
            return {}
    
    def improve_dialogue(self, text: str, character: Optional[str] = None) -> str:
        """Улучшить диалог для конкретного персонажа"""
        improved_text = text
        
        # Применяем общие улучшения
        for formal, natural in zip(
            self.dialogue_patterns["remove_formality"],
            self.dialogue_patterns["add_naturalness"]
        ):
            improved_text = improved_text.replace(formal, natural)
        
        # Применяем специфичные для персонажа улучшения
        if character and character in self.character_voices.get("characters", {}):
            char_config = self.character_voices["characters"][character]
            
            # Убираем нежелательные слова
            for avoid_word in char_config.get("avoid", []):
                improved_text = improved_text.replace(avoid_word, "")
            
            # Заменяем предпочитаемыми
            for prefer_word in char_config.get("prefer", []):
                # Простая замена (можно улучшить)
                pass
        
        return improved_text
    
    def detect_character_from_context(self, text: str, context: str) -> Optional[str]:
        """Определить персонажа по контексту"""
        # Простая эвристика - можно улучшить
        if "Цзян Чэнь" in text or "Jiang Chen" in text:
            return "Jiang_Chen"
        elif "Е Цинчэн" in text or "Ye Qingcheng" in text:
            return "Ye_Qingcheng"
        elif "Ду Гуюнь" in text or "Du Guyun" in text:
            return "Du_Guyun"
        elif "Старейшина" in text or "Elder" in text:
            return "Elders"
        return None

class QualityEvaluator:
    """Оценщик качества перевода"""
    
    def __init__(self):
        self.memory_manager = TranslationMemoryManager()
    
    def evaluate_dialogue_naturalness(self, text: str) -> float:
        """Оценить естественность диалогов (0-100)"""
        score = 100.0
        
        # Проверяем формальные конструкции
        formal_patterns = [
            "Я собираюсь", "Позвольте мне", "Не могли бы вы",
            "Я хотел бы", "Кажется, что", "Я боюсь, что"
        ]
        
        for pattern in formal_patterns:
            if pattern in text:
                score -= 10  # Штраф за формальность
        
        # Проверяем естественные конструкции
        natural_patterns = [
            "Буду", "Дай мне", "Можешь", "Хочу", "Похоже", "Боюсь"
        ]
        
        for pattern in natural_patterns:
            if pattern in text:
                score += 5  # Бонус за естественность
        
        return max(0, min(100, score))
    
    def evaluate_terminology_consistency(self, text: str, glossary: Dict) -> float:
        """Оценить консистентность терминологии (0-100)"""
        score = 100.0
        
        # Проверяем соответствие глоссарию
        for term, translation in glossary.items():
            if term in text and translation not in text:
                score -= 15  # Штраф за несоответствие терминов
        
        return max(0, min(100, score))
    
    def evaluate_character_voice(self, text: str, character: str) -> float:
        """Оценить соответствие голосу персонажа (0-100)"""
        # Базовая оценка - можно улучшить
        return 85.0
    
    def evaluate_cultural_adaptation(self, text: str) -> float:
        """Оценить культурную адаптацию (0-100)"""
        score = 100.0
        
        # Проверяем кальки
        calque_patterns = [
            "крайне", "весьма", "осуществлять", "производить впечатление"
        ]
        
        for pattern in calque_patterns:
            if pattern in text:
                score -= 10  # Штраф за кальки
        
        return max(0, min(100, score))
    
    def evaluate_translation(self, source: str, translation: str, 
                           character: Optional[str] = None, 
                           glossary: Optional[Dict] = None) -> Dict[str, float]:
        """Полная оценка качества перевода"""
        scores = {
            "dialogue_naturalness": self.evaluate_dialogue_naturalness(translation),
            "terminology_consistency": self.evaluate_terminology_consistency(
                translation, glossary or {}
            ),
            "character_voice": self.evaluate_character_voice(translation, character or ""),
            "cultural_adaptation": self.evaluate_cultural_adaptation(translation)
        }
        
        return scores

class ChapterProcessor:
    """Основной процессор глав (упрощенная версия)"""
    
    def __init__(self):
        # Новые специализированные компоненты
        self.splitter = ChapterSplitter()
        self.translator = ChapterTranslator()
        self.validator = ChapterValidator()
        
        # Старые компоненты (для обратной совместимости)
        self.dialogue_improver = DialogueImprover()
        self.quality_evaluator = QualityEvaluator()
        self.memory_manager = TranslationMemoryManager()
        self.deepl_consultant = DeepLConsultationBase()
        self.style_modernizer = StyleModernizer()
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """Разбить текст на параграфы"""
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    def translate_with_context(self, paragraphs: List[str], 
                             context: ChapterContext) -> List[str]:
        """Перевести параграфы с учетом контекста"""
        translations = []
        
        for paragraph in paragraphs:
            # Ищем похожие переводы в памяти
            similar = self.memory_manager.find_similar(paragraph)
            
            if similar:
                # Используем похожий перевод как основу
                base_translation = similar[0]['target_text']
                character = similar[0].get('character')
            else:
                # Базовый перевод (здесь должен быть вызов переводчика)
                base_translation = paragraph  # Заглушка
                character = None
            
            # Улучшаем диалоги
            if self._contains_dialogue(paragraph):
                character = self.dialogue_improver.detect_character_from_context(
                    paragraph, context.current_scene
                )
                base_translation = self.dialogue_improver.improve_dialogue(
                    base_translation, character
                )
            
            translations.append(base_translation)
        
        return translations
    
    def apply_glossary(self, translations: List[str], glossary: Dict) -> List[str]:
        """Применить глоссарий к переводам"""
        improved_translations = []
        
        for translation in translations:
            improved = translation
            for term, correct_translation in glossary.items():
                # Простая замена - можно улучшить
                improved = improved.replace(term, correct_translation)
            improved_translations.append(improved)
        
        return improved_translations
    
    def fix_common_errors(self, translations: List[str]) -> List[str]:
        """Исправить типичные ошибки"""
        # Загружаем ошибки из файла
        error_patterns = self._load_error_patterns()
        
        fixed_translations = []
        for translation in translations:
            fixed = translation
            for wrong, correct in error_patterns.items():
                fixed = fixed.replace(wrong, correct)
            fixed_translations.append(fixed)
        
        return fixed_translations
    
    def _load_error_patterns(self) -> Dict[str, str]:
        """Загрузить паттерны ошибок"""
        error_patterns = {}
        try:
            with open('ошибки-перевода.txt', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсим файл ошибок (упрощенная версия)
            lines = content.split('\n')
            for line in lines:
                if '❌ НЕПРАВИЛЬНО:' in line and '✅ ПРАВИЛЬНО:' in line:
                    # Извлекаем неправильный и правильный варианты
                    wrong_match = re.search(r'❌ НЕПРАВИЛЬНО: (.+)', line)
                    correct_match = re.search(r'✅ ПРАВИЛЬНО: (.+)', line)
                    
                    if wrong_match and correct_match:
                        wrong = wrong_match.group(1).strip()
                        correct = correct_match.group(1).strip()
                        error_patterns[wrong] = correct
        
        except Exception as e:
            print(f"⚠️ Ошибка загрузки паттернов ошибок: {e}")
        
        return error_patterns
    
    def improve_dialogues(self, translations: List[str], 
                         context: ChapterContext) -> List[str]:
        """Улучшить диалоги"""
        improved = []
        for translation in translations:
            if self._contains_dialogue(translation):
                character = self.dialogue_improver.detect_character_from_context(
                    translation, context.current_scene
                )
                improved_translation = self.dialogue_improver.improve_dialogue(
                    translation, character
                )
                improved.append(improved_translation)
            else:
                improved.append(translation)
        
        return improved
    
    def validate_consistency(self, translations: List[str], 
                           context: ChapterContext) -> Tuple[List[str], Dict]:
        """Проверить консистентность"""
        issues = []
        
        # Проверяем качество каждого перевода
        for i, translation in enumerate(translations):
            scores = self.quality_evaluator.evaluate_translation(
                "", translation  # source не используется в текущей реализации
            )
            
            # Проверяем пороги качества
            for metric, score in scores.items():
                threshold = MIN_QUALITY_THRESHOLDS.get(metric, 0)
                if score < threshold:
                    issues.append(f"Параграф {i+1}: {metric} = {score:.1f} < {threshold}")
        
        return translations, {"issues": issues, "scores": scores}
    
    def detect_issues(self, text: str) -> List[str]:
        """Обнаружить проблемные места"""
        issues = []
        
        # Проверяем формальные конструкции
        formal_patterns = [
            "Я собираюсь", "Позвольте мне", "Не могли бы вы",
            "Я хотел бы", "Кажется, что", "Я боюсь, что"
        ]
        
        for pattern in formal_patterns:
            if pattern in text:
                issues.append(f"Формальная конструкция: {pattern}")
        
        # Проверяем кальки
        calque_patterns = ["крайне", "весьма", "осуществлять"]
        for pattern in calque_patterns:
            if pattern in text:
                issues.append(f"Калька: {pattern}")
        
        return issues
    
    def consult_deepl_for_issues(self, text: str, issues: List[str]) -> str:
        """Консультация с DeepL для проблемных мест"""
        if not issues:
            return text
        
        # Извлекаем проблемные фрагменты
        problematic_fragments = []
        for issue in issues:
            # Простая эвристика - можно улучшить
            if "Формальная конструкция:" in issue:
                pattern = issue.replace("Формальная конструкция: ", "")
                if pattern in text:
                    problematic_fragments.append(pattern)
        
        if problematic_fragments:
            try:
                # Консультация с DeepL
                results = self.deepl_consultant.consult_fragments(problematic_fragments)
                # Применяем результаты (упрощенная версия)
                return text
            except Exception as e:
                print(f"⚠️ Ошибка консультации с DeepL: {e}")
        
        return text
    
    def modernize_style(self, translations: List[str], context: ChapterContext) -> List[str]:
        """Модернизировать стиль для веб-новеллы"""
        modernized = []
        
        for translation in translations:
            # Определяем персонажа по контексту
            character = self._detect_character_from_text(translation)
            
            # Модернизируем в зависимости от персонажа
            if character in CHARACTER_STYLES:
                character_style = CHARACTER_STYLES[character]["style"]
                if character_style == "modern_casual":
                    modernized_text = self.style_modernizer.modernize_character_thoughts(translation, character)
                else:
                    modernized_text = self.style_modernizer.modernize_text(translation, "adult")
            else:
                modernized_text = self.style_modernizer.modernize_text(translation, "adult")
            
            # Модернизируем системные уведомления
            modernized_text = self.style_modernizer.modernize_system_notifications(modernized_text)
            
            modernized.append(modernized_text)
        
        return modernized
    
    def _detect_character_from_text(self, text: str) -> str:
        """Определить персонажа по тексту"""
        if "Цзян Чэнь" in text or "Jiang Chen" in text:
            return "Jiang_Chen"
        elif "Е Цинчэн" in text or "Ye Qingcheng" in text:
            return "Ye_Qingcheng"
        elif "Ду Гуюнь" in text or "Du Guyun" in text:
            return "Du_Guyun"
        elif "Старейшина" in text or "Elder" in text:
            return "Elders"
        elif "Динь!" in text or "Система" in text:
            return "System"
        return "Unknown"
    
    def _contains_dialogue(self, text: str) -> bool:
        """Проверить, содержит ли текст диалог"""
        dialogue_indicators = ['"', '"', '—', '«', '»']
        return any(indicator in text for indicator in dialogue_indicators)
    
    def process_chapter(self, chapter_file: str, context: ChapterContext) -> Dict[str, Any]:
        """Обработать главу полностью (новая архитектура)"""
        print(f"🚀 ОБРАБОТКА ГЛАВЫ {context.chapter_number}")
        print("=" * 50)
        
        # Читаем файл
        try:
            with open(chapter_file, 'r', encoding='utf-8') as f:
                original_text = f.read()
        except Exception as e:
            return {"error": f"Ошибка чтения файла: {e}"}
        
        # Создаем контекст для нового переводчика
        translation_context = TranslationContext(
            chapter_number=context.chapter_number,
            previous_chapters=context.previous_chapters,
            main_characters=context.main_characters,
            current_scene=context.current_scene,
            emotional_tone=context.emotional_tone,
            translation_style="modern_web_novel"
        )
        
        # Новые этапы обработки
        stages = [
            ("Разбивка на сегменты", lambda: self.splitter.create_segments(original_text)),
            ("Перевод с контекстом", lambda: self.translator.translate_with_context(original_text, translation_context)),
            ("Модернизация стиля", lambda: self._modernize_translation_results(original_text, translation_context)),
            ("Валидация качества", lambda: self.validator.validate_chapter(original_text, original_text, {}))
        ]
        
        results = {"stages": [], "original_text": original_text}
        current_data = None
        
        for stage_name, stage_func in stages:
            print(f"📝 {stage_name}...")
            
            try:
                if stage_name == "Разбивка на сегменты":
                    current_data = stage_func()
                    results["segments"] = current_data
                elif stage_name == "Перевод с контекстом":
                    current_data = stage_func()
                    results["translation_results"] = current_data
                elif stage_name == "Модернизация стиля":
                    current_data = stage_func()
                    results["modernized_text"] = current_data
                elif stage_name == "Валидация качества":
                    current_data = stage_func()
                    results["validation"] = current_data
                
                results["stages"].append({
                    "name": stage_name,
                    "status": "completed",
                    "data_type": type(current_data).__name__ if current_data else "None"
                })
                
            except Exception as e:
                results["stages"].append({
                    "name": stage_name,
                    "status": "error",
                    "error": str(e)
                })
                print(f"❌ Ошибка в этапе '{stage_name}': {e}")
        
        # Формируем финальный текст
        if "modernized_text" in results:
            results["final_text"] = results["modernized_text"]
        elif "translation_results" in results:
            # Объединяем результаты перевода
            translated_texts = [r.translated_text for r in results["translation_results"]]
            results["final_text"] = '\n\n'.join(translated_texts)
        else:
            results["final_text"] = original_text
        
        results["chapter"] = context.chapter_number
        results["timestamp"] = datetime.now().isoformat()
        
        print("✅ Обработка завершена")
        return results
    
    def _modernize_translation_results(self, original_text: str, context: TranslationContext) -> str:
        """Модернизировать результаты перевода"""
        # Получаем переведенный текст
        translation_results = self.translator.translate_with_context(original_text, context)
        translated_text = '\n\n'.join([r.translated_text for r in translation_results])
        
        # Модернизируем стиль
        modernized_text = self.style_modernizer.modernize_text(translated_text, "adult")
        
        return modernized_text

def test_auto_processor():
    """Тестирование автоматического процессора"""
    print("🧪 ТЕСТИРОВАНИЕ АВТОМАТИЧЕСКОГО ПРОЦЕССОРА")
    print("=" * 50)
    
    processor = ChapterProcessor()
    
    # Создаем тестовый контекст
    context = ChapterContext(
        chapter_number="Тест",
        previous_chapters=["Глава 1", "Глава 2"],
        main_characters=["Цзян Чэнь", "Е Цинчэн"],
        current_scene="Диалог в горах",
        emotional_tone="напряженный"
    )
    
    # Тестируем отдельные компоненты
    test_text = "Jiang Chen said: 'I am going to the mountain.'"
    
    # Улучшение диалогов
    improved = processor.dialogue_improver.improve_dialogue(test_text, "Jiang_Chen")
    print(f"Улучшенный диалог: {improved}")
    
    # Оценка качества
    scores = processor.quality_evaluator.evaluate_translation("", improved)
    print(f"Оценки качества: {scores}")
    
    # Обнаружение проблем
    issues = processor.detect_issues(improved)
    print(f"Обнаруженные проблемы: {issues}")

if __name__ == "__main__":
    test_auto_processor()
