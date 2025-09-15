#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детектор персонажей для определения стиля речи и мыслей
Анализирует текст и определяет, какой персонаж говорит или думает
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class CharacterType(Enum):
    """Типы персонажей"""
    JIANG_CHEN = "Jiang_Chen"
    YE_QINGCHENG = "Ye_Qingcheng"
    DU_GUYUN = "Du_Guyun"
    ELDER = "Elder"
    SYSTEM = "System"
    NARRATOR = "Narrator"
    UNKNOWN = "Unknown"

@dataclass
class CharacterProfile:
    """Профиль персонажа"""
    name: str
    character_type: CharacterType
    speech_patterns: List[str]
    thought_patterns: List[str]
    keywords: List[str]
    style_preferences: Dict[str, Any]
    avoid_words: List[str]
    prefer_words: List[str]

class CharacterDetector:
    """Детектор персонажей для анализа текста"""
    
    def __init__(self, profiles_file: str = "character_voices.json"):
        self.profiles_file = profiles_file
        self.character_profiles = self._load_character_profiles()
        
        # Паттерны для определения персонажей
        self.name_patterns = {
            "Цзян Чэнь": CharacterType.JIANG_CHEN,
            "Jiang Chen": CharacterType.JIANG_CHEN,
            "цзян чэнь": CharacterType.JIANG_CHEN,
            "jiang chen": CharacterType.JIANG_CHEN,
            
            "Е Цинчэн": CharacterType.YE_QINGCHENG,
            "Ye Qingcheng": CharacterType.YE_QINGCHENG,
            "е цинчэн": CharacterType.YE_QINGCHENG,
            "ye qingcheng": CharacterType.YE_QINGCHENG,
            
            "Ду Гуюнь": CharacterType.DU_GUYUN,
            "Du Guyun": CharacterType.DU_GUYUN,
            "ду гуюнь": CharacterType.DU_GUYUN,
            "du guyun": CharacterType.DU_GUYUN,
            
            "Старейшина": CharacterType.ELDER,
            "Elder": CharacterType.ELDER,
            "старейшина": CharacterType.ELDER,
            "elder": CharacterType.ELDER,
        }
        
        # Системные паттерны
        self.system_patterns = [
            r"Динь!.*",
            r"Система.*",
            r"Оповещение.*",
            r"Получено.*",
            r"Награда.*",
            r"System.*",
            r"Notification.*"
        ]
        
        # Паттерны диалогов
        self.dialogue_patterns = [
            r'"[^"]*"',  # Обычные кавычки
            r'«[^»]*»',  # Ёлочки
            r'—[^—]*—',  # Тире
        ]
        
        # Паттерны мыслей
        self.thought_patterns = [
            r'\[[^\]]*\]',  # Квадратные скобки
            r'\([^)]*\)',   # Круглые скобки
        ]
    
    def _load_character_profiles(self) -> Dict[CharacterType, CharacterProfile]:
        """Загрузить профили персонажей"""
        try:
            with open(self.profiles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profiles = {}
            for char_type, profile_data in data.items():
                if char_type in [e.value for e in CharacterType]:
                    char_enum = CharacterType(char_type)
                    profiles[char_enum] = CharacterProfile(
                        name=profile_data.get("name", char_type),
                        character_type=char_enum,
                        speech_patterns=profile_data.get("speech_patterns", []),
                        thought_patterns=profile_data.get("thought_patterns", []),
                        keywords=profile_data.get("keywords", []),
                        style_preferences=profile_data.get("style_preferences", {}),
                        avoid_words=profile_data.get("avoid", []),
                        prefer_words=profile_data.get("prefer", [])
                    )
            
            return profiles
        except Exception as e:
            print(f"⚠️ Ошибка загрузки профилей персонажей: {e}")
            return self._create_default_profiles()
    
    def _create_default_profiles(self) -> Dict[CharacterType, CharacterProfile]:
        """Создать профили по умолчанию"""
        return {
            CharacterType.JIANG_CHEN: CharacterProfile(
                name="Цзян Чэнь",
                character_type=CharacterType.JIANG_CHEN,
                speech_patterns=["Дай мне", "Можешь", "Хочу"],
                thought_patterns=["Серьёзно?", "Блин", "Да ну нафиг"],
                keywords=["безделье", "система", "награда"],
                style_preferences={"style": "modern_casual"},
                avoid_words=["сей", "дабы", "ибо", "весьма"],
                prefer_words=["круто", "реально", "мощный"]
            ),
            CharacterType.YE_QINGCHENG: CharacterProfile(
                name="Е Цинчэн",
                character_type=CharacterType.YE_QINGCHENG,
                speech_patterns=["Позвольте", "Не могли бы вы", "Я хотела бы"],
                thought_patterns=["Неужели", "Должна ли я"],
                keywords=["элегантность", "красота", "достоинство"],
                style_preferences={"style": "elegant_modern"},
                avoid_words=["сей", "дабы", "ибо", "весьма"],
                prefer_words=["действительно", "очень", "прекрасно"]
            ),
            CharacterType.SYSTEM: CharacterProfile(
                name="Система",
                character_type=CharacterType.SYSTEM,
                speech_patterns=["Динь!", "Получено", "Награда"],
                thought_patterns=[],
                keywords=["система", "награда", "уведомление"],
                style_preferences={"style": "game_like"},
                avoid_words=[],
                prefer_words=["Динь!", "Награда получена!"]
            )
        }
    
    def detect_character_from_text(self, text: str) -> Tuple[CharacterType, float]:
        """Определить персонажа по тексту"""
        # Проверяем прямые упоминания имен
        for name, char_type in self.name_patterns.items():
            if name in text:
                return char_type, 1.0
        
        # Проверяем системные паттерны
        for pattern in self.system_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return CharacterType.SYSTEM, 0.9
        
        # Анализируем стиль речи
        style_analysis = self._analyze_speech_style(text)
        if style_analysis:
            return style_analysis
        
        # Анализируем ключевые слова
        keyword_analysis = self._analyze_keywords(text)
        if keyword_analysis:
            return keyword_analysis
        
        return CharacterType.UNKNOWN, 0.0
    
    def _analyze_speech_style(self, text: str) -> Optional[Tuple[CharacterType, float]]:
        """Анализировать стиль речи"""
        # Проверяем профили персонажей
        best_match = None
        best_score = 0.0
        
        for char_type, profile in self.character_profiles.items():
            score = 0.0
            
            # Проверяем предпочитаемые слова
            for word in profile.prefer_words:
                if word.lower() in text.lower():
                    score += 0.2
            
            # Проверяем избегаемые слова (отрицательный балл)
            for word in profile.avoid_words:
                if word.lower() in text.lower():
                    score -= 0.1
            
            # Проверяем паттерны речи
            for pattern in profile.speech_patterns:
                if pattern.lower() in text.lower():
                    score += 0.3
            
            if score > best_score:
                best_score = score
                best_match = char_type
        
        if best_match and best_score > 0.3:
            return best_match, best_score
        
        return None
    
    def _analyze_keywords(self, text: str) -> Optional[Tuple[CharacterType, float]]:
        """Анализировать ключевые слова"""
        text_lower = text.lower()
        
        # Подсчитываем совпадения ключевых слов
        keyword_scores = {}
        for char_type, profile in self.character_profiles.items():
            score = 0
            for keyword in profile.keywords:
                if keyword.lower() in text_lower:
                    score += 1
            keyword_scores[char_type] = score
        
        # Находим лучшее совпадение
        if keyword_scores:
            best_type = max(keyword_scores, key=keyword_scores.get)
            best_score = keyword_scores[best_type]
            
            if best_score > 0:
                confidence = min(0.8, best_score * 0.2)
                return best_type, confidence
        
        return None
    
    def detect_character_from_dialogue(self, dialogue: str) -> Tuple[CharacterType, float]:
        """Определить персонажа по диалогу"""
        # Убираем кавычки и лишние пробелы
        clean_dialogue = re.sub(r'["«»—]', '', dialogue).strip()
        
        # Анализируем стиль диалога
        return self.detect_character_from_text(clean_dialogue)
    
    def detect_character_from_thoughts(self, thoughts: str) -> Tuple[CharacterType, float]:
        """Определить персонажа по мыслям"""
        # Убираем скобки и лишние пробелы
        clean_thoughts = re.sub(r'[\[\]()]', '', thoughts).strip()
        
        # Анализируем стиль мыслей
        return self.detect_character_from_text(clean_thoughts)
    
    def get_character_style_preferences(self, character_type: CharacterType) -> Dict[str, Any]:
        """Получить предпочтения стиля для персонажа"""
        if character_type in self.character_profiles:
            return self.character_profiles[character_type].style_preferences
        return {}
    
    def get_character_avoid_words(self, character_type: CharacterType) -> List[str]:
        """Получить слова, которых следует избегать для персонажа"""
        if character_type in self.character_profiles:
            return self.character_profiles[character_type].avoid_words
        return []
    
    def get_character_prefer_words(self, character_type: CharacterType) -> List[str]:
        """Получить предпочитаемые слова для персонажа"""
        if character_type in self.character_profiles:
            return self.character_profiles[character_type].prefer_words
        return []
    
    def analyze_text_segments(self, text: str) -> List[Dict[str, Any]]:
        """Анализировать все сегменты текста"""
        segments = []
        
        # Разбиваем на предложения
        sentences = re.split(r'[.!?]+', text)
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Определяем тип сегмента
            segment_type = "description"
            if any(re.search(pattern, sentence) for pattern in self.dialogue_patterns):
                segment_type = "dialogue"
            elif any(re.search(pattern, sentence) for pattern in self.thought_patterns):
                segment_type = "thoughts"
            elif any(re.search(pattern, sentence, re.IGNORECASE) for pattern in self.system_patterns):
                segment_type = "system"
            
            # Определяем персонажа
            character_type, confidence = self.detect_character_from_text(sentence)
            
            segments.append({
                "index": i,
                "text": sentence,
                "type": segment_type,
                "character": character_type.value,
                "confidence": confidence,
                "style_preferences": self.get_character_style_preferences(character_type),
                "avoid_words": self.get_character_avoid_words(character_type),
                "prefer_words": self.get_character_prefer_words(character_type)
            })
        
        return segments
    
    def get_character_statistics(self, text: str) -> Dict[str, Any]:
        """Получить статистику по персонажам в тексте"""
        segments = self.analyze_text_segments(text)
        
        # Подсчитываем статистику
        character_counts = {}
        type_counts = {}
        
        for segment in segments:
            char = segment["character"]
            seg_type = segment["type"]
            
            character_counts[char] = character_counts.get(char, 0) + 1
            type_counts[seg_type] = type_counts.get(seg_type, 0) + 1
        
        return {
            "total_segments": len(segments),
            "character_distribution": character_counts,
            "type_distribution": type_counts,
            "segments": segments
        }
    
    def print_character_analysis(self, text: str):
        """Вывести анализ персонажей"""
        stats = self.get_character_statistics(text)
        
        print("\n🎭 АНАЛИЗ ПЕРСОНАЖЕЙ")
        print("=" * 40)
        print(f"Всего сегментов: {stats['total_segments']}")
        
        print("\nРаспределение по персонажам:")
        for char, count in stats['character_distribution'].items():
            print(f"  • {char}: {count}")
        
        print("\nРаспределение по типам:")
        for seg_type, count in stats['type_distribution'].items():
            print(f"  • {seg_type}: {count}")
        
        print("\nДетальный анализ:")
        for segment in stats['segments'][:5]:  # Показываем первые 5
            print(f"  {segment['index']}. [{segment['type']}] {segment['character']} ({segment['confidence']:.2f})")
            print(f"     {segment['text'][:50]}...")

def test_character_detector():
    """Тестирование детектора персонажей"""
    print("🧪 ТЕСТИРОВАНИЕ ДЕТЕКТОРА ПЕРСОНАЖЕЙ")
    print("=" * 50)
    
    detector = CharacterDetector()
    
    # Тестовые тексты
    test_texts = [
        "Цзян Чэнь посмотрел на гору и подумал: «Да пошло оно всё!»",
        "Е Цинчэн элегантно поклонилась: «Позвольте мне выразить благодарность»",
        "Динь! За успешное безделье получено: Императорское оружие!",
        "Старейшина мудро кивнул: «Молодой человек, путь твой тернист»",
        "Неизвестный персонаж что-то пробормотал"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Тест: {text}")
        char_type, confidence = detector.detect_character_from_text(text)
        print(f"   Результат: {char_type.value} (уверенность: {confidence:.2f})")
    
    # Полный анализ
    full_text = "\n".join(test_texts)
    detector.print_character_analysis(full_text)
    
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    test_character_detector()
