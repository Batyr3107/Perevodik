#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Централизованная система обработки ошибок
Обеспечивает единообразную обработку ошибок во всех компонентах
"""

import logging
import traceback
import sys
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class ErrorSeverity(Enum):
    """Уровни серьезности ошибок"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Категории ошибок"""
    API_ERROR = "api_error"
    FILE_ERROR = "file_error"
    TRANSLATION_ERROR = "translation_error"
    VALIDATION_ERROR = "validation_error"
    CONFIG_ERROR = "config_error"
    MEMORY_ERROR = "memory_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"

@dataclass
class ErrorInfo:
    """Информация об ошибке"""
    error_type: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = None
    traceback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class ErrorHandler:
    """Централизованный обработчик ошибок"""
    
    def __init__(self, log_file: str = "translation_errors.log"):
        self.log_file = log_file
        self.error_count = 0
        self.error_history = []
        
        # Настройка логирования
        self._setup_logging()
        
        # Обработчики ошибок по категориям
        self.error_handlers = {
            ErrorCategory.API_ERROR: self._handle_api_error,
            ErrorCategory.FILE_ERROR: self._handle_file_error,
            ErrorCategory.TRANSLATION_ERROR: self._handle_translation_error,
            ErrorCategory.VALIDATION_ERROR: self._handle_validation_error,
            ErrorCategory.CONFIG_ERROR: self._handle_config_error,
            ErrorCategory.MEMORY_ERROR: self._handle_memory_error,
            ErrorCategory.NETWORK_ERROR: self._handle_network_error,
            ErrorCategory.UNKNOWN: self._handle_unknown_error
        }
    
    def _setup_logging(self):
        """Настройка системы логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('TranslationSystem')
    
    def handle_error(self, error: Exception, category: ErrorCategory, 
                    context: Optional[Dict[str, Any]] = None,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> ErrorInfo:
        """Обработать ошибку"""
        self.error_count += 1
        
        # Создаем информацию об ошибке
        error_info = ErrorInfo(
            error_type=type(error).__name__,
            category=category,
            severity=severity,
            message=str(error),
            details=self._extract_error_details(error),
            traceback=traceback.format_exc(),
            context=context
        )
        
        # Добавляем в историю
        self.error_history.append(error_info)
        
        # Логируем ошибку
        self._log_error(error_info)
        
        # Вызываем специфичный обработчик
        if category in self.error_handlers:
            self.error_handlers[category](error_info)
        
        return error_info
    
    def _extract_error_details(self, error: Exception) -> Dict[str, Any]:
        """Извлечь детали ошибки"""
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        # Специфичные детали для разных типов ошибок
        if hasattr(error, 'response'):
            details["response_status"] = getattr(error.response, 'status_code', None)
            details["response_text"] = getattr(error.response, 'text', None)
        
        if hasattr(error, 'filename'):
            details["filename"] = error.filename
        
        if hasattr(error, 'errno'):
            details["errno"] = error.errno
        
        return details
    
    def _log_error(self, error_info: ErrorInfo):
        """Логировать ошибку"""
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_info.severity, logging.ERROR)
        
        self.logger.log(
            log_level,
            f"[{error_info.category.value}] {error_info.message}",
            extra={
                'error_type': error_info.error_type,
                'context': error_info.context,
                'traceback': error_info.traceback
            }
        )
    
    def _handle_api_error(self, error_info: ErrorInfo):
        """Обработка ошибок API"""
        if error_info.severity == ErrorSeverity.CRITICAL:
            print("🚨 КРИТИЧЕСКАЯ ОШИБКА API - система может быть недоступна")
        elif error_info.severity == ErrorSeverity.HIGH:
            print("⚠️ Ошибка API - проверьте подключение и ключи")
        
        # Предложения по исправлению
        suggestions = [
            "Проверьте API ключ DeepL",
            "Убедитесь в наличии интернет-соединения",
            "Проверьте лимиты API"
        ]
        self._print_suggestions(suggestions)
    
    def _handle_file_error(self, error_info: ErrorInfo):
        """Обработка ошибок файлов"""
        if error_info.severity == ErrorSeverity.CRITICAL:
            print("🚨 КРИТИЧЕСКАЯ ОШИБКА ФАЙЛА - файл недоступен")
        elif error_info.severity == ErrorSeverity.HIGH:
            print("⚠️ Ошибка файла - проверьте путь и права доступа")
        
        suggestions = [
            "Проверьте существование файла",
            "Убедитесь в правах доступа",
            "Проверьте кодировку файла (UTF-8)"
        ]
        self._print_suggestions(suggestions)
    
    def _handle_translation_error(self, error_info: ErrorInfo):
        """Обработка ошибок перевода"""
        if error_info.severity == ErrorSeverity.CRITICAL:
            print("🚨 КРИТИЧЕСКАЯ ОШИБКА ПЕРЕВОДА - перевод невозможен")
        elif error_info.severity == ErrorSeverity.HIGH:
            print("⚠️ Ошибка перевода - проверьте качество текста")
        
        suggestions = [
            "Проверьте корректность исходного текста",
            "Убедитесь в доступности переводчика",
            "Попробуйте разбить текст на меньшие части"
        ]
        self._print_suggestions(suggestions)
    
    def _handle_validation_error(self, error_info: ErrorInfo):
        """Обработка ошибок валидации"""
        if error_info.severity == ErrorSeverity.CRITICAL:
            print("🚨 КРИТИЧЕСКАЯ ОШИБКА ВАЛИДАЦИИ - качество недопустимо")
        elif error_info.severity == ErrorSeverity.HIGH:
            print("⚠️ Ошибка валидации - требуется доработка")
        
        suggestions = [
            "Проверьте соответствие правилам перевода",
            "Исправьте найденные архаизмы и кальки",
            "Улучшите читабельность текста"
        ]
        self._print_suggestions(suggestions)
    
    def _handle_config_error(self, error_info: ErrorInfo):
        """Обработка ошибок конфигурации"""
        if error_info.severity == ErrorSeverity.CRITICAL:
            print("🚨 КРИТИЧЕСКАЯ ОШИБКА КОНФИГУРАЦИИ - система не может работать")
        elif error_info.severity == ErrorSeverity.HIGH:
            print("⚠️ Ошибка конфигурации - проверьте настройки")
        
        suggestions = [
            "Проверьте файл config.py",
            "Убедитесь в корректности API ключей",
            "Проверьте пути к файлам"
        ]
        self._print_suggestions(suggestions)
    
    def _handle_memory_error(self, error_info: ErrorInfo):
        """Обработка ошибок памяти переводов"""
        if error_info.severity == ErrorSeverity.CRITICAL:
            print("🚨 КРИТИЧЕСКАЯ ОШИБКА ПАМЯТИ - контекст потерян")
        elif error_info.severity == ErrorSeverity.HIGH:
            print("⚠️ Ошибка памяти - контекст может быть неполным")
        
        suggestions = [
            "Проверьте доступность ChromaDB",
            "Убедитесь в корректности базы данных",
            "Попробуйте перезапустить систему"
        ]
        self._print_suggestions(suggestions)
    
    def _handle_network_error(self, error_info: ErrorInfo):
        """Обработка сетевых ошибок"""
        if error_info.severity == ErrorSeverity.CRITICAL:
            print("🚨 КРИТИЧЕСКАЯ СЕТЕВАЯ ОШИБКА - нет подключения")
        elif error_info.severity == ErrorSeverity.HIGH:
            print("⚠️ Сетевая ошибка - проверьте подключение")
        
        suggestions = [
            "Проверьте интернет-соединение",
            "Убедитесь в доступности API серверов",
            "Попробуйте позже"
        ]
        self._print_suggestions(suggestions)
    
    def _handle_unknown_error(self, error_info: ErrorInfo):
        """Обработка неизвестных ошибок"""
        print("❓ Неизвестная ошибка - требуется анализ")
        
        suggestions = [
            "Проверьте логи для деталей",
            "Обратитесь к разработчику",
            "Попробуйте перезапустить систему"
        ]
        self._print_suggestions(suggestions)
    
    def _print_suggestions(self, suggestions: List[str]):
        """Вывести предложения по исправлению"""
        print("💡 Предложения по исправлению:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Получить статистику ошибок"""
        if not self.error_history:
            return {"total_errors": 0}
        
        # Группировка по категориям
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            category = error.category.value
            severity = error.severity.value
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "category_counts": category_counts,
            "severity_counts": severity_counts,
            "recent_errors": self.error_history[-5:] if len(self.error_history) > 5 else self.error_history
        }
    
    def print_error_report(self):
        """Вывести отчет об ошибках"""
        stats = self.get_error_statistics()
        
        print("\n📊 ОТЧЕТ ОБ ОШИБКАХ")
        print("=" * 40)
        print(f"Всего ошибок: {stats['total_errors']}")
        
        if stats['total_errors'] > 0:
            print("\nПо категориям:")
            for category, count in stats['category_counts'].items():
                print(f"  • {category}: {count}")
            
            print("\nПо серьезности:")
            for severity, count in stats['severity_counts'].items():
                print(f"  • {severity}: {count}")
            
            print("\nПоследние ошибки:")
            for error in stats['recent_errors']:
                print(f"  • [{error.category.value}] {error.message[:50]}...")
    
    def clear_error_history(self):
        """Очистить историю ошибок"""
        self.error_history.clear()
        self.error_count = 0
        print("🧹 История ошибок очищена")

# Декоратор для автоматической обработки ошибок
def handle_errors(category: ErrorCategory, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """Декоратор для автоматической обработки ошибок"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Получаем обработчик ошибок из контекста
                error_handler = getattr(args[0], 'error_handler', None) if args else None
                if error_handler is None:
                    error_handler = ErrorHandler()
                
                context = {
                    'function': func.__name__,
                    'args': str(args)[:100],
                    'kwargs': str(kwargs)[:100]
                }
                
                error_info = error_handler.handle_error(e, category, context, severity)
                
                # Возвращаем значение по умолчанию в зависимости от типа функции
                if func.__name__.startswith('get_') or func.__name__.startswith('find_'):
                    return None
                elif func.__name__.startswith('is_') or func.__name__.startswith('has_'):
                    return False
                else:
                    return []
        
        return wrapper
    return decorator

# Глобальный обработчик ошибок
global_error_handler = ErrorHandler()

def handle_global_error(error: Exception, category: ErrorCategory, 
                       context: Optional[Dict[str, Any]] = None,
                       severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> ErrorInfo:
    """Обработать ошибку через глобальный обработчик"""
    return global_error_handler.handle_error(error, category, context, severity)

def test_error_handler():
    """Тестирование обработчика ошибок"""
    print("🧪 ТЕСТИРОВАНИЕ ОБРАБОТЧИКА ОШИБОК")
    print("=" * 50)
    
    error_handler = ErrorHandler()
    
    # Тест различных типов ошибок
    try:
        raise FileNotFoundError("Файл не найден")
    except Exception as e:
        error_handler.handle_error(e, ErrorCategory.FILE_ERROR, {"file": "test.txt"})
    
    try:
        raise ConnectionError("Нет подключения к API")
    except Exception as e:
        error_handler.handle_error(e, ErrorCategory.API_ERROR, {"api": "DeepL"}, ErrorSeverity.HIGH)
    
    try:
        raise ValueError("Некорректное значение")
    except Exception as e:
        error_handler.handle_error(e, ErrorCategory.VALIDATION_ERROR, {"field": "quality_score"})
    
    # Выводим отчет
    error_handler.print_error_report()
    
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    test_error_handler()
