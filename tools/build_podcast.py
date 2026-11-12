#!/usr/bin/env python3
"""Generate episode MP3s, feed.xml, and index.html from scripts/."""

from __future__ import annotations

import asyncio
import html
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import edge_tts
from mutagen.mp3 import MP3

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
EPISODES_DIR = ROOT / "episodes"
FEED_PATH = ROOT / "feed.xml"
INDEX_PATH = ROOT / "index.html"
COVER_PATH = ROOT / "cover.png"

BASE_URL = "https://dtrundle31-create.github.io/reading-podcast"
# Natural US English neural voice suited to articles (edge-tts, no API key).
VOICE = "en-US-AriaNeural"
# Stay under the speech service's per-request byte limit and split on sentences.
MAX_CHUNK_CHARS = 2400
TITLE = "Dan's Reading List"
DESCRIPTION = (
    "Spoken summaries and readings of articles from Dan's reading list."
)
AUTHOR = "Dan"
LANGUAGE = "en-us"
CATEGORY = "Arts"
SUBCATEGORY = "Books"

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM_NS = "http://www.w3.org/2005/Atom"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"

EPISODE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)
ABBREVIATIONS = {
    "mr.",
    "mrs.",
    "ms.",
    "dr.",
    "prof.",
    "sr.",
    "jr.",
    "st.",
    "vs.",
    "e.g.",
    "i.e.",
    "u.s.",
    "u.k.",
    "a.m.",
    "p.m.",
    "fig.",
    "no.",
}


@dataclass
class Episode:
    script_path: Path
    episode_id: str
    title: str
    source_url: str
    author: str
    published: datetime
    body: str
    audio_path: Path
    duration: float = 0.0
    nbytes: int = 0


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def xml_text(value: str) -> str:
    return html.escape(value, quote=False)


def xml_attr(value: str) -> str:
    return html.escape(value, quote=True)


def cdata(value: str) -> str:
    return "<![CDATA[" + value.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def absolute_url(relative: str) -> str:
    return BASE_URL.rstrip("/") + "/" + relative.lstrip("/")


def parse_front_matter(path: Path) -> tuple[dict[str, str], str]:
    raw = path.read_text(encoding="utf-8-sig")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    match = FRONT_MATTER_RE.match(raw)
    if match is None:
        fail(f"{path.name}: file must start with --- front matter")
    meta: dict[str, str] = {}
    for line_number, line in enumerate(match.group(1).splitlines(), start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            fail(f"{path.name}:{line_number}: expected 'key: value'")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        meta[key] = value
    return meta, match.group(2).strip()


def require_http_url(path: Path, value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        fail(f"{path.name}: source_url must be an absolute http(s) URL")
    return value


def load_episode(path: Path) -> Episode:
    if not EPISODE_ID_RE.fullmatch(path.stem):
        fail(
            f"{path.name}: filename must be lowercase letters, numbers, and hyphens "
            "(example: 2026-11-11-welcome.md)"
        )
    meta, body = parse_front_matter(path)
    missing = [key for key in ("title", "source_url", "date") if not meta.get(key)]
    if missing:
        fail(f"{path.name}: missing front matter: {', '.join(missing)}")
    title = " ".join(meta["title"].split())
    if not title:
        fail(f"{path.name}: title is empty")
    try:
        day = datetime.strptime(meta["date"], "%Y-%m-%d")
    except ValueError:
        fail(f"{path.name}: date must be YYYY-MM-DD")
    published = day.replace(hour=12, tzinfo=timezone.utc)
    if not body:
        fail(f"{path.name}: narration is empty")
    return Episode(
        script_path=path,
        episode_id=path.stem,
        title=title,
        source_url=require_http_url(path, meta["source_url"]),
        author=" ".join(meta.get("author", "").split()),
        published=published,
        body=body,
        audio_path=EPISODES_DIR / f"{path.stem}.mp3",
    )


def load_episodes() -> list[Episode]:
    if not SCRIPTS_DIR.is_dir():
        fail("scripts/ directory is missing")
    paths = [
        path
        for path in sorted(SCRIPTS_DIR.iterdir())
        if path.is_file()
        and path.suffix.lower() in {".md", ".txt"}
        and not path.name.startswith((".", "_"))
        and path.name.lower() != "readme.md"
    ]
    episodes = [load_episode(path) for path in paths]
    ids = [episode.episode_id for episode in episodes]
    if len(ids) != len(set(ids)):
        fail("two scripts resolve to the same episode id")
    episodes.sort(key=lambda episode: (episode.published, episode.episode_id), reverse=True)
    return episodes


def split_sentences(paragraph: str) -> list[str]:
    text = re.sub(r"\s+", " ", paragraph).strip()
    if not text:
        return []
    parts: list[str] = []
    start = 0
    index = 0
    while index < len(text):
        if text[index] in ".!?" and index + 1 < len(text) and text[index + 1] == " ":
            cursor = index + 1
            while cursor < len(text) and text[cursor] == " ":
                cursor += 1
            word = text[start : index + 1]
            last = word.split()[-1].lower() if word.split() else ""
            if text[index] == "." and last in ABBREVIATIONS:
                index += 1
                continue
            nxt = text[cursor] if cursor < len(text) else ""
            if nxt.isupper() or nxt in {'"', "“", "'", "‘", "("}:
                parts.append(text[start : index + 1].strip())
                start = cursor
                index = cursor
                continue
        index += 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def split_long(sentence: str, limit: int) -> list[str]:
    if len(sentence) <= limit:
        return [sentence]
    pieces: list[str] = []
    buffer = ""
    for word in sentence.split():
        if len(word) > limit:
            if buffer:
                pieces.append(buffer)
                buffer = ""
            for offset in range(0, len(word), limit):
                pieces.append(word[offset : offset + limit])
            continue
        candidate = word if not buffer else f"{buffer} {word}"
        if buffer and len(candidate) > limit:
            pieces.append(buffer)
            buffer = word
        else:
            buffer = candidate
    if buffer:
        pieces.append(buffer)
    return pieces


def chunk_text(text: str, limit: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split narration into sentence-aligned chunks the speech service can take."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    sentences: list[str] = []
    for paragraph in re.split(r"\n\s*\n", normalized):
        sentences.extend(split_sentences(paragraph))
    chunks: list[str] = []
    buffer = ""
    for sentence in sentences:
        for piece in split_long(sentence, limit):
            candidate = piece if not buffer else f"{buffer} {piece}"
            if buffer and len(candidate) > limit:
                chunks.append(buffer)
                buffer = piece
            else:
                buffer = candidate
    if buffer:
        chunks.append(buffer)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def audio_ok(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 500:
        return False
    try:
        return mp3_duration_seconds(path) > 0.3
    except Exception:
        return False


def mp3_duration_seconds(path: Path) -> float:
    audio = MP3(path)
    length = float(audio.info.length or 0)
    if length <= 0:
        raise RuntimeError(f"{path.name} has no audio duration")
    return length


def format_duration(seconds: float) -> str:
    total = int(round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        fail(f"{path.name} is not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def check_cover() -> None:
    if not COVER_PATH.is_file():
        fail("cover.png is missing (podcast artwork, at least 1400x1400)")
    width, height = png_size(COVER_PATH)
    if width != height or width < 1400 or width > 3000:
        fail(f"cover.png must be a square PNG between 1400 and 3000 pixels (got {width}x{height})")


async def synthesize_chunk(text: str, dest: Path) -> None:
    last_error: Exception | None = None
    for attempt in range(1, 5):
        try:
            communicate = edge_tts.Communicate(
                text,
                VOICE,
                connect_timeout=20,
                receive_timeout=120,
            )
            await communicate.save(str(dest))
            if not audio_ok(dest):
                raise RuntimeError("synthesized file is not a playable MP3")
            return
        except Exception as exc:
            last_error = exc
            dest.unlink(missing_ok=True)
            if attempt == 4:
                break
            wait = 2 ** (attempt - 1)
            print(
                f"  attempt {attempt} failed ({exc}); retrying in {wait}s",
                file=sys.stderr,
            )
            await asyncio.sleep(wait)
    fail(f"text-to-speech failed for a chunk: {last_error}")


def concat_mp3(parts: list[Path], dest: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        fail("ffmpeg is required to join a long narration into one MP3")
    dest.parent.mkdir(parents=True, exist_ok=True)
    list_path = dest.with_name(f".{dest.stem}.concat.txt")
    tmp_out = dest.with_name(f".{dest.stem}.tmp.mp3")
    try:
        lines = []
        for part in parts:
            escaped = str(part.resolve()).replace("'", r"'\''")
            lines.append(f"file '{escaped}'")
        list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        try:
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(list_path),
                    "-c:a",
                    "libmp3lame",
                    "-b:a",
                    "48k",
                    "-ar",
                    "24000",
                    "-ac",
                    "1",
                    str(tmp_out),
                ],
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            fail(f"ffmpeg could not join audio for {dest.name} (exit {exc.returncode})")
        if not audio_ok(tmp_out):
            fail(f"joined audio for {dest.name} is not a playable MP3")
        os.replace(tmp_out, dest)
    finally:
        list_path.unlink(missing_ok=True)
        tmp_out.unlink(missing_ok=True)


async def synthesize_episode(episode: Episode) -> None:
    chunks = chunk_text(episode.body)
    if not chunks:
        fail(f"{episode.script_path.name}: narration is empty")
    label = "chunk" if len(chunks) == 1 else "chunks"
    print(
        f"synthesize {episode.audio_path.name} "
        f"({len(chunks)} {label}, voice {VOICE})"
    )
    with tempfile.TemporaryDirectory(prefix="episode-") as tmp:
        tmpdir = Path(tmp)
        parts: list[Path] = []
        for index, chunk in enumerate(chunks, start=1):
            part = tmpdir / f"chunk-{index:03d}.mp3"
            if len(chunks) > 1:
                print(f"  chunk {index}/{len(chunks)} ({len(chunk)} characters)")
            await synthesize_chunk(chunk, part)
            parts.append(part)
        if len(parts) == 1:
            episode.audio_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_out = episode.audio_path.with_name(f".{episode.audio_path.stem}.tmp.mp3")
            shutil.copyfile(parts[0], tmp_out)
            os.replace(tmp_out, episode.audio_path)
        else:
            concat_mp3(parts, episode.audio_path)


async def ensure_audio(episodes: list[Episode]) -> None:
    EPISODES_DIR.mkdir(parents=True, exist_ok=True)
    # Oldest first so a failure leaves newer scripts still waiting, in order.
    for episode in sorted(episodes, key=lambda item: (item.published, item.episode_id)):
        if audio_ok(episode.audio_path):
            print(f"keep {episode.audio_path.relative_to(ROOT)}")
            continue
        await synthesize_episode(episode)


def remove_orphan_audio(episodes: list[Episode]) -> None:
    keep = {episode.episode_id for episode in episodes}
    if not EPISODES_DIR.is_dir():
        return
    for path in sorted(EPISODES_DIR.glob("*.mp3")):
        if path.stem not in keep:
            print(f"remove orphan {path.relative_to(ROOT)}")
            path.unlink()


def annotate_audio(episodes: list[Episode]) -> None:
    for episode in episodes:
        episode.duration = mp3_duration_seconds(episode.audio_path)
        episode.nbytes = episode.audio_path.stat().st_size


def narration_html(episode: Episode) -> str:
    paragraphs = []
    for paragraph in re.split(r"\n\s*\n", episode.body.strip()):
        text = " ".join(paragraph.split())
        if text:
            paragraphs.append(f"<p>{html.escape(text, quote=False)}</p>")
    source = html.escape(episode.source_url, quote=True)
    paragraphs.append(
        f'<p>Source: <a href="{source}">{html.escape(episode.source_url, quote=False)}</a></p>'
    )
    if episode.author:
        paragraphs.append(f"<p>Author: {html.escape(episode.author, quote=False)}</p>")
    return "\n".join(paragraphs)


def plain_summary(episode: Episode) -> str:
    text = " ".join(episode.body.split())
    if len(text) > 3600:
        text = text[:3599].rsplit(" ", 1)[0] + "..."
    lines = [text, f"Source: {episode.source_url}"]
    if episode.author:
        lines.append(f"Author: {episode.author}")
    return "\n".join(lines)


def render_item(episode: Episode) -> str:
    media_url = absolute_url(f"episodes/{episode.episode_id}.mp3")
    description = narration_html(episode)
    summary = plain_summary(episode)
    author = episode.author or AUTHOR
    lines = [
        "    <item>",
        f"      <title>{xml_text(episode.title)}</title>",
        f"      <link>{xml_text(episode.source_url)}</link>",
        f"      <description>{cdata(description)}</description>",
        f"      <content:encoded>{cdata(description)}</content:encoded>",
        f"      <itunes:summary>{cdata(summary)}</itunes:summary>",
        f"      <itunes:author>{xml_text(author)}</itunes:author>",
        (
            f'      <enclosure url="{xml_attr(media_url)}" '
            f'length="{episode.nbytes}" type="audio/mpeg"/>'
        ),
        f'      <guid isPermaLink="true">{xml_text(media_url)}</guid>',
        f"      <pubDate>{format_datetime(episode.published, usegmt=True)}</pubDate>",
        f"      <itunes:duration>{format_duration(episode.duration)}</itunes:duration>",
        "      <itunes:explicit>false</itunes:explicit>",
        "      <itunes:episodeType>full</itunes:episodeType>",
        "    </item>",
    ]
    return "\n".join(lines)


def render_feed(episodes: list[Episode]) -> str:
    newest = max(episode.published for episode in episodes)
    home = absolute_url("")
    # absolute_url("") yields a trailing slash because of the join above.
    if not home.endswith("/"):
        home += "/"
    cover = absolute_url("cover.png")
    feed = absolute_url("feed.xml")
    items = "\n".join(render_item(episode) for episode in episodes)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="{ITUNES_NS}"
     xmlns:content="{CONTENT_NS}"
     xmlns:atom="{ATOM_NS}">
  <channel>
    <title>{xml_text(TITLE)}</title>
    <link>{xml_text(home)}</link>
    <description>{xml_text(DESCRIPTION)}</description>
    <language>{LANGUAGE}</language>
    <lastBuildDate>{format_datetime(newest, usegmt=True)}</lastBuildDate>
    <generator>reading-podcast</generator>
    <atom:link href="{xml_attr(feed)}" rel="self" type="application/rss+xml"/>
    <itunes:author>{xml_text(AUTHOR)}</itunes:author>
    <itunes:summary>{xml_text(DESCRIPTION)}</itunes:summary>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    <itunes:image href="{xml_attr(cover)}"/>
    <itunes:category text="{xml_attr(CATEGORY)}">
      <itunes:category text="{xml_attr(SUBCATEGORY)}"/>
    </itunes:category>
    <image>
      <url>{xml_text(cover)}</url>
      <title>{xml_text(TITLE)}</title>
      <link>{xml_text(home)}</link>
    </image>
{items}
  </channel>
</rss>
"""


def format_human_date(published: datetime) -> str:
    return f"{published.strftime('%B')} {published.day}, {published.year}"


def render_index(episodes: list[Episode]) -> str:
    feed = absolute_url("feed.xml")
    cards = []
    for episode in episodes:
        author = (
            f"\n      <p class=\"meta\">{html.escape(episode.author, quote=False)}</p>"
            if episode.author
            else ""
        )
        source = html.escape(episode.source_url, quote=True)
        cards.append(
            f"""    <article>
      <h3>{html.escape(episode.title, quote=False)}</h3>
      <p class="meta">{html.escape(format_human_date(episode.published), quote=False)}</p>{author}
      <p><a href="{source}">Source</a></p>
      <audio controls preload="metadata" src="episodes/{html.escape(episode.episode_id, quote=True)}.mp3"></audio>
    </article>"""
        )
    listing = "\n".join(cards)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(TITLE, quote=False)}</title>
  <link rel="alternate" type="application/rss+xml" title="{html.escape(TITLE, quote=True)}" href="feed.xml">
  <style>
    :root {{ color-scheme: light; }}
    body {{
      margin: 0 auto;
      max-width: 40rem;
      padding: 2rem 1.25rem 4rem;
      color: #1b2838;
      background: #f6f1e8;
      font: 1.05rem/1.5 Georgia, "Iowan Old Style", "Palatino Linotype", serif;
    }}
    h1 {{ font-size: 2rem; line-height: 1.2; margin-bottom: 0.25rem; }}
    h2 {{ font-size: 1.35rem; margin: 2rem 0 0; }}
    h3 {{ font-size: 1.25rem; margin: 0 0 0.25rem; }}
    a {{ color: #9a4322; }}
    img.cover {{ width: 8rem; height: 8rem; display: block; margin: 1.25rem 0; }}
    .feed {{
      padding: 0.75rem 1rem;
      background: #fff;
      border: 1px solid #e2d8c8;
      overflow-wrap: anywhere;
    }}
    article {{
      margin-top: 1.75rem;
      padding-top: 1.25rem;
      border-top: 1px solid #e2d8c8;
    }}
    .meta {{ margin: 0; color: #5c6b7a; font-family: "Segoe UI", sans-serif; font-size: 0.9rem; }}
    audio {{ width: 100%; margin-top: 0.75rem; }}
  </style>
</head>
<body>
  <h1>{html.escape(TITLE, quote=False)}</h1>
  <p>{html.escape(DESCRIPTION, quote=False)}</p>
  <img class="cover" src="cover.png" alt="Cover art for {html.escape(TITLE, quote=True)}">
  <p>Subscribe in Podcast Addict with this feed address:</p>
  <p class="feed"><a href="{html.escape(feed, quote=True)}">{html.escape(feed, quote=False)}</a></p>
  <h2>Episodes</h2>
{listing}
</body>
</html>
"""


def write_outputs(episodes: list[Episode]) -> None:
    feed = render_feed(episodes)
    if not feed.endswith("\n"):
        feed += "\n"
    page = render_index(episodes)
    if not page.endswith("\n"):
        page += "\n"
    FEED_PATH.write_text(feed, encoding="utf-8", newline="\n")
    INDEX_PATH.write_text(page, encoding="utf-8", newline="\n")
    print(f"wrote {FEED_PATH.relative_to(ROOT)} ({len(episodes)} episodes)")
    print(f"wrote {INDEX_PATH.relative_to(ROOT)}")


def expect(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def validate_output(episodes: list[Episode]) -> None:
    check_cover()
    expect(FEED_PATH.is_file(), "feed.xml was not written")
    raw_feed = FEED_PATH.read_text(encoding="utf-8")
    expect(f'xmlns:itunes="{ITUNES_NS}"' in raw_feed, "itunes namespace missing")
    expect('xmlns:content="http://purl.org/rss/1.0/modules/content/"' in raw_feed, "content namespace missing")
    expect(f'xmlns:atom="{ATOM_NS}"' in raw_feed, "atom namespace missing")
    root = ET.fromstring(raw_feed)
    expect(root.tag == "rss" and root.attrib.get("version") == "2.0", "feed is not RSS 2.0")
    channel = root.find("channel")
    expect(channel is not None, "channel missing")
    assert channel is not None
    expect(channel.findtext("title") == TITLE, "channel title mismatch")
    expect(channel.findtext("description") == DESCRIPTION, "channel description mismatch")
    expect((channel.findtext("link") or "").startswith(BASE_URL), "channel link is not absolute")
    image = channel.find(f"{{{ITUNES_NS}}}image")
    expect(image is not None, "itunes:image missing")
    assert image is not None
    expect(image.attrib.get("href") == absolute_url("cover.png"), "itunes:image href mismatch")
    category = channel.find(f"{{{ITUNES_NS}}}category")
    expect(category is not None and category.attrib.get("text") == CATEGORY, "itunes:category missing")
    expect(channel.findtext(f"{{{ITUNES_NS}}}explicit") == "false", "itunes:explicit missing")
    self_link = channel.find(f"{{{ATOM_NS}}}link")
    expect(
        self_link is not None and self_link.attrib.get("href") == absolute_url("feed.xml"),
        "atom:link self href mismatch",
    )
    items = channel.findall("item")
    expect(len(items) == len(episodes), "feed item count does not match scripts")
    page = INDEX_PATH.read_text(encoding="utf-8")
    expect(absolute_url("feed.xml") in page, "index is missing the feed URL")
    for episode, item in zip(episodes, items):
        media_url = absolute_url(f"episodes/{episode.episode_id}.mp3")
        expect(item.findtext("title") == episode.title, f"{episode.episode_id}: title mismatch")
        enclosure = item.find("enclosure")
        expect(enclosure is not None, f"{episode.episode_id}: enclosure missing")
        assert enclosure is not None
        expect(enclosure.attrib.get("url") == media_url, f"{episode.episode_id}: enclosure url")
        expect(enclosure.attrib.get("type") == "audio/mpeg", f"{episode.episode_id}: enclosure type")
        expect(
            enclosure.attrib.get("length") == str(episode.audio_path.stat().st_size),
            f"{episode.episode_id}: enclosure length does not match the file",
        )
        expect(item.findtext("guid") == media_url, f"{episode.episode_id}: guid mismatch")
        expect(item.findtext("pubDate"), f"{episode.episode_id}: pubDate missing")
        expect(
            item.findtext(f"{{{ITUNES_NS}}}duration") == format_duration(episode.duration),
            f"{episode.episode_id}: itunes:duration mismatch",
        )
        description = item.findtext("description") or ""
        escaped_source = html.escape(episode.source_url, quote=True)
        expect(
            episode.source_url in description or escaped_source in description,
            f"{episode.episode_id}: description lacks source link",
        )
        expect(episode.title in page, f"index is missing {episode.title}")
        expect(audio_ok(episode.audio_path), f"{episode.episode_id}: MP3 failed validation")
    print("validated feed.xml, index.html, cover.png, and episode audio")


def main() -> None:
    check_cover()
    episodes = load_episodes()
    if not episodes:
        fail("no narration scripts found in scripts/")
    asyncio.run(ensure_audio(episodes))
    remove_orphan_audio(episodes)
    annotate_audio(episodes)
    write_outputs(episodes)
    validate_output(episodes)


if __name__ == "__main__":
    main()
