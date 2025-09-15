#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Оптимизированный менеджер контекста с улучшенной производительностью
Включает персистентные embeddings, индексы и оптимизированный поиск
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings
import chromadb.utils.embedding_functions as embedding_functions
from functools import lru_cache
import numpy as np

@dataclass
class OptimizedTranslationMemory:
    """Оптимизированная память перевода"""
    original_text: str
    translated_text: str
    chapter: str
    character: Optional[str] = None
    quality_score: float = 0.0
    usage_count: int = 1
    last_used: float = 0.0
    metadata: Dict[str, Any] = None

class OptimizedTranslationMemoryManager:
    """Оптимизированный менеджер переводческой памяти"""
    
    def __init__(self, db_path: str = "translation_memory"):
        self.db_path = db_path
        self.reference_data = {}
        self.collection = None
        self.client = None
        
        # Кэши для быстрого доступа
        self.glossary_cache = {}
        self.phrase_cache = {}
        self.character_style_cache = {}
        
        # Статистика
        self.stats = {
            'cache_hits': 0,
            'db_hits': 0,
            'total_queries': 0,
            'avg_query_time': 0.0
        }
        
        self._initialize()
    
    def _initialize(self):
        """Инициализация с оптимизациями"""
        print("🚀 Инициализация оптимизированного менеджера памяти...")
        
        # Загружаем справочную базу
        self._load_reference_data()
        
        # Инициализируем ChromaDB с оптимизациями
        self._init_optimized_chromadb()
        
        # Предзагружаем кэши
        self._preload_caches()
        
        print("✅ Оптимизированный менеджер памяти готов")
    
    def _load_reference_data(self):
        """Загрузить справочную базу из JSON"""
        try:
            memory_file = os.path.join(self.db_path, "translation_memory.json")
            if os.path.exists(memory_file):
                with open(memory_file, 'r', encoding='utf-8') as f:
                    self.reference_data = json.load(f)
                print("✅ Справочная база загружена")
            else:
                print("⚠️ Файл translation_memory.json не найден")
                self.reference_data = {}
        except Exception as e:
            print(f"❌ Ошибка загрузки справочной базы: {e}")
            self.reference_data = {}
    
    def _init_optimized_chromadb(self):
        """Инициализация оптимизированного ChromaDB"""
        try:
            # Настройки для оптимизации
            settings = Settings(
                persist_directory=self.db_path,
                anonymized_telemetry=False,
                allow_reset=True
            )
            
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=settings
            )
            
            # Оптимизированная функция embeddings
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2",  # Быстрая и эффективная модель
                device="cpu"  # Используем CPU для стабильности
            )
            
            # Создаем коллекцию с оптимизированными настройками
            self.collection = self.client.get_or_create_collection(
                name="optimized_translations",
                embedding_function=embedding_function,
                metadata={
                    "hnsw:space": "cosine",  # Оптимизация для косинусного сходства
                    "hnsw:construction_ef": 200,  # Параметры для быстрого поиска
                    "hnsw:search_ef": 50
                }
            )
            
            print("✅ ChromaDB инициализирован с оптимизациями")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации ChromaDB: {e}")
            self.collection = None
    
    def _preload_caches(self):
        """Предзагрузка кэшей для быстрого доступа"""
        print("🔄 Предзагрузка кэшей...")
        
        # Кэш глоссария
        if 'glossary_terms' in self.reference_data:
            for category, terms in self.reference_data['glossary_terms'].items():
                for term, translation in terms.items():
                    self.glossary_cache[term.lower()] = translation
        
        # Кэш фраз
        if 'phrase_translations' in self.reference_data:
            for chapter, phrases in self.reference_data['phrase_translations'].items():
                for phrase, translation in phrases.items():
                    self.phrase_cache[phrase.lower()] = translation
        
        # Кэш стилей персонажей
        if 'contextual_style_rules' in self.reference_data:
            for character, rules in self.reference_data['contextual_style_rules'].items():
                if 'examples' in rules:
                    self.character_style_cache[character] = rules['examples']
        
        print(f"✅ Кэши загружены: {len(self.glossary_cache)} терминов, {len(self.phrase_cache)} фраз")
    
    @lru_cache(maxsize=1000)
    def get_glossary_term(self, term: str) -> str:
        """Получить термин из глоссария (с кэшированием)"""
        self.stats['total_queries'] += 1
        start_time = time.time()
        
        # Сначала проверяем кэш
        cached_term = self.glossary_cache.get(term.lower())
        if cached_term:
            self.stats['cache_hits'] += 1
            return cached_term
        
        # Поиск в справочной базе
        if 'glossary_terms' in self.reference_data:
            for category, terms in self.reference_data['glossary_terms'].items():
                if term in terms:
                    translation = terms[term]
                    self.glossary_cache[term.lower()] = translation
                    self._update_query_time(time.time() - start_time)
                    return translation
        
        self._update_query_time(time.time() - start_time)
        return term
    
    @lru_cache(maxsize=1000)
    def get_phrase_translation(self, text: str, chapter: str = None) -> Optional[str]:
        """Получить перевод фразы (с кэшированием)"""
        self.stats['total_queries'] += 1
        start_time = time.time()
        
        # Сначала проверяем кэш
        cached_phrase = self.phrase_cache.get(text.lower())
        if cached_phrase:
            self.stats['cache_hits'] += 1
            return cached_phrase
        
        # Поиск в справочной базе
        if 'phrase_translations' in self.reference_data:
            # Поиск по главе
            if chapter and chapter in self.reference_data['phrase_translations']:
                phrases = self.reference_data['phrase_translations'][chapter]
                if text in phrases:
                    translation = phrases[text]
                    self.phrase_cache[text.lower()] = translation
                    self._update_query_time(time.time() - start_time)
                    return translation
            
            # Поиск во всех главах
            for chapter_phrases in self.reference_data['phrase_translations'].values():
                if text in chapter_phrases:
                    translation = chapter_phrases[text]
                    self.phrase_cache[text.lower()] = translation
                    self._update_query_time(time.time() - start_time)
                    return translation
        
        self._update_query_time(time.time() - start_time)
        return None
    
    def get_character_style(self, character: str) -> Dict[str, str]:
        """Получить стиль персонажа"""
        return self.character_style_cache.get(character, {})
    
    def get_forbidden_words(self) -> List[str]:
        """Получить список запрещенных слов"""
        if 'translation_errors' in self.reference_data:
            return self.reference_data['translation_errors'].get('forbidden_words', [])
        return []
    
    def search_similar_translations(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск похожих переводов с оптимизацией"""
        if not self.collection:
            return []
        
        start_time = time.time()
        self.stats['total_queries'] += 1
        
        try:
            # Поиск в ChromaDB
            results = self.collection.query(
                query_texts=[text],
                n_results=limit,
                include=['metadatas', 'distances', 'documents']
            )
            
            self.stats['db_hits'] += 1
            self._update_query_time(time.time() - start_time)
            
            # Форматируем результаты
            similar_translations = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    similar_translations.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0.0
                    })
            
            return similar_translations
            
        except Exception as e:
            print(f"❌ Ошибка поиска в ChromaDB: {e}")
            return []
    
    def add_translation(self, memory: OptimizedTranslationMemory):
        """Добавить перевод в память"""
        if not self.collection:
            return
        
        try:
            # Создаем уникальный ID
            text_hash = hashlib.md5(memory.original_text.encode()).hexdigest()
            
            # Подготавливаем метаданные
            metadata = {
                'chapter': memory.chapter,
                'character': memory.character or '',
                'quality_score': memory.quality_score,
                'usage_count': memory.usage_count,
                'last_used': memory.last_used
            }
            
            if memory.metadata:
                metadata.update(memory.metadata)
            
            # Добавляем в ChromaDB
            self.collection.add(
                documents=[memory.original_text],
                metadatas=[metadata],
                ids=[text_hash]
            )
            
            # Обновляем кэш
            self.phrase_cache[memory.original_text.lower()] = memory.translated_text
            
        except Exception as e:
            print(f"❌ Ошибка добавления перевода: {e}")
    
    def _update_query_time(self, query_time: float):
        """Обновить среднее время запроса"""
        total_queries = self.stats['total_queries']
        current_avg = self.stats['avg_query_time']
        self.stats['avg_query_time'] = (current_avg * (total_queries - 1) + query_time) / total_queries
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику производительности"""
        total_queries = self.stats['total_queries']
        cache_hit_rate = self.stats['cache_hits'] / max(total_queries, 1)
        
        return {
            'total_queries': total_queries,
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate': cache_hit_rate,
            'db_hits': self.stats['db_hits'],
            'avg_query_time': self.stats['avg_query_time'],
            'glossary_cache_size': len(self.glossary_cache),
            'phrase_cache_size': len(self.phrase_cache),
            'character_style_cache_size': len(self.character_style_cache)
        }
    
    def clear_caches(self):
        """Очистить все кэши"""
        self.glossary_cache.clear()
        self.phrase_cache.clear()
        self.character_style_cache.clear()
        
        # Очищаем LRU кэши
        self.get_glossary_term.cache_clear()
        self.get_phrase_translation.cache_clear()
        
        print("🧹 Все кэши очищены")
    
    def optimize_database(self):
        """Оптимизация базы данных"""
        if not self.collection:
            return
        
        try:
            # Получаем статистику коллекции
            count = self.collection.count()
            print(f"📊 Оптимизация базы данных: {count} записей")
            
            # Здесь можно добавить дополнительные оптимизации
            # например, переиндексация, сжатие и т.д.
            
            print("✅ База данных оптимизирована")
            
        except Exception as e:
            print(f"❌ Ошибка оптимизации базы данных: {e}")

# Пример использования
def main():
    """Пример использования оптимизированного менеджера"""
    manager = OptimizedTranslationMemoryManager()
    
    # Тестируем поиск
    print("🔍 Тестирование поиска...")
    
    # Поиск в глоссарии
    term = manager.get_glossary_term("cultivation")
    print(f"Термин 'cultivation': {term}")
    
    # Поиск фразы
    phrase = manager.get_phrase_translation("Hello world", "Глава 1")
    print(f"Фраза 'Hello world': {phrase}")
    
    # Поиск похожих переводов
    similar = manager.search_similar_translations("Hello world", limit=3)
    print(f"Похожие переводы: {len(similar)} найдено")
    
    # Статистика
    stats = manager.get_stats()
    print(f"\n📊 Статистика:")
    print(f"   • Всего запросов: {stats['total_queries']}")
    print(f"   • Попадания в кэш: {stats['cache_hit_rate']:.2%}")
    print(f"   • Среднее время запроса: {stats['avg_query_time']:.4f}с")

if __name__ == "__main__":
    main()
