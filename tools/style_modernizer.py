#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модернизатор стиля для веб-новелл
Приземляет высокопарный стиль до уровня "читается в метро"
"""

import re
from typing import Dict, List, Tuple

class StyleModernizer:
    """Приземляет высокопарный стиль до современного уровня"""
    
    def __init__(self):
        # Основные замены архаизмов
        self.basic_replacements = {
            # Архаизмы
            "воззрел": "посмотрел",
            "молвил": "сказал", 
            "вопрошал": "спрашивал",
            "весьма": "очень",
            "чрезвычайно": "очень",
            "дабы": "чтобы",
            "ибо": "потому что",
            "сей": "этот",
            "сия": "эта", 
            "оный": "тот",
            "ныне": "сейчас",
            "отнюдь": "совсем не",
            "непременно": "обязательно",
            "воистину": "правда",
            "осуществлять": "делать",
            "производить впечатление": "впечатлять",
            "испытывать чувство": "чувствовать",
            
            # Культивационные термины (упрощаем)
            "постичь Дао": "понять Дао",
            "снискать милость": "получить расположение", 
            "явить могущество": "показать силу",
            "вознести хвалу": "похвалить",
            "преодолеть небесную кару": "пройти небесную кару",
            "вступить в схватку": "начать бой",
            "потерпеть поражение": "проиграть",
            
            # Эмоции и реакции
            "преисполнился гневом": "разозлился",
            "впал в ярость": "взбесился", 
            "ощутил трепет": "испугался",
            "воспылал страстью": "влюбился",
            "погрузился в раздумья": "задумался",
            "издал вздох": "вздохнул",
            
            # Системные уведомления
            "Оповещение:": "Динь!",
            "Вы удостоены": "Получено",
            "награды:": "награда:",
            "благословение:": "награда:",
            "ниспослала": "дала",
            "даруется": "получено",
        }
        
        # Запрещённые архаизмы (полностью убираем)
        self.banned_archaisms = [
            "сей", "сия", "оный", "дабы", "ибо",
            "воистину", "весьма", "отнюдь", "непременно",
            "молвить", "воззреть", "вопрошать", "ныне"
        ]
        
        # Современные замены для молодых персонажей
        self.youth_slang = {
            "очень мощный": "крутой",
            "действительно": "реально", 
            "прекрасно": "топово",
            "удивительно": "прикольно",
            "страшно": "жёстко",
            "быстро": "быстро как молния",
            "сильный": "мощный",
            "красивый": "красивый как бог"
        }
        
        # Максимальная длина предложения
        self.max_sentence_length = 15
        
    def modernize_text(self, text: str, character_age: str = "adult") -> str:
        """Модернизирует текст для веб-новеллы"""
        
        # 1. Заменяем архаизмы
        modernized = self._replace_archaisms(text)
        
        # 2. Упрощаем длинные предложения
        modernized = self._simplify_sentences(modernized)
        
        # 3. Применяем сленг для молодых персонажей
        if character_age in ["young", "teen", "student"]:
            modernized = self._apply_youth_slang(modernized)
            
        # 4. Улучшаем диалоги
        modernized = self._modernize_dialogue(modernized)
        
        # 5. Упрощаем описания
        modernized = self._simplify_descriptions(modernized)
        
        return modernized
    
    def _replace_archaisms(self, text: str) -> str:
        """Заменяет архаизмы на современные слова"""
        for old, new in self.basic_replacements.items():
            text = text.replace(old, new)
        return text
    
    def _simplify_sentences(self, text: str) -> str:
        """Разбивает длинные предложения на короткие"""
        sentences = re.split(r'[.!?]+', text)
        result = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            words = sentence.split()
            if len(words) > self.max_sentence_length:
                # Разбиваем длинное предложение
                parts = self._split_long_sentence(sentence)
                result.extend(parts)
            else:
                result.append(sentence)
        
        return '. '.join(result) + '.'
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Разбивает длинное предложение на части"""
        words = sentence.split()
        if len(words) <= self.max_sentence_length:
            return [sentence]
        
        # Ищем место для разрыва (союзы, запятые)
        break_points = []
        for i, word in enumerate(words):
            if word.lower() in ['и', 'а', 'но', 'что', 'который', 'где', 'когда']:
                break_points.append(i)
        
        if not break_points:
            # Разбиваем пополам
            mid = len(words) // 2
            part1 = ' '.join(words[:mid])
            part2 = ' '.join(words[mid:])
            return [part1, part2]
        
        # Разбиваем в лучшем месте
        best_break = min(break_points, key=lambda x: abs(x - len(words) // 2))
        part1 = ' '.join(words[:best_break])
        part2 = ' '.join(words[best_break:])
        return [part1, part2]
    
    def _apply_youth_slang(self, text: str) -> str:
        """Применяет молодёжный сленг"""
        for old, new in self.youth_slang.items():
            text = text.replace(old, new)
        return text
    
    def _modernize_dialogue(self, text: str) -> str:
        """Улучшает диалоги"""
        # Убираем излишнюю вежливость
        dialogue_replacements = {
            "Позвольте мне": "Дай мне",
            "Не соблаговолите ли вы": "Не могли бы вы",
            "Осмелюсь спросить": "Можно спросить?",
            "Сие деяние недопустимо": "Так нельзя",
            "Воистину могущественный": "Реально мощный",
            "Я хотел бы": "Хочу",
            "Кажется, что": "Похоже",
            "Я боюсь, что": "Боюсь",
            "Что ты думаешь о": "Как тебе",
            "Я не понимаю": "Не понимаю",
            "Это не то, что я имел в виду": "Не то имел в виду",
            "Я не могу поверить": "Не верю"
        }
        
        for old, new in dialogue_replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _simplify_descriptions(self, text: str) -> str:
        """Упрощает описания"""
        # Убираем излишние эпитеты
        description_patterns = [
            (r'глубочайшим\s+', ''),
            (r'непостижимыми\s+', ''),
            (r'бездонным\s+', ''),
            (r'всепоглощающим\s+', ''),
            (r'необъятным\s+', ''),
            (r'неисчерпаемым\s+', ''),
        ]
        
        for pattern, replacement in description_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def modernize_character_thoughts(self, text: str, character: str) -> str:
        """Модернизирует мысли персонажа"""
        if character == "Jiang_Chen":
            # Цзян Чэнь - современный, грубоватый
            thoughts_replacements = {
                "Неужели": "Серьёзно?",
                "Должен ли я": "Мне что,",
                "смириться с ролью": "быть",
                "презренного подхалима": "подхалимом",
                "Да пошло оно всё": "Да ну нафиг",
                "не буду я больше": "не буду",
                "подлизываться": "подлизываться",
                "безмозглая дева": "дурочка",
                "вновь являет свою глупость": "опять тупит",
                "не способна узреть очевидное": "не видит очевидного",
                "Воистину, терпение моё на исходе": "Блин, как же бесит",
                "Сия": "Эта",
                "безмозглая": "дурацкая"
            }
        elif character == "Ye_Qingcheng":
            # Е Цинчэн - более формальная, но не архаичная
            thoughts_replacements = {
                "Неужели": "Неужели",
                "Должен ли я": "Мне что",
                "смириться с ролью": "быть",
                "презренного подхалима": "подхалимом"
            }
        else:
            thoughts_replacements = {}
        
        for old, new in thoughts_replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def modernize_system_notifications(self, text: str) -> str:
        """Модернизирует системные уведомления"""
        system_replacements = {
            "Оповещение: За успешное уклонение от деятельности": "Динь! За успешное безделье",
            "Вы удостоены награды:": "Получено:",
            "благословение:": "награда:",
            "ниспослала": "дала",
            "даруется": "получено",
            "Священная Техника": "Священная техника",
            "Императорское Орудие": "Императорское оружие",
            "Всенебесное Зеркало": "«Всенебесное Зеркало»",
            "Вселенная в Длани": "«Вселенная в Ладони»"
        }
        
        for old, new in system_replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def calculate_readability_score(self, text: str) -> Dict[str, float]:
        """Рассчитывает показатели читабельности"""
        sentences = re.split(r'[.!?]+', text)
        words = text.split()
        
        # Средняя длина предложения
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Количество архаизмов
        archaism_count = sum(1 for archaism in self.banned_archaisms 
                           if archaism in text.lower())
        
        # Процент длинных предложений
        long_sentences = sum(1 for sentence in sentences 
                           if len(sentence.split()) > self.max_sentence_length)
        long_sentence_percentage = (long_sentences / len(sentences)) * 100 if sentences else 0
        
        # Оценка читабельности (0-100, где 100 = очень легко)
        readability_score = 100 - (avg_sentence_length * 2) - (archaism_count * 5) - (long_sentence_percentage * 0.5)
        readability_score = max(0, min(100, readability_score))
        
        return {
            "readability_score": readability_score,
            "avg_sentence_length": avg_sentence_length,
            "archaism_count": archaism_count,
            "long_sentence_percentage": long_sentence_percentage
        }

def test_style_modernizer():
    """Тестирование модернизатора стиля"""
    print("🧪 ТЕСТИРОВАНИЕ СТИЛЬ-МОДЕРНИЗАТОРА")
    print("=" * 50)
    
    modernizer = StyleModernizer()
    
    # Тестовые тексты
    test_cases = [
        {
            "text": "Цзян Чэнь воззрел на простирающиеся пред ним просторы Изначальной Святой Земли, и сердце его преисполнилось глубочайшим презрением к сей юдоли подхалимства.",
            "character": "Jiang_Chen",
            "expected": "современный стиль"
        },
        {
            "text": "Оповещение: За успешное уклонение от деятельности Вы удостоены награды: Императорское Орудие Всенебесное Зеркало",
            "character": "System",
            "expected": "игровой стиль"
        },
        {
            "text": "Младшая сестра Е, прошу вас не препятствовать моим действиям, ибо намерения мои непреклонны",
            "character": "Jiang_Chen", 
            "expected": "естественный диалог"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 ТЕСТ {i}: {case['expected']}")
        print("-" * 30)
        
        original = case["text"]
        modernized = modernizer.modernize_text(original, case["character"])
        
        print(f"Оригинал: {original}")
        print(f"Модернизировано: {modernized}")
        
        # Оценка читабельности
        scores = modernizer.calculate_readability_score(modernized)
        print(f"Читабельность: {scores['readability_score']:.1f}/100")
        print(f"Средняя длина предложения: {scores['avg_sentence_length']:.1f} слов")
        print(f"Архаизмов: {scores['archaism_count']}")

if __name__ == "__main__":
    test_style_modernizer()
