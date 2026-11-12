# Dan's Reading List

A personal podcast of spoken summaries and readings. GitHub Pages serves it from the `main` branch (site root):

- Site: <https://dtrundle31-create.github.io/reading-podcast/>
- Feed: <https://dtrundle31-create.github.io/reading-podcast/feed.xml>

Subscribe in Podcast Addict by adding that feed address as an RSS podcast. Each item's show notes include a link to the source article. A short welcome episode is already in the repository, so the feed has something to play as soon as Pages is on.

## Adding an episode

Put one narration per file in `scripts/`. Use a `.md` or `.txt` file whose name is lowercase letters, numbers, and hyphens, for example `scripts/2026-11-12-some-article.md`. The filename becomes the audio filename (`episodes/2026-11-12-some-article.mp3`).

```markdown
---
title: A spoken title for the episode
source_url: https://example.com/the-article
author: Original author or site
date: 2026-11-12
---

Write the words that should be spoken.

Short paragraphs. Plain sentences. This is narration, not an outline.
The show notes will include the source link from source_url.
```

| Field | Required | Meaning |
| --- | --- | --- |
| `title` | yes | Episode title in the feed and on the site |
| `source_url` | yes | Absolute `http` or `https` link to the article. Included in the episode description |
| `author` | no | Original author or publication, if you know it |
| `date` | yes | Publication date, `YYYY-MM-DD` |

`author` may be omitted. The other three fields are required. The text after the closing `---` is the script that will be read aloud.

Commit the script to `main` (a merged pull request is enough). You do not generate audio yourself.

## What the pipeline does

The workflow [Build podcast](.github/workflows/build-podcast.yml) runs when a push to `main` changes `scripts/`, and when someone starts it by hand from the Actions tab (`workflow_dispatch`).

For every script that does not already have a usable MP3, it synthesizes speech with [edge-tts](https://github.com/rany2/edge-tts) and the US English neural voice `en-US-AriaNeural`. That service needs no API key. Scripts longer than about 2,400 characters are split on sentence boundaries, spoken in chunks, and joined with ffmpeg into one MP3 under `episodes/`.

It then rewrites `feed.xml` (RSS 2.0 with iTunes tags) and `index.html`, and commits those files plus any new audio back to `main`. Existing episode files are left as they are. To re-record an episode, delete its MP3 and run the workflow again (push a script change, or use **Run workflow**). Removing a script drops that episode from the feed and deletes its MP3 on the next run.

The bot commit does not start another run: it uses the workflow `GITHUB_TOKEN` (which does not trigger workflows), it does not touch `scripts/`, and the message contains `[skip ci]`.

Artwork is `cover.png` (2000×2000). Replace that file if you want different cover art. It must stay a square PNG between 1400 and 3000 pixels on a side.

## GitHub settings

Two settings have to be on before Podcast Addict can fetch the feed. Both are one-time clicks in the repository settings.

1. **Pages.** Settings → Pages → Build and deployment → Source: **Deploy from a branch**. Branch: **main**, folder: **/ (root)**. Save. The site URL above is the project page for this repository.
2. **Actions write access.** Settings → Actions → General → Workflow permissions → **Read and write permissions**. Save. The workflow asks for `contents: write`, and GitHub only grants that if the repository allows Actions to write. If `main` is protected, let the GitHub Actions bot push to `main`, or the feed commit will be rejected.

No secrets or API keys are required. `.nojekyll` is present so Pages serves the files as they are committed.
