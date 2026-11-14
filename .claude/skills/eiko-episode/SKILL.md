---
name: eiko-episode
description: 栄枯盛衰ファイルの動画を1本、テーマ選びから完成（mp4・サムネイル・概要欄）まで自動で作る。企業や産業の興亡を描く20〜25分の解説動画。「動画を作って」「次の回を作って」「○○の回を作って」などで使う。
---

# 栄枯盛衰ファイル: 1本つくる

企業・ブランド・産業の「全盛と転落」を、謎のつかみ → 5章前後の時系列 → 結論 → 参考資料の型で語る
20〜25分の横動画を、止まらずに最後まで作る。ユーザーが題材を指定していればそれを使い、
なければ自分で選ぶ。

最初に必ず読むもの:
- `channel/STYLE_GUIDE.md` — 台本の型（参考チャンネルの台本から抽出した構成・文体・リズム）
- `channel/TOPICS.md` — 題材の選び方、過去に作った回、候補リスト
- `docs/EPISODE_FORMAT.md` — episode.json の書き方

## 1. 題材を決める（指定がなければ）

`channel/TOPICS.md` の基準で候補を5つ以上挙げ、WebSearch で資料の量と「謎」の強さを確かめて1つ選ぶ。
選んだ題材・理由・slug を TOPICS.md の「制作済み・制作中」に書き足す。過去回と同じ題材は選ばない。

## 2. 調べる → `episodes/<slug>/research.md`

WebSearch / WebFetch で複数の資料を読む。優先順: 企業の公式沿革・IR資料・有価証券報告書 → 新聞・経済誌の記事
→ 書籍・専門サイト → Wikipedia（入口としてのみ）。
- 年表（年月・出来事・数字）を作り、各行に出典 URL を付ける。
- 資料で食い違う数字は両方書き、どれを使うか決めて理由を書く。
- 「なぜ消えた／なぜ転落した」の答えを、複数の要因として整理する（1つの犯人にしない）。
- 視聴者が知っている製品・CM・店・出来事など、懐かしさのフックを集める。

## 3. 台本を書く → `episodes/<slug>/episode.json`

STYLE_GUIDE.md の型どおりに書く。数字・年・社名・人名は research.md にあるものだけを使う。
- 尺の目安: ナレーション本文 6,000〜7,000字（参考動画は約6,700字で24.7分、毎分約270字）。
- つかみ（`op`）は STYLE_GUIDE の型 A/B/C から題材に合うものを選ぶ（毎回同じにしない）。章は5〜6つ。
  章タイトルは答えではなく、問い・場面・人物の言葉にする。
- 実在の人物や不祥事を扱うときは STYLE_GUIDE「不祥事・実在の人物を扱うときの必須ルール」を守る。
- block（絵1枚）ごとに 3〜8 行。絵は30〜60秒もつ場面にする。全体で30〜40枚。
- 数字と英字には `[表示|よみ]` で読みを付ける。繰り返す固有名詞は `readings` へ。
- images の prompt は英語で、その block の内容が一目でわかる具体的な場面
  （時代・場所・人物の服装・製品の形・光）を2〜4文で。画風は書かない（共通設定が足される）。
  実在の人物名は書かず、描写で表す。
- `credits.sources` に research.md の主要な出典を「発行元『タイトル』（年）」の形で並べる。
- `thumbnail`、`youtube_title`、`description`、`tags` も書く（書式は docs/EPISODE_FORMAT.md）。
  - `youtube_title` は「〇〇はなぜ消えた？＋具体的な一言（数字・意外な事実）」の形を基本にする。
  - `description` は概要欄の中身。文献が大事なので、`sources_summary`・`main_sources` と、
    research.md で実際に開いた主要な URL を `reference_urls` に10〜16件入れる。`notes` には数字の食い違いや
    同名の別法人など、視聴者が誤解しやすい点を確かめた事実だけで書く。

書いたら自分で読み直す:
1. 全ての数字・年月を research.md と照合する。
2. `tools/run_episode.sh <slug> lint` を通す。
3. STYLE_GUIDE.md のチェックリストで台本を見直す。

## 4. 生成して組み立てる

```bash
tools/run_episode.sh <slug>
```

lint → images（OpenAI）→ voice（ElevenLabs）→ assets → svml → render（Hypit + WhisperX）
→ thumb → meta → review の順に進む。有料ステージは同じ prompt / 本文なら再生成しない。
途中で失敗したら、そのステージから再実行できる（例: `tools/run_episode.sh <slug> render thumb meta review`）。

- 画像が安全フィルタで拒否されたら、その prompt を穏当な描写に直して `images` だけ再実行。
- `voice` は絵1枚ぶんずつ ElevenLabs で読ませ、WhisperX で聞き直して台本と読みを照合する。
  `out/voice-report.md` に ⚠ が付いたブロックは、「気になる箇所」を見て該当語に `[表示|よみ]` を足し
  （何度も出る語は `readings`、全回共通なら `channel/yomi.json`）、`voice` から再実行する（変わったブロックだけ作り直される）。
  ⚠ が残ったまま先へ進まない。認識側の揺れ（例: せいすい/せいずい）だけなら進めてよい。
- render は章ごとのパートに分けて書き出す（1パート20〜35分、全体で2時間半ほど）。バックグラウンドで実行し、
  ツールの時間制限で止まったら `tools/run_episode.sh <slug> render thumb meta review` をもう一度実行する
  （書き出し済みのパートは飛ばす。途中だったパートの build は Worker で続いていて、再実行するとその終わりを待って
  書き出すので、最初からやり直しにはならない）。
- render の失敗は `hypit inspect <build-id>` で原因を見る。WhisperX が止まっていたら
  `hypit programs up --endpoint whisperx.local`。メモリ不足で落ちやすいので、書き出し中は重い処理を並行させない。

## 5. 確認する

`out/review/overview-*.jpg`（10秒ごとのコマ）と `out/review/loudness.txt` を見る。
- 字幕がはみ出していないか、2行に収まっているか、テーマ帯・ロゴと重なっていないか。
- 絵が内容と合っているか、崩れた文字・不自然な手や顔が目立たないか（目立つ絵は prompt を直して再生成）。
- 章カード・タイトル画面・エンドロールが出ているか。
- 音量: Integrated が -16〜-14 LUFS 付近、True peak が -1 dBTP 以下。
問題があれば直して該当ステージから再実行する。

## 6. 渡す

`out/<slug>.mp4`、`out/thumbnail.png`、`out/description.txt`（概要欄）と `out/youtube.txt`（タイトル・タグ）の場所と、題材の要点・尺・使った画像枚数と
ElevenLabs の文字数を短く報告する。動画ファイルは git に入れない（.gitignore 済み）。
episode.json・research.md・TOPICS.md の更新はコミットしてプッシュする。
