# PowerShell скрипт для проверки русского языка в переводах
# Проверяет архаизмы, кальки, длинные предложения и читабельность

param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath,
    
    [Parameter(Mandatory=$false)]
    [switch]$Fix = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose = $false
)

# Цвета для вывода
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Cyan = "Cyan"

# Запрещённые архаизмы
$BannedArchaisms = @(
    "сей", "сия", "оный", "дабы", "ибо", 
    "воистину", "весьма", "отнюдь", "непременно",
    "молвить", "воззреть", "вопрошать", "ныне",
    "осуществлять", "производить впечатление", "испытывать чувство"
)

# Кальки и канцеляризмы
$Calques = @{
    "крайне" = "очень"
    "слева и справа" = "направо и налево"
    "совершенна" = "идеальна"
    "На его взгляд" = "С его точки зрения"
    "резюмировал" = "размышлял"
    "осуществлять" = "делать"
    "производить впечатление" = "впечатлять"
    "испытывать чувство" = "чувствовать"
}

# Формальные конструкции для диалогов
$FormalDialogue = @{
    "Я собираюсь" = "Буду"
    "Позвольте мне" = "Дай мне"
    "Не могли бы вы" = "Можешь"
    "Я хотел бы" = "Хочу"
    "Кажется, что" = "Похоже"
    "Я боюсь, что" = "Боюсь"
    "Позвольте мне выразить" = "Спасибо"
    "Не соблаговолите ли вы" = "Не могли бы вы"
    "Осмелюсь спросить" = "Можно спросить?"
    "Сие деяние недопустимо" = "Так нельзя"
    "Воистину могущественный" = "Реально мощный"
}

# Максимальная длина предложения
$MaxSentenceLength = 15

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-FileExists {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        Write-ColorOutput "❌ Файл не найден: $Path" $Red
        exit 1
    }
}

function Get-TextContent {
    param([string]$FilePath)
    try {
        $content = Get-Content -Path $FilePath -Encoding UTF8 -Raw
        return $content
    }
    catch {
        Write-ColorOutput "❌ Ошибка чтения файла: $($_.Exception.Message)" $Red
        exit 1
    }
}

function Test-Archaisms {
    param([string]$Text, [string]$FilePath)
    
    Write-ColorOutput "🔍 Проверка архаизмов..." $Cyan
    $issues = @()
    
    foreach ($archaism in $BannedArchaisms) {
        if ($Text -match $archaism) {
            $matches = [regex]::Matches($Text, $archaism, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
            foreach ($match in $matches) {
                $lineNumber = ($Text.Substring(0, $match.Index) -split "`n").Count
                $context = $Text.Substring([Math]::Max(0, $match.Index - 30), 60)
                
                $issues += @{
                    Type = "Архаизм"
                    Word = $archaism
                    Line = $lineNumber
                    Context = $context
                    Severity = "Критическая"
                }
            }
        }
    }
    
    return $issues
}

function Test-Calques {
    param([string]$Text, [string]$FilePath)
    
    Write-ColorOutput "🔍 Проверка кальки..." $Cyan
    $issues = @()
    
    foreach ($calque in $Calques.Keys) {
        if ($calque in $Text) {
            $matches = [regex]::Matches($Text, $calque, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
            foreach ($match in $matches) {
                $lineNumber = ($Text.Substring(0, $match.Index) -split "`n").Count
                $context = $Text.Substring([Math]::Max(0, $match.Index - 30), 60)
                
                $issues += @{
                    Type = "Калька"
                    Word = $calque
                    Suggestion = $Calques[$calque]
                    Line = $lineNumber
                    Context = $context
                    Severity = "Высокая"
                }
            }
        }
    }
    
    return $issues
}

function Test-FormalDialogue {
    param([string]$Text, [string]$FilePath)
    
    Write-ColorOutput "🔍 Проверка формальных диалогов..." $Cyan
    $issues = @()
    
    foreach ($formal in $FormalDialogue.Keys) {
        if ($formal in $Text) {
            $matches = [regex]::Matches($Text, $formal, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
            foreach ($match in $matches) {
                $lineNumber = ($Text.Substring(0, $match.Index) -split "`n").Count
                $context = $Text.Substring([Math]::Max(0, $match.Index - 30), 60)
                
                $issues += @{
                    Type = "Формальный диалог"
                    Word = $formal
                    Suggestion = $FormalDialogue[$formal]
                    Line = $lineNumber
                    Context = $context
                    Severity = "Средняя"
                }
            }
        }
    }
    
    return $issues
}

function Test-SentenceLength {
    param([string]$Text, [string]$FilePath)
    
    Write-ColorOutput "🔍 Проверка длины предложений..." $Cyan
    $issues = @()
    
    $sentences = $Text -split '[.!?]+'
    $lineNumber = 1
    
    foreach ($sentence in $sentences) {
        $sentence = $sentence.Trim()
        if ($sentence.Length -gt 0) {
            $words = $sentence -split '\s+' | Where-Object { $_.Length -gt 0 }
            if ($words.Count -gt $MaxSentenceLength) {
                $issues += @{
                    Type = "Длинное предложение"
                    Word = $sentence
                    Line = $lineNumber
                    WordCount = $words.Count
                    MaxAllowed = $MaxSentenceLength
                    Severity = "Средняя"
                }
            }
        }
        $lineNumber++
    }
    
    return $issues
}

function Test-Readability {
    param([string]$Text, [string]$FilePath)
    
    Write-ColorOutput "🔍 Анализ читабельности..." $Cyan
    
    $sentences = ($Text -split '[.!?]+' | Where-Object { $_.Trim().Length -gt 0 }).Count
    $words = ($Text -split '\s+' | Where-Object { $_.Length -gt 0 }).Count
    $syllables = 0
    
    # Простой подсчет слогов (приблизительный)
    $words | ForEach-Object {
        $word = $_ -replace '[^\p{L}]', ''
        if ($word.Length -gt 0) {
            $syllables += [Math]::Max(1, $word.Length / 2)
        }
    }
    
    # Формула Флеша для русского языка (упрощенная)
    $avgWordsPerSentence = if ($sentences -gt 0) { $words / $sentences } else { 0 }
    $avgSyllablesPerWord = if ($words -gt 0) { $syllables / $words } else { 0 }
    
    $readabilityScore = 206.835 - (1.3 * $avgWordsPerSentence) - (60.1 * $avgSyllablesPerWord)
    $readabilityScore = [Math]::Max(0, [Math]::Min(100, $readabilityScore))
    
    return @{
        Score = [Math]::Round($readabilityScore, 1)
        AvgWordsPerSentence = [Math]::Round($avgWordsPerSentence, 1)
        AvgSyllablesPerWord = [Math]::Round($avgSyllablesPerWord, 2)
        TotalWords = $words
        TotalSentences = $sentences
        Target = 85
        Status = if ($readabilityScore -ge 85) { "Хорошо" } elseif ($readabilityScore -ge 70) { "Удовлетворительно" } else { "Плохо" }
    }
}

function Show-Issues {
    param([array]$Issues, [string]$FilePath)
    
    if ($Issues.Count -eq 0) {
        Write-ColorOutput "✅ Проблем не найдено!" $Green
        return
    }
    
    Write-ColorOutput "`n📋 НАЙДЕННЫЕ ПРОБЛЕМЫ:" $Yellow
    Write-ColorOutput "=" * 60 $Yellow
    
    $groupedIssues = $Issues | Group-Object Type
    foreach ($group in $groupedIssues) {
        Write-ColorOutput "`n🔸 $($group.Name) ($($group.Count) проблем):" $Cyan
        
        foreach ($issue in $group.Group) {
            $severityColor = switch ($issue.Severity) {
                "Критическая" { $Red }
                "Высокая" { "Magenta" }
                "Средняя" { $Yellow }
                default { "White" }
            }
            
            Write-ColorOutput "  Строка $($issue.Line): $($issue.Word)" $severityColor
            Write-ColorOutput "  Контекст: ...$($issue.Context)..." "Gray"
            
            if ($issue.Suggestion) {
                Write-ColorOutput "  💡 Предложение: $($issue.Suggestion)" $Green
            }
            if ($issue.WordCount) {
                Write-ColorOutput "  📊 Слов: $($issue.WordCount) (максимум: $($issue.MaxAllowed))" "Gray"
            }
            Write-ColorOutput ""
        }
    }
}

function Show-ReadabilityReport {
    param([hashtable]$Readability)
    
    Write-ColorOutput "`n📊 ОТЧЕТ ПО ЧИТАБЕЛЬНОСТИ:" $Cyan
    Write-ColorOutput "=" * 40 $Cyan
    
    $statusColor = switch ($Readability.Status) {
        "Хорошо" { $Green }
        "Удовлетворительно" { $Yellow }
        "Плохо" { $Red }
    }
    
    Write-ColorOutput "Оценка читабельности: $($Readability.Score)/100 ($($Readability.Status))" $statusColor
    Write-ColorOutput "Средняя длина предложения: $($Readability.AvgWordsPerSentence) слов" "White"
    Write-ColorOutput "Среднее количество слогов на слово: $($Readability.AvgSyllablesPerWord)" "White"
    Write-ColorOutput "Всего слов: $($Readability.TotalWords)" "White"
    Write-ColorOutput "Всего предложений: $($Readability.TotalSentences)" "White"
    Write-ColorOutput "Целевая оценка: $($Readability.Target)+" "Gray"
}

function Fix-Issues {
    param([string]$Text, [array]$Issues)
    
    Write-ColorOutput "`n🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМ..." $Yellow
    
    $fixedText = $Text
    
    foreach ($issue in $Issues) {
        if ($issue.Suggestion) {
            $pattern = [regex]::Escape($issue.Word)
            $fixedText = $fixedText -replace $pattern, $issue.Suggestion
            Write-ColorOutput "  ✅ Исправлено: '$($issue.Word)' → '$($issue.Suggestion)'" $Green
        }
    }
    
    return $fixedText
}

function Save-FixedFile {
    param([string]$Text, [string]$FilePath)
    
    $backupPath = $FilePath + ".backup"
    $fixedPath = $FilePath -replace '\.txt$', '-fixed.txt'
    
    # Создаем резервную копию
    Copy-Item $FilePath $backupPath
    Write-ColorOutput "📁 Создана резервная копия: $backupPath" $Cyan
    
    # Сохраняем исправленный файл
    $Text | Out-File -FilePath $fixedPath -Encoding UTF8
    Write-ColorOutput "💾 Сохранен исправленный файл: $fixedPath" $Green
}

# ============= ОСНОВНАЯ ЛОГИКА =============

Write-ColorOutput "🔍 РУССКИЙ ЛИНТЕР ДЛЯ ПЕРЕВОДОВ" $Cyan
Write-ColorOutput "=" * 50 $Cyan

# Проверяем существование файла
Test-FileExists $FilePath

# Читаем содержимое
$content = Get-TextContent $FilePath

Write-ColorOutput "📄 Анализирую файл: $FilePath" $Cyan
Write-ColorOutput "📏 Размер: $($content.Length) символов" "Gray"

# Выполняем все проверки
$allIssues = @()

$archaismIssues = Test-Archaisms $content $FilePath
$allIssues += $archaismIssues

$calqueIssues = Test-Calques $content $FilePath
$allIssues += $calqueIssues

$dialogueIssues = Test-FormalDialogue $content $FilePath
$allIssues += $dialogueIssues

$lengthIssues = Test-SentenceLength $content $FilePath
$allIssues += $lengthIssues

# Анализ читабельности
$readability = Test-Readability $content $FilePath

# Показываем результаты
Show-Issues $allIssues $FilePath
Show-ReadabilityReport $readability

# Статистика
$criticalCount = ($allIssues | Where-Object { $_.Severity -eq "Критическая" }).Count
$highCount = ($allIssues | Where-Object { $_.Severity -eq "Высокая" }).Count
$mediumCount = ($allIssues | Where-Object { $_.Severity -eq "Средняя" }).Count

Write-ColorOutput "`n📈 СТАТИСТИКА:" $Cyan
Write-ColorOutput "Критические: $criticalCount" $(if ($criticalCount -gt 0) { $Red } else { $Green })
Write-ColorOutput "Высокие: $highCount" $(if ($highCount -gt 0) { "Magenta" } else { $Green })
Write-ColorOutput "Средние: $mediumCount" $(if ($mediumCount -gt 0) { $Yellow } else { $Green })
Write-ColorOutput "Всего проблем: $($allIssues.Count)" "White"

# Исправление (если запрошено)
if ($Fix) {
    $fixableIssues = $allIssues | Where-Object { $_.Suggestion }
    if ($fixableIssues.Count -gt 0) {
        $fixedContent = Fix-Issues $content $fixableIssues
        Save-FixedFile $fixedContent $FilePath
    } else {
        Write-ColorOutput "`n⚠️ Нет исправляемых проблем" $Yellow
    }
}

# Итоговая оценка
$totalScore = 100
$totalScore -= $criticalCount * 20
$totalScore -= $highCount * 10
$totalScore -= $mediumCount * 5
$totalScore = [Math]::Max(0, $totalScore)

$scoreColor = if ($totalScore -ge 90) { $Green } elseif ($totalScore -ge 70) { $Yellow } else { $Red }

Write-ColorOutput "`n🏆 ИТОГОВАЯ ОЦЕНКА: $totalScore/100" $scoreColor

if ($totalScore -ge 90) {
    Write-ColorOutput "🎉 Отличный перевод! Готов к публикации!" $Green
} elseif ($totalScore -ge 70) {
    Write-ColorOutput "👍 Хороший перевод, но есть что улучшить" $Yellow
} else {
    Write-ColorOutput "⚠️ Требуется серьезная доработка" $Red
}

Write-ColorOutput "`n💡 Используйте -Fix для автоматического исправления" "Gray"
Write-ColorOutput "💡 Используйте -Verbose для подробного вывода" "Gray"
