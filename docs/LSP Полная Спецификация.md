# Полная спецификация разработки Language Server Protocol для языка OSI

**Версия:** 1.0  
**Дата:** 23 декабря 2024  
**Статус:** Утверждено к разработке

---

## Содержание

1. [Введение](#1-введение)
2. [Описание языка OSI](#2-описание-языка-osi)
3. [Файловая структура](#3-файловая-структура)
4. [Синтаксис языка](#4-синтаксис-языка)
5. [Требования к Language Server](#5-требования-к-language-server)
6. [Архитектура решения](#6-архитектура-решения)
7. [План реализации](#7-план-реализации)
8. [Тестирование](#8-тестирование)
9. [Примеры и референсная документация](#9-примеры-и-референсная-документация)

---

## 1. Введение

### 1.1 Цель документа

Данный документ представляет собой полную техническую спецификацию для разработки Language Server Protocol (LSP) для специализированного языка программирования протоколов OSI.

### 1.2 Назначение языка OSI

Язык OSI предназначен для описания сетевых протоколов различных уровней модели OSI:
- Транспортный уровень
- Сеансовый уровень
- Уровень представления
- Прикладной уровень

Код организован в виде обработчиков событий (event handlers), каждый из которых реагирует на конкретное событие в системе.

### 1.3 Целевая аудитория

- Разработчики сетевых протоколов
- Исследователи в области сетевых технологий
- Студенты, изучающие модель OSI

### 1.4 Технологический стек

**Client (VS Code Extension):**
- TypeScript 5.0+
- VS Code Extension API 1.75+
- vscode-languageclient 9.0+

**Server (Language Server):**
- Python 3.10+
- pygls 1.2.0+
- lsprotocol 2023.0.0+

---

## 2. Описание языка OSI

### 2.1 Основные концепции

#### 2.1.1 Обработчики событий (Event Handlers)

Каждый обработчик - это именованный блок кода, который выполняется при возникновении соответствующего события.

```osi
HANDLER_NAME:
    ; код обработчика
    return
```

#### 2.1.2 Инициализация (INIT)

Специальный обработчик `INIT`, содержащий объявления всех переменных уровня. Не содержит исполняемого кода, только декларации.

```osi
; INIT.osi
variable_name declare type
another_var declare type
```

#### 2.1.3 Параметры обработчиков

Обработчики могут принимать параметры, которые указываются в комментарии специального формата:

```osi
; Параметры: param1 (type1), param2 (type2)

HANDLER_NAME:
    ; параметры доступны как $param1, $param2
    return
```

#### 2.1.4 События между уровнями

Обработчики могут генерировать события для передачи данных между уровнями:

```osi
EVENT.NAME generateup param1 $value1 param2 $value2    ; событие вверх
EVENT.NAME eventdown param1 $value1 param2 $value2     ; событие вниз
```

### 2.2 Типы данных

| Тип | Описание | Пример использования |
|-----|----------|---------------------|
| `integer` | Целое число | Счетчики, флаги, индексы |
| `buffer` | Буфер байтов | Пакеты данных, сообщения |
| `string` | Строка | Имена, текстовые данные |
| `queue` | Очередь | Буферизация пакетов |

### 2.3 Область видимости

**Глобальная область (уровень директории):**
- Все переменные, объявленные в `INIT.osi`
- Доступны всем обработчикам в директории

**Локальная область (обработчик):**
- Параметры обработчика
- Локальные метки

**Правило:** Параметры обработчика затеняют глобальные переменные с тем же именем.

---

## 3. Файловая структура

### 3.1 Общая структура проекта

```
project_root/
├── transport/              # Транспортный уровень
│   ├── INIT.osi           # Обязательный файл инициализации
│   ├── CONTIMER.osi       # Обработчик события CONTIMER
│   ├── N_DATAGRAM.IND.osi # Обработчик N_DATAGRAM.IND
│   ├── T_CONNECT.REQ.osi
│   ├── T_DATA.REQ.osi
│   └── ZERO_TIMER.osi
│
├── session/                # Сеансовый уровень
│   ├── INIT.osi
│   ├── S_CONNECT.REQ.osi
│   ├── S_DATA.REQ.osi
│   └── SEND_MESSAGE.osi
│
├── presentation/           # Уровень представления
│   ├── INIT.osi
│   ├── P_CONNECT.REQ.osi
│   └── P_DATA.REQ.osi
│
└── application/            # Прикладной уровень
    ├── INIT.osi
    ├── A_ASSOCIATE.REQ.osi
    └── A_DATA.REQ.osi
```

### 3.2 Правила именования

#### 3.2.1 Директории

- **Название:** Произвольное, snake_case или lowercase
- **Назначение:** Группировка обработчиков одного уровня
- **Обязательное содержимое:** Файл `INIT.osi`

#### 3.2.2 Файлы обработчиков

**Формат:** `HANDLER_NAME.osi`

**Правила:**
- ✅ Только UPPER_CASE
- ✅ Подчеркивания разрешены: `TIMER_STATE_1.osi`
- ✅ Точки разрешены: `T_CONNECT.REQ.osi`, `N_DATAGRAM.IND.osi`
- ❌ Не допускаются: пробелы, дефисы, lowercase буквы
- ⚠️ Имена начинающиеся с `TIMER` обозначают таймеры

**Примеры корректных имен:**
```
INIT.osi
CONTIMER.osi
T_CONNECT.REQ.osi
N_DATAGRAM.IND.osi
TIMER_STATE_1.osi
TIMER_RECONNECT.osi
ZERO_TIMER.osi
SEND_MESSAGE.osi
```

**Примеры некорректных имен:**
```
init.osi           ❌ lowercase
My-Handler.osi     ❌ дефис и mixed case
TIMER 1.osi        ❌ пробел
handler_name.osi   ❌ lowercase
```

#### 3.2.3 Соответствие имени файла и содержимого

Имя обработчика внутри файла **должно** совпадать с именем файла (без расширения).

```osi
; Файл: T_CONNECT.REQ.osi

T_CONNECT.REQ:        ✅ Правильно
    return

T_CONNECT_REQ:        ❌ Неправильно - не совпадает с именем файла
    return
```

### 3.3 Структура файла INIT.osi

```osi
; ============================================
; INIT.osi
; Инициализация переменных транспортного уровня
; ============================================

; Таймеры
zero_timer declare integer
con_timer declare integer
delay_timer declare integer

; Адреса
t_address declare integer
address_resolve declare integer

; Буферы
tmp_buffer declare buffer
package_buffer declare buffer
package_buffer_out declare buffer

; Счетчики
last_sent declare integer
last_received declare integer
counter declare integer

; Очереди
package_queue declare queue

; Флаги
is_connected declare integer
state declare integer
```

**Правила:**
- ✅ Только операторы `declare`
- ✅ Комментарии разрешены
- ❌ Никакого исполняемого кода
- ❌ Никаких меток
- ❌ Никаких `varset`

### 3.4 Структура файла обработчика

```osi
; ============================================
; T_CONNECT.REQ.osi
; Запрос на установление транспортного соединения
; Параметры: address (integer)
; ============================================

T_CONNECT.REQ:
    ; Инициализация переменных
    0 varset last_sent
    0 varset last_received
    
    ; Сохранение адреса
    $address varset t_address
    
    ; Формирование пакета
    $last_sent + 1 varset last_sent
    package_buffer bufferit 2 0 1 $last_sent 1
    
    ; Вычисление контрольной суммы
    calccrc pac_crc $package_buffer
    
    ; Отправка
    ZERO_TIMER timer zero_timer 0 address $t_address package $package_buffer
    
    return
```

**Обязательные элементы:**
1. Комментарий с названием обработчика
2. Комментарий с описанием (опционально)
3. Комментарий с параметрами: `; Параметры: ...`
4. Метка обработчика (совпадает с именем файла)
5. Код обработчика
6. Оператор `return`

### 3.5 Ограничения

**Запрещено:**
- ❌ Поддиректории внутри уровня
- ❌ Несколько обработчиков в одном файле
- ❌ Несколько файлов `INIT.osi` в одной директории
- ❌ Обработчики без файла `INIT.osi` в директории

**Разрешено:**
- ✅ Несколько директорий уровней в проекте
- ✅ Произвольное количество файлов обработчиков
- ✅ Пустые обработчики (только `return`)

---

## 4. Синтаксис языка

### 4.1 Лексическая структура

#### 4.1.1 Идентификаторы

**Переменные:**
```
$identifier
```

**Правила для identifier:**
- Начинается с буквы или подчеркивания: `[a-zA-Z_]`
- Продолжается буквами, цифрами или подчеркиванием: `[a-zA-Z0-9_]*`
- Примеры: `$counter`, `$my_var`, `$buffer_1`

**Метки:**
```
identifier:
```

**Имена обработчиков и событий:**
- Только UPPER_CASE
- Могут содержать подчеркивания и точки
- Примеры: `HANDLER`, `T_CONNECT.REQ`, `TIMER_STATE_1`

#### 4.1.2 Литералы

**Числовые литералы:**
```osi
0                    ; ноль
42                   ; положительное число
-15                  ; отрицательное число
1000                 ; большое число
```

**Строковые литералы:**
```osi
"Hello World"                    ; простая строка
"Path: /home/user"              ; со спецсимволами
"Error: file not found"         ; с двоеточием
"Message with \"quotes\""       ; с экранированными кавычками
```

**Escape-последовательности в строках:**
- `\"` - кавычка
- `\\` - обратный слэш
- `\n` - перевод строки
- `\t` - табуляция

**Коды символов:**
```osi
#255                 ; символ с кодом 255
#65                  ; символ 'A'
#0                   ; нулевой символ
```

#### 4.1.3 Комментарии

```osi
; Это однострочный комментарий

counter declare integer  ; комментарий после кода

; Многострочные комментарии через несколько строк:
; Строка 1
; Строка 2
; Строка 3
```

**Правила:**
- Начинаются с `;`
- Продолжаются до конца строки
- Могут быть на отдельной строке или после кода
- Вложенные комментарии не поддерживаются

#### 4.1.4 Операторы и разделители

**Арифметические операторы:**
```
+  -  *  /  %
```

**Операторы сравнения:**
```
==  !=  >  <  >=  <=
```

**Логические операторы:**
```
&&  ||
```

**Разделители:**
```
(  )  ,  :
```

### 4.2 Объявление переменных

#### 4.2.1 Синтаксис

```osi
variable_name declare type
```

**Где:**
- `variable_name` - имя переменной (без `$`)
- `declare` - ключевое слово
- `type` - один из: `integer`, `buffer`, `string`, `queue`

#### 4.2.2 Примеры

```osi
counter declare integer
data_buffer declare buffer
user_name declare string
packet_queue declare queue
```

#### 4.2.3 Правила

- ✅ Объявление только в `INIT.osi`
- ❌ Повторное объявление запрещено
- ❌ Объявление в обработчиках запрещено
- ✅ Имена переменных case-sensitive: `counter` ≠ `Counter`

### 4.3 Присваивание (varset)

#### 4.3.1 Синтаксис

```osi
expression varset variable_name
```

**Где:**
- `expression` - выражение любого типа
- `varset` - ключевое слово
- `variable_name` - имя переменной (без `$`)

#### 4.3.2 Примеры

```osi
; Присваивание литералов
0 varset counter
"Hello" varset name
#255 varset end_symbol

; Присваивание переменных
$other_var varset my_var

; Присваивание результата операции
$counter + 1 varset counter
$a * $b + $c varset result

; Присваивание результата функции
sizeof(buffer) varset buffer_size
copy($str, 1, 5) varset substring
```

#### 4.3.3 Проверка типов

```osi
; INIT.osi
counter declare integer
name declare string

; Обработчик
HANDLER:
    5 varset counter          ✅ OK: integer → integer
    "text" varset counter     ❌ ERROR: string → integer
    
    "hello" varset name       ✅ OK: string → string
    10 varset name            ❌ ERROR: integer → string
    
    return
```

**Правило:** Тип выражения должен совпадать с типом переменной.

**Исключение:** Первое присваивание определяет тип неинициализированной переменной.

### 4.4 Управление потоком выполнения

#### 4.4.1 Безусловный переход (goto)

**Синтаксис:**
```osi
goto label_name
```

**Примеры:**
```osi
HANDLER:
    goto exit
    out "Не выполнится"      ; unreachable code
    
exit:
    return
```

#### 4.4.2 Условный переход (if)

**Синтаксис:**
```osi
condition if label_name
```

**Где:**
- `condition` - логическое выражение
- `label_name` - имя метки

**Примеры:**
```osi
HANDLER:
    $counter > 10 if overflow
    $flag == 0 if process
    ($a > 0) && ($b < 10) if complex_check
    
overflow:
    out "Overflow detected"
    0 varset counter
    
process:
    out "Processing"
    
complex_check:
    out "Complex condition met"
    
    return
```

#### 4.4.3 Метки

**Синтаксис:**
```osi
label_name:
    ; код
```

**Правила:**
- ✅ Имя метки: lowercase или snake_case
- ✅ Двоеточие обязательно
- ❌ Дублирование меток в одном обработчике запрещено
- ✅ Метки видимы только внутри обработчика

**Примеры:**
```osi
exit:
    return
    
process_data:
    unbufferit buffer data 10
    goto exit
    
error_handler:
    out "Error occurred"
    goto exit
```

#### 4.4.4 Возврат (return)

**Синтаксис:**
```osi
return
```

**Правила:**
- ✅ Завершает выполнение обработчика
- ✅ Обязателен в конце каждого обработчика
- ⚠️ Код после `return` недостижим (warning)

**Примеры:**
```osi
HANDLER:
    $flag == 1 if early_exit
    ; основной код
    return
    
early_exit:
    out "Early exit"
    return
```

#### 4.4.5 Прерывание (break)

**Синтаксис:**
```osi
break
```

**Назначение:** Точка останова для отладки (в будущем)

**Примеры:**
```osi
HANDLER:
    $counter > 100 if check
    break                    ; точка останова
    goto exit
    
check:
    out "Counter exceeded 100"
    
exit:
    return
```

### 4.5 Работа с буферами

#### 4.5.1 Создание буфера (bufferit)

**Синтаксис:**
```osi
buffer_name bufferit total_length value1 length1 value2 length2 ...
```

**Где:**
- `buffer_name` - имя буфера (без `$`)
- `total_length` - общая длина буфера
- `value1`, `value2`, ... - значения полей
- `length1`, `length2`, ... - длины полей

**Примеры:**
```osi
; Простой буфер: [0, 5] (2 байта)
buffer1 bufferit 2 0 1 5 1

; Буфер с переменными
package_buffer bufferit 10 $type 1 $number 1 $data 8

; Буфер с вычислением
buffer2 bufferit sizeof(data)+2 $header 2 $data sizeof(data)

; Буфер из другого буфера
buffer3 bufferit sizeof(buffer1)+1 $buffer1 sizeof(buffer1) $crc 1
```

**Правила:**
- ✅ Если сумма длин < total_length, остаток заполняется нулями
- ❌ Если сумма длин > total_length, ошибка времени выполнения
- ✅ Длины могут быть выражениями

**Пример с padding:**
```osi
; Создаем буфер длиной 10, заполняем 5 байт
buffer bufferit 10 $data 5
; Результат: [data[0..4], 0, 0, 0, 0, 0]
```

#### 4.5.2 Разбор буфера (unbufferit)

**Синтаксис:**
```osi
unbufferit buffer_name variable1 length1 variable2 length2 ...
```

**Где:**
- `buffer_name` - имя буфера (без `$`)
- `variable1`, `variable2`, ... - имена переменных для извлечения
- `length1`, `length2`, ... - длины полей

**Примеры:**
```osi
; Извлечь два поля по 1 байту
unbufferit userdata type 1 number 1

; Извлечь с остатком
unbufferit package header 2 data sizeof(package)-2

; Извлечь в несколько шагов
unbufferit buffer field1 1 rest sizeof(buffer)-1
unbufferit rest field2 1 field3 1 remainder sizeof(rest)-2
```

**Правила:**
- ✅ Извлекаются последовательно от начала буфера
- ❌ Если сумма длин > sizeof(buffer), ошибка
- ✅ Можно извлекать буфер в буфер

**Частичное извлечение:**
```osi
; Буфер: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
unbufferit buffer first 2 rest sizeof(buffer)-2
; first = [1, 2]
; rest = [3, 4, 5, 6, 7, 8, 9, 10]
```

#### 4.5.3 Вычисление контрольной суммы (calccrc)

**Синтаксис:**
```osi
calccrc result_variable buffer_name
```

**Примеры:**
```osi
calccrc crc_value $data_buffer
calccrc checksum $package

; Использование результата
package_with_crc bufferit sizeof(package)+1 $package sizeof(package) $crc_value 1
```

**Правила:**
- ✅ Результат - integer
- ✅ Алгоритм CRC определяется реализацией

### 4.6 Работа с очередями

#### 4.6.1 Добавление в очередь (queue)

**Синтаксис:**
```osi
queue queue_name value
```

**Примеры:**
```osi
queue packet_queue $buffer
queue numbers 42
queue messages "Error occurred"
```

#### 4.6.2 Извлечение из очереди (dequeue)

**Синтаксис:**
```osi
dequeue(queue_name)
```

**Использование:**
```osi
dequeue(packet_queue) varset first_packet
dequeue(numbers) varset number

; В условии
qcount(packet_queue) > 0 if process_queue

process_queue:
    dequeue(packet_queue) varset packet
    ; обработка packet
```

**Правило:** Если очередь пуста, ошибка времени выполнения.

#### 4.6.3 Просмотр первого элемента (peek)

**Синтаксис:**
```osi
peek(queue_name)
```

**Примеры:**
```osi
peek(packet_queue) varset first_packet    ; не удаляет из очереди
qcount(packet_queue) varset count         ; по-прежнему тот же размер
```

**Отличие от dequeue:** Не удаляет элемент из очереди.

#### 4.6.4 Получение размера очереди (qcount)

**Синтаксис:**
```osi
qcount(queue_name)
```

**Примеры:**
```osi
qcount(packet_queue) varset queue_size
qcount(packet_queue) == 0 if queue_empty

queue_empty:
    out "Queue is empty"
    return
```

#### 4.6.5 Очистка очереди (clearqueue)

**Синтаксис:**
```osi
clearqueue queue_name
```

**Примеры:**
```osi
clearqueue packet_queue
qcount(packet_queue) varset size    ; size = 0
```

### 4.7 Таймеры

#### 4.7.1 Установка таймера (timer)

**Синтаксис:**
```osi
EVENT_NAME timer timer_variable delay [parameter1 value1 parameter2 value2 ...]
```

**Где:**
- `EVENT_NAME` - имя события (обработчика) для вызова
- `timer_variable` - переменная для хранения ID таймера (без `$`)
- `delay` - задержка в системных единицах (integer)
- `parameter1 value1 ...` - параметры для передачи обработчику

**Примеры:**
```osi
; Простой таймер
ZERO_TIMER timer zero_timer 0

; Таймер с задержкой
CONTIMER timer con_timer 100

; Таймер с параметрами
ZERO_TIMER timer zero_timer 0 address $t_address package $buffer

; Таймер с вычисляемой задержкой
TIMEOUT timer timeout_timer (2 * $delay + 1) address $addr

; Множественные параметры
SEND_MESSAGE timer timer1 50 userdata $data stat 3 address $addr
```

**Правила:**
- ✅ `delay` может быть выражением
- ✅ `timer_variable` должна быть типа integer
- ✅ Если таймер с данным ID уже существует, ID не меняется
- ✅ Если таймера с данным ID нет, создается новый ID
- ✅ Параметры проверяются на соответствие сигнатуре целевого обработчика

**Поведение:**
```osi
; Первый вызов - создает таймер с ID = 123
HANDLER timer t1 100        ; t1 = 123

; Второй вызов - если таймер 123 еще активен
HANDLER timer t1 200        ; t1 = 123 (не меняется)

; Если таймер 123 уже сработал
HANDLER timer t1 200        ; t1 = 456 (новый ID)
```

#### 4.7.2 Отмена таймера (untimer)

**Синтаксис:**
```osi
untimer timer_id
```

**Примеры:**
```osi
untimer $timer1
untimer $con_timer

; В условии
$flag == 1 if cancel_timer

cancel_timer:
    untimer $timer1
    return
```

**Правило:** Отменяет **все** таймеры с указанным ID.

### 4.8 События

#### 4.8.1 Генерация события вверх (generateup)

**Синтаксис:**
```osi
EVENT.NAME generateup [parameter1 value1 parameter2 value2 ...]
```

**Примеры:**
```osi
T_CONNECT.IND generateup address $address

P_DATA.IND generateup userdata $buffer

S_RELEASE.CONF generateup
```

**Семантика:** Отправляет событие на уровень выше.

#### 4.8.2 Передача события вниз (eventdown)

**Синтаксис:**
```osi
EVENT.NAME eventdown [parameter1 value1 parameter2 value2 ...]
```

**Примеры:**
```osi
N_DATAGRAM.REQ eventdown address $address userdata $buffer

T_CONNECT.REQ eventdown address $addr

P_RELEASE.REQ eventdown
```

**Семантика:** Отправляет событие на уровень ниже.

#### 4.8.3 Проверка параметров событий

LSP проверяет соответствие параметров:

```osi
; В файле N_DATAGRAM.REQ.osi:
; Параметры: address (integer), userdata (buffer)

; Правильный вызов
HANDLER:
    N_DATAGRAM.REQ eventdown address $addr userdata $buf    ✅
    
    ; Неправильные вызовы
    N_DATAGRAM.REQ eventdown address "string"               ❌ тип
    N_DATAGRAM.REQ eventdown address $addr                  ❌ отсутствует userdata
    N_DATAGRAM.REQ eventdown userdata $buf                  ❌ отсутствует address
    N_DATAGRAM.REQ eventdown wrong_param $x                 ❌ неизвестный параметр
    
    return
```

### 4.9 Встроенные функции

#### 4.9.1 sizeof - размер буфера/строки

**Синтаксис:**
```osi
sizeof(variable)
```

**Примеры:**
```osi
sizeof(buffer) varset buffer_size
sizeof(name) varset name_length

; В выражениях
buffer2 bufferit sizeof(buffer1)+1 $buffer1 sizeof(buffer1) $crc 1
unbufferit data field1 5 rest sizeof(data)-5
```

**Возвращает:** integer

#### 4.9.2 copy - копирование подстроки

**Синтаксис:**
```osi
copy(string, start, length)
```

**Где:**
- `string` - исходная строка
- `start` - начальная позиция (1-based)
- `length` - длина подстроки

**Примеры:**
```osi
copy(structure_string, 2, 5) varset substring
copy($name, 1, 3) varset prefix

; Копирование до конца
copy($str, 5, sizeof(str)-4) varset tail
```

**Возвращает:** string

#### 4.9.3 pos - поиск подстроки

**Синтаксис:**
```osi
pos(needle, haystack)
```

**Где:**
- `needle` - искомая подстрока
- `haystack` - строка для поиска

**Примеры:**
```osi
pos($innerOpenSymb, structure_string) varset index
pos(":", $path) varset colon_pos

; Проверка наличия
pos($substring, $text) > 0 if found
```

**Возвращает:** integer (позиция или 0 если не найдено)

#### 4.9.4 locguide - справочник локаций

**Синтаксис:**
```osi
locguide(name)
```

**Примеры:**
```osi
locguide($name) varset address
locguide("Guide") varset guide_address
```

**Возвращает:** buffer (специфичная для приложения структура)

#### 4.9.5 CurrentSystemName - имя системы

**Синтаксис:**
```osi
CurrentSystemName()
```

**Примеры:**
```osi
out "System: " CurrentSystemName()
CurrentSystemName() varset sys_name
```

**Возвращает:** string

### 4.10 Вывод отладочной информации

#### 4.10.1 Синтаксис

```osi
out expression
```

**Примеры:**
```osi
out "Debug message"
out $counter
out "Counter value: " $counter
out "Buffer size: " sizeof(buffer)
```

**Правила:**
- ✅ Принимает любое выражение
- ✅ Можно конкатенировать строки и числа
- ✅ Для buffer выводит размер

### 4.11 Выражения

#### 4.11.1 Арифметические операции

```osi
$a + $b                 ; сложение
$a - $b                 ; вычитание
$a * $b                 ; умножение
$a / $b                 ; деление
$a % $b                 ; остаток от деления
```

**Приоритет операций:**
1. `*`, `/`, `%`
2. `+`, `-`

**Ассоциативность:** Лево-ассоциативная

**Примеры:**
```osi
$a + $b * $c        ; = $a + ($b * $c)
$a * $b + $c        ; = ($a * $b) + $c
($a + $b) * $c      ; = ($a + $b) * $c
```

#### 4.11.2 Операции сравнения

```osi
$a == $b            ; равно
$a != $b            ; не равно
$a > $b             ; больше
$a < $b             ; меньше
$a >= $b            ; больше или равно
$a <= $b            ; меньше или равно
```

**Возвращают:** логическое значение (используется в `if`)

#### 4.11.3 Логические операции

```osi
$a && $b            ; логическое И
$a || $b            ; логическое ИЛИ
```

**Приоритет:**
1. `&&`
2. `||`

**Примеры:**
```osi
($a > 0) && ($b < 10) if label
($flag1 == 1) || ($flag2 == 1) if process
```

#### 4.11.4 Порядок вычисления

**Полный приоритет операций (от высшего к низшему):**
1. Скобки `()`
2. Функции: `sizeof()`, `copy()`, `pos()`
3. Унарный минус `-`
4. `*`, `/`, `%`
5. `+`, `-`
6. `>`, `<`, `>=`, `<=`
7. `==`, `!=`
8. `&&`
9. `||`

**Примеры:**
```osi
$a + $b * $c - $d / $e           ; = $a + ($b * $c) - ($d / $e)
$a > 0 && $b < 10               ; = ($a > 0) && ($b < 10)
$a == 1 || $b == 2 && $c == 3   ; = ($a == 1) || (($b == 2) && ($c == 3))
```

---

## 5. Требования к Language Server

### 5.1 Обязательные возможности (MVP)

#### 5.1.1 Подсветка синтаксиса (Syntax Highlighting)

**Требование:** Корректная подсветка всех элементов языка согласно TextMate грамматике.

**Элементы для подсветки:**

| Элемент | Scope | Цвет | Стиль |
|---------|-------|------|-------|
| Комментарии | `comment.line.semicolon.osi` | `#6A9955` | обычный |
| Имя обработчика | `entity.name.function.osi` | `#DCDCAA` | жирный |
| Внутренние метки | `entity.name.label.osi` | `#4EC9B0` | обычный |
| Ключевые слова управления | `keyword.control.osi` | `#C586C0` | обычный |
| declare, varset | `keyword.other.osi` | `#569CD6` | обычный |
| Типы | `storage.type.osi` | `#4EC9B0` | обычный |
| Операторы | `support.function.osi` | `#DCDCAA` | обычный |
| События | `keyword.other.event.osi` | `#4FC1FF` | обычный |
| Встроенные функции | `support.function.builtin.osi` | `#DCDCAA` | обычный |
| Переменные | `variable.other.osi` | `#9CDCFE` | обычный |
| Строки | `string.quoted.double.osi` | `#CE9178` | обычный |
| Числа | `constant.numeric.osi` | `#B5CEA8` | обычный |
| Коды символов | `constant.numeric.charcode.osi` | `#B5CEA8` | обычный |
| Имена событий | `entity.name.type.osi` | `#4EC9B0` | обычный |
| Операторы | `keyword.operator.osi` | `#D4D4D4` | обычный |

**Специальные случаи:**

1. **TIMER в именах:**
```osi
TIMER_HANDLER:        ; TIMER - фиолетовый, _HANDLER - желтый
```

2. **Параметры в комментариях:**
```osi
; Параметры: address (integer), userdata (buffer)
  ^^^^^^^^^^   ^^^^^^^   ^^^^^^^   ^^^^^^^^  ^^^^^^
  синий        голубой   циановый  голубой   циановый
  жирный
```

#### 5.1.2 Диагностика (Diagnostics)

**Уровни серьезности:**
- **Error** - критическая ошибка, код не будет работать
- **Warning** - потенциальная проблема
- **Information** - информационное сообщение
- **Hint** - подсказка для улучшения кода

**Список проверок:**

**A. Ошибки объявления переменных:**

1. **Необъявленная переменная**
```osi
HANDLER:
    $undefined varset x        ❌ ERROR
    return
```
Сообщение: `Variable 'undefined' is not declared`

2. **Повторное объявление**
```osi
; INIT.osi
counter declare integer
counter declare integer        ❌ ERROR
```
Сообщение: `Variable 'counter' is already declared at line X`

3. **Объявление вне INIT**
```osi
HANDLER:
    counter declare integer    ❌ ERROR
    return
```
Сообщение: `Variable declarations are only allowed in INIT.osi`

**B. Ошибки типов:**

4. **Несоответствие типов в varset**
```osi
; INIT.osi
counter declare integer

HANDLER:
    "string" varset counter    ❌ ERROR
    return
```
Сообщение: `Type mismatch: cannot assign 'string' to 'integer'`

5. **Несовместимые операции**
```osi
HANDLER:
    $counter + "string" varset x    ❌ ERROR
    return
```
Сообщение: `Cannot apply operator '+' to types 'integer' and 'string'`

6. **Неправильный тип параметра события**
```osi
; TARGET.osi ожидает: address (integer)

HANDLER:
    TARGET eventdown address "wrong"    ❌ ERROR
    return
```
Сообщение: `Parameter 'address' expects type 'integer', got 'string'`

**C. Ошибки меток:**

7. **Несуществующая метка**
```osi
HANDLER:
    goto nonexistent    ❌ ERROR
    return
```
Сообщение: `Label 'nonexistent' not found`

8. **Дублирование метки**
```osi
HANDLER:
    goto exit
exit:
    return
exit:                  ❌ ERROR
    return
```
Сообщение: `Label 'exit' is already defined at line X`

**D. Ошибки файловой структуры:**

9. **Отсутствие INIT.osi**
```
directory/
├── HANDLER.osi        ❌ ERROR: no INIT.osi
```
Сообщение: `Directory 'directory' must contain INIT.osi file`

10. **Несоответствие имени обработчика и файла**
```osi
; Файл: HANDLER1.osi

HANDLER2:              ❌ ERROR
    return
```
Сообщение: `Handler name 'HANDLER2' does not match filename 'HANDLER1.osi'`

11. **Несуществующий файл обработчика**
```osi
HANDLER:
    NONEXISTENT timer t 100    ❌ ERROR
    return
```
Сообщение: `Handler file 'NONEXISTENT.osi' not found in directory`

**E. Ошибки параметров:**

12. **Отсутствие обязательного параметра**
```osi
; TARGET.osi ожидает: address (integer), userdata (buffer)

HANDLER:
    TARGET eventdown address $x    ❌ ERROR: missing userdata
    return
```
Сообщение: `Missing required parameter 'userdata' for event 'TARGET'`

13. **Неизвестный параметр**
```osi
; TARGET.osi ожидает: address (integer)

HANDLER:
    TARGET eventdown unknown $x    ❌ ERROR
    return
```
Сообщение: `Unknown parameter 'unknown' for event 'TARGET'`

14. **Неправильный формат комментария параметров**
```osi
; Параметры address (integer)    ❌ ERROR: нет двоеточия
```
Сообщение: `Invalid parameter comment format. Expected: '; Параметры: name (type), ...'`

**F. Предупреждения (Warnings):**

15. **Неиспользуемая переменная**
```osi
; INIT.osi
unused declare integer    ⚠️ WARNING

HANDLER:
    0 varset counter
    return
```
Сообщение: `Variable 'unused' is declared but never used`

16. **Неиспользуемая метка**
```osi
HANDLER:
    return
    
unused_label:         ⚠️ WARNING
    return
```
Сообщение: `Label 'unused_label' is defined but never used`

17. **Недостижимый код**
```osi
HANDLER:
    return
    out "Never executes"    ⚠️ WARNING
```
Сообщение: `Unreachable code detected`

18. **Использование до инициализации**
```osi
HANDLER:
    out $counter        ⚠️ WARNING
    0 varset counter
    return
```
Сообщение: `Variable 'counter' may be used before initialization`

19. **Отсутствие return**
```osi
HANDLER:
    out "Test"
    ; нет return        ⚠️ WARNING
```
Сообщение: `Handler should end with 'return' statement`

**G. Информационные сообщения (Info):**

20. **Параметр затеняет глобальную переменную**
```osi
; INIT.osi
address declare integer

; HANDLER.osi
; Параметры: address (integer)

HANDLER:
    $address varset x    ℹ️ INFO
    return
```
Сообщение: `Parameter 'address' shadows global variable with same name`

#### 5.1.3 Автодополнение (Completion)

**Контексты автодополнения:**

**A. После ввода declare:**
```osi
counter declare |
                ^
```
Предложить: `integer`, `buffer`, `string`, `queue`

**B. После varset:**
```osi
5 varset |
         ^
```
Предложить: все объявленные переменные (без `$`)

**C. В начале строки:**
```osi
|
^
```
Предложить: ключевые слова (`goto`, `if`, `return`, `out`, операторы)

**D. После $:**
```osi
$|
 ^
```
Предложить: все переменные и параметры

**E. После goto/if:**
```osi
goto |
     ^
```
Предложить: все метки в текущем обработчике

**F. После timer:**
```osi
HANDLER timer |
              ^
```
Предложить: все переменные типа integer

**G. В вызове события:**
```osi
EVENT eventdown |
                ^
```
Предложить: параметры из комментария целевого обработчика

**Формат предложений:**

```typescript
{
  label: "counter",
  kind: CompletionItemKind.Variable,
  detail: "integer",
  documentation: "Declared at line 5 in INIT.osi",
  insertText: "counter",
  sortText: "0_counter"  // для сортировки
}
```

**Приоритет предложений:**
1. Параметры текущего обработчика
2. Локальные метки
3. Глобальные переменные из INIT.osi
4. Ключевые слова
5. Имена обработчиков

#### 5.1.4 Hover (Всплывающие подсказки)

**Для переменных:**

Наведение на `$counter`:
```markdown
**counter**: `integer`

Declared at INIT.osi:12

Used 5 times in this handler
```

**Для параметров:**

Наведение на `$address` (параметр):
```markdown
**address**: `integer` (parameter)

Defined in handler comment
```

**Для меток:**

Наведение на `exit`:
```markdown
**exit**: label

Defined at line 45

Referenced 3 times
```

**Для ключевых слов:**

Наведение на `bufferit`:
```markdown
**bufferit** - Create buffer

Syntax: `buffer_name bufferit total_length value1 len1 ...`

Creates a buffer of specified length from fields.
```

**Для обработчиков в вызовах:**

Наведение на `ZERO_TIMER` в вызове:
```markdown
**ZERO_TIMER**

File: ZERO_TIMER.osi

Parameters: address (integer), package (buffer)
```

#### 5.1.5 Go to Definition

**Для переменных:**
- Клик на `$counter` → переход к строке объявления в INIT.osi

**Для параметров:**
- Клик на `$address` → переход к комментарию с параметрами

**Для меток:**
- Клик на `exit` в `goto exit` → переход к `exit:`

**Для обработчиков:**
- Клик на `ZERO_TIMER` в вызове → открытие файла `ZERO_TIMER.osi`

#### 5.1.6 Find References

**Для переменных:**
Найти все использования `counter`:
```
INIT.osi:5      counter declare integer
HANDLER1.osi:10 0 varset counter
HANDLER1.osi:15 $counter + 1 varset counter
HANDLER2.osi:8  out $counter
```

**Для меток:**
Найти все использования метки `exit`:
```
HANDLER.osi:20  goto exit
HANDLER.osi:25  $flag == 1 if exit
HANDLER.osi:40  exit:
```

**Для обработчиков:**
Найти все вызовы `ZERO_TIMER`:
```
T_CONNECT.REQ.osi:25  ZERO_TIMER timer zero_timer 0 ...
T_DATA.REQ.osi:18     ZERO_TIMER timer zero_timer 1 ...
```

### 5.2 Расширенные возможности (Future)

#### 5.2.1 Rename Symbol

Переименование переменной с обновлением всех использований:
```
counter → packet_counter

INIT.osi:5           counter → packet_counter
HANDLER.osi:10       $counter → $packet_counter
HANDLER.osi:15       $counter → $packet_counter
```

#### 5.2.2 Code Actions (Quick Fixes)

**"Объявить отсутствующую переменную":**
```osi
HANDLER:
    $undefined varset x    ❌ ERROR
    return
```

Quick Fix → добавляет в INIT.osi:
```osi
undefined declare integer
```

**"Инициализировать переменную":**
```osi
HANDLER:
    out $counter          ⚠️ WARNING
    return
```

Quick Fix → добавляет перед использованием:
```osi
HANDLER:
    0 varset counter
    out $counter
    return
```

**"Удалить неиспользуемую переменную":**
```osi
; INIT.osi
unused declare integer    ⚠️ WARNING
```

Quick Fix → удаляет объявление

#### 5.2.3 Code Lens

Показ информации над обработчиками:
```osi
; 👁️ 3 references | 📝 Last modified: 2 days ago
HANDLER:
    return
```

#### 5.2.4 Semantic Highlighting

Дополнительная подсветка после анализа:
- Параметры - особый цвет
- Неинициализированные переменные - серым
- Константы (никогда не меняются) - другим оттенком

#### 5.2.5 Snippets

Быстрая вставка шаблонов:

**Объявление с инициализацией:**
```
Trigger: "deci"
Result:
${1:variable} declare integer
0 varset ${1:variable}
```

**Условный переход:**
```
Trigger: "ifg"
Result:
$${1:condition} if ${2:label}

${2:label}:
    ${3:code}
    return
```

**Создание буфера:**
```
Trigger: "buff"
Result:
${1:buffer_name} bufferit ${2:length} ${3:value1} ${4:len1}
```

#### 5.2.6 Formatting

Автоматическое форматирование:
```osi
; До
HANDLER:
$counter+1 varset counter
goto   exit
exit:
return

; После
HANDLER:
    $counter + 1 varset counter
    goto exit
    
exit:
    return
```

**Правила:**
- Отступ 4 пробела для кода внутри обработчика
- Пробелы вокруг операторов
- Пустая строка перед метками
- Выравнивание комментариев

#### 5.2.7 Document Symbols

Outline/структура документа:
```
HANDLER.osi
├── HANDLER (handler)
├── process (label)
├── error_handler (label)
└── exit (label)
```

#### 5.2.8 Call Hierarchy

Иерархия вызовов:
```
T_CONNECT.REQ
├─> calls ZERO_TIMER
│   └─> calls N_DATAGRAM.REQ
└─> calls T_CONNECT.IND (generateup)
```

---

## 6. Архитектура решения

### 6.1 Общая архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    VS Code Editor                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │         VS Code Extension (TypeScript)           │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │        Language Client                     │  │  │
│  │  │  - Manages LSP connection                  │  │  │
│  │  │  - Handles UI integration                  │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           │ LSP Protocol (JSON-RPC over stdio)
                           │
┌─────────────────────────▼─────────────────────────────────┐
│         Language Server (Python + pygls)                  │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Server Core                           │  │
│  │  - Connection handling                             │  │
│  │  - Document management                             │  │
│  │  - LSP protocol implementation                     │  │
│  └────────────────────────────────────────────────────┘  │
│                           │                               │
│  ┌────────────────────────▼────────────────────────────┐ │
│  │             Parser Pipeline                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │  Lexer   │─>│  Parser  │─>│   AST Builder    │ │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘ │  │
│  └────────────────────────────────────────────────────┘ │
│                           │                               │
│  ┌────────────────────────▼────────────────────────────┐ │
│  │            Analysis Engine                         │  │
│  │  ┌─────────────────┐  ┌──────────────────────────┐ │  │
│  │  │  Symbol Table   │  │    Type Checker          │ │  │
│  │  │  Manager        │  │  - Type inference        │ │  │
│  │  │  - Variables    │  │  - Type compatibility    │ │  │
│  │  │  - Labels       │  │  - Parameter validation  │ │  │
│  │  │  - Handlers     │  └──────────────────────────┘ │  │
│  │  └─────────────────┘                                │  │
│  │  ┌─────────────────┐  ┌──────────────────────────┐ │  │
│  │  │  Scope Resolver │  │   Flow Analyzer          │ │  │
│  │  │  - Global scope │  │  - Reachability          │ │  │
│  │  │  - Local scope  │  │  - Initialization        │ │  │
│  │  │  - Parameters   │  │  - Dead code             │ │  │
│  │  └─────────────────┘  └──────────────────────────┘ │  │
│  └────────────────────────────────────────────────────┘ │
│                           │                               │
│  ┌────────────────────────▼────────────────────────────┐ │
│  │              LSP Providers                         │  │
│  │  ┌──────────────────┐  ┌──────────────────────────┐│ │
│  │  │   Diagnostics    │  │     Completion           ││ │
│  │  │   Provider       │  │     Provider             ││ │
│  │  └──────────────────┘  └──────────────────────────┘│ │
│  │  ┌──────────────────┐  ┌──────────────────────────┐│ │
│  │  │     Hover        │  │     Definition           ││ │
│  │  │     Provider     │  │     Provider             ││ │
│  │  └──────────────────┘  └──────────────────────────┘│ │
│  │  ┌──────────────────┐  ┌──────────────────────────┐│ │
│  │  │   References     │  │     Formatting           ││ │
│  │  │   Provider       │  │     Provider             ││ │
│  │  └──────────────────┘  └──────────────────────────┘│ │
│  └────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

### 6.2 Структура директорий проекта

```
osi-language-server/
├── README.md
├── LICENSE
├── .gitignore
├── package.json                    # Root package.json
│
├── client/                         # VS Code Extension
│   ├── src/
│   │   ├── extension.ts           # Extension entry point
│   │   ├── client.ts              # LSP client setup
│   │   └── utils.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── .vscodeignore
│
├── server/                         # Language Server (Python)
│   ├── pyproject.toml
│   ├── setup.py
│   ├── requirements.txt
│   ├── README.md
│   │
│   ├── osi_lsp/                   # Main package
│   │   ├── __init__.py
│   │   ├── __main__.py            # Entry point
│   │   ├── server.py              # Main LSP server
│   │   ├── config.py              # Configuration
│   │   │
│   │   ├── parser/                # Parsing subsystem
│   │   │   ├── __init__.py
│   │   │   ├── lexer.py          # Lexical analyzer
│   │   │   ├── tokens.py         # Token definitions
│   │   │   ├── ast_nodes.py      # AST node classes
│   │   │   ├── parser.py         # Syntax parser
│   │   │   └── visitor.py        # AST visitor pattern
│   │   │
│   │   ├── analysis/              # Semantic analysis
│   │   │   ├── __init__.py
│   │   │   ├── symbol_table.py   # Symbol table management
│   │   │   ├── types.py          # Type system
│   │   │   ├── type_checker.py   # Type checking
│   │   │   ├── scope_resolver.py # Scope resolution
│   │   │   ├── flow_analyzer.py  # Control flow analysis
│   │   │   └── validator.py      # Semantic validation
│   │   │
│   │   ├── workspace/             # Workspace management
│   │   │   ├── __init__.py
│   │   │   ├── document.py       # Document representation
│   │   │   ├── project.py        # Project structure
│   │   │   └── file_manager.py   # File operations
│   │   │
│   │   ├── providers/             # LSP providers
│   │   │   ├── __init__.py
│   │   │   ├── diagnostics.py    # Error/warning reporting
│   │   │   ├── completion.py     # Auto-completion
│   │   │   ├── hover.py          # Hover information
│   │   │   ├── definition.py     # Go to definition
│   │   │   ├── references.py     # Find references
│   │   │   ├── formatting.py     # Code formatting
│   │   │   └── symbols.py        # Document symbols
│   │   │
│   │   └── utils/                 # Utilities
│   │       ├── __init__.py
│   │       ├── position.py       # Position/Range helpers
│   │       ├── text.py           # Text manipulation
│   │       └── logging.py        # Logging configuration
│   │
│   └── tests/                     # Tests
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_lexer.py
│       ├── test_parser.py
│       ├── test_symbol_table.py
│       ├── test_type_checker.py
│       └── fixtures/
│           ├── valid/
│           └── invalid/
│
├── syntaxes/                       # TextMate grammar
│   ├── osi.tmLanguage.json
│   └── osi.configuration.json
│
├── examples/                       # Example projects
│   ├── simple/
│   │   ├── transport/
│   │   │   ├── INIT.osi
│   │   │   └── HANDLER.osi
│   │   └── session/
│   │       ├── INIT.osi
│   │       └── HANDLER.osi
│   └── complete/
│       ├── transport/
│       ├── session/
│       ├── presentation/
│       └── application/
│
├── docs/                           # Documentation
│   ├── language-spec.md
│   ├── lsp-features.md
│   ├── development.md
│   └── api/
│
└── scripts/                        # Build/utility scripts
    ├── build.sh
    ├── test.sh
    └── package.sh
```

### 6.3 Компоненты Language Server

#### 6.3.1 Lexer (Лексический анализатор)

**Назначение:** Преобразование текста в последовательность токенов.

**Класс TokenType:**
```python
class TokenType(Enum):
    # Keywords
    DECLARE = "DECLARE"
    VARSET = "VARSET"
    GOTO = "GOTO"
    IF = "IF"
    RETURN = "RETURN"
    BREAK = "BREAK"
    
    # Operators
    BUFFERIT = "BUFFERIT"
    UNBUFFERIT = "UNBUFFERIT"
    CALCCRC = "CALCCRC"
    TIMER = "TIMER"
    UNTIMER = "UNTIMER"
    QUEUE = "QUEUE"
    CLEARQUEUE = "CLEARQUEUE"
    DEQUEUE = "DEQUEUE"
    PEEK = "PEEK"
    QCOUNT = "QCOUNT"
    
    # Events
    GENERATEUP = "GENERATEUP"
    EVENTDOWN = "EVENTDOWN"
    
    # Types
    INTEGER = "INTEGER"
    BUFFER = "BUFFER"
    STRING = "STRING"
    QUEUE_TYPE = "QUEUE"
    
    # Functions
    SIZEOF = "SIZEOF"
    COPY = "COPY"
    POS = "POS"
    LOCGUIDE = "LOCGUIDE"
    CURRENTSYSTEMNAME = "CURRENTSYSTEMNAME"
    OUT = "OUT"
    
    # Literals
    NUMBER = "NUMBER"
    STRING_LITERAL = "STRING_LITERAL"
    CHAR_CODE = "CHAR_CODE"
    
    # Identifiers
    IDENTIFIER = "IDENTIFIER"
    VARIABLE = "VARIABLE"
    LABEL = "LABEL"
    
    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    MODULO = "MODULO"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    GREATER = "GREATER"
    LESS = "LESS"
    GREATER_EQUAL = "GREATER_EQUAL"
    LESS_EQUAL = "LESS_EQUAL"
    AND = "AND"
    OR = "OR"
    
    # Punctuation
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    COLON = "COLON"
    
    # Special
    NEWLINE = "NEWLINE"
    EOF = "EOF"
    COMMENT = "COMMENT"
```

**Класс Token:**
```python
@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    length: int
```

**Основные методы Lexer:**
```python
class Lexer:
    def __init__(self, text: str, uri: str):
        self.text = text
        self.uri = uri
        self.pos = 0
        self.line = 0
        self.column = 0
        
    def tokenize(self) -> List[Token]:
        """Токенизировать весь текст"""
        
    def next_token(self) -> Token:
        """Получить следующий токен"""
        
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Посмотреть следующий символ"""
        
    def read_number(self) -> Token:
        """Прочитать число"""
        
    def read_string(self) -> Token:
        """Прочитать строку"""
        
    def read_identifier(self) -> Token:
        """Прочитать идентификатор"""
        
    def read_variable(self) -> Token:
        """Прочитать переменную $var"""
        
    def skip_whitespace(self) -> None:
        """Пропустить пробелы"""
        
    def skip_comment(self) -> Optional[Token]:
        """Пропустить/прочитать комментарий"""
```

#### 6.3.2 Parser (Синтаксический анализатор)

**Назначение:** Построение AST из последовательности токенов.

**AST Nodes:**
```python
# Base
class ASTNode(ABC):
    line: int
    column: int
    
    @abstractmethod
    def accept(self, visitor: 'Visitor'):
        pass

# Program
@dataclass
class Program(ASTNode):
    handler: Handler

# Handler
@dataclass
class Handler(ASTNode):
    name: str
    parameters: List[Parameter]
    statements: List[Statement]

@dataclass
class Parameter:
    name: str
    param_type: str
    line: int

# Statements
@dataclass
class DeclareStatement(ASTNode):
    variable: str
    var_type: str

@dataclass
class VarsetStatement(ASTNode):
    expression: Expression
    variable: str

@dataclass
class BufferitStatement(ASTNode):
    buffer_name: str
    total_length: Expression
    fields: List[Tuple[Expression, Expression]]

@dataclass
class UnbufferitStatement(ASTNode):
    buffer_name: str
    fields: List[Tuple[str, Expression]]

@dataclass
class GotoStatement(ASTNode):
    label: str

@dataclass
class IfStatement(ASTNode):
    condition: Expression
    label: str

@dataclass
class LabelStatement(ASTNode):
    name: str

@dataclass
class ReturnStatement(ASTNode):
    pass

@dataclass
class TimerStatement(ASTNode):
    event_name: str
    timer_var: str
    delay: Expression
    parameters: Dict[str, Expression]

@dataclass
class GenerateupStatement(ASTNode):
    event_name: str
    parameters: Dict[str, Expression]

@dataclass
class EventdownStatement(ASTNode):
    event_name: str
    parameters: Dict[str, Expression]

# Expressions
@dataclass
class NumberLiteral(ASTNode):
    value: int

@dataclass
class StringLiteral(ASTNode):
    value: str

@dataclass
class VariableExpression(ASTNode):
    name: str

@dataclass
class BinaryOperation(ASTNode):
    left: Expression
    operator: str
    right: Expression

@dataclass
class FunctionCall(ASTNode):
    name: str
    arguments: List[Expression]
```

**Основные методы Parser:**
```python
class Parser:
    def __init__(self, tokens: List[Token], uri: str):
        self.tokens = tokens
        self.uri = uri
        self.pos = 0
        
    def parse(self) -> Program:
        """Парсинг программы"""
        
    def parse_handler(self) -> Handler:
        """Парсинг обработчика"""
        
    def parse_statement(self) -> Statement:
        """Парсинг оператора"""
        
    def parse_expression(self) -> Expression:
        """Парсинг выражения"""
        
    def parse_declare(self) -> DeclareStatement:
        """Парсинг declare"""
        
    def parse_varset(self) -> VarsetStatement:
        """Парсинг varset"""
        
    # ... остальные методы парсинга
    
    def current_token(self) -> Token:
        """Текущий токен"""
        
    def peek_token(self, offset: int = 1) -> Optional[Token]:
        """Посмотреть следующий токен"""
        
    def consume(self, expected: TokenType) -> Token:
        """Потребить токен ожидаемого типа"""
        
    def match(self, *types: TokenType) -> bool:
        """Проверка соответствия типу"""
```

#### 6.3.3 Symbol Table (Таблица символов)

**Назначение:** Хранение информации о переменных, метках, обработчиках.

```python
@dataclass
class VariableSymbol:
    name: str
    var_type: str  # 'integer', 'buffer', 'string', 'queue'
    is_parameter: bool
    declared_at: Position
    initialized: bool = False
    used: bool = False
    uses: List[Position] = field(default_factory=list)

@dataclass
class LabelSymbol:
    name: str
    defined_at: Position
    used: bool = False
    uses: List[Position] = field(default_factory=list)

@dataclass
class HandlerSymbol:
    name: str
    file_uri: str
    parameters: List[Parameter]
    defined_at: Position
    calls: List[str] = field(default_factory=list)

class SymbolTable:
    def __init__(self, directory: str):
        self.directory = directory
        self.variables: Dict[str, VariableSymbol] = {}
        self.labels: Dict[str, LabelSymbol] = {}
        self.handlers: Dict[str, HandlerSymbol] = {}
        
    def declare_variable(self, name: str, var_type: str, 
                        position: Position, is_param: bool = False) -> bool:
        """Объявить переменную"""
        
    def get_variable(self, name: str) -> Optional[VariableSymbol]:
        """Получить переменную"""
        
    def use_variable(self, name: str, position: Position):
        """Отметить использование переменной"""
        
    def initialize_variable(self, name: str):
        """Отметить инициализацию"""
        
    def define_label(self, name: str, position: Position) -> bool:
        """Определить метку"""
        
    def use_label(self, name: str, position: Position):
        """Отметить использование метки"""
        
    def register_handler(self, name: str, file_uri: str,
                        parameters: List[Parameter], position: Position):
        """Зарегистрировать обработчик"""
        
    def get_unused_variables(self) -> List[VariableSymbol]:
        """Получить неиспользованные переменные"""
        
    def get_unused_labels(self) -> List[LabelSymbol]:
        """Получить неиспользованные метки"""
        
    def get_uninitialized_variables(self) -> List[VariableSymbol]:
        """Получить неинициализированные переменные"""
```

#### 6.3.4 Type Checker (Проверка типов)

```python
class TypeChecker:
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.errors: List[Diagnostic] = []
        
    def check_varset(self, stmt: VarsetStatement) -> Optional[str]:
        """Проверить varset statement"""
        var_type = self.get_variable_type(stmt.variable)
        expr_type = self.infer_expression_type(stmt.expression)
        
        if var_type != expr_type:
            self.add_error(...)
            
    def infer_expression_type(self, expr: Expression) -> str:
        """Вывести тип выражения"""
        if isinstance(expr, NumberLiteral):
            return 'integer'
        elif isinstance(expr, StringLiteral):
            return 'string'
        elif isinstance(expr, VariableExpression):
            return self.get_variable_type(expr.name)
        elif isinstance(expr, BinaryOperation):
            return self.infer_binary_op_type(expr)
        # ...
        
    def check_event_call(self, stmt: Union[GenerateupStatement, EventdownStatement]):
        """Проверить вызов события"""
        handler = self.symbol_table.handlers.get(stmt.event_name)
        if not handler:
            self.add_error(f"Handler '{stmt.event_name}' not found")
            return
            
        # Проверка параметров
        for param in handler.parameters:
            if param.name not in stmt.parameters:
                self.add_error(f"Missing parameter '{param.name}'")
            else:
                # Проверка типа
                actual_type = self.infer_expression_type(stmt.parameters[param.name])
                if actual_type != param.param_type:
                    self.add_error(f"Type mismatch for parameter '{param.name}'")
```

#### 6.3.5 Flow Analyzer (Анализ потока управления)

```python
class FlowAnalyzer:
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.warnings: List[Diagnostic] = []
        
    def analyze_handler(self, handler: Handler):
        """Анализ обработчика"""
        self.check_reachability(handler)
        self.check_initialization(handler)
        self.check_return(handler)
        
    def check_reachability(self, handler: Handler):
        """Проверка достижимости кода"""
        reachable = True
        for stmt in handler.statements:
            if not reachable:
                self.add_warning(stmt, "Unreachable code")
            if isinstance(stmt, ReturnStatement):
                reachable = False
                
    def check_initialization(self, handler: Handler):
        """Проверка инициализации переменных"""
        initialized = set()
        
        for stmt in handler.statements:
            if isinstance(stmt, VarsetStatement):
                initialized.add(stmt.variable)
            elif self.uses_variable(stmt):
                vars_used = self.get_used_variables(stmt)
                for var in vars_used:
                    if var not in initialized:
                        if not self.symbol_table.get_variable(var).is_parameter:
                            self.add_warning(stmt, 
                                f"Variable '{var}' may be used before initialization")
```

### 6.4 Workspace Management

**Управление файловой структурой:**

```python
@dataclass
class OSIDocument:
    uri: str
    text: str
    version: int
    ast: Optional[Program] = None
    tokens: List[Token] = field(default_factory=list)
    diagnostics: List[Diagnostic] = field(default_factory=list)

class OSIProject:
    def __init__(self, root_uri: str):
        self.root_uri = root_uri
        self.directories: Dict[str, DirectoryContext] = {}
        
    def get_directory(self, file_uri: str) -> DirectoryContext:
        """Получить контекст директории для файла"""
        
    def find_init_file(self, directory: str) -> Optional[str]:
        """Найти INIT.osi в директории"""
        
    def find_handler_file(self, directory: str, handler_name: str) -> Optional[str]:
        """Найти файл обработчика"""
        
    def get_all_handlers(self, directory: str) -> List[str]:
        """Получить все обработчики в директории"""

@dataclass
class DirectoryContext:
    path: str
    init_file: Optional[str]
    handler_files: Dict[str, str]  # name -> uri
    symbol_table: SymbolTable
```

### 6.5 LSP Protocol Implementation

**Server endpoints:**

```python
@server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: LanguageServer, params: lsp.DidOpenTextDocumentParams):
    """Документ открыт"""
    
@server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: LanguageServer, params: lsp.DidChangeTextDocumentParams):
    """Документ изменен"""
    
@server.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
async def did_save(ls: LanguageServer, params: lsp.DidSaveTextDocumentParams):
    """Документ сохранен"""
    
@server.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
async def did_close(ls: LanguageServer, params: lsp.DidCloseTextDocumentParams):
    """Документ закрыт"""
    
@server.feature(lsp.TEXT_DOCUMENT_COMPLETION)
async def completion(ls: LanguageServer, params: lsp.CompletionParams) -> lsp.CompletionList:
    """Автодополнение"""
    
@server.feature(lsp.TEXT_DOCUMENT_HOVER)
async def hover(ls: LanguageServer, params: lsp.HoverParams) -> Optional[lsp.Hover]:
    """Hover информация"""
    
@server.feature(lsp.TEXT_DOCUMENT_DEFINITION)
async def definition(ls: LanguageServer, params: lsp.DefinitionParams) -> Optional[lsp.Location]:
    """Go to definition"""
    
@server.feature(lsp.TEXT_DOCUMENT_REFERENCES)
async def references(ls: LanguageServer, params: lsp.ReferenceParams) -> List[lsp.Location]:
    """Find references"""
```

---

## 7. План реализации

### 7.1 Фаза 0: Подготовка (3 дня)

**Задачи:**
1. Настройка окружения разработки
2. Создание структуры проекта
3. Настройка CI/CD
4. Создание базовой документации

**Deliverables:**
- ✅ Репозиторий Git
- ✅ Структура директорий
- ✅ package.json, pyproject.toml
- ✅ README.md с инструкциями

**Критерии приемки:**
- Можно собрать пустое расширение VS Code
- Можно запустить пустой Python сервер
- Проходит lint (eslint, mypy, flake8)

### 7.2 Фаза 1: Lexer (5 дней)

**Задачи:**
1. Реализация TokenType enum
2. Реализация класса Token
3. Реализация Lexer
4. Тестирование лексера

**Реализуемые методы:**
```python
- Lexer.__init__()
- Lexer.tokenize()
- Lexer.next_token()
- Lexer.read_number()
- Lexer.read_string()
- Lexer.read_identifier()
- Lexer.read_variable()
- Lexer.skip_whitespace()
- Lexer.skip_comment()
```

**Тесты:**
```python
def test_lexer_numbers():
    assert tokenize("42") == [Token(NUMBER, "42", ...)]
    assert tokenize("-15") == [Token(NUMBER, "-15", ...)]
    
def test_lexer_strings():
    assert tokenize('"hello"') == [Token(STRING_LITERAL, "hello", ...)]
    
def test_lexer_variables():
    assert tokenize("$counter") == [Token(VARIABLE, "$counter", ...)]
    
def test_lexer_keywords():
    assert tokenize("declare varset goto") == [
        Token(DECLARE, "declare", ...),
        Token(VARSET, "varset", ...),
        Token(GOTO, "goto", ...)
    ]
```

**Deliverables:**
- ✅ Полностью рабочий лексер
- ✅ 50+ unit тестов
- ✅ Coverage > 90%

**Критерии приемки:**
- Лексер корректно распознает все токены
- Все тесты проходят
- Обрабатываются граничные случаи

### 7.3 Фаза 2: Parser (7 дней)

**Задачи:**
1. Определение AST узлов
2. Реализация Parser
3. Тестирование парсера
4. Обработка ошибок

**Реализуемые классы:**
```python
- Program, Handler, Parameter
- All Statement classes
- All Expression classes
- Parser с методами парсинга
```

**Тесты:**
```python
def test_parse_declare():
    ast = parse("counter declare integer")
    assert isinstance(ast.handler.statements[0], DeclareStatement)
    
def test_parse_varset():
    ast = parse("5 varset counter")
    assert isinstance(ast.handler.statements[0], VarsetStatement)
    
def test_parse_handler():
    code = """
    HANDLER:
        0 varset counter
        return
    """
    ast = parse(code)
    assert ast.handler.name == "HANDLER"
    assert len(ast.handler.statements) == 2
```

**Deliverables:**
- ✅ Полный парсер
- ✅ 100+ unit тестов
- ✅ Coverage > 85%

**Критерии приемки:**
- Парсер строит корректное AST
- Обрабатываются синтаксические ошибки
- Все примеры из спецификации парсятся

### 7.4 Фаза 3: Symbol Table (5 дней)

**Задачи:**
1. Реализация классов символов
2. Реализация SymbolTable
3. Интеграция с Parser через Visitor
4. Тестирование

**Реализуемые классы:**
```python
- VariableSymbol
- LabelSymbol
- HandlerSymbol
- SymbolTable
- SymbolTableBuilder (Visitor)
```

**Тесты:**
```python
def test_symbol_table_declare():
    table = build_symbol_table("counter declare integer")
    assert "counter" in table.variables
    assert table.variables["counter"].var_type == "integer"
    
def test_symbol_table_duplicate():
    with pytest.raises(DuplicateDeclarationError):
        build_symbol_table("""
        counter declare integer
        counter declare integer
        """)
```

**Deliverables:**
- ✅ Рабочая таблица символов
- ✅ 60+ unit тестов
- ✅ Coverage > 90%

**Критерии приемки:**
- Корректное отслеживание символов
- Обнаружение дубликатов
- Отслеживание использований

### 7.5 Фаза 4: Type Checker (7 дней)

**Задачи:**
1. Реализация TypeChecker
2. Вывод типов выражений
3. Проверка присваиваний
4. Проверка параметров событий
5. Тестирование

**Реализуемые методы:**
```python
- TypeChecker.check_program()
- TypeChecker.check_varset()
- TypeChecker.infer_expression_type()
- TypeChecker.check_event_call()
- TypeChecker.check_timer_call()
```

**Тесты:**
```python
def test_type_checker_varset_mismatch():
    errors = check_types("""
    counter declare integer
    HANDLER:
        "string" varset counter
    """)
    assert len(errors) == 1
    assert "type mismatch" in errors[0].message.lower()
    
def test_type_checker_event_params():
    errors = check_types("""
    ; TARGET.osi expects: address (integer)
    HANDLER:
        TARGET eventdown address "wrong"
    """)
    assert len(errors) == 1
```

**Deliverables:**
- ✅ Полная проверка типов
- ✅ 80+ unit тестов
- ✅ Coverage > 85%

**Критерии приемки:**
- Корректная проверка типов
- Вывод типов выражений работает
- Проверка параметров событий работает

### 7.6 Фаза 5: Workspace Management (4 дня)

**Задачи:**
1. Реализация OSIDocument
2. Реализация OSIProject
3. Реализация DirectoryContext
4. Управление INIT.osi
5. Тестирование

**Реализуемые классы:**
```python
- OSIDocument
- OSIProject
- DirectoryContext
- FileManager
```

**Тесты:**
```python
def test_find_init_file():
    project = OSIProject(root_uri)
    init_uri = project.find_init_file("transport")
    assert init_uri.endswith("INIT.osi")
    
def test_find_handler_file():
    project = OSIProject(root_uri)
    handler_uri = project.find_handler_file("transport", "T_CONNECT.REQ")
    assert handler_uri.endswith("T_CONNECT.REQ.osi")
```

**Deliverables:**
- ✅ Управление workspace
- ✅ 40+ unit тестов
- ✅ Coverage > 90%

**Критерии приемки:**
- Корректное обнаружение INIT.osi
- Корректный поиск обработчиков
- Работа с несколькими директориями

### 7.7 Фаза 6: Diagnostics Provider (5 дней)

**Задачи:**
1. Реализация DiagnosticsProvider
2. Интеграция всех проверок
3. Форматирование сообщений об ошибках
4. Тестирование

**Реализуемые методы:**
```python
- DiagnosticsProvider.get_diagnostics()
- DiagnosticsProvider.check_file_structure()
- DiagnosticsProvider.check_handler_name()
- DiagnosticsProvider.check_parameters()
```

**Проверки:**
- ✅ Необъявленные переменные
- ✅ Дублирование объявлений
- ✅ Несоответствие типов
- ✅ Несуществующие метки
- ✅ Отсутствие INIT.osi
- ✅ Несоответствие имени обработчика
- ✅ Неправильные параметры событий
- ✅ Неиспользуемые переменные (warning)
- ✅ Недостижимый код (warning)

**Deliverables:**
- ✅ Полная диагностика
- ✅ 100+ integration тестов
- ✅ Все ошибки из спецификации

**Критерии приемки:**
- Все типы ошибок обнаруживаются
- Корректные позиции ошибок
- Понятные сообщения

### 7.8 Фаза 7: Completion Provider (4 дня)

**Задачи:**
1. Реализация CompletionProvider
2. Контекстное автодополнение
3. Сортировка и фильтрация
4. Тестирование

**Контексты:**
- После `declare` → типы
- После `varset` → переменные
- После `$` → переменные
- После `goto`/`if` → метки
- После оператора событий → параметры

**Deliverables:**
- ✅ Автодополнение работает
- ✅ 50+ integration тестов

**Критерии приемки:**
- Корректные предложения в каждом контексте
- Правильная сортировка
- Работает filtering при наборе

### 7.9 Фаза 8: Hover Provider (3 дня)

**Задачи:**
1. Реализация HoverProvider
2. Форматирование markdown
3. Тестирование

**Информация для hover:**
- Переменные: тип, место объявления, использования
- Параметры: тип, определение
- Метки: место определения, использования
- Ключевые слова: синтаксис, описание
- Обработчики: файл, параметры

**Deliverables:**
- ✅ Hover работает
- ✅ 30+ integration тестов

### 7.10 Фаза 9: Definition & References (4 дня)

**Задачи:**
1. Реализация DefinitionProvider
2. Реализация ReferencesProvider
3. Тестирование

**Go to definition:**
- Переменная → declare в INIT.osi
- Параметр → комментарий
- Метка → определение
- Обработчик → файл

**Find references:**
- Все использования символа

**Deliverables:**
- ✅ Navigation работает
- ✅ 40+ integration тестов

### 7.11 Фаза 10: TextMate Grammar (3 дня)

**Задачи:**
1. Написание osi.tmLanguage.json
2. Тестирование подсветки
3. Настройка цветовой темы

**Deliverables:**
- ✅ Подсветка синтаксиса
- ✅ Работает в VS Code

### 7.12 Фаза 11: VS Code Extension (4 дня)

**Задачи:**
1. Реализация extension.ts
2. Настройка клиента LSP
3. Конфигурация расширения
4. Тестирование

**Deliverables:**
- ✅ Расширение работает
- ✅ Можно устанавливать
- ✅ Интеграция с LSP работает

### 7.13 Фаза 12: Integration Testing (5 дней)

**Задачи:**
1. End-to-end тесты
2. Тестирование на реальных проектах
3. Исправление багов
4. Оптимизация производительности

**Тестовые сценарии:**
- Открытие проекта
- Редактирование файлов
- Сохранение
- Автодополнение
- Navigation
- Refactoring

**Deliverables:**
- ✅ Все E2E тесты проходят
- ✅ Performance < 100ms для операций

### 7.14 Фаза 13: Documentation (3 дня)

**Задачи:**
1. Пользовательская документация
2. API документация
3. Примеры
4. Видео-туториал

**Deliverables:**
- ✅ README.md
- ✅ Docs website
- ✅ API docs
- ✅ Examples

### 7.15 Фаза 14: Release (2 дня)

**Задачи:**
1. Финальное тестирование
2. Упаковка расширения
3. Публикация в VS Code Marketplace
4. Announcement

**Deliverables:**
- ✅ v1.0.0 released
- ✅ Published on Marketplace

---

## 8. Тестирование

### 8.1 Unit Tests

**Покрытие:** > 85%

**Категории:**
- Lexer tests (50+)
- Parser tests (100+)
- Symbol table tests (60+)
- Type checker tests (80+)
- Flow analyzer tests (40+)
- Workspace tests (40+)

**Frameworks:**
- pytest
- pytest-cov
- pytest-mock

### 8.2 Integration Tests

**Покрытие:** Все LSP фичи

**Категории:**
- Diagnostics (100+)
- Completion (50+)
- Hover (30+)
- Definition (20+)
- References (20+)

### 8.3 End-to-End Tests

**Сценарии:**
1. Создание нового проекта
2. Открытие существующего проекта
3. Редактирование файлов
4. Автодополнение
5. Go to definition
6. Find references
7. Рефакторинг

**Tools:**
- VS Code Extension Tester

### 8.4 Performance Tests

**Метрики:**
- Completion response time < 100ms
- Diagnostics response time < 200ms
- Hover response time < 50ms
- Memory usage < 100MB

**Tools:**
- pytest-benchmark
- memory_profiler

### 8.5 Regression Tests

**Цель:** Предотвращение регрессий

**Процесс:**
1. Фиксация тестов для каждого бага
2. Автоматический запуск на каждый commit
3. CI/CD блокирует merge при падении тестов

---

## 9. Примеры и референсная документация

### 9.1 Минимальный пример

**transport/INIT.osi:**
```osi
; Минимальная инициализация
counter declare integer
```

**transport/SIMPLE.osi:**
```osi
; Параметры: нет

SIMPLE:
    0 varset counter
    out "Counter: " $counter
    return
```

### 9.2 Пример с параметрами

**transport/T_CONNECT.REQ.osi:**
```osi
; ============================================
; Запрос на установление транспортного соединения
; Параметры: address (integer)
; ============================================

T_CONNECT.REQ:
    ; Инициализация
    0 varset last_sent
    0 varset last_received
    
    ; Сохранение адреса
    $address varset t_address
    
    ; Формирование пакета
    $last_sent + 1 varset last_sent
    package_buffer bufferit 2 0 1 $last_sent 1
    
    ; Контрольная сумма
    calccrc pac_crc $package_buffer
    
    ; Добавление CRC к пакету
    package_buffer_out bufferit sizeof(package_buffer)+1 $package_buffer sizeof(package_buffer) $pac_crc 1
    
    ; Установка таймера
    ZERO_TIMER timer zero_timer 0 address $t_address package $package_buffer_out
    
    return
```

### 9.3 Пример с условными переходами

**transport/HANDLER.osi:**
```osi
; Параметры: нет

HANDLER:
    ; Инициализация счетчика
    0 varset counter
    
main_loop:
    ; Увеличение счетчика
    $counter + 1 varset counter
    
    ; Проверка на overflow
    $counter > 100 if overflow
    
    ; Проверка на выход
    $counter == 50 if exit
    
    ; Продолжаем
    goto main_loop
    
overflow:
    out "Counter overflow!"
    0 varset counter
    goto main_loop
    
exit:
    out "Exit at " $counter
    return
```

### 9.4 Пример с событиями

**transport/DATA_HANDLER.osi:**
```osi
; Параметры: userdata (buffer)

DATA_HANDLER:
    ; Разбор буфера
    unbufferit userdata type 1 data sizeof(userdata)-1
    
    ; Проверка типа
    $type == 1 if process_type1
    $type == 2 if process_type2
    goto unknown_type
    
process_type1:
    out "Processing type 1"
    T_DATA.IND generateup userdata $data
    goto done
    
process_type2:
    out "Processing type 2"
    T_DATA.IND generateup userdata $data
    goto done
    
unknown_type:
    out "Unknown packet type"
    
done:
    return
```

### 9.5 Пример с таймерами

**transport/TIMER_EXAMPLE.osi:**
```osi
; Параметры: нет

TIMER_EXAMPLE:
    ; Простой таймер
    TIMEOUT_HANDLER timer timeout_timer 1000
    
    ; Таймер с параметрами
    RETRY_HANDLER timer retry_timer 500 address $addr count $retry_count
    
    ; Отмена таймера
    $flag == 1 if cancel_timers
    
    goto done
    
cancel_timers:
    untimer $timeout_timer
    untimer $retry_timer
    
done:
    return
```

### 9.6 Полный пример проекта

**Структура:**
```
example_project/
├── transport/
│   ├── INIT.osi
│   ├── T_CONNECT.REQ.osi
│   ├── T_DATA.REQ.osi
│   ├── N_DATAGRAM.IND.osi
│   └── ZERO_TIMER.osi
└── session/
    ├── INIT.osi
    ├── S_CONNECT.REQ.osi
    └── S_DATA.REQ.osi
```

**transport/INIT.osi:**
```osi
; ============================================
; Транспортный уровень - Инициализация
; ============================================

; Таймеры
zero_timer declare integer
con_timer declare integer
delay_timer declare integer

; Адреса
t_address declare integer

; Буферы
tmp_buffer declare buffer
package_buffer declare buffer
package_buffer_out declare buffer

; Счетчики и флаги
last_sent declare integer
last_received declare integer
package_type declare integer
package_number declare integer

; Контрольные суммы
pac_crc declare integer
crc_buffer declare integer

; Очереди
package_queue declare queue
```

**transport/T_CONNECT.REQ.osi:**
```osi
; ============================================
; Запрос на установление соединения
; Параметры: address (integer)
; ============================================

T_CONNECT.REQ:
    ; Инициализация состояния
    0 varset last_sent
    0 varset last_received
    
    ; Сохранение адреса
    $address varset t_address
    
    ; Подготовка пакета соединения
    $last_sent + 1 varset last_sent
    package_buffer bufferit 2 0 1 $last_sent 1
    
    ; Вычисление контрольной суммы
    calccrc pac_crc $package_buffer
    
    ; Добавление CRC
    package_buffer_out bufferit sizeof(package_buffer)+1 $package_buffer sizeof(package_buffer) $pac_crc 1
    
    ; Отправка через ZERO_TIMER
    ZERO_TIMER timer zero_timer 0 address $t_address package $package_buffer_out
    
    return
```

**transport/ZERO_TIMER.osi:**
```osi
; ============================================
; Таймер для немедленной отправки
; Параметры: address (integer), package (buffer)
; ============================================

ZERO_TIMER:
    ; Многократная отправка для надежности
    N_DATAGRAM.REQ eventdown address $address userdata $package
    N_DATAGRAM.REQ eventdown address $address userdata $package
    N_DATAGRAM.REQ eventdown address $address userdata $package
    
    return
```

**transport/N_DATAGRAM.IND.osi:**
```osi
; ============================================
; Индикация получения датаграммы
; Параметры: address (integer), userdata (buffer)
; ============================================

N_DATAGRAM.IND:
    ; Проверка минимального размера
    sizeof(userdata) < 3 if corrupted
    
    ; Извлечение CRC и данных
    unbufferit userdata tmp_buffer sizeof(userdata)-1 pac_crc 1
    
    ; Проверка CRC
    calccrc crc_buffer $tmp_buffer
    $crc_buffer != $pac_crc if corrupted
    
    ; Извлечение типа и номера пакета
    unbufferit tmp_buffer package_type 1 package_number 1
    
    ; Обработка по типу
    $package_type == 0 if connect_req
    $package_type == 1 if connect_resp
    $package_type == 10 if data_packet
    goto done
    
connect_req:
    $address varset t_address
    T_CONNECT.IND generateup address $address
    goto done
    
connect_resp:
    untimer $con_timer
    T_CONNECT.CONF generateup address $address
    goto done
    
data_packet:
    unbufferit tmp_buffer data sizeof(tmp_buffer)-2
    T_DATA.IND generateup userdata $data
    goto done
    
corrupted:
    out "Corrupted packet received"
    ; Можно отправить запрос повтора
    
done:
    return
```

---

## 10. Приложения

### 10.1 Список зависимостей

**Python (server/requirements.txt):**
```txt
pygls>=1.2.0
lsprotocol>=2023.0.0
dataclasses-json>=0.6.0
typing-extensions>=4.8.0

# Development
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
mypy>=1.5.0
black>=23.7.0
flake8>=6.1.0
```

**Node.js (client/package.json):**
```json
{
  "dependencies": {
    "vscode-languageclient": "^9.0.0"
  },
  "devDependencies": {
    "@types/node": "^18.17.0",
    "@types/vscode": "^1.75.0",
    "typescript": "^5.1.0",
    "eslint": "^8.47.0",
    "@typescript-eslint/eslint-plugin": "^6.4.0",
    "@typescript-eslint/parser": "^6.4.0"
  }
}
```

### 10.2 Конфигурационные файлы

**pyproject.toml:**
```toml
[tool.poetry]
name = "osi-language-server"
version = "1.0.0"
description = "Language Server for OSI Protocol Language"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.10"
pygls = "^1.2.0"
lsprotocol = "^2023.0.0"

[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
mypy = "^1.5.0"
black = "^23.7.0"

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.black]
line-length = 100
target-version = ['py310']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
```

**tsconfig.json:**
```json
{
  "compilerOptions": {
    "module": "commonjs",
    "target": "ES2020",
    "outDir": "out",
    "lib": ["ES2020"],
    "sourceMap": true,
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src"],
  "exclude": ["node_modules", ".vscode-test"]
}
```

### 10.3 Метрики проекта

**Оценка трудозатрат:**
- Всего фаз: 14
- Всего дней: ~60 рабочих дней
- Команда: 1-2 разработчика
- Календарное время: 3-4 месяца

**Оценка кода:**
- Python код: ~10,000 строк
- TypeScript код: ~1,000 строк
- Tests: ~8,000 строк
- Всего: ~19,000 строк кода

**Оценка тестов:**
- Unit tests: ~400 тестов
- Integration tests: ~200 тестов
- E2E tests: ~30 тестов
- Всего: ~630 тестов

---

## 11. Глоссарий

**AST (Abstract Syntax Tree)** - Абстрактное синтаксическое дерево, представление структуры программы

**Diagnostic** - Сообщение об ошибке, предупреждении или информации

**Handler** - Обработчик события в языке OSI

**Hover** - Всплывающая подсказка при наведении курсора

**LSP (Language Server Protocol)** - Протокол для взаимодействия редактора и языкового сервера

**Symbol Table** - Таблица символов, хранящая информацию о переменных, метках, обработчиках

**Token** - Лексема, минимальная единица языка

**Type Inference** - Вывод типов, автоматическое определение типа выражения

**Workspace** - Рабочая область, корневая директория проекта

---

## 12. Контакты и поддержка

**Разработчики:**
- Email: dev@example.com
- GitHub: https://github.com/org/osi-language-server

**Сообщения об ошибках:**
- GitHub Issues: https://github.com/org/osi-language-server/issues

**Документация:**
- https://osi-language-server.readthedocs.io

---

**Конец документа**
