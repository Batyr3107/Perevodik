#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Переводчик глав с учетом контекста
Интегрирует различные источники переводов и контекстную память
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from config import get_api_key, TRANSLATION_MEMORY
from tools.context_manager import TranslationMemoryManager
from tools.consultation_base import DeepLConsultationBase
from tools.chapter_splitter import ChapterSplitter, TextSegment
from tools.deepl_cache import CachedDeepLTranslator
from tools.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity, handle_errors
from tools.character_detector import CharacterDetector, CharacterType
from tools.performance_optimizer import PerformanceOptimizer, optimize_performance

@dataclass
class TranslationContext:
    """Контекст для перевода"""
    chapter_number: str
    previous_chapters: List[str]
    main_characters: List[str]
    current_scene: str
    emotional_tone: str
    translation_style: str = "modern_web_novel"

@dataclass
class TranslationResult:
    """Результат перевода"""
    original_text: str
    translated_text: str
    translator: str
    confidence: float
    context_used: bool
    memory_hit: bool
    quality_score: float
    timestamp: str

class ChapterTranslator:
    """Переводчик глав с контекстной памятью"""
    
    def __init__(self):
        self.memory_manager = TranslationMemoryManager()
        self.deepl_consultant = DeepLConsultationBase()
        self.splitter = ChapterSplitter()
        
        # Кэшированный DeepL переводчик
        self.cached_translator = CachedDeepLTranslator()
        
        # Обработчик ошибок
        self.error_handler = ErrorHandler()
        
        # Детектор персонажей
        self.character_detector = CharacterDetector()
        
        # Оптимизатор производительности
        self.performance_optimizer = PerformanceOptimizer()
        
        # Локальный кэш для быстрого доступа
        self.translation_cache = {}
        
    @optimize_performance("translate_with_context")
    def translate_with_context(self, text: str, context: TranslationContext) -> List[TranslationResult]:
        """Перевести текст с учетом контекста"""
        print(f"🔄 Перевод главы {context.chapter_number} с контекстом...")
        
        # Разбиваем построчно для сохранения структуры
        segments = self.splitter.split_by_lines(text)
        results = []
        
        # Оптимизированная обработка сегментов
        if len(segments) > 10:
            # Для больших текстов используем пакетную обработку
            results = self._translate_segments_batch(segments, context)
        else:
            # Для малых текстов обрабатываем последовательно
            for segment in segments:
                result = self._translate_segment(segment, context)
                results.append(result)
                
                # Сохраняем в память для будущего использования
                self._save_to_memory(segment, result, context)
        
        return results
    
    def _translate_segments_batch(self, segments: List[TextSegment], context: TranslationContext) -> List[TranslationResult]:
        """Пакетная обработка сегментов для оптимизации"""
        results = []
        
        # Группируем сегменты по типам для оптимизации
        dialogue_segments = [s for s in segments if s.is_dialogue]
        system_segments = [s for s in segments if s.is_system]
        other_segments = [s for s in segments if not s.is_dialogue and not s.is_system]
        
        # Обрабатываем каждую группу
        for segment_group, group_name in [(dialogue_segments, "dialogue"), 
                                        (system_segments, "system"), 
                                        (other_segments, "other")]:
            if segment_group:
                print(f"📝 Обработка {len(segment_group)} {group_name} сегментов...")
                
                for segment in segment_group:
                    result = self._translate_segment(segment, context)
                    results.append(result)
                    self._save_to_memory(segment, result, context)
        
        return results
    
    def _translate_segment(self, segment: TextSegment, context: TranslationContext) -> TranslationResult:
        """Перевести отдельный сегмент"""
        
        # Если пустая строка - возвращаем как есть
        if segment.segment_type == 'empty_line' or not segment.content.strip():
            return TranslationResult(
                original_text=segment.content,
                translated_text='',
                translator="Empty_Line",
                confidence=1.0,
                context_used=False,
                memory_hit=False,  # Не сохраняем пустые строки в память
                quality_score=100.0,
                timestamp=datetime.now().isoformat()
            )
        
        # Проверяем кэш
        cache_key = f"{segment.content}_{context.translation_style}"
        if cache_key in self.translation_cache:
            cached_result = self.translation_cache[cache_key]
            return TranslationResult(
                original_text=segment.content,
                translated_text=cached_result['translated_text'],
                translator="Cache",
                confidence=0.9,
                context_used=True,
                memory_hit=True,
                quality_score=cached_result['quality_score'],
                timestamp=datetime.now().isoformat()
            )
        
        # Сначала ищем готовый перевод фразы в справочной базе
        phrase_translation = self.memory_manager.get_phrase_translation(
            segment.content, 
            context.chapter_number
        )
        
        if phrase_translation:
            return TranslationResult(
                original_text=segment.content,
                translated_text=phrase_translation,
                translator="Reference_Base",
                confidence=1.0,
                context_used=True,
                memory_hit=True,
                quality_score=98.0,
                timestamp=datetime.now().isoformat()
            )
        
        # Ищем похожие переводы в памяти
        similar_translations = self.memory_manager.find_similar(
            segment.content, 
            threshold=TRANSLATION_MEMORY["similarity_threshold"]
        )
        
        if similar_translations:
            # Используем похожий перевод как основу
            best_match = similar_translations[0]
            base_translation = best_match['target_text']
        else:
            # Базовый перевод через DeepL
            base_translation = self.cached_translator.translate_text(segment.content)
        
        # Применяем глоссарий
        base_translation = self._apply_glossary(base_translation)
        
        # Проверяем запрещенные слова
        base_translation = self._check_forbidden_words(base_translation)
        
        # Применяем стили персонажей
        character_type, confidence = self.character_detector.detect_character_from_text(segment.content)
        if character_type != CharacterType.UNKNOWN:
            base_translation = self._apply_character_style(base_translation, character_type.value)
        
        # Адаптируем под текущий контекст
        adapted_translation = self._adapt_translation(
            base_translation, segment, context
        )
        
        # Определяем источник перевода
        if similar_translations:
            translator = "Memory+Adaptation"
            confidence = similar_translations[0].get('similarity', 0.8)
            memory_hit = True
        else:
            translator = "DeepL+Adaptation"
            confidence = 0.8
            memory_hit = False
        
        result = TranslationResult(
            original_text=segment.content,
            translated_text=adapted_translation,
            translator=translator,
            confidence=confidence,
            context_used=True,
            memory_hit=memory_hit,
            quality_score=self._calculate_quality_score(adapted_translation),
            timestamp=datetime.now().isoformat()
        )
        
        # Кэшируем результат
        self.translation_cache[cache_key] = {
            'translated_text': result.translated_text,
            'quality_score': result.quality_score
        }
        
        return result
    
    def _adapt_translation(self, base_translation: str, segment: TextSegment, 
                          context: TranslationContext) -> str:
        """Адаптировать перевод под текущий контекст"""
        adapted = base_translation
        
        # Адаптация под персонажа
        if segment.character:
            adapted = self._adapt_for_character(adapted, segment.character, context)
        
        # Адаптация под сцену
        if context.current_scene:
            adapted = self._adapt_for_scene(adapted, context.current_scene)
        
        # Адаптация под эмоциональный тон
        if context.emotional_tone:
            adapted = self._adapt_for_tone(adapted, context.emotional_tone)
        
        return adapted
    
    def _adapt_for_character(self, text: str, character: str, context: TranslationContext) -> str:
        """Адаптировать перевод под персонажа"""
        # Определяем тип персонажа
        char_type, confidence = self.character_detector.detect_character_from_text(text)
        
        if char_type != CharacterType.UNKNOWN and confidence > 0.5:
            # Получаем предпочтения персонажа
            avoid_words = self.character_detector.get_character_avoid_words(char_type)
            prefer_words = self.character_detector.get_character_prefer_words(char_type)
            
            # Убираем нежелательные слова
            for word in avoid_words:
                if word in text:
                    # Заменяем на более подходящее слово
                    replacement = self._find_replacement(word, prefer_words)
                    text = text.replace(word, replacement)
            
            # Применяем предпочитаемые слова где возможно
            for word in prefer_words:
                if word not in text and self._should_apply_word(word, text):
                    # Логика применения предпочитаемых слов
                    pass
        
        return text
    
    def _find_replacement(self, word: str, prefer_words: List[str]) -> str:
        """Найти замену для нежелательного слова"""
        # Простая логика замены - можно расширить
        replacements = {
            "сей": "этот",
            "дабы": "чтобы", 
            "ибо": "потому что",
            "весьма": "очень",
            "отнюдь": "совсем не"
        }
        
        return replacements.get(word, word)
    
    def _should_apply_word(self, word: str, text: str) -> bool:
        """Определить, стоит ли применять предпочитаемое слово"""
        # Простая логика - можно расширить
        return len(text) > 20 and word not in text
    
    def _adapt_for_scene(self, text: str, scene: str) -> str:
        """Адаптировать перевод под сцену"""
        # Простая адаптация - можно расширить
        scene_adaptations = {
            "боевая": {
                "замедленно": "медленно",
                "осторожно": "осторожно"
            },
            "романтическая": {
                "грубо": "нежно",
                "резко": "мягко"
            }
        }
        
        if scene in scene_adaptations:
            adaptations = scene_adaptations[scene]
            for old, new in adaptations.items():
                text = text.replace(old, new)
        
        return text
    
    def _adapt_for_tone(self, text: str, tone: str) -> str:
        """Адаптировать перевод под эмоциональный тон"""
        tone_adaptations = {
            "напряженный": {
                "спокойно": "напряженно",
                "медленно": "быстро"
            },
            "грустный": {
                "радостно": "грустно",
                "весело": "печально"
            }
        }
        
        if tone in tone_adaptations:
            adaptations = tone_adaptations[tone]
            for old, new in adaptations.items():
                text = text.replace(old, new)
        
        return text
    
    def _calculate_quality_score(self, text: str) -> float:
        """Рассчитать оценку качества перевода"""
        score = 80.0  # Базовая оценка
        
        # Проверяем длину
        if len(text) < 10:
            score -= 20
        elif len(text) > 500:
            score -= 10
        
        # Проверяем на архаизмы
        archaisms = ["сей", "дабы", "ибо", "весьма", "отнюдь"]
        for archaism in archaisms:
            if archaism in text.lower():
                score -= 5
        
        # Проверяем на естественность
        natural_patterns = ["Дай мне", "Можешь", "Хочу", "Похоже"]
        for pattern in natural_patterns:
            if pattern in text:
                score += 2
        
        return max(0, min(100, score))
    
    def _save_to_memory(self, segment: TextSegment, result: TranslationResult, 
                       context: TranslationContext):
        """Сохранить перевод в память"""
        try:
            from tools.context_manager import TranslationMemory
            
            memory = TranslationMemory(
                source_text=segment.content,
                target_text=result.translated_text,
                chapter=context.chapter_number,
                character=segment.character,
                context=context.current_scene,
                quality_score=result.quality_score
            )
            
            self.memory_manager.add_translation(memory)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения в память: {e}")
    
    def _apply_glossary(self, text: str) -> str:
        """Применить глоссарий к переводу"""
        if not self.memory_manager.reference_data or 'glossary_terms' not in self.memory_manager.reference_data:
            return text
        
        glossary = self.memory_manager.reference_data['glossary_terms']
        
        # Применяем термины из всех категорий глоссария
        for category, terms in glossary.items():
            for english_term, russian_term in terms.items():
                # Заменяем английские термины на русские
                text = text.replace(english_term, russian_term)
        
        return text
    
    def _check_forbidden_words(self, text: str) -> str:
        """Проверить и заменить запрещенные слова"""
        forbidden_words = self.memory_manager.get_forbidden_words()
        
        if not forbidden_words:
            return text
        
        # Получаем предпочтительные альтернативы
        alternatives = {}
        if (self.memory_manager.reference_data and 
            'translation_errors' in self.memory_manager.reference_data and
            'preferred_alternatives' in self.memory_manager.reference_data['translation_errors']):
            alternatives = self.memory_manager.reference_data['translation_errors']['preferred_alternatives']
        
        # Заменяем запрещенные слова
        for forbidden_word in forbidden_words:
            if forbidden_word in text:
                if forbidden_word in alternatives:
                    # Используем первую альтернативу
                    alternative = alternatives[forbidden_word].split(',')[0].strip()
                    text = text.replace(forbidden_word, alternative)
                    print(f"⚠️ Заменено запрещенное слово '{forbidden_word}' на '{alternative}'")
                else:
                    print(f"⚠️ Найдено запрещенное слово: '{forbidden_word}'")
        
        return text
    
    def _apply_character_style(self, text: str, character: str) -> str:
        """Применить стиль персонажа"""
        character_style = self.memory_manager.get_character_style(character)
        
        if not character_style or 'examples' not in character_style:
            return text
        
        examples = character_style['examples']
        
        # Применяем стилистические замены
        for english_word, russian_style in examples.items():
            if english_word.lower() in text.lower():
                text = text.replace(english_word, russian_style)
        
        return text
    
    def _validate_structure(self, original_text: str, translated_text: str) -> Dict[str, Any]:
        """Проверить соответствие структуры оригинала и перевода"""
        original_lines = original_text.split('\n')
        translated_lines = translated_text.split('\n')
        
        validation = {
            'structure_match': len(original_lines) == len(translated_lines),
            'original_lines': len(original_lines),
            'translated_lines': len(translated_lines),
            'empty_lines_match': True,
            'issues': []
        }
        
        if not validation['structure_match']:
            validation['issues'].append(f"Количество строк не совпадает: {len(original_lines)} → {len(translated_lines)}")
        
        # Проверяем пустые строки
        for i, (orig_line, trans_line) in enumerate(zip(original_lines, translated_lines)):
            orig_empty = not orig_line.strip()
            trans_empty = not trans_line.strip()
            
            if orig_empty != trans_empty:
                validation['empty_lines_match'] = False
                validation['issues'].append(f"Строка {i+1}: пустая в оригинале ({orig_empty}) != пустая в переводе ({trans_empty})")
        
        return validation
    
    def translate_file(self, file_path: str, context: TranslationContext) -> Dict[str, Any]:
        """Перевести файл целиком"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            results = self.translate_with_context(text, context)
            
            # Объединяем результаты построчно
            translated_text = '\n'.join([r.translated_text for r in results])
            
            # Проверяем структуру
            structure_validation = self._validate_structure(text, translated_text)
            
            if not structure_validation['structure_match']:
                print(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Структура не совпадает!")
                for issue in structure_validation['issues']:
                    print(f"   • {issue}")
            
            # Статистика
            total_segments = len(results)
            memory_hits = sum(1 for r in results if r.memory_hit)
            avg_quality = sum(r.quality_score for r in results) / total_segments if total_segments > 0 else 0
            
            return {
                'original_text': text,
                'translated_text': translated_text,
                'results': results,
                'structure_validation': structure_validation,
                'statistics': {
                    'total_segments': total_segments,
                    'memory_hits': memory_hits,
                    'memory_hit_rate': memory_hits / total_segments if total_segments > 0 else 0,
                    'average_quality': avg_quality,
                    'translators_used': list(set(r.translator for r in results))
                },
                'context': context,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Ошибка перевода файла: {e}")
            return {'error': str(e)}

def test_chapter_translator():
    """Тестирование переводчика глав"""
    print("🧪 ТЕСТИРОВАНИЕ ПЕРЕВОДЧИКА ГЛАВ")
    print("=" * 50)
    
    translator = ChapterTranslator()
    
    # Создаем тестовый контекст
    context = TranslationContext(
        chapter_number="Тест",
        previous_chapters=["Глава 1"],
        main_characters=["Цзян Чэнь", "Е Цинчэн"],
        current_scene="Диалог в горах",
        emotional_tone="напряженный"
    )
    
    # Тестовый текст
    test_text = """"Finally, she's gone!" Jiang Chen exhaled with relief.

From his perspective, apart from being brainless, Ye Qingcheng was like bad luck - better to stay as far away from her as possible.

"System, would it count as interfering with slacking off if I take action?" Jiang Chen inquired."""
    
    # Тест перевода
    results = translator.translate_with_context(test_text, context)
    
    print(f"📝 Переведено сегментов: {len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Переводчик: {result.translator}")
        print(f"   Качество: {result.quality_score:.1f}/100")
        print(f"   Память: {'Да' if result.memory_hit else 'Нет'}")
        print(f"   Текст: {result.translated_text[:100]}...")
    
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    test_chapter_translator()
