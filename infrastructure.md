```mermaid
graph TB
    subgraph "Telegram Bot"
        TB[Telegram Bot API]
        WB[Webhook Server]
    end

    subgraph "База данных"
        DB[(SQLite Database)]
        subgraph "Таблицы"
            CH[Channels]
            PS[Posts]
            CM[Comments]
            LN[Links]
            LC[Link Clicks]
            GS[Group Stats]
        end
    end

    subgraph "Аналитика"
        SA[Sentiment Analyzer]
        LS[Link Shortener]
    end

    subgraph "Внешние сервисы"
        TG[Telegram API]
        EX[External Links]
    end

    %% Связи
    TB --> WB
    WB --> DB
    DB --> CH
    DB --> PS
    DB --> CM
    DB --> LN
    DB --> LC
    DB --> GS
    
    PS --> SA
    CM --> SA
    LN --> LS
    
    TB --> TG
    LS --> EX

    %% Стили
    classDef default fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#01579b;
    classDef database fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#2e7d32;
    classDef external fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#e65100;
    
    class DB database;
    class TG,EX external;
```

# Инфраструктура проекта

## Основные компоненты

### 1. Telegram Bot
- **Telegram Bot API**: Основной интерфейс взаимодействия с пользователями
- **Webhook Server**: Сервер для обработки входящих webhook-запросов от Telegram

### 2. База данных (SQLite)
- **Channels**: Информация о каналах
- **Posts**: Посты и их метаданные
- **Comments**: Комментарии с оценкой настроения
- **Links**: Ссылки и их сокращения
- **Link Clicks**: Статистика кликов по ссылкам
- **Group Stats**: Статистика групп

### 3. Аналитика
- **Sentiment Analyzer**: Анализ настроения в постах и комментариях
- **Link Shortener**: Сервис сокращения ссылок

### 4. Внешние сервисы
- **Telegram API**: API для взаимодействия с Telegram
- **External Links**: Внешние ссылки и их обработка

## Взаимодействие компонентов

1. Telegram Bot получает команды от пользователей через Telegram API
2. Webhook Server обрабатывает входящие запросы
3. Данные сохраняются в SQLite базе данных
4. Sentiment Analyzer анализирует тексты постов и комментариев
5. Link Shortener обрабатывает ссылки и собирает статистику
6. Вся статистика и аналитика доступна через команды бота 