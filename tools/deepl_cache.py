#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Кэширование для DeepL API
Уменьшает количество запросов и ускоряет работу
"""

import json
import hashlib
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

class DeepLCache:
    """Кэш для DeepL API запросов"""
    
    def __init__(self, cache_dir: str = "./deepl_cache", max_age_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_age_hours = max_age_hours
        self.cache_file = self.cache_dir / "translations.json"
        
        # Загружаем существующий кэш
        self.cache = self._load_cache()
        
        # Статистика
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0,
            "cache_size": 0
        }
    
    def _load_cache(self) -> Dict[str, Any]:
        """Загрузить кэш из файла"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('cache', {})
            except Exception as e:
                print(f"⚠️ Ошибка загрузки кэша: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Сохранить кэш в файл"""
        try:
            data = {
                'cache': self.cache,
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'stats': self.stats
                }
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения кэша: {e}")
    
    def _generate_key(self, text: str, source_lang: str = 'EN', target_lang: str = 'RU') -> str:
        """Генерировать ключ кэша для текста"""
        # Создаем хэш от текста и языков
        content = f"{text}|{source_lang}|{target_lang}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _is_expired(self, timestamp: str) -> bool:
        """Проверить, истек ли срок кэша"""
        try:
            cache_time = datetime.fromisoformat(timestamp)
            expiry_time = cache_time + timedelta(hours=self.max_age_hours)
            return datetime.now() > expiry_time
        except Exception:
            return True
    
    def get(self, text: str, source_lang: str = 'EN', target_lang: str = 'RU') -> Optional[str]:
        """Получить перевод из кэша"""
        key = self._generate_key(text, source_lang, target_lang)
        self.stats["total_requests"] += 1
        
        if key in self.cache:
            cache_entry = self.cache[key]
            
            # Проверяем срок действия
            if not self._is_expired(cache_entry['timestamp']):
                self.stats["hits"] += 1
                return cache_entry['translation']
            else:
                # Удаляем устаревшую запись
                del self.cache[key]
        
        self.stats["misses"] += 1
        return None
    
    def set(self, text: str, translation: str, source_lang: str = 'EN', target_lang: str = 'RU'):
        """Сохранить перевод в кэш"""
        key = self._generate_key(text, source_lang, target_lang)
        
        self.cache[key] = {
            'original_text': text,
            'translation': translation,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'timestamp': datetime.now().isoformat(),
            'text_length': len(text)
        }
        
        self.stats["cache_size"] = len(self.cache)
        
        # Периодически сохраняем кэш
        if len(self.cache) % 10 == 0:
            self._save_cache()
    
    def get_or_translate(self, text: str, translate_func, source_lang: str = 'EN', target_lang: str = 'RU') -> str:
        """Получить из кэша или перевести"""
        # Проверяем кэш
        cached_translation = self.get(text, source_lang, target_lang)
        if cached_translation:
            return cached_translation
        
        # Переводим
        try:
            translation = translate_func(text)
            self.set(text, translation, source_lang, target_lang)
            return translation
        except Exception as e:
            print(f"⚠️ Ошибка перевода: {e}")
            return text  # Fallback
    
    def batch_get_or_translate(self, texts: List[str], translate_func, 
                              source_lang: str = 'EN', target_lang: str = 'RU') -> List[str]:
        """Пакетное получение/перевод"""
        results = []
        texts_to_translate = []
        indices_to_translate = []
        
        # Проверяем кэш для каждого текста
        for i, text in enumerate(texts):
            cached = self.get(text, source_lang, target_lang)
            if cached:
                results.append(cached)
            else:
                results.append(None)  # Placeholder
                texts_to_translate.append(text)
                indices_to_translate.append(i)
        
        # Переводим только те, которых нет в кэше
        if texts_to_translate:
            try:
                translations = translate_func(texts_to_translate)
                for i, translation in enumerate(translations):
                    original_index = indices_to_translate[i]
                    original_text = texts_to_translate[i]
                    
                    results[original_index] = translation
                    self.set(original_text, translation, source_lang, target_lang)
            except Exception as e:
                print(f"⚠️ Ошибка пакетного перевода: {e}")
                # Fallback - используем оригинальные тексты
                for i, original_index in enumerate(indices_to_translate):
                    if results[original_index] is None:
                        results[original_index] = texts[original_index]
        
        return results
    
    def clear_expired(self):
        """Очистить устаревшие записи"""
        expired_keys = []
        for key, entry in self.cache.items():
            if self._is_expired(entry['timestamp']):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        self.stats["cache_size"] = len(self.cache)
        print(f"🧹 Удалено устаревших записей: {len(expired_keys)}")
    
    def clear_all(self):
        """Очистить весь кэш"""
        self.cache.clear()
        self.stats["cache_size"] = 0
        print("🧹 Кэш полностью очищен")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        hit_rate = (self.stats["hits"] / self.stats["total_requests"] * 100) if self.stats["total_requests"] > 0 else 0
        
        return {
            "cache_size": self.stats["cache_size"],
            "total_requests": self.stats["total_requests"],
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "cache_file": str(self.cache_file),
            "max_age_hours": self.max_age_hours
        }
    
    def print_stats(self):
        """Вывести статистику кэша"""
        stats = self.get_stats()
        
        print("\n📊 СТАТИСТИКА КЭША DEEPL")
        print("=" * 40)
        print(f"Размер кэша: {stats['cache_size']} записей")
        print(f"Всего запросов: {stats['total_requests']}")
        print(f"Попаданий: {stats['hits']}")
        print(f"Промахов: {stats['misses']}")
        print(f"Процент попаданий: {stats['hit_rate']}%")
        print(f"Файл кэша: {stats['cache_file']}")
        print(f"Максимальный возраст: {stats['max_age_hours']} часов")
    
    def cleanup(self):
        """Очистка и сохранение"""
        self.clear_expired()
        self._save_cache()
        print("✅ Кэш очищен и сохранен")

class CachedDeepLTranslator:
    """DeepL переводчик с кэшированием"""
    
    def __init__(self, cache_dir: str = "./deepl_cache"):
        self.cache = DeepLCache(cache_dir)
        
        # Инициализируем базовый переводчик
        try:
            from tools.deepl_translator import DeepLFileTranslator
            self.translator = DeepLFileTranslator()
        except ImportError:
            print("⚠️ DeepLFileTranslator не найден")
            self.translator = None
    
    def translate_text(self, text: str, source_lang: str = 'EN', target_lang: str = 'RU') -> str:
        """Перевести текст с кэшированием"""
        if not self.translator:
            return text
        
        def translate_func(t):
            return self.translator.translate_text(t, source_lang, target_lang)
        
        return self.cache.get_or_translate(text, translate_func, source_lang, target_lang)
    
    def translate_fragments(self, fragments: List[str], source_lang: str = 'EN', target_lang: str = 'RU') -> List[str]:
        """Перевести фрагменты с кэшированием"""
        if not self.translator:
            return fragments
        
        def translate_func(texts):
            return self.translator.translate_text(texts, source_lang, target_lang)
        
        return self.cache.batch_get_or_translate(fragments, translate_func, source_lang, target_lang)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        return self.cache.get_stats()
    
    def print_cache_stats(self):
        """Вывести статистику кэша"""
        self.cache.print_stats()
    
    def cleanup_cache(self):
        """Очистить кэш"""
        self.cache.cleanup()

def test_deepl_cache():
    """Тестирование кэша DeepL"""
    print("🧪 ТЕСТИРОВАНИЕ КЭША DEEPL")
    print("=" * 50)
    
    # Создаем кэш
    cache = DeepLCache(max_age_hours=1)
    
    # Тестовые данные
    test_texts = [
        "Hello, world!",
        "This is a test.",
        "Hello, world!",  # Дубликат для проверки кэша
        "Another test text."
    ]
    
    # Симуляция функции перевода
    def mock_translate(text):
        time.sleep(0.1)  # Имитация задержки API
        return f"[RU] {text}"
    
    print("🔄 Тестирование без кэша...")
    start_time = time.time()
    for text in test_texts:
        result = mock_translate(text)
    no_cache_time = time.time() - start_time
    
    print("🔄 Тестирование с кэшем...")
    start_time = time.time()
    for text in test_texts:
        result = cache.get_or_translate(text, mock_translate)
    with_cache_time = time.time() - start_time
    
    # Статистика
    cache.print_stats()
    
    print(f"\n⏱️ Время без кэша: {no_cache_time:.2f}с")
    print(f"⏱️ Время с кэшем: {with_cache_time:.2f}с")
    print(f"🚀 Ускорение: {no_cache_time/with_cache_time:.1f}x")
    
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    test_deepl_cache()
