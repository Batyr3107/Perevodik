#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Оптимизатор производительности
Мониторинг и оптимизация работы системы перевода
"""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

@dataclass
class PerformanceMetric:
    """Метрика производительности"""
    name: str
    value: float
    unit: str
    timestamp: str
    category: str

@dataclass
class PerformanceProfile:
    """Профиль производительности операции"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_usage: float
    cpu_usage: float
    success: bool
    error_message: Optional[str] = None

class PerformanceMonitor:
    """Монитор производительности"""
    
    def __init__(self):
        self.metrics = []
        self.profiles = []
        self.start_time = time.time()
        
        # Системные метрики
        self.system_metrics = {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "disk_total": psutil.disk_usage('/').total
        }
    
    def start_profile(self, operation_name: str) -> PerformanceProfile:
        """Начать профилирование операции"""
        profile = PerformanceProfile(
            operation_name=operation_name,
            start_time=time.time(),
            end_time=0,
            duration=0,
            memory_usage=psutil.Process().memory_info().rss,
            cpu_usage=psutil.cpu_percent(),
            success=False
        )
        return profile
    
    def end_profile(self, profile: PerformanceProfile, success: bool = True, error_message: str = None):
        """Завершить профилирование операции"""
        profile.end_time = time.time()
        profile.duration = profile.end_time - profile.start_time
        profile.success = success
        profile.error_message = error_message
        profile.memory_usage = psutil.Process().memory_info().rss
        profile.cpu_usage = psutil.cpu_percent()
        
        self.profiles.append(profile)
    
    def add_metric(self, name: str, value: float, unit: str, category: str = "general"):
        """Добавить метрику"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now().isoformat(),
            category=category
        )
        self.metrics.append(metric)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Получить системные метрики"""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available": psutil.virtual_memory().available,
            "disk_percent": psutil.disk_usage('/').percent,
            "disk_free": psutil.disk_usage('/').free,
            "uptime": time.time() - self.start_time
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Получить сводку по производительности"""
        if not self.profiles:
            return {"message": "Нет данных о производительности"}
        
        # Статистика по операциям
        operation_stats = {}
        for profile in self.profiles:
            op_name = profile.operation_name
            if op_name not in operation_stats:
                operation_stats[op_name] = {
                    "count": 0,
                    "total_duration": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "avg_duration": 0,
                    "min_duration": float('inf'),
                    "max_duration": 0
                }
            
            stats = operation_stats[op_name]
            stats["count"] += 1
            stats["total_duration"] += profile.duration
            stats["success_count"] += 1 if profile.success else 0
            stats["error_count"] += 0 if profile.success else 1
            
            stats["min_duration"] = min(stats["min_duration"], profile.duration)
            stats["max_duration"] = max(stats["max_duration"], profile.duration)
        
        # Вычисляем средние значения
        for op_name, stats in operation_stats.items():
            if stats["count"] > 0:
                stats["avg_duration"] = stats["total_duration"] / stats["count"]
                stats["success_rate"] = stats["success_count"] / stats["count"] * 100
        
        return {
            "total_operations": len(self.profiles),
            "operation_stats": operation_stats,
            "system_metrics": self.get_system_metrics(),
            "uptime": time.time() - self.start_time
        }
    
    def print_performance_report(self):
        """Вывести отчет о производительности"""
        summary = self.get_performance_summary()
        
        print("\n📊 ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ")
        print("=" * 50)
        
        # Системные метрики
        sys_metrics = summary["system_metrics"]
        print(f"🖥️ Система:")
        print(f"   CPU: {sys_metrics['cpu_percent']:.1f}%")
        print(f"   Память: {sys_metrics['memory_percent']:.1f}%")
        print(f"   Диск: {sys_metrics['disk_percent']:.1f}%")
        print(f"   Время работы: {sys_metrics['uptime']:.1f}с")
        
        # Статистика операций
        if "operation_stats" in summary:
            print(f"\n⚡ Операции:")
            for op_name, stats in summary["operation_stats"].items():
                print(f"   {op_name}:")
                print(f"     Выполнений: {stats['count']}")
                print(f"     Успешных: {stats['success_count']} ({stats['success_rate']:.1f}%)")
                print(f"     Среднее время: {stats['avg_duration']:.3f}с")
                print(f"     Мин/Макс: {stats['min_duration']:.3f}с / {stats['max_duration']:.3f}с")

class PerformanceOptimizer:
    """Оптимизатор производительности"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.optimization_rules = []
        self.cache_hits = 0
        self.cache_misses = 0
    
    def profile_operation(self, operation_name: str):
        """Декоратор для профилирования операций"""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                profile = self.monitor.start_profile(operation_name)
                try:
                    result = func(*args, **kwargs)
                    self.monitor.end_profile(profile, success=True)
                    return result
                except Exception as e:
                    self.monitor.end_profile(profile, success=False, error_message=str(e))
                    raise
            return wrapper
        return decorator
    
    def optimize_translation_batch(self, texts: List[str], translate_func: Callable, 
                                 batch_size: int = 5) -> List[str]:
        """Оптимизированный пакетный перевод"""
        profile = self.monitor.start_profile("batch_translation")
        
        try:
            results = []
            
            # Разбиваем на батчи
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Переводим батч
                batch_results = translate_func(batch)
                results.extend(batch_results)
                
                # Небольшая пауза между батчами
                time.sleep(0.1)
            
            self.monitor.end_profile(profile, success=True)
            return results
            
        except Exception as e:
            self.monitor.end_profile(profile, success=False, error_message=str(e))
            raise
    
    def optimize_parallel_processing(self, tasks: List[Callable], max_workers: int = 4) -> List[Any]:
        """Оптимизированная параллельная обработка"""
        profile = self.monitor.start_profile("parallel_processing")
        
        try:
            results = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Запускаем задачи
                future_to_task = {executor.submit(task): task for task in tasks}
                
                # Собираем результаты
                for future in as_completed(future_to_task):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        print(f"⚠️ Ошибка в параллельной задаче: {e}")
                        results.append(None)
            
            self.monitor.end_profile(profile, success=True)
            return results
            
        except Exception as e:
            self.monitor.end_profile(profile, success=False, error_message=str(e))
            raise
    
    def optimize_memory_usage(self, func: Callable, *args, **kwargs):
        """Оптимизация использования памяти"""
        profile = self.monitor.start_profile("memory_optimized_operation")
        
        try:
            # Принудительная сборка мусора
            import gc
            gc.collect()
            
            # Выполняем операцию
            result = func(*args, **kwargs)
            
            # Снова собираем мусор
            gc.collect()
            
            self.monitor.end_profile(profile, success=True)
            return result
            
        except Exception as e:
            self.monitor.end_profile(profile, success=False, error_message=str(e))
            raise
    
    def add_cache_hit(self):
        """Увеличить счетчик попаданий в кэш"""
        self.cache_hits += 1
    
    def add_cache_miss(self):
        """Увеличить счетчик промахов кэша"""
        self.cache_misses += 1
    
    def get_cache_efficiency(self) -> float:
        """Получить эффективность кэша"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total * 100
    
    def suggest_optimizations(self) -> List[str]:
        """Предложить оптимизации на основе метрик"""
        suggestions = []
        summary = self.monitor.get_performance_summary()
        
        # Анализируем системные метрики
        sys_metrics = summary["system_metrics"]
        
        if sys_metrics["cpu_percent"] > 80:
            suggestions.append("🔴 Высокая загрузка CPU - рассмотрите уменьшение количества параллельных задач")
        
        if sys_metrics["memory_percent"] > 85:
            suggestions.append("🔴 Высокая загрузка памяти - рассмотрите очистку кэша или уменьшение размера батчей")
        
        if sys_metrics["disk_percent"] > 90:
            suggestions.append("🔴 Мало места на диске - очистите временные файлы")
        
        # Анализируем операции
        if "operation_stats" in summary:
            for op_name, stats in summary["operation_stats"].items():
                if stats["success_rate"] < 90:
                    suggestions.append(f"🟡 Низкий процент успеха для {op_name}: {stats['success_rate']:.1f}%")
                
                if stats["avg_duration"] > 5.0:
                    suggestions.append(f"🟡 Медленная операция {op_name}: {stats['avg_duration']:.1f}с")
        
        # Анализируем кэш
        cache_efficiency = self.get_cache_efficiency()
        if cache_efficiency < 50:
            suggestions.append(f"🟡 Низкая эффективность кэша: {cache_efficiency:.1f}%")
        
        return suggestions
    
    def print_optimization_report(self):
        """Вывести отчет об оптимизации"""
        self.monitor.print_performance_report()
        
        print(f"\n💾 Кэш:")
        print(f"   Попаданий: {self.cache_hits}")
        print(f"   Промахов: {self.cache_misses}")
        print(f"   Эффективность: {self.get_cache_efficiency():.1f}%")
        
        suggestions = self.suggest_optimizations()
        if suggestions:
            print(f"\n💡 Рекомендации по оптимизации:")
            for suggestion in suggestions:
                print(f"   {suggestion}")

# Глобальный оптимизатор
global_optimizer = PerformanceOptimizer()

def optimize_performance(operation_name: str):
    """Декоратор для оптимизации производительности"""
    return global_optimizer.profile_operation(operation_name)

def test_performance_optimizer():
    """Тестирование оптимизатора производительности"""
    print("🧪 ТЕСТИРОВАНИЕ ОПТИМИЗАТОРА ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 50)
    
    optimizer = PerformanceOptimizer()
    
    # Тест профилирования
    @optimizer.profile_operation("test_operation")
    def test_function():
        time.sleep(0.1)
        return "test_result"
    
    result = test_function()
    print(f"Результат тестовой функции: {result}")
    
    # Тест кэша
    for _ in range(10):
        optimizer.add_cache_hit()
    for _ in range(5):
        optimizer.add_cache_miss()
    
    print(f"Эффективность кэша: {optimizer.get_cache_efficiency():.1f}%")
    
    # Выводим отчет
    optimizer.print_optimization_report()
    
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    test_performance_optimizer()
