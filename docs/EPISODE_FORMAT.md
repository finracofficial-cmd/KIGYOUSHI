# episode.json の書き方

1本の動画は `episodes/<slug>/episode.json` 1ファイルで決まる。ここから画像・ナレーション・
Hypit のソース（`episode.svml`）・サムネイルがすべて生成される。`<slug>` は英小文字とハイフン（例: `sanyo`）。

```jsonc
{
  "slug": "sanyo",
  "youtube_title": "三洋電機はなぜ消えた？倒産していないのに名前が消えた理由",
  "youtube_description": "概要欄の本文（章のタイムスタンプは自動で追記される）",
  "tags": ["三洋電機", "企業史", "パナソニック"],

  // 本編中ずっと左上に出るテーマ帯（2段）
  "theme": { "main": "なぜ「SANYO」の名前は消えたのか？", "sub": "売上2兆円企業「三洋電機」の興亡" },

  // 繰り返し出る固有名詞の読み。字幕は左、ナレーションは右で読まれる
  "readings": { "井植歳男": "いうえとしお", "SANYO": "さんよー" },

  // 絵。キーは英小文字とハイフン。prompt は英語で場面だけを書く（画風はチャンネル共通設定が足される）
  "images": {
    "store-aisle": { "prompt": "A crowded Japanese electronics store aisle in the early 2000s ..." }
  },

  // 本編。opening（つかみ）1つ + chapter（章）5つ前後
  "segments": [
    { "id": "op", "kind": "opening", "blocks": [
      { "image": "store-aisle", "lines": ["洗濯機、冷蔵庫、テレビ、エアコン。", "..."] }
    ]},
    { "id": "ch01", "kind": "chapter", "title": "洗濯機のサンヨー", "blocks": [
      { "image": "bicycle-lamp", "lines": ["三洋電機の創業は、[1947年|せんきゅうひゃくよんじゅうななねん]。"] },
      { "image": "washboard",    "lines": ["当時、日本の家庭では……"] }
    ]}
  ],

  // 最後に流れる参考資料（エンドロール）とその背景の絵
  "credits": { "image": "solar-ark", "sources": ["パナソニック「三洋電機株式会社 会社概要」", "..."] },

  // サムネイル。image は images のキー。lines は2〜3行（最後の行は赤帯）
  "thumbnail": { "image": "sign-removal", "lines": ["三洋電機", "なぜ消えた？", "倒産してないのに…"] },

  // 任意: タイトル画面の背景（省略時は最初の絵）、BGM ファイル（省略時は channel/bgm/ の先頭）
  "ident_image": "store-aisle",
  "bgm": "assets/bgm.mp3"
}
```

## ルール

- **lines の1要素 = 字幕1枚。** 64字以内、1〜2文。読み終わるまで画面に出る。
- **block = 絵1枚。** 絵は block の最初の文が読まれ始める瞬間にクロスフェードで切り替わる。
  参考動画と同じく1枚を30〜60秒見せるので、1 block は3〜8行が目安。
- **数字と英字には必ず読みを付ける。** `[表示|よみ]` の形。例: `[2兆5000億円|にちょうごせんおくえん]`、
  `[Xacti|ざくてぃ]`。読みが無いと `tools/run_episode.sh <slug> lint` が止める。
  繰り返し出る名前は `readings` にまとめれば本文に書かなくてよい。
- 「」は字幕にそのまま出る。`[` `]` `|` は読み指定の記号なので本文には使わない。
- 章の `id` は `ch01`〜。`op` はつかみ（タイトル帯なし、最後にタイトル画面が入る）。
- 画像 prompt には実在の人物名を書かない（「1940年代の日本人経営者」のように描写する）。
  実在ブランド名は必要なときだけ短く書く（看板・製品の文字は崩れやすい）。

## 生成されるもの

| パス | 中身 |
| --- | --- |
| `assets/images/<id>.png` | OpenAI で生成した絵（`.prompt.txt` が隣にあり、prompt が同じなら再生成しない） |
| `assets/narration-raw/<seg>.mp3` | ElevenLabs のナレーション（`.txt` が同じなら再生成しない） |
| `assets/narration/<seg>.m4a` | 音量をそろえたナレーション |
| `assets/derived/` | タイトル画面・エンドロールの背景、BGM ベッド |
| `episode.svml` / `episode.svrun` | Hypit のソース（自動生成。手で直さない） |
| `out/<slug>.mp4` | 完成動画 |
| `out/thumbnail.png` | サムネイル |
| `out/youtube.txt` | タイトル・概要欄（章タイムスタンプ付き）・タグ |
| `out/review/` | 確認用のコマ一覧と音量測定 |
