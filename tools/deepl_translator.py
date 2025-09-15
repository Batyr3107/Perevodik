import requests
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Union

class DeepLFileTranslator:
    """
    Класс для перевода файлов через DeepL API
    Специально для интеграции с ИИ в Cursor
    """
    
    def __init__(self, api_key: str = None):
        """Инициализация с API ключом"""
        self.api_key = api_key or os.getenv('DEEPL_API_KEY')
        if not self.api_key:
            raise ValueError("API ключ не найден! Установите DEEPL_API_KEY")
        
        # Определяем тип API (бесплатный или платный)
        if self.api_key.endswith(':fx'):
            self.base_url = "https://api-free.deepl.com/v2"
        else:
            self.base_url = "https://api.deepl.com/v2"
    
    def translate_text(self, text: Union[str, List[str]], 
                      source_lang: str = 'EN', 
                      target_lang: str = 'RU') -> Union[str, List[str]]:
        """
        Перевод текста или списка текстов
        
        Args:
            text: Текст или список текстов для перевода
            source_lang: Исходный язык (по умолчанию EN)
            target_lang: Целевой язык (по умолчанию RU)
        
        Returns:
            Переведенный текст или список текстов
        """
        endpoint = f"{self.base_url}/translate"
        
        # Подготовка данных
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        params = {
            'auth_key': self.api_key,
            'text': texts,
            'source_lang': source_lang,
            'target_lang': target_lang
        }
        
        try:
            response = requests.post(endpoint, data=params)
            response.raise_for_status()
            
            result = response.json()
            translations = [t['text'] for t in result['translations']]
            
            return translations[0] if is_single else translations
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {response.text}")
            raise
        except Exception as e:
            print(f"Error: {e}")
            raise
    
    def translate_file(self, input_file: str, output_file: str = None,
                      source_lang: str = 'EN', target_lang: str = 'RU',
                      file_format: str = 'auto') -> Dict:
        """
        Перевод файла с текстом
        
        Args:
            input_file: Путь к входному файлу
            output_file: Путь к выходному файлу (опционально)
            source_lang: Исходный язык
            target_lang: Целевой язык
            file_format: Формат файла (auto, txt, json, lines)
        
        Returns:
            Словарь с результатами перевода
        """
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Файл не найден: {input_file}")
        
        # Автоопределение формата
        if file_format == 'auto':
            if input_path.suffix == '.json':
                file_format = 'json'
            elif input_path.suffix in ['.txt', '.text']:
                file_format = 'txt'
            else:
                file_format = 'lines'
        
        # Чтение файла
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Обработка в зависимости от формата
        if file_format == 'json':
            data = json.loads(content)
            translated_data = self._translate_json(data, source_lang, target_lang)
            result = {
                'format': 'json',
                'original': data,
                'translated': translated_data
            }
        elif file_format == 'lines':
            # Каждая строка - отдельный текст
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            translated_lines = self.translate_text(lines, source_lang, target_lang)
            result = {
                'format': 'lines',
                'original': lines,
                'translated': translated_lines
            }
        else:  # txt - весь файл как один текст
            translated_content = self.translate_text(content, source_lang, target_lang)
            result = {
                'format': 'txt',
                'original': content,
                'translated': translated_content
            }
        
        # Сохранение результата
        if output_file:
            self._save_result(output_file, result)
        
        # Добавляем метаданные
        result['metadata'] = {
            'input_file': str(input_path),
            'output_file': output_file,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return result
    
    def _translate_json(self, data: Union[Dict, List], 
                       source_lang: str, target_lang: str) -> Union[Dict, List]:
        """Рекурсивный перевод JSON структуры"""
        if isinstance(data, str):
            return self.translate_text(data, source_lang, target_lang)
        elif isinstance(data, list):
            return [self._translate_json(item, source_lang, target_lang) for item in data]
        elif isinstance(data, dict):
            return {key: self._translate_json(value, source_lang, target_lang) 
                   for key, value in data.items()}
        else:
            return data
    
    def _save_result(self, output_file: str, result: Dict):
        """Сохранение результата в файл"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if result['format'] == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result['translated'], f, ensure_ascii=False, indent=2)
        elif result['format'] == 'lines':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(result['translated']))
        else:  # txt
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result['translated'])


# ============= ГЛАВНАЯ ФУНКЦИЯ ДЛЯ ИИ В CURSOR =============

def ai_translate_file(input_file: str, 
                      output_file: str = None,
                      api_key: str = None) -> Dict:
    """
    Главная функция для ИИ в Cursor
    
    Args:
        input_file: Путь к файлу, созданному ИИ
        output_file: Путь для сохранения перевода (опционально)
        api_key: API ключ DeepL (если не в переменных окружения)
    
    Returns:
        Словарь с переведенными данными
    
    Пример использования:
        result = ai_translate_file('texts.txt')
        translated_text = result['translated']
    """
    # Инициализация переводчика
    translator = DeepLFileTranslator(api_key)
    
    # Если выходной файл не указан, создаем автоматически
    if not output_file:
        input_path = Path(input_file)
        output_file = f"translated_{input_path.stem}_RU{input_path.suffix}"
    
    # Переводим файл
    result = translator.translate_file(
        input_file=input_file,
        output_file=output_file,
        source_lang='EN',
        target_lang='RU'
    )
    
    print(f"✓ Перевод завершен!")
    print(f"  Входной файл: {input_file}")
    print(f"  Выходной файл: {output_file}")
    print(f"  Формат: {result['format']}")
    
    return result


# ============= ФУНКЦИЯ ДЛЯ НАШЕГО WORKFLOW =============

def translate_chapter_with_deepl(english_file: str, output_file: str = None) -> Dict:
    """
    Специальная функция для перевода глав новеллы через DeepL
    
    Args:
        english_file: Путь к файлу с английским текстом главы
        output_file: Путь для сохранения русского перевода
    
    Returns:
        Результат перевода с метаданными
    """
    try:
        print(f"🤖 Отправляю главу на перевод через DeepL API...")
        print(f"📄 Исходный файл: {english_file}")
        
        # Используем функцию перевода
        result = ai_translate_file(
            input_file=english_file,
            output_file=output_file
        )
        
        print(f"✅ Перевод получен от DeepL!")
        
        # Добавляем информацию о переводчике
        result['translator'] = 'DeepL API'
        result['translation_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при переводе через DeepL: {e}")
        raise


if __name__ == "__main__":
    # Пример использования для тестирования
    print("🔧 Тест DeepL переводчика...")
    
    # Создаем тестовый файл
    test_file = "test_chapter.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""Chapter Test: Simple Translation

This is a test chapter for our translation system.
It contains multiple lines and should be translated properly.

"Hello world!" said the character.
"This is a dialogue example," replied another character.

The end of test chapter.""")
    
    try:
        # Тестируем перевод
        result = translate_chapter_with_deepl(test_file, "test_chapter_ru.txt")
        print(f"📊 Результат перевода:")
        print(f"   Формат: {result['format']}")
        print(f"   Переводчик: {result['translator']}")
        print(f"   Дата: {result['translation_date']}")
        print(f"📝 Переведенный текст:")
        print(result['translated'][:200] + "..." if len(result['translated']) > 200 else result['translated'])
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("💡 Убедитесь, что установлен API ключ DeepL:")
        print("   export DEEPL_API_KEY='your-key:fx'")
