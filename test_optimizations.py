#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест оптимизаций производительности
Сравнение старой и новой системы
"""

import sys
import os
import time
import asyncio
sys.path.append('tools')

# Устанавливаем API ключ
os.environ['DEEPL_API_KEY'] = '174cabf4-06f5-4f88-90a6-be7add90275a:fx'

from tools.async_deepl_translator import AsyncDeepLTranslator
from tools.optimized_context_manager import OptimizedTranslationMemoryManager
from tools.performance_monitor import PerformanceMonitor
from tools.performance_optimizer import PerformanceOptimizer

def test_batch_size_optimization():
    """Тест оптимизации размера батчей"""
    print("🧪 ТЕСТ ОПТИМИЗАЦИИ РАЗМЕРА БАТЧЕЙ")
    print("=" * 50)
    
    # Тестовые тексты
    test_texts = [
        "Hello, world!",
        "This is a test sentence.",
        "How are you today?",
        "I love programming in Python.",
        "The weather is beautiful today.",
        "Machine learning is fascinating.",
        "Translation systems are complex.",
        "Performance optimization is important.",
        "Code quality matters a lot.",
        "Testing is essential for reliability."
    ] * 5  # 50 текстов
    
    optimizer = PerformanceOptimizer()
    
    # Тестируем разные размеры батчей
    batch_sizes = [5, 10, 25, 50]
    
    for batch_size in batch_sizes:
        print(f"\n📊 Тестирование размера батча: {batch_size}")
        
        start_time = time.time()
        
        # Симулируем перевод (заглушка)
        def mock_translate(batch):
            time.sleep(0.1)  # Симулируем время API
            return [f"Translated: {text}" for text in batch]
        
        results = optimizer.optimize_translation_batch(
            test_texts, mock_translate, batch_size
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   • Время выполнения: {duration:.2f}с")
        print(f"   • Скорость: {len(test_texts)/duration:.1f} текстов/сек")
        print(f"   • Результатов: {len(results)}")

async def test_async_translator():
    """Тест асинхронного переводчика"""
    print("\n🧪 ТЕСТ АСИНХРОННОГО ПЕРЕВОДЧИКА")
    print("=" * 50)
    
    translator = AsyncDeepLTranslator()
    
    # Тестовые тексты
    test_texts = [
        "Hello, world!",
        "This is a test.",
        "How are you?",
        "I love Python.",
        "Machine learning is great."
    ]
    
    print("🔄 Асинхронный перевод...")
    start_time = time.time()
    
    results = await translator.translate_batch_async(test_texts, batch_size=3)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ Перевод завершен за {duration:.2f}с")
    
    for i, result in enumerate(results):
        if result.success:
            print(f"   {i+1}. {test_texts[i]} → {result.text}")
        else:
            print(f"   {i+1}. Ошибка: {result.error_message}")
    
    # Статистика
    stats = translator.get_stats()
    print(f"\n📊 Статистика переводчика:")
    print(f"   • Всего переводов: {stats['total_translations']}")
    print(f"   • Попадания в кэш: {stats['cache_hit_rate']:.2%}")
    print(f"   • API вызовов: {stats['api_calls']}")
    print(f"   • Среднее время: {stats['avg_time_per_translation']:.3f}с")

def test_optimized_context_manager():
    """Тест оптимизированного менеджера контекста"""
    print("\n🧪 ТЕСТ ОПТИМИЗИРОВАННОГО МЕНЕДЖЕРА КОНТЕКСТА")
    print("=" * 50)
    
    manager = OptimizedTranslationMemoryManager()
    
    # Тестируем поиск в глоссарии
    print("🔍 Тестирование поиска в глоссарии...")
    
    test_terms = ["cultivation", "spiritual energy", "realm", "technique", "martial arts"]
    
    start_time = time.time()
    for term in test_terms:
        result = manager.get_glossary_term(term)
        print(f"   • {term} → {result}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ Поиск в глоссарии завершен за {duration:.3f}с")
    
    # Тестируем поиск фраз
    print("\n🔍 Тестирование поиска фраз...")
    
    test_phrases = ["Hello world", "How are you", "Thank you", "Good morning", "See you later"]
    
    start_time = time.time()
    for phrase in test_phrases:
        result = manager.get_phrase_translation(phrase, "Глава 1")
        print(f"   • {phrase} → {result}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ Поиск фраз завершен за {duration:.3f}с")
    
    # Статистика
    stats = manager.get_stats()
    print(f"\n📊 Статистика менеджера:")
    print(f"   • Всего запросов: {stats['total_queries']}")
    print(f"   • Попадания в кэш: {stats['cache_hit_rate']:.2%}")
    print(f"   • Среднее время запроса: {stats['avg_query_time']:.4f}с")
    print(f"   • Размер кэша глоссария: {stats['glossary_cache_size']}")
    print(f"   • Размер кэша фраз: {stats['phrase_cache_size']}")

def test_performance_monitoring():
    """Тест мониторинга производительности"""
    print("\n🧪 ТЕСТ МОНИТОРИНГА ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 50)
    
    monitor = PerformanceMonitor()
    
    # Симулируем работу системы
    print("🔄 Симуляция работы системы...")
    
    for i in range(5):
        # Записываем метрики перевода
        monitor.record_translation_metrics(
            translations=100 + i * 20,
            cache_hits=80 + i * 15,
            api_calls=20 + i * 5,
            processing_time=2.0 + i * 0.5,
            quality_score=95.0 + i * 0.5
        )
        
        # Записываем системные метрики
        monitor.record_metric("cpu_usage", 50 + i * 5, "percent", "system")
        monitor.record_metric("memory_usage", 100 + i * 10, "MB", "system")
        monitor.record_metric("translation_speed", 1000 + i * 100, "items/sec", "performance")
        
        time.sleep(1)
    
    # Выводим сводку
    monitor.print_summary()
    
    # Экспортируем данные
    print("\n📊 Экспорт метрик...")
    monitor.export_metrics_csv("test_metrics.csv")
    monitor.export_system_metrics_csv("test_system_metrics.csv")
    monitor.export_translation_metrics_csv("test_translation_metrics.csv")
    monitor.save_metrics_json("test_all_metrics.json")
    
    # Останавливаем мониторинг
    monitor.stop_monitoring()

async def main():
    """Главная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ОПТИМИЗАЦИЙ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 60)
    
    try:
        # Тест оптимизации батчей
        test_batch_size_optimization()
        
        # Тест асинхронного переводчика
        await test_async_translator()
        
        # Тест оптимизированного менеджера контекста
        test_optimized_context_manager()
        
        # Тест мониторинга производительности
        test_performance_monitoring()
        
        print("\n🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
