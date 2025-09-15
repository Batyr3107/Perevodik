#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Мониторинг производительности системы перевода
Сбор метрик, анализ производительности и экспорт данных
"""

import time
import psutil
import csv
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
import queue
import os

@dataclass
class PerformanceMetric:
    """Метрика производительности"""
    timestamp: str
    metric_name: str
    value: float
    unit: str
    category: str
    details: Dict[str, Any] = None

@dataclass
class SystemMetrics:
    """Системные метрики"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    active_threads: int
    timestamp: str

@dataclass
class TranslationMetrics:
    """Метрики перевода"""
    total_translations: int
    cache_hits: int
    api_calls: int
    avg_translation_time: float
    total_processing_time: float
    error_count: int
    quality_score_avg: float
    timestamp: str

class PerformanceMonitor:
    """Монитор производительности системы"""
    
    def __init__(self, log_file: str = "performance_metrics.json"):
        self.log_file = log_file
        self.metrics_queue = queue.Queue()
        self.metrics_history = []
        self.start_time = time.time()
        
        # Системные метрики
        self.system_metrics = []
        self.translation_metrics = []
        
        # Статистика
        self.stats = {
            'total_metrics_collected': 0,
            'system_checks': 0,
            'translation_checks': 0,
            'errors': 0
        }
        
        # Запускаем фоновый сбор метрик
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self.monitor_thread.start()
        
        print("📊 Мониторинг производительности запущен")
    
    def record_metric(self, metric_name: str, value: float, unit: str, 
                     category: str, details: Dict[str, Any] = None):
        """Записать метрику"""
        metric = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            metric_name=metric_name,
            value=value,
            unit=unit,
            category=category,
            details=details or {}
        )
        
        self.metrics_queue.put(metric)
        self.stats['total_metrics_collected'] += 1
    
    def record_translation_metrics(self, translations: int, cache_hits: int, 
                                 api_calls: int, processing_time: float,
                                 errors: int = 0, quality_score: float = 0.0):
        """Записать метрики перевода"""
        metric = TranslationMetrics(
            total_translations=translations,
            cache_hits=cache_hits,
            api_calls=api_calls,
            avg_translation_time=processing_time / max(translations, 1),
            total_processing_time=processing_time,
            error_count=errors,
            quality_score_avg=quality_score,
            timestamp=datetime.now().isoformat()
        )
        
        self.translation_metrics.append(metric)
        self.stats['translation_checks'] += 1
        
        # Записываем в общие метрики
        self.record_metric("translations_total", translations, "count", "translation")
        self.record_metric("cache_hit_rate", cache_hits / max(translations, 1), "percent", "performance")
        self.record_metric("api_calls", api_calls, "count", "api")
        self.record_metric("avg_translation_time", processing_time / max(translations, 1), "seconds", "performance")
    
    def get_system_metrics(self) -> SystemMetrics:
        """Получить текущие системные метрики"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Память
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024
            memory_available_mb = memory.available / 1024 / 1024
            
            # Диск
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Потоки
            active_threads = threading.active_count()
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                active_threads=active_threads,
                timestamp=datetime.now().isoformat()
            )
            
            self.system_metrics.append(metrics)
            self.stats['system_checks'] += 1
            
            return metrics
            
        except Exception as e:
            print(f"❌ Ошибка получения системных метрик: {e}")
            self.stats['errors'] += 1
            return None
    
    def _background_monitoring(self):
        """Фоновый сбор метрик"""
        while self.monitoring_active:
            try:
                # Собираем системные метрики каждые 5 секунд
                self.get_system_metrics()
                
                # Обрабатываем очередь метрик
                while not self.metrics_queue.empty():
                    try:
                        metric = self.metrics_queue.get_nowait()
                        self.metrics_history.append(metric)
                    except queue.Empty:
                        break
                
                time.sleep(5)  # Пауза между проверками
                
            except Exception as e:
                print(f"❌ Ошибка в фоновом мониторинге: {e}")
                self.stats['errors'] += 1
                time.sleep(10)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Получить сводку производительности"""
        uptime = time.time() - self.start_time
        
        # Анализ системных метрик
        if self.system_metrics:
            avg_cpu = sum(m.cpu_percent for m in self.system_metrics) / len(self.system_metrics)
            avg_memory = sum(m.memory_percent for m in self.system_metrics) / len(self.system_metrics)
            max_memory = max(m.memory_used_mb for m in self.system_metrics)
        else:
            avg_cpu = avg_memory = max_memory = 0.0
        
        # Анализ метрик перевода
        if self.translation_metrics:
            total_translations = sum(m.total_translations for m in self.translation_metrics)
            total_cache_hits = sum(m.cache_hits for m in self.translation_metrics)
            total_api_calls = sum(m.api_calls for m in self.translation_metrics)
            avg_quality = sum(m.quality_score_avg for m in self.translation_metrics) / len(self.translation_metrics)
            cache_hit_rate = total_cache_hits / max(total_translations, 1)
        else:
            total_translations = total_cache_hits = total_api_calls = avg_quality = cache_hit_rate = 0
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'system_metrics': {
                'avg_cpu_percent': avg_cpu,
                'avg_memory_percent': avg_memory,
                'max_memory_used_mb': max_memory,
                'system_checks_count': len(self.system_metrics)
            },
            'translation_metrics': {
                'total_translations': total_translations,
                'total_cache_hits': total_cache_hits,
                'total_api_calls': total_api_calls,
                'cache_hit_rate': cache_hit_rate,
                'avg_quality_score': avg_quality,
                'translation_checks_count': len(self.translation_metrics)
            },
            'monitoring_stats': {
                'total_metrics_collected': self.stats['total_metrics_collected'],
                'errors': self.stats['errors'],
                'metrics_history_size': len(self.metrics_history)
            }
        }
    
    def export_metrics_csv(self, filename: str = None):
        """Экспорт метрик в CSV"""
        if not filename:
            filename = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'metric_name', 'value', 'unit', 'category', 'details']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for metric in self.metrics_history:
                    writer.writerow(asdict(metric))
            
            print(f"📊 Метрики экспортированы в {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Ошибка экспорта CSV: {e}")
            return None
    
    def export_system_metrics_csv(self, filename: str = None):
        """Экспорт системных метрик в CSV"""
        if not filename:
            filename = f"system_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'cpu_percent', 'memory_percent', 'memory_used_mb', 
                             'memory_available_mb', 'disk_usage_percent', 'active_threads']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for metric in self.system_metrics:
                    writer.writerow(asdict(metric))
            
            print(f"📊 Системные метрики экспортированы в {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Ошибка экспорта системных метрик: {e}")
            return None
    
    def export_translation_metrics_csv(self, filename: str = None):
        """Экспорт метрик перевода в CSV"""
        if not filename:
            filename = f"translation_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'total_translations', 'cache_hits', 'api_calls',
                             'avg_translation_time', 'total_processing_time', 'error_count', 'quality_score_avg']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for metric in self.translation_metrics:
                    writer.writerow(asdict(metric))
            
            print(f"📊 Метрики перевода экспортированы в {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Ошибка экспорта метрик перевода: {e}")
            return None
    
    def save_metrics_json(self, filename: str = None):
        """Сохранение всех метрик в JSON"""
        if not filename:
            filename = f"all_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            data = {
                'summary': self.get_performance_summary(),
                'system_metrics': [asdict(m) for m in self.system_metrics],
                'translation_metrics': [asdict(m) for m in self.translation_metrics],
                'performance_metrics': [asdict(m) for m in self.metrics_history],
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"📊 Все метрики сохранены в {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Ошибка сохранения JSON: {e}")
            return None
    
    def print_summary(self):
        """Вывести сводку производительности"""
        summary = self.get_performance_summary()
        
        print("\n" + "="*60)
        print("📊 СВОДКА ПРОИЗВОДИТЕЛЬНОСТИ")
        print("="*60)
        
        print(f"⏱️  Время работы: {summary['uptime_formatted']}")
        
        print(f"\n🖥️  СИСТЕМНЫЕ МЕТРИКИ:")
        sys_metrics = summary['system_metrics']
        print(f"   • Средняя загрузка CPU: {sys_metrics['avg_cpu_percent']:.1f}%")
        print(f"   • Среднее использование памяти: {sys_metrics['avg_memory_percent']:.1f}%")
        print(f"   • Максимальная память: {sys_metrics['max_memory_used_mb']:.1f} MB")
        print(f"   • Проверок системы: {sys_metrics['system_checks_count']}")
        
        print(f"\n🔄 МЕТРИКИ ПЕРЕВОДА:")
        trans_metrics = summary['translation_metrics']
        print(f"   • Всего переводов: {trans_metrics['total_translations']}")
        print(f"   • Попадания в кэш: {trans_metrics['cache_hit_rate']:.2%}")
        print(f"   • API вызовов: {trans_metrics['total_api_calls']}")
        print(f"   • Средняя оценка качества: {trans_metrics['avg_quality_score']:.1f}")
        
        print(f"\n📈 МОНИТОРИНГ:")
        monitor_stats = summary['monitoring_stats']
        print(f"   • Собрано метрик: {monitor_stats['total_metrics_collected']}")
        print(f"   • Ошибок: {monitor_stats['errors']}")
        print(f"   • Размер истории: {monitor_stats['metrics_history_size']}")
        
        print("="*60)
    
    def stop_monitoring(self):
        """Остановить мониторинг"""
        self.monitoring_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        print("🛑 Мониторинг остановлен")

# Пример использования
def main():
    """Пример использования монитора производительности"""
    monitor = PerformanceMonitor()
    
    # Симулируем работу
    print("🔄 Симуляция работы системы...")
    
    for i in range(10):
        # Записываем метрики перевода
        monitor.record_translation_metrics(
            translations=100 + i * 10,
            cache_hits=80 + i * 8,
            api_calls=20 + i * 2,
            processing_time=5.0 + i * 0.5,
            quality_score=95.0 + i * 0.1
        )
        
        # Записываем произвольные метрики
        monitor.record_metric("processing_speed", 1000 + i * 100, "items/sec", "performance")
        monitor.record_metric("memory_usage", 50 + i * 2, "MB", "system")
        
        time.sleep(1)
    
    # Выводим сводку
    monitor.print_summary()
    
    # Экспортируем данные
    monitor.export_metrics_csv()
    monitor.export_system_metrics_csv()
    monitor.export_translation_metrics_csv()
    monitor.save_metrics_json()
    
    # Останавливаем мониторинг
    monitor.stop_monitoring()

if __name__ == "__main__":
    main()
