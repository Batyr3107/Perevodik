#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для тестирования системы перевода
Устраняет дублирование тестового кода
"""

import os
import sys
import tempfile
from typing import Dict, Any, Optional, List

# Добавляем корневую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_api_key, print_config_status, validate_config
from tools.translation_workflow import ChapterTranslationManager
from tools.consultation_base import DeepLConsultationBase, QuickConsultant


class TestEnvironment:
    """Класс для настройки тестовой среды"""
    
    def __init__(self):
        self.original_env = os.environ.copy()
        self.test_files = []
    
    def setup(self) -> bool:
        """Настройка тестовой среды"""
        print("🔧 Настройка тестовой среды...")
        
        # Проверяем конфигурацию
        errors = validate_config()
        if errors:
            print("❌ Ошибки конфигурации:")
            for error in errors:
                print(f"   • {error}")
            return False
        
        # Устанавливаем API ключ
        api_key = get_api_key()
        if api_key:
            os.environ['DEEPL_API_KEY'] = api_key
            print(f"✅ API ключ установлен: {api_key[:10]}...{api_key[-3:]}")
        else:
            print("❌ API ключ не найден")
            return False
        
        print("✅ Тестовая среда настроена")
        return True
    
    def cleanup(self):
        """Очистка тестовой среды"""
        print("🧹 Очистка тестовой среды...")
        
        # Удаляем тестовые файлы
        for file_path in self.test_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"   Удален: {file_path}")
            except Exception as e:
                print(f"   Ошибка удаления {file_path}: {e}")
        
        # Восстанавливаем переменные окружения
        os.environ.clear()
        os.environ.update(self.original_env)
        
        print("✅ Очистка завершена")
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Создание тестового файла"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.test_files.append(filename)
        print(f"✅ Создан тестовый файл: {filename}")
        return filename


class TestManager:
    """Менеджер для создания тестовых объектов"""
    
    @staticmethod
    def create_translation_manager() -> ChapterTranslationManager:
        """Создание менеджера переводов"""
        try:
            manager = ChapterTranslationManager()
            print("✅ ChapterTranslationManager создан успешно")
            return manager
        except Exception as e:
            print(f"❌ Ошибка создания менеджера: {e}")
            raise
    
    @staticmethod
    def create_consultation_base() -> DeepLConsultationBase:
        """Создание базового консультанта"""
        try:
            consultant = DeepLConsultationBase()
            print("✅ DeepLConsultationBase создан успешно")
            return consultant
        except Exception as e:
            print(f"❌ Ошибка создания консультанта: {e}")
            raise
    
    @staticmethod
    def create_quick_consultant() -> QuickConsultant:
        """Создание быстрого консультанта"""
        try:
            consultant = QuickConsultant()
            print("✅ QuickConsultant создан успешно")
            return consultant
        except Exception as e:
            print(f"❌ Ошибка создания быстрого консультанта: {e}")
            raise


class TestRunner:
    """Запуск различных тестов"""
    
    def __init__(self):
        self.env = TestEnvironment()
        self.manager = None
        self.consultant = None
    
    def run_basic_tests(self) -> bool:
        """Запуск базовых тестов"""
        print("\n🧪 БАЗОВЫЕ ТЕСТЫ")
        print("="*40)
        
        # Тест 1: Настройка среды
        if not self.env.setup():
            return False
        
        # Тест 2: Создание менеджера
        try:
            self.manager = TestManager.create_translation_manager()
        except Exception as e:
            print(f"❌ Тест создания менеджера не прошел: {e}")
            return False
        
        # Тест 3: Создание консультанта
        try:
            self.consultant = TestManager.create_consultation_base()
        except Exception as e:
            print(f"❌ Тест создания консультанта не прошел: {e}")
            return False
        
        print("✅ Все базовые тесты пройдены")
        return True
    
    def run_translation_tests(self) -> bool:
        """Тесты перевода"""
        print("\n📝 ТЕСТЫ ПЕРЕВОДА")
        print("="*40)
        
        if not self.manager:
            print("❌ Менеджер не инициализирован")
            return False
        
        # Тест простого перевода
        try:
            test_text = "Hello, this is a test!"
            result = self.manager.translate_text(test_text)
            print(f"✅ Простой перевод: '{test_text}' → '{result}'")
        except Exception as e:
            print(f"❌ Ошибка простого перевода: {e}")
            return False
        
        # Тест перевода файла
        try:
            test_file = self.env.create_test_file(
                "test_english.txt",
                """Chapter Test: Translation System

"Finally, she's gone!" Jiang Chen exhaled with relief.

From his perspective, apart from being brainless, Ye Qingcheng was like bad luck."""
            )
            
            result = self.manager.translate_file(test_file, "test_russian.txt")
            print(f"✅ Перевод файла: {result['metadata']['output_file']}")
            
        except Exception as e:
            print(f"❌ Ошибка перевода файла: {e}")
            return False
        
        print("✅ Все тесты перевода пройдены")
        return True
    
    def run_consultation_tests(self) -> bool:
        """Тесты консультаций"""
        print("\n🤖 ТЕСТЫ КОНСУЛЬТАЦИЙ")
        print("="*40)
        
        if not self.consultant:
            print("❌ Консультант не инициализирован")
            return False
        
        # Тест консультации по фрагментам
        try:
            test_fragments = [
                "Hello, this is a test!",
                "The system works perfectly."
            ]
            
            test_my_translations = [
                "Привет, это тест!",
                "Система работает отлично."
            ]
            
            result = self.consultant.consult_and_compare(test_fragments, test_my_translations)
            
            if result['success']:
                print("✅ Консультация по фрагментам прошла успешно")
            else:
                print("❌ Консультация по фрагментам не удалась")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка консультации: {e}")
            return False
        
        print("✅ Все тесты консультаций пройдены")
        return True
    
    def run_full_workflow_test(self) -> bool:
        """Тест полного workflow"""
        print("\n⚙️ ТЕСТ ПОЛНОГО WORKFLOW")
        print("="*40)
        
        if not self.manager:
            print("❌ Менеджер не инициализирован")
            return False
        
        try:
            # Создаем тестовую главу
            test_chapter = self.env.create_test_file(
                "Тест Глава Workflow.txt",
                """Chapter 999: Full Workflow Test

"Finally, the integration is working!" the developer exclaimed with relief.

This is a test chapter to verify that the full translation workflow works correctly.

"System, would it count as interfering with slacking off if I translate using DeepL?" the AI inquired.

The developer was pleased with the result."""
            )
            
            # Запускаем полный workflow
            result = self.manager.translate_chapter_deepl(test_chapter, chapter_number=999)
            
            print(f"✅ Workflow завершен:")
            print(f"   Переводчик: {result['translator']}")
            print(f"   Качество: {result['quality_score']}/100")
            print(f"   Структура: {result['structure_match']['structure_score']}/100")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка workflow: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК ПОЛНОГО ТЕСТИРОВАНИЯ")
        print("="*50)
        
        try:
            # Базовые тесты
            if not self.run_basic_tests():
                return False
            
            # Тесты перевода
            if not self.run_translation_tests():
                return False
            
            # Тесты консультаций
            if not self.run_consultation_tests():
                return False
            
            # Тест полного workflow
            if not self.run_full_workflow_test():
                return False
            
            print("\n🎉🎉🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! 🎉🎉🎉")
            print("✅ Система готова к использованию!")
            return True
            
        except Exception as e:
            print(f"\n❌ Критическая ошибка тестирования: {e}")
            return False
        
        finally:
            # Очистка
            self.env.cleanup()


# Удобные функции для быстрого тестирования
def quick_test():
    """Быстрый тест системы"""
    runner = TestRunner()
    return runner.run_basic_tests()


def full_test():
    """Полный тест системы"""
    runner = TestRunner()
    return runner.run_all_tests()


def test_deepl_setup():
    """Тест настройки DeepL"""
    print("🧪 Тестирование DeepL API...")
    
    # Проверяем API ключ
    api_key = get_api_key()
    if not api_key:
        print("❌ API ключ не найден!")
        return False
    
    print(f"✅ API ключ найден: {api_key[:10]}...{api_key[-3:]}")
    
    # Тестируем импорт модулей
    try:
        from tools.deepl_translator import DeepLFileTranslator
        print("✅ Модули deepl_translator импортированы успешно")
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    
    # Тестируем создание переводчика
    try:
        translator = DeepLFileTranslator()
        print("✅ DeepLFileTranslator создан успешно")
    except Exception as e:
        print(f"❌ Ошибка создания переводчика: {e}")
        return False
    
    # Тестируем простой перевод
    try:
        print("🔄 Тестируем простой перевод...")
        test_text = "Hello, this is a test!"
        result = translator.translate_text(test_text)
        print(f"✅ Перевод работает: '{test_text}' → '{result}'")
    except Exception as e:
        print(f"❌ Ошибка перевода: {e}")
        return False
    
    print("🎉 Все тесты пройдены успешно!")
    return True


if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ ПЕРЕВОДА")
    print("="*50)
    
    # Показываем статус конфигурации
    print_config_status()
    
    # Запускаем тесты
    if full_test():
        print("\n✅ Система полностью готова к работе!")
    else:
        print("\n❌ Обнаружены проблемы в системе")
        sys.exit(1)
