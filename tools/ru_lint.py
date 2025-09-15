#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python скрипт для проверки русского языка в переводах
Альтернатива PowerShell скрипту
"""

import sys
import re
import argparse
from typing import List, Dict, Any, Tuple

class RussianLinter:
    """Линтер для проверки русского языка"""
    
    def __init__(self):
        # Запрещённые архаизмы
        self.banned_archaisms = [
            "сей", "сия", "оный", "дабы", "ибо", 
            "воистину", "весьма", "отнюдь", "непременно",
            "молвить", "воззреть", "вопрошать", "ныне",
            "осуществлять", "производить впечатление", "испытывать чувство"
        ]
        
        # Кальки и канцеляризмы
        self.calques = {
            "крайне": "очень",
            "слева и справа": "направо и налево",
            "совершенна": "идеальна",
            "На его взгляд": "С его точки зрения",
            "резюмировал": "размышлял",
            "осуществлять": "делать",
            "производить впечатление": "впечатлять",
            "испытывать чувство": "чувствовать"
        }
        
        # Формальные конструкции для диалогов
        self.formal_dialogue = {
            "Я собираюсь": "Буду",
            "Позвольте мне": "Дай мне",
            "Не могли бы вы": "Можешь",
            "Я хотел бы": "Хочу",
            "Кажется, что": "Похоже",
            "Я боюсь, что": "Боюсь",
            "Позвольте мне выразить": "Спасибо",
            "Не соблаговолите ли вы": "Не могли бы вы",
            "Осмелюсь спросить": "Можно спросить?",
            "Сие деяние недопустимо": "Так нельзя",
            "Воистину могущественный": "Реально мощный"
        }
        
        # Максимальная длина предложения
        self.max_sentence_length = 15
    
    def check_archaisms(self, text: str) -> List[Dict[str, Any]]:
        """Проверка на архаизмы"""
        issues = []
        
        for archaism in self.banned_archaisms:
            if archaism.lower() in text.lower():
                # Находим все вхождения
                for match in re.finditer(re.escape(archaism), text, re.IGNORECASE):
                    line_number = text[:match.start()].count('\n') + 1
                    context = text[max(0, match.start()-30):match.end()+30]
                    
                    issues.append({
                        "type": "Архаизм",
                        "word": archaism,
                        "line": line_number,
                        "context": context,
                        "severity": "Критическая"
                    })
        
        return issues
    
    def check_calques(self, text: str) -> List[Dict[str, Any]]:
        """Проверка на кальки"""
        issues = []
        
        for calque, suggestion in self.calques.items():
            if calque in text:
                for match in re.finditer(re.escape(calque), text):
                    line_number = text[:match.start()].count('\n') + 1
                    context = text[max(0, match.start()-30):match.end()+30]
                    
                    issues.append({
                        "type": "Калька",
                        "word": calque,
                        "suggestion": suggestion,
                        "line": line_number,
                        "context": context,
                        "severity": "Высокая"
                    })
        
        return issues
    
    def check_formal_dialogue(self, text: str) -> List[Dict[str, Any]]:
        """Проверка формальных диалогов"""
        issues = []
        
        for formal, suggestion in self.formal_dialogue.items():
            if formal in text:
                for match in re.finditer(re.escape(formal), text):
                    line_number = text[:match.start()].count('\n') + 1
                    context = text[max(0, match.start()-30):match.end()+30]
                    
                    issues.append({
                        "type": "Формальный диалог",
                        "word": formal,
                        "suggestion": suggestion,
                        "line": line_number,
                        "context": context,
                        "severity": "Средняя"
                    })
        
        return issues
    
    def check_sentence_length(self, text: str) -> List[Dict[str, Any]]:
        """Проверка длины предложений"""
        issues = []
        
        sentences = re.split(r'[.!?]+', text)
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if sentence:
                words = sentence.split()
                if len(words) > self.max_sentence_length:
                    line_number = text.find(sentence) // 50 + 1  # Приблизительно
                    issues.append({
                        "type": "Длинное предложение",
                        "word": sentence,
                        "line": line_number,
                        "word_count": len(words),
                        "max_allowed": self.max_sentence_length,
                        "severity": "Средняя"
                    })
        
        return issues
    
    def calculate_readability(self, text: str) -> Dict[str, Any]:
        """Расчет читабельности"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        words = text.split()
        words = [w for w in words if w.strip()]
        
        # Средняя длина предложения
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Количество архаизмов
        archaism_count = sum(1 for archaism in self.banned_archaisms 
                           if archaism.lower() in text.lower())
        
        # Процент длинных предложений
        long_sentences = sum(1 for sentence in sentences 
                           if len(sentence.split()) > self.max_sentence_length)
        long_sentence_percentage = (long_sentences / len(sentences)) * 100 if sentences else 0
        
        # Оценка читабельности (0-100, где 100 = очень легко)
        readability_score = 100 - (avg_sentence_length * 2) - (archaism_count * 5) - (long_sentence_percentage * 0.5)
        readability_score = max(0, min(100, readability_score))
        
        return {
            "score": round(readability_score, 1),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "archaism_count": archaism_count,
            "long_sentence_percentage": round(long_sentence_percentage, 1),
            "total_words": len(words),
            "total_sentences": len(sentences),
            "target": 85,
            "status": "Хорошо" if readability_score >= 85 else "Удовлетворительно" if readability_score >= 70 else "Плохо"
        }
    
    def lint_file(self, file_path: str) -> Dict[str, Any]:
        """Проверить файл"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            return {"error": f"Ошибка чтения файла: {e}"}
        
        # Выполняем все проверки
        all_issues = []
        
        archaism_issues = self.check_archaisms(text)
        all_issues.extend(archaism_issues)
        
        calque_issues = self.check_calques(text)
        all_issues.extend(calque_issues)
        
        dialogue_issues = self.check_formal_dialogue(text)
        all_issues.extend(dialogue_issues)
        
        length_issues = self.check_sentence_length(text)
        all_issues.extend(length_issues)
        
        # Анализ читабельности
        readability = self.calculate_readability(text)
        
        # Статистика
        critical_count = len([i for i in all_issues if i["severity"] == "Критическая"])
        high_count = len([i for i in all_issues if i["severity"] == "Высокая"])
        medium_count = len([i for i in all_issues if i["severity"] == "Средняя"])
        
        # Итоговая оценка
        total_score = 100
        total_score -= critical_count * 20
        total_score -= high_count * 10
        total_score -= medium_count * 5
        total_score = max(0, total_score)
        
        return {
            "file_path": file_path,
            "text_length": len(text),
            "issues": all_issues,
            "readability": readability,
            "statistics": {
                "total_issues": len(all_issues),
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count
            },
            "total_score": total_score
        }
    
    def print_report(self, result: Dict[str, Any]):
        """Вывести отчет"""
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        
        print("🔍 РУССКИЙ ЛИНТЕР ДЛЯ ПЕРЕВОДОВ")
        print("=" * 50)
        print(f"📄 Файл: {result['file_path']}")
        print(f"📏 Размер: {result['text_length']} символов")
        
        # Проблемы по типам
        if result["issues"]:
            print(f"\n📋 НАЙДЕННЫЕ ПРОБЛЕМЫ:")
            print("=" * 60)
            
            # Группируем по типам
            issue_groups = {}
            for issue in result["issues"]:
                issue_type = issue["type"]
                if issue_type not in issue_groups:
                    issue_groups[issue_type] = []
                issue_groups[issue_type].append(issue)
            
            for issue_type, issues in issue_groups.items():
                print(f"\n🔸 {issue_type} ({len(issues)} проблем):")
                
                for issue in issues:
                    severity_color = {
                        "Критическая": "🔴",
                        "Высокая": "🟠", 
                        "Средняя": "🟡"
                    }.get(issue["severity"], "⚪")
                    
                    print(f"  {severity_color} Строка {issue['line']}: {issue['word']}")
                    if 'context' in issue:
                        print(f"     Контекст: ...{issue['context']}...")
                    
                    if "suggestion" in issue:
                        print(f"     💡 Предложение: {issue['suggestion']}")
                    if "word_count" in issue:
                        print(f"     📊 Слов: {issue['word_count']} (максимум: {issue['max_allowed']})")
        else:
            print("\n✅ Проблем не найдено!")
        
        # Отчет по читабельности
        readability = result["readability"]
        print(f"\n📊 ОТЧЕТ ПО ЧИТАБЕЛЬНОСТИ:")
        print("=" * 40)
        
        status_color = {
            "Хорошо": "✅",
            "Удовлетворительно": "⚠️",
            "Плохо": "❌"
        }.get(readability["status"], "❓")
        
        print(f"Оценка читабельности: {readability['score']}/100 {status_color} {readability['status']}")
        print(f"Средняя длина предложения: {readability['avg_sentence_length']} слов")
        print(f"Архаизмов: {readability['archaism_count']}")
        print(f"Длинных предложений: {readability['long_sentence_percentage']}%")
        print(f"Всего слов: {readability['total_words']}")
        print(f"Всего предложений: {readability['total_sentences']}")
        print(f"Целевая оценка: {readability['target']}+")
        
        # Статистика
        stats = result["statistics"]
        print(f"\n📈 СТАТИСТИКА:")
        print(f"Критические: {stats['critical']}")
        print(f"Высокие: {stats['high']}")
        print(f"Средние: {stats['medium']}")
        print(f"Всего проблем: {stats['total_issues']}")
        
        # Итоговая оценка
        total_score = result["total_score"]
        score_color = "✅" if total_score >= 90 else "⚠️" if total_score >= 70 else "❌"
        
        print(f"\n🏆 ИТОГОВАЯ ОЦЕНКА: {total_score}/100 {score_color}")
        
        if total_score >= 90:
            print("🎉 Отличный перевод! Готов к публикации!")
        elif total_score >= 70:
            print("👍 Хороший перевод, но есть что улучшить")
        else:
            print("⚠️ Требуется серьезная доработка")

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Русский линтер для переводов")
    parser.add_argument("file_path", help="Путь к файлу для проверки")
    parser.add_argument("--fix", action="store_true", help="Автоматически исправить проблемы")
    parser.add_argument("--verbose", action="store_true", help="Подробный вывод")
    
    args = parser.parse_args()
    
    linter = RussianLinter()
    result = linter.lint_file(args.file_path)
    linter.print_report(result)

if __name__ == "__main__":
    main()
