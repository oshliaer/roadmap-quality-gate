# Roadmap Quality Gate

This action performs an AI-powered analysis of your repository using Google Gemini and provides feedback based on roadmap.sh project rules.

## Inputs

## `google_api_key`

**Required** Google Gemini API Key for AI analysis.

## `github_token`

**Required** GitHub Token for repository access and commenting on PRs.

## `roadmap_url`

**Required** Roadmap.sh project URL to fetch rules from.

## Outputs

## `analysis_report`

The complete analysis report generated by Gemini AI.

## Example usage

```yaml
- name: Run Roadmap Quality Analysis
  uses: oshliaer/roadmap-quality-gate@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    roadmap_url: 'https://roadmap.sh/projects/your-project'
```
