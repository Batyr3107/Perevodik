#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер контекстной памяти для переводов
Использует ChromaDB для хранения и поиска похожих переводов
"""

import json
import os
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ ChromaDB не установлен. Установите: pip install chromadb")

@dataclass
class TranslationMemory:
    """Структура для хранения перевода в памяти"""
    source_text: str
    target_text: str
    chapter: str
    character: Optional[str] = None
    context: Optional[str] = None
    quality_score: Optional[float] = None
    timestamp: Optional[str] = None

class TranslationMemoryManager:
    """Менеджер контекстной памяти для переводов"""
    
    def __init__(self, db_path: str = "./translation_memory"):
        self.db_path = db_path
        self.client = None
        self.collection = None
        
        # Загружаем справочную базу из translation_memory.json
        self.reference_data = self._load_reference_data()
        
        if CHROMADB_AVAILABLE:
            self._initialize_database()
        else:
            print("❌ ChromaDB недоступен. Используется файловая система.")
            self._initialize_file_system()
    
    def _load_reference_data(self) -> Dict[str, Any]:
        """Загрузить справочную базу из translation_memory.json"""
        try:
            memory_file = os.path.join(self.db_path, "translation_memory.json")
            if os.path.exists(memory_file):
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print("✅ Справочная база загружена из translation_memory.json")
                return data
            else:
                print("⚠️ Файл translation_memory.json не найден, создается пустая база")
                return {}
        except Exception as e:
            print(f"❌ Ошибка загрузки справочной базы: {e}")
            return {}
    
    def _initialize_database(self):
        """Инициализация ChromaDB"""
        try:
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name="translations",
                metadata={"description": "Translation memory for novel chapters"}
            )
            print("✅ ChromaDB инициализирован")
        except Exception as e:
            print(f"❌ Ошибка инициализации ChromaDB: {e}")
            self._initialize_file_system()
    
    def _initialize_file_system(self):
        """Инициализация файловой системы как fallback"""
        os.makedirs(self.db_path, exist_ok=True)
        self.memory_file = os.path.join(self.db_path, "translation_memory.json")
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        print("✅ Файловая система инициализирована")
    
    def add_translation(self, memory: TranslationMemory) -> str:
        """Добавить перевод в память"""
        if self.collection:
            return self._add_to_chromadb(memory)
        else:
            return self._add_to_file_system(memory)
    
    def _add_to_chromadb(self, memory: TranslationMemory) -> str:
        """Добавить в ChromaDB"""
        try:
            # Генерируем уникальный ID
            memory_id = hashlib.md5(
                f"{memory.source_text}_{memory.chapter}".encode()
            ).hexdigest()
            
            # Подготавливаем метаданные
            metadata = {
                "chapter": memory.chapter,
                "character": memory.character or "",
                "context": memory.context or "",
                "quality_score": memory.quality_score or 0.0,
                "timestamp": memory.timestamp or datetime.now().isoformat()
            }
            
            # Добавляем в коллекцию
            self.collection.add(
                documents=[memory.source_text],
                metadatas=[metadata],
                ids=[memory_id]
            )
            
            return memory_id
        except Exception as e:
            print(f"❌ Ошибка добавления в ChromaDB: {e}")
            return self._add_to_file_system(memory)
    
    def _add_to_file_system(self, memory: TranslationMemory) -> str:
        """Добавить в файловую систему"""
        try:
            # Читаем существующие данные
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Генерируем ID
            memory_id = hashlib.md5(
                f"{memory.source_text}_{memory.chapter}".encode()
            ).hexdigest()
            
            # Добавляем новый перевод
            translation_data = {
                "id": memory_id,
                "source_text": memory.source_text,
                "target_text": memory.target_text,
                "chapter": memory.chapter,
                "character": memory.character,
                "context": memory.context,
                "quality_score": memory.quality_score,
                "timestamp": memory.timestamp or datetime.now().isoformat()
            }
            
            data.append(translation_data)
            
            # Сохраняем обратно
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return memory_id
        except Exception as e:
            print(f"❌ Ошибка добавления в файловую систему: {e}")
            return ""
    
    def find_similar(self, text: str, threshold: float = 0.85, max_results: int = 5) -> List[Dict]:
        """Найти похожие переводы"""
        if self.collection:
            return self._find_similar_chromadb(text, threshold, max_results)
        else:
            return self._find_similar_file_system(text, threshold, max_results)
    
    def _find_similar_chromadb(self, text: str, threshold: float, max_results: int) -> List[Dict]:
        """Поиск в ChromaDB"""
        try:
            results = self.collection.query(
                query_texts=[text],
                n_results=max_results
            )
            
            similar_translations = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if 'distances' in results else 0.0
                    similarity = 1.0 - distance  # Преобразуем расстояние в схожесть
                    
                    if similarity >= threshold:
                        similar_translations.append({
                            "source_text": doc,
                            "target_text": metadata.get("target_text", ""),
                            "chapter": metadata.get("chapter", ""),
                            "character": metadata.get("character", ""),
                            "similarity": similarity,
                            "context": metadata.get("context", "")
                        })
            
            return similar_translations
        except Exception as e:
            print(f"❌ Ошибка поиска в ChromaDB: {e}")
            return []
    
    def _find_similar_file_system(self, text: str, threshold: float, max_results: int) -> List[Dict]:
        """Поиск в файловой системе (упрощенный)"""
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            similar_translations = []
            for item in data:
                # Простая проверка на схожесть по ключевым словам
                source_words = set(text.lower().split())
                item_words = set(item['source_text'].lower().split())
                
                if source_words and item_words:
                    similarity = len(source_words.intersection(item_words)) / len(source_words.union(item_words))
                    
                    if similarity >= threshold:
                        similar_translations.append({
                            "source_text": item['source_text'],
                            "target_text": item['target_text'],
                            "chapter": item['chapter'],
                            "character": item.get('character', ''),
                            "similarity": similarity,
                            "context": item.get('context', '')
                        })
            
            # Сортируем по схожести и возвращаем топ результатов
            similar_translations.sort(key=lambda x: x['similarity'], reverse=True)
            return similar_translations[:max_results]
        except Exception as e:
            print(f"❌ Ошибка поиска в файловой системе: {e}")
            return []
    
    def get_phrase_translation(self, text: str, chapter: str = None) -> Optional[str]:
        """Найти готовый перевод фразы из справочной базы"""
        if not self.reference_data or 'phrase_translations' not in self.reference_data:
            return None
        
        phrase_translations = self.reference_data['phrase_translations']
        
        # Ищем точное совпадение
        for chapter_key, phrases in phrase_translations.items():
            if text in phrases:
                return phrases[text]
        
        # Ищем частичное совпадение
        for chapter_key, phrases in phrase_translations.items():
            for phrase, translation in phrases.items():
                if text.lower() in phrase.lower() or phrase.lower() in text.lower():
                    return translation
        
        return None
    
    def get_glossary_term(self, term: str) -> Optional[str]:
        """Найти термин в глоссарии"""
        if not self.reference_data or 'glossary_terms' not in self.reference_data:
            return None
        
        glossary = self.reference_data['glossary_terms']
        
        # Ищем во всех категориях глоссария
        for category, terms in glossary.items():
            if term in terms:
                return terms[term]
        
        return None
    
    def get_forbidden_words(self) -> List[str]:
        """Получить список запрещенных слов"""
        if not self.reference_data or 'translation_errors' not in self.reference_data:
            return []
        
        errors = self.reference_data['translation_errors']
        return errors.get('forbidden_words', [])
    
    def get_character_style(self, character: str) -> Dict[str, Any]:
        """Получить стиль персонажа"""
        if not self.reference_data or 'contextual_style_rules' not in self.reference_data:
            return {}
        
        style_rules = self.reference_data['contextual_style_rules']
        return style_rules.get(f"{character}_thoughts", {})
    
    def get_system_style(self) -> Dict[str, Any]:
        """Получить стиль системных уведомлений"""
        if not self.reference_data or 'contextual_style_rules' not in self.reference_data:
            return {}
        
        style_rules = self.reference_data['contextual_style_rules']
        return style_rules.get('system_notifications', {})
    
    def get_chapter_context(self, chapter: str, context_window: int = 3) -> List[Dict]:
        """Получить контекст главы"""
        if self.collection:
            try:
                results = self.collection.query(
                    query_texts=[""],
                    where={"chapter": chapter},
                    n_results=100  # Получаем все переводы из главы
                )
                
                translations = []
                if results['documents'] and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        metadata = results['metadatas'][0][i]
                        translations.append({
                            "source_text": doc,
                            "target_text": metadata.get("target_text", ""),
                            "character": metadata.get("character", ""),
                            "context": metadata.get("context", "")
                        })
                
                return translations
            except Exception as e:
                print(f"❌ Ошибка получения контекста главы: {e}")
                return []
        else:
            # Файловая система
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                chapter_translations = [
                    item for item in data 
                    if item.get('chapter') == chapter
                ]
                
                return chapter_translations
            except Exception as e:
                print(f"❌ Ошибка получения контекста главы: {e}")
                return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику по переводам"""
        if self.collection:
            try:
                count = self.collection.count()
                return {
                    "total_translations": count,
                    "database_type": "ChromaDB"
                }
            except Exception as e:
                print(f"❌ Ошибка получения статистики: {e}")
                return {"total_translations": 0, "database_type": "ChromaDB (ошибка)"}
        else:
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                chapters = set(item.get('chapter', '') for item in data)
                characters = set(item.get('character', '') for item in data if item.get('character'))
                
                return {
                    "total_translations": len(data),
                    "chapters": len(chapters),
                    "characters": len(characters),
                    "database_type": "File System"
                }
            except Exception as e:
                print(f"❌ Ошибка получения статистики: {e}")
                return {"total_translations": 0, "database_type": "File System (ошибка)"}

def test_translation_memory():
    """Тестирование системы памяти переводов"""
    print("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ ПАМЯТИ ПЕРЕВОДОВ")
    print("=" * 50)
    
    # Создаем менеджер
    manager = TranslationMemoryManager()
    
    # Добавляем тестовые переводы
    test_translations = [
        TranslationMemory(
            source_text="Jiang Chen looked at the mountain",
            target_text="Цзян Чэнь посмотрел на гору",
            chapter="Глава 1",
            character="Jiang_Chen",
            quality_score=95.0
        ),
        TranslationMemory(
            source_text="Ye Qingcheng was angry",
            target_text="Е Цинчэн была зла",
            chapter="Глава 1", 
            character="Ye_Qingcheng",
            quality_score=90.0
        )
    ]
    
    # Добавляем переводы
    for translation in test_translations:
        memory_id = manager.add_translation(translation)
        print(f"✅ Добавлен перевод: {memory_id[:8]}...")
    
    # Ищем похожие
    similar = manager.find_similar("Jiang Chen saw the mountain", threshold=0.5)
    print(f"\n🔍 Найдено похожих переводов: {len(similar)}")
    for item in similar:
        print(f"   • {item['similarity']:.2f}: {item['target_text']}")
    
    # Статистика
    stats = manager.get_statistics()
    print(f"\n📊 Статистика: {stats}")

if __name__ == "__main__":
    test_translation_memory()
