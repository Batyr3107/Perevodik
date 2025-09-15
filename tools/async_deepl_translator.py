#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Асинхронный переводчик DeepL API
Оптимизированная версия с поддержкой батчей и параллельной обработки
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import os
from urllib.parse import urljoin

@dataclass
class TranslationRequest:
    """Запрос на перевод"""
    text: str
    source_lang: str = "EN"
    target_lang: str = "RU"
    formality: str = "less"
    split_sentences: str = "nonewlines"
    preserve_formatting: bool = True

@dataclass
class TranslationResponse:
    """Ответ от DeepL API"""
    text: str
    detected_source_language: str
    success: bool
    error_message: Optional[str] = None
    processing_time: float = 0.0

class AsyncDeepLTranslator:
    """Асинхронный переводчик DeepL с оптимизациями"""
    
    def __init__(self, api_key: Optional[str] = None, max_concurrent: int = 10):
        self.api_key = api_key or os.getenv('DEEPL_API_KEY')
        if not self.api_key:
            raise ValueError("API ключ не найден! Установите DEEPL_API_KEY")
        
        self.base_url = "https://api-free.deepl.com/v2/translate"
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Кэш для переводов
        self.translation_cache = {}
        self.cache_hits = 0
        self.total_requests = 0
        
        # Статистика
        self.stats = {
            'total_translations': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'total_time': 0.0,
            'errors': 0
        }
    
    async def translate_batch_async(self, texts: List[str], 
                                  batch_size: int = 25,
                                  source_lang: str = "EN", 
                                  target_lang: str = "RU") -> List[TranslationResponse]:
        """Асинхронный перевод батчами"""
        start_time = time.time()
        
        # Фильтруем пустые тексты
        non_empty_texts = [(i, text) for i, text in enumerate(texts) if text.strip()]
        if not non_empty_texts:
            return [TranslationResponse("", source_lang, True) for _ in texts]
        
        # Разбиваем на батчи
        batches = []
        for i in range(0, len(non_empty_texts), batch_size):
            batch = non_empty_texts[i:i + batch_size]
            batches.append(batch)
        
        # Обрабатываем батчи параллельно
        tasks = []
        for batch in batches:
            task = self._translate_batch(batch, source_lang, target_lang)
            tasks.append(task)
        
        # Ждем завершения всех батчей
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Объединяем результаты
        all_results = []
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                # Обрабатываем ошибки
                error_response = TranslationResponse(
                    "", source_lang, False, str(batch_result)
                )
                all_results.append(error_response)
                self.stats['errors'] += 1
            else:
                all_results.extend(batch_result)
        
        # Восстанавливаем порядок с пустыми строками
        final_results = []
        result_index = 0
        
        for i, text in enumerate(texts):
            if text.strip():
                final_results.append(all_results[result_index])
                result_index += 1
            else:
                final_results.append(TranslationResponse("", source_lang, True))
        
        # Обновляем статистику
        self.stats['total_translations'] += len(texts)
        self.stats['total_time'] += time.time() - start_time
        
        return final_results
    
    async def _translate_batch(self, batch: List[tuple], 
                             source_lang: str, target_lang: str) -> List[TranslationResponse]:
        """Перевод одного батча"""
        async with self.semaphore:
            try:
                # Проверяем кэш
                cache_key = f"{source_lang}_{target_lang}_{hash(tuple(text for _, text in batch))}"
                if cache_key in self.translation_cache:
                    self.stats['cache_hits'] += 1
                    return self.translation_cache[cache_key]
                
                # Подготавливаем данные для API
                texts_to_translate = [text for _, text in batch]
                
                # Вызываем API
                results = await self._call_deepl_api(texts_to_translate, source_lang, target_lang)
                
                # Кэшируем результат
                self.translation_cache[cache_key] = results
                
                return results
                
            except Exception as e:
                # Возвращаем ошибки для каждого текста в батче
                return [TranslationResponse("", source_lang, False, str(e)) for _ in batch]
    
    async def _call_deepl_api(self, texts: List[str], 
                            source_lang: str, target_lang: str) -> List[TranslationResponse]:
        """Вызов DeepL API"""
        async with aiohttp.ClientSession() as session:
            data = {
                'auth_key': self.api_key,
                'text': texts,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'formality': 'less',  # Для веб-новелл
                'split_sentences': 'nonewlines',  # Сохранение структуры
                'preserve_formatting': 'true',
                'tag_handling': 'xml',
                'outline_detection': 'false'  # Ускорение
            }
            
            start_time = time.time()
            
            try:
                async with session.post(self.base_url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Обрабатываем ответ
                        translations = []
                        for item in result.get('translations', []):
                            translation = TranslationResponse(
                                text=item.get('text', ''),
                                detected_source_language=item.get('detected_source_language', source_lang),
                                success=True,
                                processing_time=time.time() - start_time
                            )
                            translations.append(translation)
                        
                        self.stats['api_calls'] += 1
                        return translations
                    
                    else:
                        error_text = await response.text()
                        error_response = TranslationResponse(
                            "", source_lang, False, f"API Error {response.status}: {error_text}"
                        )
                        return [error_response for _ in texts]
                        
            except Exception as e:
                error_response = TranslationResponse(
                    "", source_lang, False, f"Network Error: {str(e)}"
                )
                return [error_response for _ in texts]
    
    async def translate_single_async(self, text: str, 
                                   source_lang: str = "EN", 
                                   target_lang: str = "RU") -> TranslationResponse:
        """Перевод одного текста"""
        results = await self.translate_batch_async([text], 1, source_lang, target_lang)
        return results[0] if results else TranslationResponse("", source_lang, False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику"""
        total_time = self.stats['total_time']
        avg_time = total_time / max(self.stats['total_translations'], 1)
        cache_hit_rate = self.stats['cache_hits'] / max(self.stats['total_translations'], 1)
        
        return {
            'total_translations': self.stats['total_translations'],
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate': cache_hit_rate,
            'api_calls': self.stats['api_calls'],
            'total_time': total_time,
            'avg_time_per_translation': avg_time,
            'errors': self.stats['errors'],
            'cache_size': len(self.translation_cache)
        }
    
    def clear_cache(self):
        """Очистить кэш"""
        self.translation_cache.clear()
        print("🧹 Кэш переводов очищен")
    
    def save_cache(self, filepath: str):
        """Сохранить кэш в файл"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
        print(f"💾 Кэш сохранен в {filepath}")
    
    def load_cache(self, filepath: str):
        """Загрузить кэш из файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.translation_cache = json.load(f)
            print(f"📂 Кэш загружен из {filepath}")
        except FileNotFoundError:
            print(f"⚠️ Файл кэша {filepath} не найден")
        except Exception as e:
            print(f"❌ Ошибка загрузки кэша: {e}")

# Пример использования
async def main():
    """Пример использования асинхронного переводчика"""
    translator = AsyncDeepLTranslator()
    
    # Тестовые тексты
    texts = [
        "Hello, world!",
        "This is a test.",
        "How are you today?",
        "I love programming.",
        "Python is awesome!"
    ]
    
    print("🔄 Асинхронный перевод...")
    results = await translator.translate_batch_async(texts, batch_size=3)
    
    for i, result in enumerate(results):
        if result.success:
            print(f"{i+1}. {texts[i]} → {result.text}")
        else:
            print(f"{i+1}. Ошибка: {result.error_message}")
    
    # Статистика
    stats = translator.get_stats()
    print(f"\n📊 Статистика:")
    print(f"   • Всего переводов: {stats['total_translations']}")
    print(f"   • Попадания в кэш: {stats['cache_hit_rate']:.2%}")
    print(f"   • API вызовов: {stats['api_calls']}")
    print(f"   • Среднее время: {stats['avg_time_per_translation']:.3f}с")

if __name__ == "__main__":
    asyncio.run(main())
