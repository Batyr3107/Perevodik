#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Валидатор глав для проверки консистентности и качества
Проверяет соответствие правилам перевода и качество
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from config import QUALITY_METRICS, MIN_QUALITY_THRESHOLDS, BANNED_ARCHAISMS
from tools.chapter_splitter import ChapterSplitter, TextSegment

@dataclass
class ValidationIssue:
    """Проблема валидации"""
    issue_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    message: str
    line_number: int
    context: str
    suggestion: Optional[str] = None

@dataclass
class ValidationResult:
    """Результат валидации"""
    is_valid: bool
    issues: List[ValidationIssue]
    quality_scores: Dict[str, float]
    overall_score: float
    recommendations: List[str]

class ChapterValidator:
    """Валидатор глав для проверки качества и консистентности"""
    
    def __init__(self):
        self.splitter = ChapterSplitter()
        
        # Паттерны для проверки
        self.archaism_patterns = BANNED_ARCHAISMS
        self.calque_patterns = [
            "крайне", "слева и справа", "совершенна", 
            "На его взгляд", "резюмировал", "осуществлять",
            "производить впечатление", "испытывать чувство"
        ]
        self.formal_dialogue_patterns = [
            "Я собираюсь", "Позвольте мне", "Не могли бы вы",
            "Я хотел бы", "Кажется, что", "Я боюсь, что"
        ]
        
        # Терминология из глоссария
        self.glossary_terms = {
            "Slack-Off System": "Система Безделья",
            "Holy Son": "Святой Сын",
            "Banished Immortal Peak": "Пик Изгнанного Бессмертного",
            "Primordial Holy Land": "Изначальная Святая Земля",
            "dog licker": "подхалим"
        }
    
    def validate_chapter(self, original_text: str, translated_text: str, 
                        context: Optional[Dict] = None) -> ValidationResult:
        """Полная валидация главы"""
        print("🔍 Валидация главы...")
        
        issues = []
        
        # 1. Проверка структуры
        structure_issues = self._validate_structure(original_text, translated_text)
        issues.extend(structure_issues)
        
        # 2. Проверка архаизмов
        archaism_issues = self._validate_archaisms(translated_text)
        issues.extend(archaism_issues)
        
        # 3. Проверка кальки
        calque_issues = self._validate_calques(translated_text)
        issues.extend(calque_issues)
        
        # 4. Проверка диалогов
        dialogue_issues = self._validate_dialogues(translated_text)
        issues.extend(dialogue_issues)
        
        # 5. Проверка терминологии
        terminology_issues = self._validate_terminology(translated_text)
        issues.extend(terminology_issues)
        
        # 6. Проверка читабельности
        readability_issues = self._validate_readability(translated_text)
        issues.extend(readability_issues)
        
        # 7. Проверка консистентности
        consistency_issues = self._validate_consistency(translated_text)
        issues.extend(consistency_issues)
        
        # Рассчитываем оценки качества
        quality_scores = self._calculate_quality_scores(translated_text, issues)
        overall_score = self._calculate_overall_score(quality_scores)
        
        # Генерируем рекомендации
        recommendations = self._generate_recommendations(issues, quality_scores)
        
        # Определяем общую валидность
        critical_issues = [i for i in issues if i.severity == 'critical']
        is_valid = len(critical_issues) == 0 and overall_score >= 70
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            quality_scores=quality_scores,
            overall_score=overall_score,
            recommendations=recommendations
        )
    
    def _validate_structure(self, original: str, translated: str) -> List[ValidationIssue]:
        """Проверка соответствия структуры"""
        issues = []
        
        # Проверяем количество строк
        orig_lines = len([l for l in original.split('\n') if l.strip()])
        trans_lines = len([l for l in translated.split('\n') if l.strip()])
        
        if abs(orig_lines - trans_lines) > 2:
            issues.append(ValidationIssue(
                issue_type="Структура",
                severity="high",
                message=f"Количество строк не соответствует: {trans_lines} vs {orig_lines}",
                line_number=0,
                context="Общая структура",
                suggestion="Проверить разбивку на абзацы"
            ))
        
        # Проверяем пустые строки
        orig_empty = original.count('\n\n')
        trans_empty = translated.count('\n\n')
        
        if abs(orig_empty - trans_empty) > 1:
            issues.append(ValidationIssue(
                issue_type="Структура",
                severity="medium",
                message=f"Количество пустых строк не соответствует: {trans_empty} vs {orig_empty}",
                line_number=0,
                context="Пустые строки",
                suggestion="Нормализовать пустые строки"
            ))
        
        return issues
    
    def _validate_archaisms(self, text: str) -> List[ValidationIssue]:
        """Проверка на архаизмы"""
        issues = []
        
        for archaism in self.archaism_patterns:
            if archaism in text.lower():
                # Находим все вхождения
                for match in re.finditer(re.escape(archaism), text, re.IGNORECASE):
                    line_number = text[:match.start()].count('\n') + 1
                    context = text[max(0, match.start()-30):match.end()+30]
                    
                    issues.append(ValidationIssue(
                        issue_type="Архаизм",
                        severity="critical",
                        message=f"Найден архаизм: '{archaism}'",
                        line_number=line_number,
                        context=context,
                        suggestion=f"Заменить на современный аналог"
                    ))
        
        return issues
    
    def _validate_calques(self, text: str) -> List[ValidationIssue]:
        """Проверка на кальки"""
        issues = []
        
        for calque in self.calque_patterns:
            if calque in text:
                for match in re.finditer(re.escape(calque), text):
                    line_number = text[:match.start()].count('\n') + 1
                    context = text[max(0, match.start()-30):match.end()+30]
                    
                    issues.append(ValidationIssue(
                        issue_type="Калька",
                        severity="high",
                        message=f"Найдена калька: '{calque}'",
                        line_number=line_number,
                        context=context,
                        suggestion="Переформулировать естественно"
                    ))
        
        return issues
    
    def _validate_dialogues(self, text: str) -> List[ValidationIssue]:
        """Проверка диалогов"""
        issues = []
        
        for pattern in self.formal_dialogue_patterns:
            if pattern in text:
                for match in re.finditer(re.escape(pattern), text):
                    line_number = text[:match.start()].count('\n') + 1
                    context = text[max(0, match.start()-30):match.end()+30]
                    
                    issues.append(ValidationIssue(
                        issue_type="Формальный диалог",
                        severity="medium",
                        message=f"Формальная конструкция: '{pattern}'",
                        line_number=line_number,
                        context=context,
                        suggestion="Упростить для естественности"
                    ))
        
        return issues
    
    def _validate_terminology(self, text: str) -> List[ValidationIssue]:
        """Проверка терминологии"""
        issues = []
        
        for en_term, ru_term in self.glossary_terms.items():
            if en_term in text and ru_term not in text:
                issues.append(ValidationIssue(
                    issue_type="Терминология",
                    severity="high",
                    message=f"Неправильный термин: '{en_term}' вместо '{ru_term}'",
                    line_number=0,
                    context="Терминология",
                    suggestion=f"Использовать '{ru_term}'"
                ))
        
        return issues
    
    def _validate_readability(self, text: str) -> List[ValidationIssue]:
        """Проверка читабельности"""
        issues = []
        
        # Проверяем длину предложений
        sentences = re.split(r'[.!?]+', text)
        long_sentences = []
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if sentence:
                words = sentence.split()
                if len(words) > 15:  # Максимальная длина предложения
                    line_number = text.find(sentence) // 50 + 1  # Приблизительно
                    long_sentences.append((i+1, len(words), sentence[:50]))
        
        if long_sentences:
            for line_num, word_count, context in long_sentences:
                issues.append(ValidationIssue(
                    issue_type="Читабельность",
                    severity="medium",
                    message=f"Длинное предложение: {word_count} слов",
                    line_number=line_num,
                    context=context,
                    suggestion="Разбить на более короткие предложения"
                ))
        
        return issues
    
    def _validate_consistency(self, text: str) -> List[ValidationIssue]:
        """Проверка консистентности"""
        issues = []
        
        # Проверяем консистентность имен персонажей
        character_names = {
            "Цзян Чэнь": ["Jiang Chen", "цзян чэнь"],
            "Е Цинчэн": ["Ye Qingcheng", "е цинчэн"],
            "Ду Гуюнь": ["Du Guyun", "ду гуюнь"]
        }
        
        for correct_name, variants in character_names.items():
            found_variants = []
            for variant in variants:
                if variant in text:
                    found_variants.append(variant)
            
            if len(found_variants) > 1:
                issues.append(ValidationIssue(
                    issue_type="Консистентность",
                    severity="high",
                    message=f"Несогласованность имен: {', '.join(found_variants)}",
                    line_number=0,
                    context="Имена персонажей",
                    suggestion=f"Использовать только '{correct_name}'"
                ))
        
        return issues
    
    def _calculate_quality_scores(self, text: str, issues: List[ValidationIssue]) -> Dict[str, float]:
        """Рассчитать оценки качества по метрикам"""
        scores = {}
        
        # Естественность диалогов (30%)
        dialogue_issues = [i for i in issues if i.issue_type == "Формальный диалог"]
        dialogue_score = max(0, 100 - len(dialogue_issues) * 10)
        scores["dialogue_naturalness"] = dialogue_score
        
        # Консистентность терминов (25%)
        term_issues = [i for i in issues if i.issue_type == "Терминология"]
        term_score = max(0, 100 - len(term_issues) * 15)
        scores["terminology_consistency"] = term_score
        
        # Голос персонажа (25%) - упрощенная оценка
        archaism_issues = [i for i in issues if i.issue_type == "Архаизм"]
        voice_score = max(0, 100 - len(archaism_issues) * 20)
        scores["character_voice"] = voice_score
        
        # Культурная адаптация (20%)
        calque_issues = [i for i in issues if i.issue_type == "Калька"]
        cultural_score = max(0, 100 - len(calque_issues) * 15)
        scores["cultural_adaptation"] = cultural_score
        
        return scores
    
    def _calculate_overall_score(self, quality_scores: Dict[str, float]) -> float:
        """Рассчитать общую оценку качества"""
        total_score = 0
        for metric, weight in QUALITY_METRICS.items():
            if metric in quality_scores:
                total_score += quality_scores[metric] * weight
        return round(total_score, 1)
    
    def _generate_recommendations(self, issues: List[ValidationIssue], 
                                 quality_scores: Dict[str, float]) -> List[str]:
        """Генерировать рекомендации по улучшению"""
        recommendations = []
        
        # Рекомендации по критическим проблемам
        critical_issues = [i for i in issues if i.severity == "critical"]
        if critical_issues:
            recommendations.append(f"🔴 Критические проблемы: {len(critical_issues)} - требуют немедленного исправления")
        
        # Рекомендации по качеству
        for metric, score in quality_scores.items():
            threshold = MIN_QUALITY_THRESHOLDS.get(metric, 0)
            if score < threshold:
                recommendations.append(f"⚠️ {metric}: {score:.1f}/{threshold} - ниже порога")
        
        # Общие рекомендации
        if quality_scores.get("dialogue_naturalness", 0) < 80:
            recommendations.append("💬 Упростить диалоги - убрать формальность")
        
        if quality_scores.get("terminology_consistency", 0) < 90:
            recommendations.append("📚 Проверить терминологию по глоссарию")
        
        if quality_scores.get("cultural_adaptation", 0) < 75:
            recommendations.append("🌍 Убрать кальки - адаптировать под русский")
        
        return recommendations
    
    def print_validation_report(self, result: ValidationResult):
        """Вывести отчет о валидации"""
        print("\n" + "="*60)
        print("📋 ОТЧЕТ О ВАЛИДАЦИИ")
        print("="*60)
        
        # Общая оценка
        status_color = "🟢" if result.is_valid else "🔴"
        print(f"{status_color} Общая оценка: {result.overall_score:.1f}/100")
        print(f"📊 Валидность: {'✅ Валидно' if result.is_valid else '❌ Невалидно'}")
        
        # Детальные оценки
        print(f"\n📈 ДЕТАЛЬНЫЕ ОЦЕНКИ:")
        for metric, score in result.quality_scores.items():
            threshold = MIN_QUALITY_THRESHOLDS.get(metric, 0)
            status = "✅" if score >= threshold else "❌"
            print(f"   {status} {metric}: {score:.1f}/{threshold}")
        
        # Проблемы по типам
        if result.issues:
            print(f"\n🔍 ПРОБЛЕМЫ ПО ТИПАМ:")
            issue_groups = {}
            for issue in result.issues:
                if issue.issue_type not in issue_groups:
                    issue_groups[issue.issue_type] = []
                issue_groups[issue.issue_type].append(issue)
            
            for issue_type, issues in issue_groups.items():
                critical = len([i for i in issues if i.severity == "critical"])
                high = len([i for i in issues if i.severity == "high"])
                medium = len([i for i in issues if i.severity == "medium"])
                print(f"   • {issue_type}: {len(issues)} (🔴{critical} 🟠{high} 🟡{medium})")
        
        # Рекомендации
        if result.recommendations:
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            for rec in result.recommendations:
                print(f"   {rec}")
        
        print("="*60)

def test_chapter_validator():
    """Тестирование валидатора глав"""
    print("🧪 ТЕСТИРОВАНИЕ ВАЛИДАТОРА ГЛАВ")
    print("=" * 50)
    
    validator = ChapterValidator()
    
    # Тестовые тексты
    original_text = """Chapter 1: Test

"Hello!" said the character.

This is a test chapter with some content."""
    
    translated_text = """Глава 1: Тест

"Привет!" сказал персонаж.

Сей тест содержит весьма интересный контент."""
    
    # Валидация
    result = validator.validate_chapter(original_text, translated_text)
    
    # Выводим отчет
    validator.print_validation_report(result)
    
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    test_chapter_validator()
