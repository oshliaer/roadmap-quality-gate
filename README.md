# Roadmap Quality Gate

Вот структура проекта:

## 1. Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей
RUN apt-get update && apt-get install -y git

# Копирование файлов
COPY requirements.txt .
COPY scripts/analysis_script.py ./scripts/
COPY system_prompt.md .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Точка входа для Action
ENTRYPOINT ["python", "/app/scripts/analysis_script.py"]
```

## 2. action.yml

```yaml
name: 'Project Analysis Bot'
description: 'AI-powered repository analysis using Gemini'
branding:
  icon: 'activity'
  color: 'blue'

inputs:
  google_api_key:
    description: 'Google Gemini API Key'
    required: true
  github_token:
    description: 'GitHub Token'
    required: true
  roadmap_url:
    description: 'Roadmap.sh project URL'
    required: false

runs:
  using: 'docker'
  image: 'Dockerfile'
  args:
    - ${{ inputs.google_api_key }}
    - ${{ inputs.github_token }}
    - ${{ inputs.roadmap_url }}
```

## 3. Обновленный workflow (.github/workflows/analysis.yml)

```yaml
name: Project Analysis Bot

on:
  pull_request:
    branches: [master]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Extract Roadmap URL
      id: extract-url
      run: |
        URL=$(grep -oE 'https://roadmap\.sh/projects/[^\s\/]+' README.md || echo '')
        echo "roadmap_url=$URL" >> $GITHUB_OUTPUT

    - name: Run Analysis
      if: steps.extract-url.outputs.roadmap_url != ''
      uses: ./
      with:
        google_api_key: ${{ secrets.GOOGLE_API_KEY }}
        github_token: ${{ secrets.GITHUB_TOKEN }}
        roadmap_url: ${{ steps.extract-url.outputs.roadmap_url }}
```

## 4. Обновленный analysis_script.py

```python
import os
import sys
import requests
from gitingest.parser import parse_repository
import google.generativeai as genai
from github import Github

def main():
    try:
        # Получаем аргументы
        google_api_key = sys.argv[1]
        github_token = sys.argv[2]
        roadmap_url = sys.argv[3]

        # Шаг 1: Загрузка правил проекта
        rules_response = requests.get(f"{roadmap_url}/rules")
        rules_response.raise_for_status()
        rules = rules_response.text

        # Шаг 2: Анализ репозитория
        repo_analysis = parse_repository(os.getcwd())

        # Шаг 3: Загрузка системного промпта
        with open('/app/system_prompt.md', 'r') as f:
            system_prompt = f.read()

        # Шаг 4: Анализ через Gemini
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content(
            f"## System Prompt\n{system_prompt}\n\n"
            f"## Project Rules\n{rules}\n\n"
            f"## Repository Analysis\n{repo_analysis}"
        )

        # Шаг 5: Отправка комментария
        g = Github(github_token)
        repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
        pr_number = int(os.getenv('GITHUB_REF').split('/')[2])
        pr = repo.get_pull(pr_number)
        
        comment = f"## 🤖 AI Analysis Report\n\n{response.text}"
        pr.create_issue_comment(comment)

    except Exception as e:
        print(f"::error:: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Структура проекта

```
.
├── .github
│   └── workflows
│       └── analysis.yml
├── scripts
│   └── analysis_script.py
├── action.yml
├── Dockerfile
├── system_prompt.md
└── requirements.txt
```

## Как использовать

1. Соберите Docker-образ локально (опционально):

```bash
docker build -t repo-analyzer .
```

1. Запустите тестирование

```bash
docker run -e GITHUB_REPOSITORY=your/repo -e GITHUB_REF=refs/pull/1/merge \
  -v $(pwd):/app repo-analyzer:latest \
  your_google_api_key your_github_token https://roadmap.sh/projects/your-project
```

## Ключевые особенности

1. Полная изоляция зависимостей в Docker-контейнере
2. Возможность публикации Action в GitHub Marketplace
3. Параметризация через входные аргументы
4. Автоматическая обработка ошибок с аннотациями
5. Компактный образ (~300MB с учетом Python и зависимостей)

## Чтобы опубликовать Action

1. Создайте репозиторий с названием `repo-analyzer-action`
2. Добавьте тег версии (например `v1.0.0`)
3. Настройте Marketplace publication в настройках репозитория

## Для использования в других репозиториях

```yaml
- name: Run Analysis
  uses: your-username/repo-analyzer-action@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    roadmap_url: ${{ steps.extract-url.outputs.roadmap_url }}
```
