#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Инструмент для консультации с DeepL по отдельным фрагментам текста
Для гибридной системы перевода
"""

import os
import sys
from typing import List, Dict
from pathlib import Path

# Добавляем путь к нашему модулю
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from deepl_translator import DeepLFileTranslator
except ImportError:
    print("❌ Не удалось импортировать deepl_translator")
    print("💡 Убедитесь, что установлены зависимости: pip install requests")
    sys.exit(1)


class FragmentConsultant:
    """Консультант для проверки отдельных фрагментов через DeepL"""
    
    def __init__(self):
        """Инициализация консультанта"""
        try:
            self.translator = DeepLFileTranslator()
            print("✅ DeepL консультант готов")
        except Exception as e:
            print(f"❌ Ошибка инициализации DeepL: {e}")
            raise
    
    def consult_fragments(self, fragments: List[str], my_translations: List[str] = None) -> Dict:
        """
        Консультация по списку фрагментов
        
        Args:
            fragments: Список английских фрагментов для проверки
            my_translations: Мои переводы (опционально для сравнения)
            
        Returns:
            Словарь с результатами консультации
        """
        print(f"🤖 Консультируюсь с DeepL по {len(fragments)} фрагментам...")
        
        results = {
            'fragments': [],
            'comparison': [],
            'recommendations': []
        }
        
        for i, fragment in enumerate(fragments):
            try:
                # Получаем перевод от DeepL
                deepl_version = self.translator.translate_text(fragment.strip())
                
                fragment_result = {
                    'index': i + 1,
                    'original': fragment,
                    'deepl_translation': deepl_version,
                    'my_translation': my_translations[i] if my_translations and i < len(my_translations) else None
                }
                
                results['fragments'].append(fragment_result)
                
                # Если есть мой перевод - делаем сравнение
                if my_translations and i < len(my_translations):
                    my_version = my_translations[i].strip()
                    comparison = self._compare_translations(my_version, deepl_version, fragment)
                    results['comparison'].append(comparison)
                
                print(f"  ✅ Фрагмент {i+1}/{len(fragments)} обработан")
                
            except Exception as e:
                print(f"  ❌ Ошибка с фрагментом {i+1}: {e}")
                fragment_result = {
                    'index': i + 1,
                    'original': fragment,
                    'error': str(e)
                }
                results['fragments'].append(fragment_result)
        
        # Генерируем общие рекомендации
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _compare_translations(self, my_version: str, deepl_version: str, original: str) -> Dict:
        """Сравнение двух вариантов перевода"""
        
        # Базовые метрики
        length_diff = abs(len(my_version) - len(deepl_version))
        similarity_score = self._calculate_similarity(my_version, deepl_version)
        
        # Анализ качества
        analysis = {
            'my_version': my_version,
            'deepl_version': deepl_version,
            'original': original,
            'length_difference': length_diff,
            'similarity_score': similarity_score,
            'recommendation': self._get_recommendation(my_version, deepl_version, similarity_score)
        }
        
        return analysis
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Простой расчет схожести текстов"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _get_recommendation(self, my_version: str, deepl_version: str, similarity: float) -> str:
        """Генерация рекомендации по выбору варианта"""
        
        if similarity > 0.8:
            return "🟢 Варианты очень похожи - любой хорош"
        elif similarity > 0.5:
            return "🟡 Варианты отличаются - выбери более естественный"
        else:
            return "🔴 Варианты сильно отличаются - требует внимания"
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Генерация общих рекомендаций"""
        recommendations = []
        
        if not results['comparison']:
            return ["💡 Только консультация DeepL - используй результаты как референс"]
        
        total_comparisons = len(results['comparison'])
        high_similarity = sum(1 for c in results['comparison'] if c['similarity_score'] > 0.8)
        low_similarity = sum(1 for c in results['comparison'] if c['similarity_score'] < 0.5)
        
        if high_similarity / total_comparisons > 0.8:
            recommendations.append("✅ Большинство переводов очень хорошие - минимальные правки")
        
        if low_similarity / total_comparisons > 0.3:
            recommendations.append("⚠️ Много расхождений с DeepL - пересмотри проблемные места")
        
        recommendations.append(f"📊 Статистика: {high_similarity}/{total_comparisons} схожих переводов")
        
        return recommendations
    
    def print_consultation_report(self, results: Dict):
        """Красивый вывод отчета консультации"""
        
        print("\n" + "="*60)
        print("📋 ОТЧЕТ КОНСУЛЬТАЦИИ С DEEPL")
        print("="*60)
        
        # Общая статистика
        total_fragments = len(results['fragments'])
        successful = len([f for f in results['fragments'] if 'error' not in f])
        
        print(f"📊 Обработано фрагментов: {successful}/{total_fragments}")
        
        # Результаты по фрагментам
        for fragment in results['fragments']:
            if 'error' in fragment:
                print(f"\n❌ Фрагмент {fragment['index']}: ОШИБКА")
                print(f"   {fragment['error']}")
                continue
                
            print(f"\n📝 Фрагмент {fragment['index']}:")
            print(f"   🇬🇧 Оригинал: {fragment['original'][:60]}{'...' if len(fragment['original']) > 60 else ''}")
            print(f"   🤖 DeepL: {fragment['deepl_translation']}")
            
            if fragment.get('my_translation'):
                print(f"   👤 Мой: {fragment['my_translation']}")
        
        # Сравнения (если есть)
        if results['comparison']:
            print(f"\n🔍 СРАВНЕНИЕ ПЕРЕВОДОВ:")
            for i, comp in enumerate(results['comparison'], 1):
                print(f"\n   {i}. {comp['recommendation']}")
                print(f"      Схожесть: {comp['similarity_score']:.2f}")
        
        # Рекомендации
        if results['recommendations']:
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            for rec in results['recommendations']:
                print(f"   {rec}")
        
        print("\n" + "="*60)


def quick_consult(fragment: str, my_translation: str = None) -> Dict:
    """
    Быстрая консультация по одному фрагменту
    
    Args:
        fragment: Английский текст для проверки
        my_translation: Мой перевод (опционально)
        
    Returns:
        Результат консультации
    """
    consultant = FragmentConsultant()
    
    my_translations = [my_translation] if my_translation else None
    results = consultant.consult_fragments([fragment], my_translations)
    
    consultant.print_consultation_report(results)
    
    return results


def consult_file_fragments(file_path: str, my_translations_file: str = None) -> Dict:
    """
    Консультация по фрагментам из файла
    
    Args:
        file_path: Путь к файлу с английскими фрагментами (каждый на отдельной строке)
        my_translations_file: Путь к файлу с моими переводами (опционально)
        
    Returns:
        Результат консультации
    """
    
    # Читаем фрагменты
    with open(file_path, 'r', encoding='utf-8') as f:
        fragments = [line.strip() for line in f if line.strip()]
    
    # Читаем мои переводы (если есть)
    my_translations = None
    if my_translations_file and Path(my_translations_file).exists():
        with open(my_translations_file, 'r', encoding='utf-8') as f:
            my_translations = [line.strip() for line in f if line.strip()]
    
    # Консультация
    consultant = FragmentConsultant()
    results = consultant.consult_fragments(fragments, my_translations)
    
    consultant.print_consultation_report(results)
    
    return results


if __name__ == "__main__":
    print("🧪 Тестирование консультанта фрагментов...")
    
    # Тест 1: Быстрая консультация
    test_fragment = '"Finally, she\'s gone!" Jiang Chen exhaled with relief.'
    my_test_translation = '"Наконец-то она ушла!" Цзян Чэнь с облегчением выдохнул.'
    
    print("\n1️⃣ Тест быстрой консультации:")
    quick_consult(test_fragment, my_test_translation)
    
    # Тест 2: Консультация по нескольким фрагментам
    test_fragments = [
        "From his perspective, apart from being brainless, Ye Qingcheng was like bad luck",
        "System, would it count as interfering with slacking off if I take action?",
        "The children of destiny are notoriously hard to kill"
    ]
    
    my_translations = [
        "С его точки зрения, помимо безмозглости, Е Цинчэн была как невезение",
        "Система, будет ли считаться вмешательством в безделье, если я предприму действия?",
        "Детей судьбы печально известно трудно убить"
    ]
    
    print("\n2️⃣ Тест консультации по списку:")
    consultant = FragmentConsultant()
    results = consultant.consult_fragments(test_fragments, my_translations)
    consultant.print_consultation_report(results)
