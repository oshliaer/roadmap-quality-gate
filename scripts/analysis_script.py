import asyncio
import datetime
import glob
import os
import re
import sys

import requests
from dotenv import load_dotenv
from github import Github
from gitingest import ingest_async
from google import genai
from markdownify import markdownify as md
from pyquery import PyQuery as pq

load_dotenv("./.env")  # basic variables
load_dotenv("./.env.local", override=True)

now = datetime.datetime.now()
date_string = now.strftime("%Y-%m-%d")


def get_env(name, dflt=None):
    value = os.getenv(name)
    if value is None or value == "":
        if dflt:
            return dflt
        raise ValueError(f"Required environment variable {name} is not set")
    return value


workspace_path = get_env("WORKSPACE_PATH", "/github/workspace")
google_api_key = get_env("GOOGLE_API_KEY")
github_token = get_env("GITHUB_TOKEN")
gw = get_env("GITHUB_WORKSPACE")


def get_roadmap_url():

    readme_paths = glob.glob(f"{workspace_path}/[rR][eE][aA][dD][mM][eE].[mM][dD]")

    if not readme_paths:
        raise ValueError("README.md file not found in the repository")

    for readme_path in readme_paths:
        with open(readme_path, "r", encoding="utf-8") as readme_file:
            readme_content = readme_file.read()
            roadmap_match = re.search(r"https://roadmap\.sh/projects/([a-zA-Z0-9_-]+)", readme_content)
            if roadmap_match:
                roadmap_url = roadmap_match.group(0)
                break

    if not roadmap_url:
        raise ValueError("Roadmap.sh project URL not found in README.md")

    print(f"Project URL found: {roadmap_url}")

    return roadmap_url


def generate_content_ai(google_api_key, date_string, system_prompt, rules, repo_analysis):
    client = genai.Client(api_key=google_api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                f"Analysis Date: {date_string}",
                f"## System Prompt\n{system_prompt}\n\n",
                f"## Project Rules\n{rules}\n\n",
                f"## Repository Analysis\n{repo_analysis}",
            ],
        )

        # Check for errors in the response
        if hasattr(response, "error") and response.error:
            raise ValueError(f"Content generation error: {response.error}")

        # Check for blocked content
        if not response.text.strip():
            raise ValueError("Model returned an empty response - content might have been blocked")

        print("Analysis successfully generated")

        return response.text

    except genai.types.generation.StopCandidateException as e:
        raise ValueError(f"Content was blocked by the security system: {str(e)}")

    except genai.types.generation.BlockedPromptException as e:
        raise ValueError(f"Request was blocked by the security system: {str(e)}")

    except genai.exceptions.GoogleGenerativeAIError as e:
        if "quota" in str(e).lower():
            raise ValueError(f"Gemini API quota exceeded: {str(e)}")
        elif "rate limit" in str(e).lower():
            raise ValueError(f"Gemini API rate limit exceeded: {str(e)}")
        else:
            raise ValueError(f"Google Generative AI error: {str(e)}")

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Network error when accessing Gemini API: {str(e)}")

    except Exception as e:
        raise ValueError(f"Unexpected error during content generation: {str(e)}")


async def main():
    try:
        roadmap_url = get_roadmap_url()

        # Step 1: Load project rules
        rules_response = requests.get(f"{roadmap_url}")
        rules_response.raise_for_status()

        doc = pq(rules_response.text)
        container_div = doc("div.container")

        if not container_div or container_div.html() is None:
            raise ValueError(f"Element div.container not found on the page {roadmap_url}")

        rules = md(container_div.html())

        print("Rules obtained")

        # Step 2: Repository analysis
        repo_analysis = await ingest_async(workspace_path)

        print("Repository content obtained")

        # Step 3: Load system prompt
        with open("/app/system_prompt.md", "r") as f:
            system_prompt = f.read()

        if not system_prompt:
            raise ValueError("No system prompt")

        print("System prompt content obtained")

        # Step 4: Analysis using Gemini

        analys = generate_content_ai(
            google_api_key=google_api_key,
            date_string=date_string,
            system_prompt=system_prompt,
            rules=rules,
            repo_analysis=repo_analysis,
        )

        print(analys)
        # genai.co.configure(api_key=google_api_key)
        # model = genai. GenerativeModel()

        # response = model.generate_content(
        #     f"## System Prompt\n{system_prompt}\n\n"
        #     f"## Project Rules\n{rules}\n\n"
        #     f"## Repository Analysis\n{repo_analysis}"
        # )

        # Step 5: Send comment
        g = Github(github_token)
        repo = g.get_repo(os.getenv("GITHUB_REPOSITORY"))

        print(repo.name)

        pr_number = int(os.getenv("GITHUB_REF").split("/")[2])

        print(pr_number)

        pr = repo.get_pull(pr_number)

        comment = f"## 🤖 AI Analysis Report\n\n{analys}"
        pr.create_issue_comment(comment)

    except Exception as e:
        print(f"::error:: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
