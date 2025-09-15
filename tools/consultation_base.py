#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Базовый класс для консультаций с DeepL
Устраняет дублирование кода в консультационных скриптах
"""

import sys
import os
from typing import List, Dict, Any, Optional

# Добавляем корневую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_api_key, MAX_CONSULTATION_FRAGMENTS, API_TIMEOUT
from tools.translation_workflow import ChapterTranslationManager


class DeepLConsultationBase:
    """Базовый класс для консультаций с DeepL API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация консультанта
        
        Args:
            api_key: API ключ DeepL (если не указан, берется из конфига)
        """
        self.api_key = api_key or get_api_key()
        if not self.api_key:
            raise ValueError("API ключ не найден! Проверьте config.py")
        
        # Инициализируем менеджер переводов
        try:
            self.manager = ChapterTranslationManager()
        except Exception as e:
            raise RuntimeError(f"Ошибка инициализации менеджера переводов: {e}")
    
    def consult_fragments(self, fragments: List[str]) -> List[str]:
        """
        Консультация с DeepL по списку фрагментов
        
        Args:
            fragments: Список английских фрагментов для перевода
            
        Returns:
            Список переводов от DeepL
        """
        if not fragments:
            return []
        
        if len(fragments) > MAX_CONSULTATION_FRAGMENTS:
            print(f"⚠️  Слишком много фрагментов ({len(fragments)}). Максимум: {MAX_CONSULTATION_FRAGMENTS}")
            fragments = fragments[:MAX_CONSULTATION_FRAGMENTS]
        
        try:
            print(f"🤖 Консультируюсь с DeepL по {len(fragments)} фрагментам...")
            return self.manager.translate_fragments_deepl(fragments)
        except Exception as e:
            print(f"❌ Ошибка консультации с DeepL: {e}")
            return []
    
    def print_comparison(self, fragments: List[str], alternatives: List[str], 
                        my_translations: Optional[List[str]] = None) -> None:
        """
        Вывод сравнения переводов
        
        Args:
            fragments: Оригинальные английские фрагменты
            alternatives: Переводы от DeepL
            my_translations: Мои переводы (опционально)
        """
        print("\n" + "="*60)
        print("📊 СРАВНЕНИЕ ПЕРЕВОДОВ")
        print("="*60)
        
        for i, (fragment, alt) in enumerate(zip(fragments, alternatives)):
            print(f"\n{i+1}. 🇬🇧 Оригинал:")
            print(f"   {fragment}")
            
            if my_translations and i < len(my_translations):
                print(f"\n   👤 Мой перевод:")
                print(f"   {my_translations[i]}")
            
            print(f"\n   🤖 DeepL предлагает:")
            print(f"   {alt}")
            
            if i < len(fragments) - 1:
                print("-" * 40)
    
    def consult_and_compare(self, fragments: List[str], 
                           my_translations: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Полная консультация с выводом сравнения
        
        Args:
            fragments: Оригинальные фрагменты
            my_translations: Мои переводы (опционально)
            
        Returns:
            Словарь с результатами консультации
        """
        print(f"🔍 КОНСУЛЬТАЦИЯ ПО {len(fragments)} ФРАГМЕНТАМ")
        print("="*50)
        
        # Получаем переводы от DeepL
        deepl_translations = self.consult_fragments(fragments)
        
        if not deepl_translations:
            print("❌ Не удалось получить переводы от DeepL")
            return {
                'success': False,
                'fragments': fragments,
                'my_translations': my_translations,
                'deepl_translations': [],
                'recommendations': []
            }
        
        # Выводим сравнение
        self.print_comparison(fragments, deepl_translations, my_translations)
        
        # Анализируем рекомендации
        recommendations = self._analyze_recommendations(fragments, my_translations, deepl_translations)
        
        return {
            'success': True,
            'fragments': fragments,
            'my_translations': my_translations,
            'deepl_translations': deepl_translations,
            'recommendations': recommendations
        }
    
    def _analyze_recommendations(self, fragments: List[str], 
                                my_translations: Optional[List[str]], 
                                deepl_translations: List[str]) -> List[Dict[str, Any]]:
        """
        Анализ рекомендаций по переводам
        
        Returns:
            Список рекомендаций с оценками
        """
        recommendations = []
        
        for i, (fragment, deepl_translation) in enumerate(zip(fragments, deepl_translations)):
            rec = {
                'index': i,
                'fragment': fragment,
                'deepl_translation': deepl_translation,
                'recommendation': 'use_deepl',
                'confidence': 0.8,
                'reason': 'DeepL предложение'
            }
            
            if my_translations and i < len(my_translations):
                my_translation = my_translations[i]
                rec['my_translation'] = my_translation
                
                # Простой анализ качества (можно улучшить)
                if len(deepl_translation) > len(my_translation) * 1.5:
                    rec['recommendation'] = 'use_mine'
                    rec['reason'] = 'Мой перевод более лаконичный'
                elif 'не' in my_translation and 'не' not in deepl_translation:
                    rec['recommendation'] = 'use_mine'
                    rec['reason'] = 'Мой перевод сохраняет отрицание'
            
            recommendations.append(rec)
        
        return recommendations
    
    def print_recommendations(self, recommendations: List[Dict[str, Any]]) -> None:
        """Вывод рекомендаций по переводам"""
        print("\n" + "="*60)
        print("💡 РЕКОМЕНДАЦИИ")
        print("="*60)
        
        for rec in recommendations:
            print(f"\n{rec['index']+1}. {rec['fragment'][:50]}...")
            print(f"   Рекомендация: {rec['recommendation']}")
            print(f"   Причина: {rec['reason']}")
            print(f"   Уверенность: {rec['confidence']:.1%}")


class QuickConsultant:
    """Быстрый консультант для отдельных фрагментов"""
    
    def __init__(self):
        self.base_consultant = DeepLConsultationBase()
    
    def quick_consult(self, fragment: str, my_translation: str) -> Dict[str, Any]:
        """
        Быстрая консультация по одному фрагменту
        
        Args:
            fragment: Английский фрагмент
            my_translation: Мой перевод
            
        Returns:
            Результат консультации
        """
        print(f"⚡ БЫСТРАЯ КОНСУЛЬТАЦИЯ")
        print(f"🇬🇧 {fragment}")
        print(f"👤 {my_translation}")
        
        result = self.base_consultant.consult_and_compare([fragment], [my_translation])
        
        if result['success'] and result['deepl_translations']:
            deepl_translation = result['deepl_translations'][0]
            print(f"🤖 {deepl_translation}")
            
            # Простая рекомендация
            if len(deepl_translation) < len(my_translation) * 0.8:
                recommendation = "Используй DeepL - более лаконично"
            elif 'не' in my_translation and 'не' not in deepl_translation:
                recommendation = "Используй свой - сохраняет отрицание"
            else:
                recommendation = "Оба варианта хороши"
            
            print(f"💡 {recommendation}")
        
        return result


# Удобные функции для быстрого использования
def quick_consult(fragment: str, my_translation: str) -> Dict[str, Any]:
    """Быстрая консультация по фрагменту"""
    consultant = QuickConsultant()
    return consultant.quick_consult(fragment, my_translation)


def consult_fragments(fragments: List[str], my_translations: Optional[List[str]] = None) -> Dict[str, Any]:
    """Консультация по списку фрагментов"""
    consultant = DeepLConsultationBase()
    return consultant.consult_and_compare(fragments, my_translations)


if __name__ == "__main__":
    # Тестирование базового функционала
    print("🧪 ТЕСТИРОВАНИЕ БАЗОВОГО КОНСУЛЬТАНТА")
    
    test_fragments = [
        "Hello, this is a test!",
        "The system works perfectly."
    ]
    
    test_my_translations = [
        "Привет, это тест!",
        "Система работает отлично."
    ]
    
    try:
        consultant = DeepLConsultationBase()
        result = consultant.consult_and_compare(test_fragments, test_my_translations)
        
        if result['success']:
            print("\n✅ Тест прошел успешно!")
            consultant.print_recommendations(result['recommendations'])
        else:
            print("\n❌ Тест не прошел")
            
    except Exception as e:
        print(f"\n❌ Ошибка тестирования: {e}")
