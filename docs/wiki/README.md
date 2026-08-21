# GitHub Wiki - staging & publish guide

These pages are ready to publish to the repository wiki. GitHub wikis are a
separate git repo: **AI_Token_Saving.wiki.git**.

## Enable + publish (one-time, ~2 minutes)

1. **Enable the wiki** - repo Settings > General > Features > check
   *Wikis*. (No API can do this; the current token lacks repo-admin,
   so it must be a manual click.)
2. Clone the wiki repo:
   ```bash
   git clone https://github.com/remembervictorchatbot-vip/AI_Token_Saving.wiki.git
   cd AI_Token_Saving.wiki
   ```
3. Copy the staging pages in (they use GitHub-wiki filenames already):
   ```bash
   cp ../AI_Token_Saving/docs/wiki/*.md .
   git add . && git commit -m "docs: publish wiki" && git push
   ```
   (Authenticate with a token that has access to the wiki - a classic PAT
   with repo scope, or the browser session.)
4. Optional: update the sidebar by editing the *Sidebar* page in the wiki UI.

## Page list

| Page | Content |
|---|---|
| [[Home]] | What the project is + quick start |
| [[Installation]] | Universal path, WorkBuddy, Hermes, others |
| [[Architecture]] | Input pipeline, output economics, continuity |
| [[CLI-Reference]] | Every toks / crl command |
| [[Benchmark]] | Measured savings + reproduction |
| [[Skills]] | The four skills and their delegation model |
| [[DeepSeek-Harness-Adapter]] | Context filter wiring + env vars |
| [[Design-Principles]] | Kept vs rejected from three OSS projects |
| [[FAQ]] | Common questions |

## Keeping it in sync

Staging pages are maintained in-repo at docs/wiki/. When the README or
skills change, update the staging pages here and re-copy to the wiki repo.

Related: the [Obsidian vault](../obsidian/) holds the same knowledge as a
link-graph for study.