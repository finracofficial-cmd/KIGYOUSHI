# KIGYOUSHI — 栄枯盛衰ファイル 制作リポジトリ

YouTube チャンネル「栄枯盛衰ファイル」の動画を Claude Code で自動制作する。
企業・ブランド・産業の全盛と転落を、AI イラスト＋AI ナレーション＋字幕で語る20〜25分の横動画。

- 1本作る手順: `.claude/skills/eiko-episode/SKILL.md`（「動画を作って」で起動）
- 台本の型: `channel/STYLE_GUIDE.md` / 題材: `channel/TOPICS.md`
- エピソードの書式: `docs/EPISODE_FORMAT.md`
- チャンネル共通設定（名前・ロゴ・色・声・画風・尺）: `channel/channel.json`、字幕と文字の見た目: `channel/look.svs`
- 参考チャンネルの分析: `references/`（台本は型を学ぶためだけに使い、文章は写さない）

## 仕組み

```
episode.json ─┬─ tools/gen_images.py   OpenAI (gpt-image)      → assets/images/
              ├─ tools/gen_voice.py    ElevenLabs TTS          → assets/narration-raw/
              ├─ tools/prepare_assets.py 音量・背景・BGM       → assets/narration/, assets/derived/
              ├─ tools/build_svml.py   Hypit ソース生成         → episode.svml / episode.svrun
              ├─ hypit build           WhisperX で字幕と絵の切替を音声に合わせ、1920x1080 で書き出し
              ├─ tools/make_thumbnail.py / tools/youtube_meta.py
              └─ tools/review_sheets.py 確認用コマ一覧・音量
```
まとめて `tools/run_episode.sh <slug> [stage...]`。

## 環境（クラウドセッションは毎回まっさらなので、最初に整える）

```bash
npm install --global @hypit/hypit   # Hypit CLI
npm install                         # フォント（@fontsource-variable/noto-sans-jp ほか）
hypit programs up --endpoint whisperx.local   # 音声と台本の位置合わせ（初回は数GBのダウンロード）
hypit programs prepare --endpoint html.local  # 書き出し用ブラウザ
```
- WhisperX 準備で NLTK が「proxied fetch」を拒否したら、punkt_tab を
  `https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt_tab.zip` から取って
  `~/.local/state/hypit/programs/whisperx-whisperx.local-127.0.0.1%3A8765/nltk_data/tokenizers/` に展開してから再実行。
- `hypit transcribe` は1回の処理が5分を超えるとクライアント側でタイムアウトする。長い音声は
  `tools/chunk_audio.py` で4分以下に分けてから。
- API キーは環境変数 `OPENAI_API_KEY` / `ELEVENLABS_API_KEY`（クラウド環境の設定に保存済み）。
- 動画・音声・生成画像は git に入れない（.gitignore 済み）。episode.json と research.md はコミットする。
