"""Builds episodes/hands/episode.json (kept beside the episode so the script stays editable)."""
import json
import re
from pathlib import Path

images = {
  "op-rain-closing": "The entrance of an old multi-level store on a sloping street in Shibuya, Tokyo, at night in the rain in November 2026: a row of staff in green aprons bowing deeply in front of a half-closed shutter, a crowd of people with umbrellas applauding. Emotional farewell. Faces not identifiable. No logos or readable text.",
  "op-thanks-sign": "Present-day Tokyo in November 2026, night, rain: an eight-story 1970s concrete store building at a Y-shaped sloping intersection in Shibuya, with a very tall vertical green sign panel on its corner glowing softly. Modern 2020s cars, LED street lights, contemporary young people in raincoats holding clear plastic umbrellas and smartphones, looking up at the sign. Modern glass buildings in the background. Emotional, nostalgic mood. The letters on the sign are not legible. No trams, no vintage cars, no logos.",
  "op-mall-store": "A bright, modern, compact lifestyle goods store inside a Japanese shopping mall in 2026: neat shelves of stationery, cosmetics and household goods, green accents, a few shoppers. Clean and cheerful. No logos or readable text.",
  "op-question": "The interior of an empty old store at night: a narrow spiral of short staircases connecting split-level floors, worn wooden handrails painted green, dim lights, empty shelves. Quiet, mysterious mood. No readable text.",
  "udagawa-1972": "An awkward L-shaped vacant lot on a steep slope in a back street of Shibuya, Tokyo, in 1972, used as a small parking lot, an old wooden church building nearby, a few cars from the early 1970s. Muted, nostalgic colors. No readable text.",
  "planning-1975": "A Japanese corporate meeting room in 1975: young planners in shirts and ties lay out hammers, saws, paint cans, model kits and wood samples on a long table, papers and ashtrays, excited discussion. Faces not in sharp focus. No readable text.",
  "goto-1975": "The executive office of a Japanese business leader in 1975, seen from behind: an older man in a dark suit at a large wooden desk looking at a store plan, a younger planner standing beside him holding two hands up. Warm, decisive mood. No faces visible, no readable text.",
  "fujisawa-1976": "A small new hobby and do-it-yourself store in a Japanese suburban town in 1976: shelves of tools, lumber, paints and craft kits, a clerk in an apron explaining a tool to a father and son. Warm, hopeful mood. No logos or readable text.",
  "shibuya-opening-1978": "Opening day of a new multi-level store on a sloping street in Shibuya, Tokyo, in September 1978: a very long queue of young people in late-1970s fashion stretching down the hill, staff holding plain placards, a brand-new concrete building. Festive mood. No logos or readable text.",
  "consult-1980s": "Inside a Japanese do-it-yourself store in the 1980s: an expert clerk in a green apron explaining wood types and glues to a young woman with a sketch of a shelf, rows of screws, hinges and tools behind them. Helpful, warm mood. No logos or readable text.",
  "green-bag-1980s": "A busy Shibuya street in the mid-1980s: fashionable young people in DC-brand-era outfits carrying designer paper shopping bags and plain green paper shopping bags without logos, a hill street with shops. Energetic, trendy mood. No readable text.",
  "hands-award-1983": "An exhibition of handmade works in a Japanese store event space in 1983: wooden toys, furniture, sculptures and crafts on display tables, visitors admiring them, a ribbon on the winning piece. Cheerful, creative mood. No readable text.",
  "phone-1980s": "A Japanese store's customer service counter in the 1980s: a smiling female staff member on a rotary telephone, a notebook and a catalog on the counter, shelves of goods behind. Lighthearted mood. No readable text.",
  "sannomiya-1995": "A damaged store entrance in Kobe in early 1995 after the earthquake, reopened: a table in front with piles of free work gloves, calendars and wood scraps, local residents in winter coats taking items, a hand-written paper notice without readable text. Warm, compassionate mood.",
  "shinjuku-1996": "The opening of a large new store inside a modern department-store complex in Shinjuku, Tokyo, in October 1996: huge crowds of shoppers on the floors, staff guiding people. Lively, prosperous mood. No logos or readable text.",
  "quiet-1992": "A quiet aisle of a large Japanese hobby and tools store on a weekday in 1992, few customers, a staff member arranging goods, sale signs without readable text. Subdued mood after the bubble. No logos.",
  "competitors-1990s": "A collage-like scene of Japanese retail in the 1990s: a huge suburban home center with a large parking lot in front and, in the distance, a bright 100-yen shop and a stylish lifestyle goods store. Competitive mood. No logos or readable text.",
  "chart-2002": "A Japanese company office in 2002: a manager looking at a wall chart where a line rises to a peak and then flattens, papers on the desk, evening light through blinds. Thoughtful mood. No readable text or numbers.",
  "hands-be-2008": "A small bright shop inside a Japanese station building in 2008: cosmetics, natural skincare and stationery on white shelves, young women browsing. Cute, light mood. No logos or readable text.",
  "map-2021": "A large map of Japan on a meeting room wall in 2021 with many green pins clustered in big cities, a few pins in Singapore and Taiwan on a side map, executives looking at it. Ambiguous mood. No readable text.",
  "showroom": "A customer in a Japanese store holding an item and checking prices on a smartphone while a knowledgeable clerk in an apron explains nearby, rows of products behind. Slightly uneasy mood. No logos or readable text.",
  "diy-video": "A young Japanese man at home in the 2010s watching a do-it-yourself tutorial on a laptop while building a wooden shelf, tools on the floor. Casual, modern mood. No readable text on the screen.",
  "inventory-backroom": "A cramped stockroom behind a Japanese store: towering stacks of cardboard boxes, dusty unsold goods, a staff member with a clipboard looking tired. Heavy mood. No readable text.",
  "shibuya-redevelopment": "Shibuya, Tokyo, in the late 2010s: new glass skyscrapers rising behind the station, tower cranes, crowds at the scramble crossing at dusk. Changing city mood. No readable text or logos.",
  "pandemic-2020": "A Japanese shopping street and a big store in 2020 during the pandemic: shutters half down, a few people in face masks, empty escalators visible through glass. Lonely, uneasy mood. No readable text.",
  "ikebukuro-2021": "The last day of a large store on a busy street in Ikebukuro, Tokyo, in October 2021: people in masks taking photos of the building, a message board full of sticky notes without readable text. Bittersweet mood. No logos.",
  "boardroom-2021": "A corporate boardroom in Tokyo in December 2021: executives in dark suits and face masks around a long table raising their hands to vote, thick documents in front of them, a city view at dusk. Serious, decisive mood. Faces not in sharp focus. No readable text.",
  "sale-2021": "A press conference room in Tokyo in December 2021: two executives in dark suits at separate podiums, one empty chair left at the side, journalists in masks with cameras. Faces not in sharp focus. No logos or readable text.",
  "sign-change-2022": "Workers on a lift replacing a large store sign on a building facade in Japan in 2022, the old sign panel being lowered, a new green panel waiting on the ground. Transitional mood. No readable text or logos.",
  "cainz-method": "A Japanese store being reorganized in 2023: staff with handheld scanners checking neat, uniform shelves, inventory data on a tablet, well-organized aisles. Efficient, positive mood. No logos or readable text.",
  "record-2025": "A busy, bright lifestyle goods store in Japan in 2025 on a weekend: shoppers at a fast-moving checkout, full shelves, staff smiling. Revived, energetic mood. No logos or readable text.",
  "small-store-2026": "A compact new lifestyle goods shop in a stylish Tokyo neighborhood building in 2026 with a dark interior and green accents, stationery, gifts and cosmetics, a few shoppers. Modern, intimate mood. No logos or readable text.",
  "shibuya-building-2026": "An old concrete store building on a Y-shaped sloping intersection in Shibuya on a grey day in 2026, a tall green vertical sign on its corner, modern buildings around it. Melancholic, nostalgic mood. The sign letters are not legible. No logos.",
  "last-day-cards": "A wall in a store covered with thousands of colorful handwritten message cards, a few people reading them, warm lights. Emotional mood. The handwriting is not legible. No logos.",
  "last-day-rain": "A crowd of people holding umbrellas in the rain at night in front of an old store on a Shibuya slope, applauding as the shutter comes down, reflections on the wet street. Emotional farewell. Faces not identifiable. No readable text.",
  "ending-stairs": "Morning light falling on an empty spiral of short staircases and split-level floors inside an old store, green wooden handrails, a single cardboard box left on a step. Quiet, hopeful mood. No readable text.",
  "drugstore-competition": "A corridor in a Japanese shopping mall in the 2010s: a small lifestyle goods shop with cosmetics and stationery next to a drugstore and a 100-yen shop showing similar items, shoppers passing by. Crowded, competitive mood. No logos or readable text.",
  "ending-green-bag": "A plain green paper shopping bag without any logo left on a wooden bench on a quiet sloping street in Shibuya at dawn, soft golden light, wet pavement after rain. Hopeful, reflective mood. No readable text.",
  "credits-tools": "A wooden workbench with old hand tools, a hammer, a saw, a tape measure and small wood scraps, soft light, dark background. Quiet, reflective mood. No readable text.",
}

op = [
  {"image": "op-rain-closing", "lines": [
    "[2026年11月15日|にせんにじゅうろくねんじゅういちがつじゅうごにち]、日曜日。雨の渋谷。",
    "午後[7時|しちじ]、坂の途中の古いビルで、シャッターが下りました。",
    "店の前に並んだスタッフが、深く頭を下げます。",
    "「[48年間|よんじゅうはちねんかん]、ありがとうございました。また、渋谷に戻って参ります」",
  ]},
  {"image": "op-thanks-sign", "lines": [
    "見上げると、高さおよそ[17|じゅうなな]メートルの、緑の看板。",
    "[HANDS|はんず]の文字に[T|てぃー]を足し、[D|でぃー]を[K|けー]に変えて、[THANKS|さんくす]。",
    "店の名前が、そのまま「ありがとう」になっていました。",
    "ハンズ渋谷店。かつての東急ハンズの、原点の店です。",
  ]},
  {"image": "op-mall-store", "lines": [
    "東急ハンズという名前は、[2022年|にせんにじゅうにねん]に消えました。",
    "親会社の東急不動産ホールディングスが、ホームセンターのカインズに会社を売ったのです。",
    "ところが不思議なことに、いまのハンズは、経常利益で[32年|さんじゅうにねん]ぶりの最高益。",
    "店の数は、およそ[100|ひゃく]にまで増えています。",
  ]},
  {"image": "op-question", "lines": [
    "何でも揃う店は、なぜ稼げなくなったのか。",
    "東急は、なぜ手放したのか。そしてカインズは、何を変えたのか。",
    "今回ひもとくのは、東急ハンズの栄枯盛衰です。",
  ]},
]

ch01 = [
  {"image": "udagawa-1972", "lines": [
    "物語は、渋谷の、ある使いにくい土地から始まります。",
    "[1972年|せんきゅうひゃくななじゅうにねん]、東急不動産が、渋谷区宇田川町の教会の跡地を買いました。",
    "駅から[500|ごひゃく]メートル。形はL字で、敷地の中に[6|ろく]メートルの高低差。",
    "駅から遠い、形が悪い、裏通り。のちに「[3悪|さんあく]」と呼ばれた土地です。",
    "ビルやホテルの案は出ては消え、土地はしばらく、駐車場のまま眠っていました。",
  ]},
  {"image": "planning-1975", "lines": [
    "そこで企画担当の社員たちが考えたのが、これまでの世の中にない店でした。",
    "手本の[1つ|ひとつ]は、銀座の文具店、伊東屋がつくったホビー売り場だったといいます。",
    "木材、工具、金物、塗料から、ホビーまで。暮らしに関わる素材と道具を集めた、手づくりの専門店。",
    "[1975年|せんきゅうひゃくななじゅうごねん]、外部の研究所と練った構想で、会社は「手の復権」という言葉を掲げます。",
    "大量生産のモノがあふれる時代に、自分の手でつくる喜びを。そんな願いでした。",
  ]},
  {"image": "goto-1975", "lines": [
    "社内の反対は強いものでした。小売りは素人だ、立地が悪い、失敗したら建物を他に使えない。",
    "背中を押したのは、東急グループの総帥、五島昇です。",
    "社史によれば、五島は「手は[2本|にほん]あるのだから、[HAND|はんど]ではなく[HANDS|はんず]にしてはどうか」と提案。",
    "大きな赤字の見通しにも、「[30億円|さんじゅうおくえん]程度の赤字なら、素人の発想で思い切りやってみよ」と言ったと記されています。",
  ]},
  {"image": "fujisawa-1976", "lines": [
    "[1976年|せんきゅうひゃくななじゅうろくねん]、会社として東急ハンズが生まれ、神奈川の藤沢に、実験の[1号店|いちごうてん]が開きます。",
    "翌年には二子玉川にも。豊富な品揃えと、手づくりしたい客に寄り添う接客で、どちらも順調に滑り出しました。",
  ]},
  {"image": "shibuya-opening-1978", "lines": [
    "そして[1978年9月9日|せんきゅうひゃくななじゅうはちねんくがつここのか]。あの坂の土地に、渋谷店が開きます。",
    "高低差を逆手にとり、[1つ|ひとつ]の階を[3つ|みっつ]の床に分けて、らせん状につないだスキップフロア。入口は、坂の上と下に[2つ|ふたつ]。",
    "開店の日、行列はおよそ[700|ななひゃく]メートルにわたって続いたといいます。",
    "初日の客は、およそ[2万5,000人|にまんごせんにん]。記念に配った名前入りの軍手は、[3日間|みっかかん]で[10万|じゅうまん]枚にのぼったと伝えられています。",
  ]},
]

ch02 = [
  {"image": "consult-1980s", "lines": [
    "ハンズの売り物は、品揃えと、人でした。",
    "客がつくりたいものを聞き、合う素材と使い方を提案する。棚になければ、店員が自分で仕入れ先を探してくる。",
    "社史は、これを「ないで終わらせない接客」と呼んでいます。",
    "他の業界で専門の仕事をしてきた人も多く働き、売り場は、プロの知恵が集まる場所になりました。",
    "[2003年|にせんさんねん]の新宿店には、電動工具、革、画材、接着剤、合い鍵など、専門の技能を持つ社員が[38人|さんじゅうはちにん]いました。",
  ]},
  {"image": "green-bag-1980s", "lines": [
    "[1980年代|せんきゅうひゃくはちじゅうねんだい]、ハンズは渋谷の名所になります。",
    "おしゃれなブランドの紙袋と並んで、緑の手のマークの袋を下げて歩く若者たち。",
    "撮影で急に小道具が要るときも、行き先はハンズ。",
    "ハンズに行けば、なんとかなる。当時の雑誌のライターたちの、共通の認識だったといいます。",
  ]},
  {"image": "hands-award-1983", "lines": [
    "[1983年|せんきゅうひゃくはちじゅうさんねん]には、手づくりの作品を広く募る「ハンズ大賞」が始まり、",
    "年に一度の大売り出し「ハンズメッセ」も、この年の渋谷店の、[5周年|ごしゅうねん]のセールから生まれました。",
    "池袋、横浜と店が増え、[1994年|せんきゅうひゃくきゅうじゅうよねん]のある調査では、女子高校生が好きな雑貨店の[1位|いちい]に、渋谷店が選ばれています。",
  ]},
  {"image": "phone-1980s", "lines": [
    "地方では、「東京ハンズ」と言い間違えられることがとても多かった、とハンズの広報は笑います。",
    "東急百貨店の仲間と思われがちでしたが、親会社は不動産会社。小売りの素人が始めた店でした。",
  ]},
  {"image": "sannomiya-1995", "lines": [
    "[1995年|せんきゅうひゃくきゅうじゅうごねん]、阪神・淡路大震災。神戸の三宮店は、スプリンクラーの配管が壊れ、館内が水浸しになりました。",
    "[50日|ごじゅうにち]あまりで店を開けると、店先に「どうぞご自由にお持ちください」の張り紙。",
    "カレンダー[2万部|にまんぶ]、軍手[2万組|にまんくみ]、木の端材[2トン|にとん]が、被災した街に無料で配られました。",
  ]},
  {"image": "shinjuku-1996", "lines": [
    "[1996年|せんきゅうひゃくきゅうじゅうろくねん]に開いた新宿店には、ハンズによれば、初日だけで[3万1,000人|さんまんせんにん]が訪れます。",
    "[2000年|にせんねん]には池袋店の[8階|はっかい]に、猫と遊べる「ねこぶくろ」まで登場します。",
    "何でも揃う、ちょっと変わった大きな店。ハンズは、時代の主役の[1つ|ひとつ]になっていました。",
  ]},
]

ch03 = [
  {"image": "quiet-1992", "lines": [
    "けれども、陰りは意外に早く訪れていました。",
    "バブルが崩れたあとの[1992年度|せんきゅうひゃくきゅうじゅうにねんど]、会社ができて初めて、客[1人|ひとり]あたりの買い物の額が、前の年を下回ります。",
    "来る客の数も減り始めました。",
    "新しい店を出すことで、全体の売上をなんとか保つ。そんな形が、ここから始まります。",
  ]},
  {"image": "competitors-1990s", "lines": [
    "ライバルも次々に現れます。[1987年|せんきゅうひゃくはちじゅうななねん]には、すぐ近くに西武のロフトが開業。",
    "郊外には大きなホームセンター。[1990年代|せんきゅうひゃくきゅうじゅうねんだい]には、[100円|ひゃくえん]ショップのダイソーが勢いを増していきます。",
    "のちにハンズを買うカインズの[1号店|いちごうてん]も、渋谷店と同じ[1978年|せんきゅうひゃくななじゅうはちねん]に生まれていました。",
  ]},
  {"image": "chart-2002", "lines": [
    "[1990年代|せんきゅうひゃくきゅうじゅうねんだい]の後半には、ハンズ単体での株式の上場も計画されたといいます。実現はしませんでした。",
    "それでも、売上は伸びていきます。親会社の資料で確かめられる売上の頂点は、[2002年3月期|にせんにねんさんがつき]の[1,002億円|せんにおくえん]。",
    "ところが、利益の山は、それよりずっと前にありました。",
    "のちに経常利益で「[32年|さんじゅうにねん]ぶりの最高益」と報じられたことから逆算すると、",
    "利益の頂点は、[1990年代|せんきゅうひゃくきゅうじゅうねんだい]の前半だったことになります。",
  ]},
  {"image": "hands-be-2008", "lines": [
    "売上が下り坂に入った[2007年3月期|にせんななねんさんがつき]には、本業で[4億円|よんおくえん]の赤字を出します。",
    "[2008年|にせんはちねん]、ハンズは駅ビルなどに入る小さな店、ハンズ ビーを始めました。",
    "中心は、[20代|にじゅうだい]、[30代|さんじゅうだい]の女性に向けたコスメや文具です。",
    "[2009年|にせんきゅうねん]には渋谷店を[19年|じゅうきゅうねん]ぶりに改装し、「ヒント・マーケット」という新しい言葉を掲げました。",
    "大きな店から、小さな店へ。ハンズは、店の数で巻き返しを図ります。",
  ]},
]

ch04 = [
  {"image": "map-2021", "lines": [
    "[2005年|にせんごねん]に[16|じゅうろく]だったハンズの店は、[2021年|にせんにじゅういちねん]には、フランチャイズや海外を含めて[63|ろくじゅうさん]に。",
    "さらに、小さなハンズ ビーが[20|にじゅう]店。",
    "ところが売上は、[20年|にじゅうねん]近く、[750億円|ななひゃくごじゅうおくえん]から[975億円|きゅうひゃくななじゅうごおくえん]のあいだを行き来するだけでした。",
    "本業の利益率は、ほとんどの年で[1%|いちぱーせんと]前後。売っても、利益がほとんど残らなかったのです。",
  ]},
  {"image": "showroom", "lines": [
    "なぜ稼げなくなったのか。見方は、[1つ|ひとつ]ではありません。",
    "流通に詳しい中井彰人さんは、ネット通販の広がりで、店が「ショールーム」になったことを挙げます。",
    "知識のある店員の説明を聞いて、買うのはネットの最安値。",
    "そうなれば、人件費を払っているハンズの立つ瀬がない、と。",
  ]},
  {"image": "diy-video", "lines": [
    "ノンフィクションライターの窪田順生さんは、もう[1つ|ひとつ]の変化を指摘します。",
    "SNSや動画サイトにはプロ顔負けの知恵があふれ、店員だけが専門知識を持つ時代ではなくなった。",
    "さらに[100円|ひゃくえん]ショップ、ドン・キホーテ、ホームセンター、そしてロフト。",
    "日経新聞は、ハンズの稼ぐ力は、[2|に]から[3%|さんぱーせんと]の利益率を確保するロフトに見劣りすると報じました。",
    "窪田さんは、見て回るだけで楽しい店で時代に合わせたロフトに対し、ハンズは品揃えとプロのこだわりに固執した、と見ます。",
  ]},
  {"image": "drugstore-competition", "lines": [
    "流通ジャーナリストの長浜淳之介さんは、駅ビルなどの小さな店はDIYの色が薄く、",
    "化粧品や文具で、[100円|ひゃくえん]ショップやドラッグストアと競い合っていた、と指摘します。",
    "手づくりの店の顔が、少しずつ見えにくくなっていたのです。",
  ]},
  {"image": "inventory-backroom", "lines": [
    "ハンズ自身の仕組みに理由を見る声もあります。",
    "ハンズは、店長が仕入れに大きな裁量を持つ、個店主義の会社でした。それが店ごとの個性を生んだ一方で、",
    "東洋経済は、各店が仕入れた独自の商品を売り切れず、在庫が長く滞る状態が続いたと書いています。",
    "親会社の東急不動産ホールディングスにも、小売りを立て直すノウハウはなかった、と。",
  ]},
  {"image": "shibuya-redevelopment", "lines": [
    "渋谷の人の流れも、再開発で大きく変わっていきました。",
    "長浜さんによれば、JR渋谷駅の[1日|いちにち]の乗車人員は、[2012年|にせんじゅうにねん]の[41万人|よんじゅういちまんにん]から、[37万人|さんじゅうななまんにん]前後に減っていました。",
    "それでもハンズは、手を打ち続けます。[2014年|にせんじゅうよねん]にはシンガポールに出店。",
    "[2018年|にせんじゅうはちねん]には、個性的な販売員を「店主」に見立て、仕入れまで任せる取り組みも始めました。",
    "[2019年|にせんじゅうきゅうねん]には、駅の上にできた渋谷スクランブルスクエアにも店を出しました。",
    "けれども、数字は動きませんでした。",
  ]},
]

ch05 = [
  {"image": "pandemic-2020", "lines": [
    "そこへ、コロナが襲います。",
    "都心の大きな店が多いハンズは、休業と時短、人出の減少で、まともに打撃を受けました。",
    "[2021年3月期|にせんにじゅういちねんさんがつき]、売上は前の年より[3分の1|さんぶんのいち]以上減って、およそ[630億円|ろっぴゃくさんじゅうおくえん]。",
    "最終赤字は、[71億円|ななじゅういちおくえん]に達します。",
  ]},
  {"image": "ikebukuro-2021", "lines": [
    "[2020年|にせんにじゅうねん]の末には、神戸の三宮店などを閉め、",
    "[2021年10月|にせんにじゅういちねんじゅうがつ]には、[37年|さんじゅうななねん]続いた池袋店も閉店しました。",
    "その建物には翌年、家具のニトリの大きな店が入ります。",
  ]},
  {"image": "boardroom-2021", "lines": [
    "[2021年12月22日|にせんにじゅういちねんじゅうにがつにじゅうににち]。東急不動産ホールディングスは、東急ハンズをカインズに売ると発表しました。",
    "郊外の店が中心だったカインズにとって、ハンズは、都市部の店を一気に手に入れる機会でした。",
    "入札で、複数の候補から選んだ相手でした。値段は公表されていません。日経新聞は、[200億円|にひゃくおくえん]を超えるとみられると伝えています。",
    "東急不動産ホールディングスの西川弘典社長は、ハンズはプライベートブランドとネット通販の展開が、決定的に遅れていたと語っています。",
  ]},
  {"image": "sale-2021", "lines": [
    "会見に、売った側の東急不動産ホールディングスは姿を見せませんでした。",
    "並んだのは、カインズの高家正行社長と、東急ハンズの社長。売り手の社長のメッセージは、買い手の社長が読み上げました。",
    "高家さんは、東急ハンズとつくる新しいDIY文化を、日本から世界に発信したいと語り、",
    "こうも言いました。いちばんやってはいけないのは、中途半端に混ぜて、[2社|にしゃ]のとがった部分が丸くなることだ、と。",
  ]},
  {"image": "sign-change-2022", "lines": [
    "[2022年3月|にせんにじゅうにねんさんがつ]、ハンズはカインズの子会社に。[10月|じゅうがつ]には社名から「東急」が外れ、株式会社ハンズになります。",
    "[46年|よんじゅうろくねん]使われた手書き風のロゴは、デザイナーの佐藤オオキさんによる、漢字の「手」の一筆書きへ。",
    "色だけは、ハンズグリーンと呼ばれた緑を受け継ぎました。",
    "渋谷店の大看板が「[TOKYU HANDS|とうきゅうはんず]」から「[HANDS|はんず]」に変わったのは、[2023年3月|にせんにじゅうさんねんさんがつ]のことです。",
    "東急ハンズという名前は、こうして消えていったのです。",
  ]},
]

ch06 = [
  {"image": "cainz-method", "lines": [
    "カインズは、何を変えたのか。",
    "店ごとにばらばらだった棚づくりに、全店共通の、定番の並べ方を決めました。",
    "在庫を細かく管理し、欠品を減らし、レジ待ちを短くする。",
    "高家さんの言葉を借りれば、取り入れたのは、基本的なチェーンストアのやり方でした。",
  ]},
  {"image": "record-2025", "lines": [
    "結果は、すぐに出ます。[2025年2月期|にせんにじゅうごねんにがつき]、コロナから続いた赤字は黒字に変わり、",
    "経常利益は、[32年|さんじゅうにねん]ぶりの最高になりました。",
    "高家さんは、人や店を減らすリストラは、いっさい行わずに最高益を出せた、と語ります。",
    "ただし、売上はまだ、コロナ前の[7割|ななわり]ほど。戻ったのは、稼ぐ力のほうでした。",
  ]},
  {"image": "small-store-2026", "lines": [
    "店の形も変わりました。新しく出すのは、ショッピングモールや駅ビルに入る、小さな店です。",
    "[2026年|にせんにじゅうろくねん]に開いた自由が丘の店は、およそ[480|よんひゃくはちじゅう]平方メートル。渋谷店の、[11分の1|じゅういちぶんのいち]ほどの広さです。",
    "並ぶのは、コスメや文具、ギフトが中心。店の数は、[6月|ろくがつ]に[100|ひゃく]に達しました。",
    "熟練の店員[180人|ひゃくはちじゅうにん]の知識を学ばせた、[AI|えーあい]の接客も始まっています。",
    "会社は、[2030年|にせんさんじゅうねん]には[150|ひゃくごじゅう]店にする目標を掲げています。",
  ]},
  {"image": "shibuya-building-2026", "lines": [
    "その一方で、[2026年5月|にせんにじゅうろくねんごがつ]、渋谷店の閉店が発表されます。理由は、建物の賃貸借の契約が満了すること。",
    "高家会長は、建物の老朽化などの事情から、契約を更新できなかったと説明しました。",
    "日経新聞によれば、跡地は建て替えられ、ホテルになる見通しです。",
    "その[4か月|よんかげつ]前、高家さんは渋谷店をこう語っていました。小売業にとっては最も使いづらいビル。だが、このフロアがハンズの象徴だ、と。",
  ]},
  {"image": "last-day-cards", "lines": [
    "最後のひと月、渋谷店には、お客さんの手書きのメッセージが、[1万枚|いちまんまい]以上寄せられました。",
    "中学生のころから来ていたのに。おじいちゃんの代からお世話になりました。",
    "隣の壁には、街の仲間たちの寄せ書き。ライバルの渋谷ロフトは「友へ」。[9月|くがつ]に閉店した西武渋谷店は「同志へ」。",
  ]},
  {"image": "last-day-rain", "lines": [
    "前日の[14日|じゅうよっか]、客の数は前の年のおよそ[1.5倍|いってんごばい]。",
    "そして、[11月15日|じゅういちがつじゅうごにち]。開店前には、およそ[200人|にひゃくにん]の列ができました。",
    "雨の中、[午後7時|ごごしちじ]。シャッターが下りると、傘を差した人たちから、拍手と「ありがとう」の声が上がります。",
  ]},
  {"image": "ending-stairs", "lines": [
    "駅から遠く、形の悪い、坂の土地。小売りの素人が、そこに、どこにもない店をつくりました。",
    "最後の店長は、一日に何度も「出口はどこですか」と聞かれる、迷路のような店だった、と振り返ります。",
    "[24|にじゅうよん]のフロアと、[408段|よんひゃくはちだん]の階段。最も使いづらいビルは、最も愛された店になりました。",
  ]},
  {"image": "ending-green-bag", "lines": [
    "東急ハンズの名前は消え、原点の店も閉じました。それでもハンズは、およそ[100|ひゃく]の店で続いています。",
    "社長は、できれば渋谷にもう一度店を出したいと、場所を探していることを明かしています。まだ、決まったわけではありません。",
    "ハンズに行けば、なんとかなる。その言葉を、小さな店たちは受け継いでいけるのか。",
    "東急ハンズの栄枯盛衰。このファイルは、まだ閉じられていません。",
  ]},
]

shorts = [
  {
    "id": "s1",
    "youtube_title": "渋谷のハンズ、最後の日に看板が「THANKS」に #shorts",
    "title": ["ハンズ渋谷店", "最後の看板"],
    "scenes": [
      {"image": "op-rain-closing", "lines": [
        "[2026年11月15日|にせんにじゅうろくねんじゅういちがつじゅうごにち]。[48年|よんじゅうはちねん]続いたハンズ渋谷店が、閉店しました。"]},
      {"image": "op-thanks-sign", "lines": [
        "最後の日、高さ[17|じゅうなな]メートルの看板は、[HANDS|はんず]に[T|てぃー]を足し、[D|でぃー]を[K|けー]に変えて、",
        "[THANKS|さんくす]になっていました。"]},
      {"image": "shibuya-opening-1978", "lines": [
        "[1978年|せんきゅうひゃくななじゅうはちねん]、駅から遠い、坂の途中の使いにくい土地に生まれた店です。"]},
      {"image": "op-question", "lines": [
        "[24|にじゅうよん]のフロアに、階段は[408段|よんひゃくはちだん]。「出口はどこですか」と毎日聞かれる、迷路のような店でした。"]},
      {"image": "last-day-cards", "lines": [
        "お客さんの手書きのメッセージは、[1万枚|いちまんまい]を超えました。"]},
      {"image": "op-mall-store", "lines": [
        "でも実は、いまのハンズは、経常利益で[32年|さんじゅうにねん]ぶりの最高益。なぜなのか。答えは、本編で。"]},
    ],
    "description": [
      "2026年11月15日、48年続いたハンズ渋谷店が閉店しました。最後の日、高さ約17メートルの看板は「HANDS」から「THANKS」に。駅から遠い坂の土地に生まれた、24フロア・階段408段の迷路のような店でした。",
      "一方で、いまのハンズは経常利益で32年ぶりの最高益。本編で、東急ハンズの誕生から現在までをたどっています。"],
    "hashtags": ["ハンズ", "東急ハンズ", "ハンズ渋谷店", "渋谷", "閉店"],
  },
  {
    "id": "s2",
    "youtube_title": "東急ハンズはなぜ「東急」を失った？ #shorts",
    "title": ["東急ハンズは", "なぜ消えた？"],
    "scenes": [
      {"image": "consult-1980s", "lines": [
        "ハンズに行けば、なんとかなる。そう言われた店、東急ハンズ。",
        "その名前から、[2022年|にせんにじゅうにねん]、「東急」が消えました。"]},
      {"image": "map-2021", "lines": [
        "売上の頂点は[2002年|にせんにねん]。その後[20年|にじゅうねん]、店は増えても売上は横ばいで、利益はほとんど残りませんでした。"]},
      {"image": "pandemic-2020", "lines": [
        "コロナで最終赤字は[71億円|ななじゅういちおくえん]。東急不動産ホールディングスは、ハンズをカインズに売却します。"]},
      {"image": "record-2025", "lines": [
        "ところがカインズのもとで、経常利益は[32年|さんじゅうにねん]ぶりの最高に。"]},
      {"image": "op-question", "lines": [
        "何が変わったのか。答えは、本編で。"]},
    ],
    "description": [
      "「ハンズに行けば、なんとかなる」と言われた東急ハンズ。売上の頂点は2002年で、その後20年は店が増えても売上は横ばいでした。コロナで最終赤字71億円となり、東急不動産ホールディングスはカインズに売却。2022年に社名から「東急」が消えました。",
      "ところがカインズのもとで、経常利益は32年ぶりの最高に。本編で、その理由をたどっています。"],
    "hashtags": ["東急ハンズ", "ハンズ", "カインズ", "企業史", "経済"],
  },
  {
    "id": "s3",
    "youtube_title": "東急ハンズ、名前の由来は総帥のひと言 #shorts",
    "title": ["東急ハンズ", "名前の由来"],
    "scenes": [
      {"image": "planning-1975", "lines": [
        "[1975年|せんきゅうひゃくななじゅうごねん]。不動産会社の社員たちが、手づくりの専門店を計画していました。",
        "仮の名前は、東急スーパーハンド。"]},
      {"image": "goto-1975", "lines": [
        "社史によれば、東急の総帥、五島昇がこう言いました。",
        "手は[2本|にほん]あるのだから、[HAND|はんど]ではなく[HANDS|はんず]にしてはどうか。"]},
      {"image": "sannomiya-1995", "lines": [
        "その店は、阪神・淡路大震災のあと、軍手[2万組|にまんくみ]とカレンダー[2万部|にまんぶ]を、店先で無料で配りました。"]},
      {"image": "op-rain-closing", "lines": [
        "そして[2026年|にせんにじゅうろくねん]、原点の渋谷店は、[48年|よんじゅうはちねん]の歴史に幕を下ろしました。",
        "なぜ東急ハンズは消えたのか。答えは、本編で。"]},
    ],
    "description": [
      "東急ハンズの名前は、東急グループの総帥・五島昇の「手は2本あるのだから、HANDではなくHANDSにしてはどうか」というひと言から生まれたと、社史に記されています。",
      "阪神・淡路大震災のあとには、三宮店が軍手2万組とカレンダー2万部を無料で配りました。2026年に48年の歴史を閉じた渋谷店まで、本編でたどっています。"],
    "hashtags": ["東急ハンズ", "ハンズ", "五島昇", "雑学", "企業史"],
  },
]

USED = {b["image"] for seg in (op, ch01, ch02, ch03, ch04, ch05, ch06) for b in seg}
USED |= {sc["image"] for s in shorts for sc in s["scenes"]} | {"credits-tools", "op-thanks-sign", "last-day-rain", "op-question"}

ep = {
  "slug": "hands",
  "youtube_title": "東急ハンズはなぜ消えた？渋谷店48年の最後と、カインズで32年ぶり最高益の理由【栄枯盛衰ファイル】",
  "tags": ["東急ハンズ","ハンズ","ハンズ渋谷店","ハンズ 閉店","東急ハンズ 閉店","東急ハンズ なぜ","渋谷 閉店","カインズ","カインズ ハンズ","東急不動産","ロフト","渋谷","THANKS","企業の歴史","企業史","小売","懐かしい","栄枯盛衰","栄枯盛衰ファイル","経済解説"],
  "theme": {"main": "なぜ「東急ハンズ」は消えたのか？", "sub": "何でも揃う店の栄枯盛衰"},
  "readings": {
    "東急ハンズ": "とうきゅうはんず",
    "東急不動産ホールディングス": "とうきゅうふどうさんほーるでぃんぐす",
    "東急不動産": "とうきゅうふどうさん",
    "東急百貨店": "とうきゅうひゃっかてん",
    "宇田川町": "うだがわちょう",
    "高低差": "こうていさ",
    "五島昇": "ごとうのぼる",
    "五島": "ごとう",
    "総帥": "そうすい",
    "手の復権": "てのふっけん",
    "素人": "しろうと",
    "藤沢": "ふじさわ",
    "二子玉川": "ふたこたまがわ",
    "品揃え": "しなぞろえ",
    "小売り": "こうり",
    "小売業": "こうりぎょう",
    "ハンズ大賞": "はんずたいしょう",
    "女子高校生": "じょしこうこうせい",
    "三宮店": "さんのみやてん",
    "館内": "かんない",
    "店先": "みせさき",
    "張り紙": "はりがみ",
    "軍手": "ぐんて",
    "端材": "はざい",
    "客単価": "きゃくたんか",
    "経常利益": "けいじょうりえき",
    "最高益": "さいこうえき",
    "中井彰人": "なかいあきひと",
    "長浜淳之介": "ながはまじゅんのすけ",
    "伊東屋": "いとうや",
    "合い鍵": "あいかぎ",
    "乗車人員": "じょうしゃじんいん",
    "販売員": "はんばいいん",
    "DIY": "でぃーあいわい",
    "JR": "じぇいあーる",
    "窪田順生": "くぼたまさき",
    "立つ瀬": "たつせ",
    "見劣り": "みおとり",
    "日経新聞": "にっけいしんぶん",
    "東洋経済": "とうようけいざい",
    "個店主義": "こてんしゅぎ",
    "裁量": "さいりょう",
    "滞る": "とどこおる",
    "西川弘典": "にしかわひろのり",
    "高家正行": "たかいえまさゆき",
    "高家": "たかいえ",
    "佐藤オオキ": "さとうおおき",
    "一筆書き": "ひとふでがき",
    "定番": "ていばん",
    "欠品": "けっぴん",
    "賃貸借": "ちんたいしゃく",
    "老朽化": "ろうきゅうか",
    "跡地": "あとち",
    "渋谷ロフト": "しぶやろふと",
    "西武渋谷店": "せいぶしぶやてん",
    "寄せ書き": "よせがき",
    "SNS": "えすえぬえす",
    "L字": "えるじ",
    "ハンズ ビー": "はんず びー",
  },
  "images": {k: {"prompt": v} for k, v in images.items() if k in USED},
  "segments": [
    {"id": "op", "kind": "opening", "blocks": op},
    {"id": "ch01", "kind": "chapter", "title": "3悪の土地", "blocks": ch01},
    {"id": "ch02", "kind": "chapter", "title": "ハンズに行けば、なんとかなる", "blocks": ch02},
    {"id": "ch03", "kind": "chapter", "title": "最初の陰り", "blocks": ch03},
    {"id": "ch04", "kind": "chapter", "title": "3倍の店、横ばいの売上", "blocks": ch04},
    {"id": "ch05", "kind": "chapter", "title": "東急が手放した日", "blocks": ch05},
    {"id": "ch06", "kind": "chapter", "title": "THANKS", "blocks": ch06},
  ],
  "ident_image": "op-thanks-sign",
  "credits": {"image": "credits-tools", "sources": [
    "東急株式会社『東急100年史』（ウェブ版）",
    "加藤健太「東急ハンズの誕生と浜野安宏」『高崎経済大学論集』第55巻第4号（2013年）",
    "株式会社ハンズ 沿革・会社概要・ニュースリリース（2022〜2026年）",
    "東急不動産・東急不動産ホールディングス 決算資料、有価証券報告書、株主総会資料",
    "流通ニュース、シブヤ経済新聞、Impress Watch、アドタイ",
    "日本経済新聞、東洋経済オンライン、ダイヤモンド・チェーンストア、ITmedia ビジネスオンライン",
    "現代ビジネス、デイリー新潮、ゲットナビ、FASHIONSNAP、BCN、経済界",
  ]},
  "thumbnail": {"image": "op-thanks-sign", "lines": ["東急ハンズ", "なぜ消えた？", "渋谷店48年の最後…"]},
  "thumbnail_variants": [
    {"image": "last-day-rain", "lines": ["HANDS→THANKS", "最後の看板", "東急ハンズの栄枯盛衰"]},
    {"image": "op-question", "lines": ["32年ぶり最高益", "なのに渋谷閉店", "ハンズに何が？"]},
  ],
  "shorts": shorts,
  "description": {
    "intro": [
      "「ハンズに行けば、なんとかなる」。素材も工具も、ちょっと変わったモノも揃う店として愛された「東急ハンズ」。",
      "2026年11月15日、その原点だった渋谷店が48年の歴史に幕を下ろしました。最後の日、高さ約17メートルの看板は「HANDS」から「THANKS」に。「東急ハンズ」という名前も、2022年に親会社がカインズへ会社を売却したことで、すでに消えていました。",
      "ところが不思議なことに、カインズのもとで、いまのハンズは経常利益で32年ぶりの最高益。店の数は約100にまで増えています。"
    ],
    "questions": [
      "なぜ、何でも揃う店は稼げなくなったのでしょうか。",
      "なぜ東急はハンズを手放し、カインズは何を変えたのでしょうか。"
    ],
    "overview": "今回の「栄枯盛衰ファイル」では、1972年に東急不動産が買った「使いにくい土地」から始まり、「手の復権」を掲げた創業、渋谷店の開店と全盛期、バブル後の最初の陰り、店が増えても売上が伸びなかった20年、コロナとカインズへの売却、「東急」の名前が消えた日、そして渋谷店の最後の日まで、東急ハンズの歴史をたどります。",
    "comment_prompt": "ハンズ渋谷店の思い出、ハンズで買った忘れられないモノがあれば、ぜひコメント欄で教えてください。",
    "sources_summary": "本動画は、東急の社史、東急ハンズの誕生を扱った学術論文、ハンズの沿革とニュースリリース、東急不動産ホールディングスの決算資料・有価証券報告書、流通専門紙や新聞・経済誌の報道などを参考に制作しています。",
    "main_sources": ["東急株式会社『東急100年史』","高崎経済大学論集","株式会社ハンズ","東急不動産ホールディングス","カインズ","流通ニュース","シブヤ経済新聞","Impress Watch","日本経済新聞","東洋経済オンライン","ダイヤモンド・チェーンストア","ITmedia ビジネスオンライン"],
    "notes": [
      "※株式会社ハンズは倒産しておらず、カインズの子会社として約100店舗で営業を続けています（2026年11月時点）。閉店したのは渋谷店です。",
      "※渋谷店の閉店理由について、会社の発表は「賃貸借契約の満了」で、高家会長は建物の老朽化などの事情を挙げています。跡地のホテル計画は日本経済新聞の報道によるものです。",
      "※「32年ぶりの最高益」は経常利益ベース（2025年2月期）で、売上高はコロナ前の約7割です。",
      "※東急ハンズの売却価格は非公表で、「200億円超」は日本経済新聞の推定です。",
      "※停滞の要因は一つではなく、動画では記事の筆者・報道機関・経営者の見方として紹介しています。",
      "※五島昇氏の言葉は、社史の記録（学術論文による引用）にもとづいています。",
      "※動画の内容は、2026年11月22日時点の情報にもとづいています。"
    ],
    "reference_urls": [
      {"title": "東急株式会社『東急100年史』 「ファッションコミュニティ109」と「東急ハンズ」の開店", "url": "https://www.tokyu.co.jp/history/chapter04_9_2/"},
      {"title": "加藤健太「東急ハンズの誕生と浜野安宏」（高崎経済大学論集、2013年）", "url": "https://tcue.repo.nii.ac.jp/record/690/files/KJ00008479199.pdf"},
      {"title": "株式会社ハンズ 沿革", "url": "https://info.hands.net/company/enkaku.html"},
      {"title": "東急株式会社『東急100年史』 阪神・淡路大震災", "url": "https://www.tokyu.co.jp/history/chapter06_1_2/"},
      {"title": "東急不動産 2006年3月期 中間参考資料（小売セグメント）", "url": "https://pdf.irpocket.com/C3289/xNh6/x57l/Iq64.pdf"},
      {"title": "東急不動産ホールディングス 2022年3月期 決算短信", "url": "https://www2.jpx.co.jp/disc/32890/140120220511538890.pdf"},
      {"title": "流通ニュース カインズが東急ハンズを買収（2021年12月22日）", "url": "https://www.ryutsuu.biz/strategy/n122219.html"},
      {"title": "東洋経済オンライン 東急不動産HD・西川社長インタビュー（2022年1月28日）", "url": "https://toyokeizai.net/articles/-/576606"},
      {"title": "ITmedia ビジネスオンライン 中井彰人氏の寄稿（2022年1月26日）", "url": "https://www.itmedia.co.jp/business/articles/2201/26/news011.html"},
      {"title": "株式会社ハンズ 商号（会社名）変更のお知らせ（2022年9月26日）", "url": "https://info.hands.net/news/20220926_syougou_new_hp.pdf"},
      {"title": "流通ニュース ハンズ 創業50周年と今後の出店（2026年1月）", "url": "https://www.ryutsuu.biz/strategy/s012143.html"},
      {"title": "東洋経済オンライン カインズ・高家社長インタビュー（2026年3月）", "url": "https://toyokeizai.net/articles/-/938538"},
      {"title": "株式会社ハンズ 渋谷店 営業終了のお知らせ（2026年5月25日）", "url": "https://info.hands.net/news/20260525_shibuyaclose.pdf"},
      {"title": "株式会社ハンズ 渋谷店の大看板を「THANKS」に（2026年10月30日）", "url": "https://info.hands.net/news/20261030_shibuyaHANDS_THANKS.pdf"},
      {"title": "シブヤ経済新聞 ハンズ渋谷店 最終日（2026年11月）", "url": "https://www.shibukei.com/headline/20282/"},
      {"title": "Impress Watch ハンズ渋谷店 営業終了（2026年11月16日）", "url": "https://www.watch.impress.co.jp/docs/news/2156736.html"}
    ],
    "hashtags": ["東急ハンズ","ハンズ","ハンズ渋谷店","渋谷","カインズ","閉店","懐かしい","企業史","栄枯盛衰ファイル"]
  },
}

out = Path(__file__).resolve().parent / "episode.json"
json.dump(ep, open(out, "w"), ensure_ascii=False, indent=2)
total = 0
for s in ep["segments"]:
    n = sum(len(re.sub(r"\[([^|\]]+)\|[^\]]+\]", r"\1", l)) for b in s["blocks"] for l in b["lines"])
    total += n
    print(s["id"], len(s["blocks"]), "blocks", n, "chars")
print("total", total, "chars;", len(ep["images"]), "images; unused:", sorted(set(images) - USED))
for s in shorts:
    n = sum(len(re.sub(r"\[([^|\]]+)\|[^\]]+\]", r"\1", l)) for sc in s["scenes"] for l in sc["lines"])
    print("short", s["id"], n, "chars")
