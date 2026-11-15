"""Builds episodes/toysrus/episode.json (kept beside the episode so the script stays editable)."""
import json
import re
from pathlib import Path

images = {
  "kashihara-heli-1992": "A winter afternoon in January 1992 on the edge of a small Japanese city in Nara: a large helicopter lands on a dirt field next to a brand-new giant warehouse-style toy store. Hundreds of local residents line the road waving small Japanese and American paper flags while police keep order. Low mountains in the distance, cold clear light.",
  "kashihara-ceremony-1992": "Inside a huge new American-style toy warehouse store in Japan in January 1992: an opening ceremony at a small podium decorated with Japanese and American flags, the speaker seen from behind, rows of journalists and TV cameras, towering shelves of colorful boxed toys and oversized shopping carts. No readable text or logos.",
  "store-night-2026": "A large suburban toy store in Japan on an autumn night in 2026: the colorful building is lit up, a few families walk out with shopping bags across a nearly empty parking lot, a paper notice taped to the glass door. Quiet, uncertain mood. No readable text or logos.",
  "kidult-shelves-2026": "A busy modern hobby shop in Tokyo in 2026: adults in their twenties to forties browse walls of trading card displays, capsule toy machines and collectible figures, with a few parents and children among them. Bright, crowded, energetic. No readable text or logos.",
  "furniture-store-1948": "A small children's furniture shop in Washington, D.C., in 1948: a young American man in his mid-twenties in shirt sleeves arranges wooden cribs, high chairs and a few toys, while a young mother with a baby carriage looks in from the doorway. Post-war optimism, warm afternoon light.",
  "toy-supermarket-1957": "The first big self-service toy supermarket in suburban Maryland in the late 1950s: tall metal shelves stacked with boxed toys, families pushing shopping carts down wide aisles, checkout counters at the front, cars with tail fins in the parking lot outside. Bright fluorescent lighting. No readable store sign.",
  "giraffe-mascot-1965": "A friendly cartoon giraffe mascot costume greets excited children at the entrance of a big American toy store in the mid-1960s; parents smile, balloons and colorful toy boxes behind them. Cheerful, nostalgic mood. No logos or readable text.",
  "warehouse-store-1980s": "A vast warehouse-style American toy superstore in the late 1980s: identical long aisles with boxed toys stacked to the high ceiling, computer cash registers at the front, staff restocking from pallets, crowds of families. Enormous, efficient scale. No readable signs.",
  "toyshop-arcade-1989": "A small family-run toy shop in a covered Japanese shopping arcade in 1989: an elderly shopkeeper behind a glass counter, narrow shelves with boxed robots, dolls and board games, a few children looking in. Warm, slightly cramped, nostalgic. No readable text.",
  "jv-signing-1989": "A Tokyo executive office in autumn 1989: a Japanese businessman in a dark suit signs a joint-venture agreement with American retail executives at a polished table, small Japanese and American desk flags, the city skyline through the window. Faces not in sharp focus.",
  "niigata-protest-1990": "A provincial Japanese city in spring 1990: owners of small local shops, men and women in jackets and white headbands, hold a protest gathering in a covered shopping arcade, raising their fists; hand-painted banners without readable text. Serious, determined mood.",
  "trade-talks-1990": "A formal Japan-United States trade negotiation in 1990: two delegations of officials in dark suits face each other across a long table with small national flags, interpreters and thick document folders, news cameras at the side of the room. Tense atmosphere.",
  "first-store-queue-1991": "A cold December morning in 1991 in rural Ibaraki, Japan: more than a thousand people in winter coats queue outside a huge new warehouse-style toy store; children bounce with excitement, rows of oversized shopping carts wait by the entrance, frost on the parking lot. No readable signs.",
  "kashihara-traffic-1992": "A suburban road in Nara in January 1992 jammed with cars and delayed buses heading to a giant new toy store, families walking along the sidewalk carrying big toy boxes, traffic police directing cars. Busy, excited atmosphere.",
  "roadside-store-1995": "A giant roadside toy store along a Japanese national highway in the mid-1990s: a huge parking lot full of family cars on a weekend, parents and children walking toward the colorful warehouse building, a traffic jam on the highway. Sunny day. No readable text.",
  "game-launch-1994": "Inside a big Japanese toy store in December 1994: young people and parents line up between shelves to buy newly released home video game consoles, staff in vests hand over boxes, a wall of game boxes behind them. Excited holiday mood. No brand logos.",
  "family-cart-1998": "A Japanese family shopping in a huge children's store in the late 1990s: their cart holds toys, packs of diapers, children's clothes and small shoes; a young mother checks a price tag while a toddler points at stuffed animals. Bright, practical atmosphere. No readable text.",
  "toyshop-shutter-1997": "An old toy shop in a quiet Japanese shopping street in the late 1990s with its metal shutter half closed, faded posters in the window, an elderly owner sweeping the doorway alone. Melancholy late afternoon light. No readable text.",
  "store-100-2000": "A celebratory opening ceremony at a big new toy store in Tokyo in 2000: staff in matching vests, balloons and a ribbon-cutting line of guests seen from behind, children and parents cheering. Festive daytime. No readable text or logos.",
  "peak-christmas-2006": "A packed big toy store in Japan during the Christmas season of 2006: long lines at the checkouts, carts loaded with handheld game consoles and toys, Christmas decorations hanging from the high ceiling. Busy, prosperous mood. No brand logos.",
  "discount-aisle-1998": "A giant American discount superstore in the late 1990s: a long toy aisle next to groceries and household goods, bright low-price signs without readable text, shoppers pushing big carts. Flat fluorescent light.",
  "lbo-boardroom-2005": "A Wall Street boardroom at night in 2005: investment fund executives in dark suits sign thick acquisition and loan documents, stacks of binders on the table, Manhattan skyline lights through the windows. Faces out of focus.",
  "tokyo-tob-2009": "A Tokyo corporate office in 2009: Japanese managers in suits read a tender offer document at a meeting table, a stock price chart on a monitor, grey winter light through the blinds. Subdued mood. No readable text.",
  "quiet-store-2012": "A large Japanese toy store on a weekday afternoon in the early 2010s: wide aisles almost empty, one staff member restocking shelves, a lone parent with a stroller. Fluorescent light, quiet mood. No readable text.",
  "us-liquidation-2018": "An American toy superstore in spring 2018 during its closing-down sale: big banners without readable text, mostly empty shelves, scattered boxes, a few shoppers with carts, grey sky outside the glass doors.",
  "japan-store-2018": "A Japanese toy store in spring 2018 open as usual: parents with strollers and children entering through the automatic doors, a small paper notice on the glass, neat shelves inside. Calm, ordinary atmosphere. No readable text.",
  "office-loss-2019": "A back office of a Japanese retail chain around 2019: a manager seen from behind studies printed sales reports with downward charts, cardboard boxes of unsold toys stacked by the wall, evening light. No readable text.",
  "capsule-cards-2025": "A Tokyo station shopping area in 2025: long rows of colorful capsule toy machines and a trading card shop counter crowded with adults and teenagers, a few families passing by. Bright, lively. No readable text or logos.",
  "empty-parking-2020s": "A huge suburban toy store with a mostly empty parking lot on a grey weekday in the 2020s in Japan, a big shopping mall in the distance and a train line on the other side. Lonely atmosphere. No readable text.",
  "price-compare-2010s": "A Japanese parent at home in the late 2010s comparing toy prices on a laptop and a smartphone at the dining table, delivery boxes stacked by the front door, a child playing on the floor. Warm evening light. No readable text.",
  "discount-tags-2020s": "A Japanese toy store in the early 2020s with many red discount tags on the shelves, staff in masks counting piles of unsold boxes in the back stockroom. Tired, stretched atmosphere. No readable text.",
  "kidult-shop-2025": "A small modern toy shop for adult collectors inside a Japanese shopping mall in 2025: shelves of blind boxes and collectible vinyl figures, young adult customers taking photos with their phones. Stylish lighting. No logos.",
  "news-night-2026": "A Japanese living room late at night in September 2026: a smartphone on the coffee table glows with breaking business news, a toy store shopping bag and a child's crayon drawing nearby, a parent's hand reaching for the phone. No readable text.",
  "briefing-2026": "A corporate press briefing in Tokyo in October 2026: executives at a podium in front of a large screen showing an illustration of a bright toy store with a play area, reporters typing on laptops, camera flashes. No readable text or logos.",
  "last-day-2026": "The last evening of a big toy store inside a Tokyo shopping complex in October 2026: staff in vests bow at the entrance to departing customers, some shelves already empty, a child holding a parent's hand looks back. Bittersweet mood. No readable text.",
  "christmas-2026": "A Japanese toy store decorated for Christmas in November 2026: a large open play area where children build with blocks, new colorful shelves, families shopping, a big Christmas tree. Warm, hopeful light. No readable text or logos.",
  "us-revival-2026": "A brand-new bright toy store in an American shopping mall in autumn 2026 with a friendly giraffe statue at the entrance, families with holiday shopping bags, cheerful window displays. No readable logos.",
  "kashihara-sunset-2026": "A quiet suburban road in Nara at sunset in 2026: a large toy store with its lights on, a family walking out carrying a balloon and a small bag, low mountains in the distance. Gentle, reflective mood. No readable text.",
  "credits-cart": "An empty toy store aisle at night with a single shopping cart standing in soft light, shelves of toys fading into the dark. Nostalgic, quiet mood. No readable text.",
}

op = [
  {"image": "kashihara-heli-1992", "lines": [
    "[1992年1月7日|せんきゅうひゃくきゅうじゅうにねんいちがつなのか]、奈良県橿原市。",
    "郊外の空き地に、一機のヘリコプターが降りてきます。",
    "沿道には住民が集まり、数百人が日本とアメリカの小旗を振っていました。",
    "降り立ったのは、アメリカのブッシュ大統領です。",
    "向かった先は、工場でも、役所でもありません。開店したばかりの、おもちゃ屋でした。",
  ]},
  {"image": "kashihara-ceremony-1992", "lines": [
    "店の名前は、トイザらス。",
    "大統領は、孫たちにおもちゃを買ってやりたいが、妻にこづかいを減らされた、と冗談を言って会場を笑わせました。",
    "そして、日本のことわざを引きます。「石の上にも三年」。日本に店を開くまでの、苦労の年月のことでした。",
    "アメリカから来た巨大なおもちゃ屋は、日本の市場をこじ開ける「黒船」と呼ばれていたのです。",
  ]},
  {"image": "store-night-2026", "lines": [
    "それから、およそ[35年|さんじゅうごねん]。",
    "[2026年10月1日|にせんにじゅうろくねんじゅうがつついたち]、日本トイザらスは、東京地方裁判所に民事再生法の適用を申請しました。",
    "負債はおよそ[132億円|ひゃくさんじゅうにおくえん]。東京商工リサーチによれば、債権者は[1,159|せんひゃくごじゅうきゅう]にのぼります。",
    "店は、その月のうちに、ドン・キホーテを展開するグループへと引き継がれました。",
  ]},
  {"image": "kidult-shelves-2026", "lines": [
    "不思議なのは、ここからです。日本のおもちゃ市場は、縮んでいたわけではありません。",
    "日本玩具協会によれば、[2025年度|にせんにじゅうごねんど]の国内の市場規模はおよそ[1兆1,664億円|いっちょうせんろっぴゃくろくじゅうよんおくえん]。過去最高でした。",
    "おもちゃは、かつてないほど売れていた。それなのに、おもちゃ屋の代名詞だった店が、立ち行かなくなったのです。",
    "なぜ、大統領に祝福された「黒船」は、日本で行き詰まったのか。",
    "なぜ、おもちゃが売れる時代に、トイザらスは売れなくなったのか。",
    "そして、トイザらスの店は、今どうなっているのか。",
    "今回ひもとくのは、トイザらスの栄枯盛衰です。",
  ]},
]

ch01 = [
  {"image": "furniture-store-1948", "lines": [
    "物語は、[1948年|せんきゅうひゃくよんじゅうはちねん]のアメリカ、首都ワシントンから始まります。",
    "[25歳|にじゅうごさい]のチャールズ・ラザラスが、子ども用の家具を売る小さな店を開きました。",
    "戦後のベビーブームで、ベビーベッドはよく売れました。しかし、丈夫なベッドは、一度買えばそれで終わりです。",
    "おもちゃは違いました。遊べば壊れ、飽きれば次がほしくなる。何度でも売れるのです。",
  ]},
  {"image": "toy-supermarket-1957", "lines": [
    "ラザラスは、店の中心をおもちゃへと移し、スーパーマーケットのような売り方を取り入れます。",
    "棚を高く積み上げ、客が自分でカートに入れて、レジで払う。",
    "[1957年|せんきゅうひゃくごじゅうななねん]、トイザらスの名前を掲げた最初の店が生まれます。",
    "看板の「[R|あーる]」は、わざと裏返し。子どもが書いた字のように見せるためだったといいます。",
  ]},
  {"image": "giraffe-mascot-1965", "lines": [
    "[1965年|せんきゅうひゃくろくじゅうごねん]には、キリンのキャラクター「ジェフリー」が登場します。",
    "途中で店を手放し、買い手の会社が経営破綻するという曲折もありました。",
    "それでも[1978年|せんきゅうひゃくななじゅうはちねん]、トイザらスを社名にした会社として再出発し、ラザラスが経営の先頭に立ちます。",
  ]},
  {"image": "warehouse-store-1980s", "lines": [
    "店は倉庫のような大型店。どの店も、通路の並びまで同じでした。",
    "問屋を通さずにメーカーから直接仕入れ、小さなおもちゃ屋より[1割|いちわり]から[2割|にわり]安く売る。",
    "[1988年|せんきゅうひゃくはちじゅうはちねん]までに、アメリカのおもちゃ市場のおよそ[2割|にわり]を握り、売上は[40億ドル|よんじゅうおくどる]を超えます。",
    "海外にも乗り出し、イギリスでは進出から[5年|ごねん]で地元のおもちゃ屋が大きく減ったと、業界が抗議しています。",
    "次に狙いを定めたのが、アメリカに次ぐ世界[2位|にい]のおもちゃ市場、日本でした。",
  ]},
]

ch02 = [
  {"image": "toyshop-arcade-1989", "lines": [
    "当時の日本で、おもちゃを買う場所といえば、商店街のおもちゃ屋でした。",
    "おもちゃは問屋から仕入れ、メーカーが決めた希望小売価格で売る。売れ残れば、返品ができる。",
    "公正取引委員会の調べでは、[1989年|せんきゅうひゃくはちじゅうきゅうねん]、おもちゃ屋の[7割|ななわり]が希望小売価格のまま売っていたといいます。",
    "そして、大型店の出店には、地元の商店街との調整を求める法律がありました。大規模小売店舗法、いわゆる大店法です。",
  ]},
  {"image": "jv-signing-1989", "lines": [
    "トイザらスは、日本の大手小売業者と組む道も探りましたが、問屋を通すよう求められ、話はまとまらなかったといいます。",
    "そこで手を組んだのが、日本マクドナルドの創業者、藤田田でした。",
    "[1989年11月|せんきゅうひゃくはちじゅうきゅうねんじゅういちがつ]、日本トイザらスが設立されます。出資はアメリカ本社が[8割|はちわり]、日本マクドナルドが[2割|にわり]。",
    "藤田は、日本の遅れた小売の仕組みに風穴を開けたい、と語ったとされています。",
  ]},
  {"image": "niigata-protest-1990", "lines": [
    "[1990年1月|せんきゅうひゃくきゅうじゅうねんいちがつ]、トイザらスは新潟市への出店を表明します。",
    "国会で示された試算では、市内のおもちゃ屋の売上の半分近くを、一店で取るほどの計画でした。",
    "国会では、地元の商店主たちが「生まれて初めて」団結の鉢巻きを締めて立ち上がった、と紹介されています。",
    "一方、アメリカの通商代表は、安くて品ぞろえの多い店を開けばいい、気に入らなければ失敗するだけだ、と言い放ちました。",
  ]},
  {"image": "trade-talks-1990", "lines": [
    "ちょうどこの頃、日本とアメリカは、日米構造協議の真っただ中にありました。",
    "アメリカが、日本の市場を閉ざす仕組みとして挙げたものの一つが、大店法だったのです。",
    "[1990年5月|せんきゅうひゃくきゅうじゅうねんごがつ]、通産省は大店法の運用を改め、出店の調整にかける期間を[1年半|いちねんはん]までと区切ります。",
    "翌年には、法律そのものも改正されました。",
  ]},
  {"image": "first-store-queue-1991", "lines": [
    "[1991年12月20日|せんきゅうひゃくきゅうじゅういちねんじゅうにがつはつか]。",
    "茨城県阿見町に、日本のトイザらスの[1号店|いちごうてん]、荒川沖店が開店します。",
    "午前[10時|じゅうじ]の開店前には、[1,000人|せんにん]を超える行列。売場はおよそ[4,100平方メートル|よんせんひゃくへいほうめーとる]、品数は[8,000|はっせん]。",
    "アメリカサイズの大きなカートは、開店から数分で、おもちゃでいっぱいになったといいます。",
    "任天堂をはじめ、[50社|ごじゅっしゃ]を超える日本のメーカーが、問屋を通さない直接の取引に応じていました。",
  ]},
  {"image": "kashihara-traffic-1992", "lines": [
    "そして[18日|じゅうはちにち]後。ブッシュ大統領が、橿原店の開店に訪れます。",
    "国会で読み上げられた新聞の見出しによれば、初日の人出は[2万4,000人|にまんよんせんにん]。道路は大渋滞になりました。",
    "実は、この[2店|にてん]は、改正された大店法が施行される前に開いています。",
    "反対の強かった新潟店が開いたのは、出店の表明から[4年8か月|よねんはちかげつ]後のことでした。",
  ]},
]

ch03 = [
  {"image": "roadside-store-1995", "lines": [
    "黒船の上陸は、成功でした。",
    "掲げた目標は、[10年|じゅうねん]で[100店|ひゃくてん]。[1994年1月|せんきゅうひゃくきゅうじゅうよねんいちがつ]に[16店|じゅうろくてん]だった店は、毎年[10店|じゅってん]あまりのペースで増えていきます。",
    "郊外の国道沿いに巨大な店ができ、週末には家族連れの車が列をなしました。",
    "相模原店の開店日には、ふだん[30分|さんじゅっぷん]ほどのバスが[3時間|さんじかん]かかった、と国会で紹介されています。",
  ]},
  {"image": "game-launch-1994", "lines": [
    "追い風になったのが、テレビゲームです。",
    "[1994年|せんきゅうひゃくきゅうじゅうよねん]の年末、新しいゲーム機が相次いで発売されると、日本の売上は大きく伸びました。",
    "上陸のころ、トイザらスの幹部は、自分たちは任天堂にとって世界最大の単独の取引先だ、と語っています。",
  ]},
  {"image": "family-cart-1998", "lines": [
    "ただ、日本のトイザらスは、単なるおもちゃの安売り屋ではありませんでした。",
    "[1998年|せんきゅうひゃくきゅうじゅうはちねん]、国会で流通の専門家は、売上のうちおもちゃは[3割|さんわり]ほどだと説明しています。",
    "おもちゃのついでに、服や靴、ベビー用品も買っていく。だから買い物の額が大きく、値段を下げられるのだ、と。",
    "専門家によれば、当時の店は[64店|ろくじゅうよんてん]、売上はおよそ[1,000億円|せんおくえん]。しかも、すべての店が黒字だったといいます。",
  ]},
  {"image": "toyshop-shutter-1997", "lines": [
    "その陰で、町のおもちゃ屋は苦しくなっていきます。",
    "[1997年|せんきゅうひゃくきゅうじゅうななねん]、国会である議員は、おもちゃ屋の倒産が、上陸した年の[7件|ななけん]から[1996年|せんきゅうひゃくきゅうじゅうろくねん]には[41件|よんじゅういっけん]に増えたと訴えました。",
    "議員は、これを「トイザらス・ショック」と呼んでいます。",
  ]},
  {"image": "store-100-2000", "lines": [
    "[2000年|にせんねん]、トイザらスは節目を迎えます。",
    "[4月|しがつ]に株式を店頭市場、のちのジャスダックに公開。この年、日本で[100店|ひゃくてん]目の店を開きます。",
    "上陸から[10年|じゅうねん]足らず。掲げた目標を、ほぼそのとおりに達成したのです。",
    "ところが同じ年の[6月|ろくがつ]、大店法が廃止されます。",
    "トイザらスのために開かれた扉は、ほかの大型店にも、同じように開かれたのでした。",
  ]},
  {"image": "peak-christmas-2006", "lines": [
    "日本トイザらスの売上が頂点に達したのは、[2007年1月期|にせんななねんいちがつき]。東京商工リサーチによれば、およそ[1,944億円|せんきゅうひゃくよんじゅうよんおくえん]でした。",
    "携帯ゲーム機の大ブームに、新しい家庭用ゲーム機の発売が重なった時期です。",
    "ただし、アメリカ本社の報告書には、気になる数字があります。",
    "日本の粗利率、つまり売上に占めるもうけの割合は[28.1%|にじゅうはってんいちぱーせんと]。ほかの海外事業の平均[37.8%|さんじゅうななてんはちぱーせんと]を大きく下回っていました。",
    "理由は、もうけの薄いゲーム機や電子機器の割合が高いこと。売上の頂点は、薄い利幅の上に乗っていたのです。",
  ]},
]

ch04 = [
  {"image": "discount-aisle-1998", "lines": [
    "その頃、本家のアメリカでは、トイザらスの足元が揺らいでいました。",
    "[1998年|せんきゅうひゃくきゅうじゅうはちねん]、アメリカのおもちゃ販売で、ディスカウント大手のウォルマートが首位に立ちます。",
    "何でも売る大型店がおもちゃ売場を広げ、安値で客を奪っていったのです。",
    "ネット販売は[2000年|にせんねん]からアマゾンに任せましたが、のちに独占の約束をめぐって裁判になります。",
  ]},
  {"image": "lbo-boardroom-2005", "lines": [
    "そして[2005年|にせんごねん]。トイザらスは、ベインキャピタルやKKRなどの投資ファンドに買収されます。",
    "買収額は[66億ドル|ろくじゅうろくおくどる]。ファンドが出したお金はおよそ[13億ドル|じゅうさんおくどる]で、残りの多くは借金でした。",
    "その借金を背負ったのは、買収されたトイザらス自身です。",
    "支払う利息は、買収前の年度の[1億3,000万ドル|いちおくさんぜんまんどる]から、買収の翌年度には[5億3,700万ドル|ごおくさんぜんななひゃくまんどる]。およそ[4倍|よんばい]に膨らみます。",
    "店に回るはずのお金が、利息に消えていく。この重荷は、最後まで外れませんでした。",
  ]},
  {"image": "tokyo-tob-2009", "lines": [
    "日本にも、その影響が及びます。",
    "[2006年|にせんろくねん]、アメリカ本社とファンドの側が、日本トイザらスの取締役会の過半数を握りました。",
    "日本マクドナルドとの契約は打ち切られ、[2008年|にせんはちねん]、日本マクドナルドは株を手放します。",
    "アメリカ本社は、業績の不振と立て直しを急ぐことを理由に株式を買い集め、日本トイザらスは[2010年|にせんじゅうねん]に上場を廃止しました。",
  ]},
  {"image": "quiet-store-2012", "lines": [
    "上場をやめた後も、日本の売上は少しずつ減っていきます。",
    "[2018年1月期|にせんじゅうはちねんいちがつき]の売上は、およそ[1,395億円|せんさんびゃくきゅうじゅうごおくえん]。ピークから[3割|さんわり]近く減っていました。",
    "それでも、この期の日本トイザらスは、まだ黒字を保っていました。",
  ]},
  {"image": "us-liquidation-2018", "lines": [
    "先に崩れたのは、アメリカでした。",
    "[2017年9月18日|にせんじゅうななねんくがつじゅうはちにち]、アメリカのトイザらスは、連邦破産法[11条|じゅういちじょう]の適用を申請します。",
    "日本の民事再生にあたる手続きです。抱えていた長期の借金は、およそ[50億ドル|ごじゅうおくどる]。",
    "[2018年3月|にせんじゅうはちねんさんがつ]、アメリカの全[735店|ななひゃくさんじゅうごてん]を閉じることが決まり、最大でおよそ[3万3,000人|さんまんさんぜんにん]が職を失うと伝えられました。",
    "その[1週間|いっしゅうかん]後、創業者のラザラスが、[94歳|きゅうじゅうよんさい]で亡くなりました。",
  ]},
  {"image": "japan-store-2018", "lines": [
    "日本トイザらスはすぐに、アメリカとは別の会社で、日本の店はこれまでどおり営業すると説明します。",
    "実際、日本の会社は、アメリカの破産手続きの外にありました。",
    "ただ、その持ち主は、アメリカ本社の借金と無関係ではいられません。",
    "[2018年12月|にせんじゅうはちねんじゅうにがつ]、日本を含むアジアの事業は、およそ[7億6,000万ドル|ななおくろくせんまんどる]で売られます。",
    "買い手は、アメリカ本社の社債を持つ債権者たちと、香港の小売グループでした。",
    "上陸から[27年|にじゅうななねん]。日本のトイザらスは、生みの親の手を離れました。",
  ]},
]

ch05 = [
  {"image": "office-loss-2019", "lines": [
    "新しい持ち主のもとで、日本トイザらスは赤字に転じます。",
    "[2019年1月期|にせんじゅうきゅうねんいちがつき]の最終損益は、[33億円|さんじゅうさんおくえん]あまりの赤字。ここから[8期|はっき]続けて最終赤字となります。",
    "[2025年12月期|にせんにじゅうごねんじゅうにがつき]の売上は、およそ[752億円|ななひゃくごじゅうにおくえん]。頂点だったころの、およそ[4割|よんわり]にまで縮んでいました。",
    "ところが、同じ時期、日本のおもちゃ市場は伸び続けていたのです。",
  ]},
  {"image": "capsule-cards-2025", "lines": [
    "日本玩具協会の数字では、国内の市場は[2006年度|にせんろくねんど]のおよそ[7,236億円|ななせんにひゃくさんじゅうろくおくえん]から、[2025年度|にせんにじゅうごねんど]には[1兆円|いっちょうえん]を大きく超えました。",
    "出生数が[1990年|せんきゅうひゃくきゅうじゅうねん]のおよそ[122万人|ひゃくにじゅうにまんにん]から、[2018年|にせんじゅうはちねん]には[92万人|きゅうじゅうにまんにん]ほどに減った後も、市場は大きくなっていたのです。",
    "伸びを支えたのは、トレーディングカードやカプセルトイ、そして大人の客だったと伝えられています。",
    "大人になっても、おもちゃを楽しむ人たち。キダルトと呼ばれる客です。",
  ]},
  {"image": "empty-parking-2020s", "lines": [
    "では、なぜトイザらスには、その波が届かなかったのでしょうか。",
    "少子化のせい、と言われることがあります。しかし、それだけでは説明がつきません。",
    "一つ目は、店の形です。トイザらスの多くは、郊外の大きな店でした。",
    "家族で車に乗って出かけ、一日がかりで選ぶ。上陸のころは、それが魅力でした。",
    "けれども、伸びていた大人の需要を、郊外の大きな店では取り込めなかった。流通アナリストは、そう分析しています。",
  ]},
  {"image": "price-compare-2010s", "lines": [
    "二つ目は、値段の競争です。",
    "[2004年|にせんよねん]、アマゾンの日本のサイトにおもちゃの売場ができ、最大[3割|さんわり]引きをうたいました。",
    "家電量販店もおもちゃを強化し、帝国データバンクは、他の業態との競争が激しくなったと分析しています。",
    "会社自身も、民事再生の申請にあたり、ネット通販の企業などとの激しい価格競争を理由に挙げました。",
  ]},
  {"image": "discount-tags-2020s", "lines": [
    "三つ目は、抜け出せない悪循環です。",
    "東京商工リサーチによれば、値引きで利幅が下がり、店に投資する資金がなくなっていきました。そこに新型コロナも重なります。",
    "事業を引き継いだ側も、十分な成長投資が行われていなかった、と振り返っています。",
    "そして四つ目は、持ち主が何度も代わったことです。",
    "日米の合弁から、アメリカ本社の子会社へ。香港の会社の下に入り、最後は債権者たちの手に。",
    "持ち主が代わるたびに、日本の店の行く先も揺れ続けました。",
  ]},
  {"image": "kidult-shop-2025", "lines": [
    "会社も、手をこまねいていたわけではありません。",
    "[2023年|にせんにじゅうさんねん]には全品を値引きするアウトレット店を、[2025年10月|にせんにじゅうごねんじゅうがつ]には大人向けのキダルト専門店を開きました。",
    "しかし、東京商工リサーチは、[2025年12月期|にせんにじゅうごねんじゅうにがつき]の赤字で、借入の条件に抵触したと伝えています。",
    "残された時間は、もう多くありませんでした。",
  ]},
]

ch06 = [
  {"image": "news-night-2026", "lines": [
    "[2026年9月29日|にせんにじゅうろくねんくがつにじゅうくにち]の夜。",
    "トイザらスが日本での店の運営から撤退し、ドン・キホーテの運営会社が事業を引き継ぐ方向だ、と報じられます。",
    "[10月1日|じゅうがつついたち]、日本トイザらスは民事再生法の適用を申請しました。",
    "民事再生は、会社をたたむのではなく、事業を続けながら借金を整理する、再建型の手続きです。",
    "店はこの日も、ふだんどおり開いていました。",
  ]},
  {"image": "briefing-2026", "lines": [
    "同じ日、ドン・キホーテを展開するPPIHが、スポンサーとして事業を引き継ぐと発表します。",
    "社長は、この案件を「新たな収益成長機会」と表現しました。",
    "狙いは、伸び続けるおもちゃの市場と大人の客、そしてドンキには足を運ばない、およそ[3,000万人|さんぜんまんにん]との接点です。",
    "おもちゃを買う場所から、遊ぶ場所へ。売場のおよそ[1割|いちわり]を、遊び場にするといいます。",
  ]},
  {"image": "last-day-2026", "lines": [
    "[10月30日|じゅうがつさんじゅうにち]、事業の譲渡が実行されます。引き継がれたのは、トイザらスとベビーザらスの[154店|ひゃくごじゅうよんてん]。",
    "東京商工リサーチは、譲渡の価格をおよそ[28億8,000万円|にじゅうはちおくはっせんまんえん]と伝えています。",
    "同じ日、[2000年|にせんねん]から続いた池袋サンシャインシティの店が、営業を終えました。",
    "上陸から、およそ[35年|さんじゅうごねん]。日本のトイザらスは、日本の小売グループの手に渡ったのです。",
  ]},
  {"image": "christmas-2026", "lines": [
    "ただ、トイザらスの名前は、消えたわけではありません。",
    "[11月|じゅういちがつ]、新しい運営会社のもとで、初めてのクリスマスの売り出しが始まりました。",
    "店の名前も、ベビーザらスも、オンラインストアも、今はそのまま続いています。",
    "ただし、PPIHは、ブランドを使い続けるかを正式には決めていないと説明しています。",
  ]},
  {"image": "us-revival-2026", "lines": [
    "一方、海の向こうでは、別の物語が進んでいます。",
    "アメリカで一度すべての店を閉じたトイザらスは、ブランドを持つ会社のもとで、よみがえりつつあります。",
    "[2026年9月|にせんにじゅうろくねんくがつ]には、年末に向けて単独の店を[160店|ひゃくろくじゅってん]に増やすと発表しました。",
    "日本で民事再生が申請される、およそ[10日|とおか]前のことでした。",
  ]},
  {"image": "kashihara-sunset-2026", "lines": [
    "[1992年|せんきゅうひゃくきゅうじゅうにねん]、橿原の店で、ブッシュ大統領は「石の上にも三年」と語りました。",
    "それから[30年|さんじゅうねん]あまり。",
    "黒船は、日本のおもちゃの売り方を変え、町のおもちゃ屋を追い詰めました。",
    "そして今度は、自らが、時代に追い越されていったのです。",
    "おもちゃは今も、かつてないほど売れています。店も、名前も、まだある。",
    "それでも、あの「黒船」の時代は、もう終わったのかもしれません。",
    "時代を変えた者も、やがて時代に変えられる。",
    "トイザらスの栄枯盛衰。そのファイルを、ここで閉じます。",
  ]},
]

ep = {
  "slug": "toysrus",
  "youtube_title": "トイザらスはなぜ倒産した？大統領が祝った「黒船」がドンキに渡るまで【栄枯盛衰ファイル】",
  "tags": ["トイザらス","日本トイザらス","トイザらス 倒産","トイザらス 民事再生","トイザらス ドンキ","ベビーザらス","ドン・キホーテ","PPIH","おもちゃ屋","大店法","日米構造協議","黒船","キダルト","企業の歴史","企業史","倒産","栄枯盛衰","栄枯盛衰ファイル","平成レトロ","経済解説"],
  "theme": {"main": "なぜ「トイザらス」は倒産したのか？", "sub": "大統領が祝った黒船、35年の栄枯盛衰"},
  "readings": {
    "橿原市": "かしはらし",
    "橿原店": "かしはらてん",
    "橿原": "かしはら",
    "民事再生法": "みんじさいせいほう",
    "民事再生": "みんじさいせい",
    "東京商工リサーチ": "とうきょうしょうこうりさーち",
    "帝国データバンク": "ていこくでーたばんく",
    "債権者": "さいけんしゃ",
    "日本玩具協会": "にほんがんぐきょうかい",
    "代名詞": "だいめいし",
    "チャールズ・ラザラス": "ちゃーるず・らざらす",
    "問屋": "とんや",
    "希望小売価格": "きぼうこうりかかく",
    "公正取引委員会": "こうせいとりひきいいんかい",
    "大規模小売店舗法": "だいきぼこうりてんぽほう",
    "大店法": "だいてんほう",
    "藤田田": "ふじたでん",
    "日本マクドナルド": "にほんまくどなるど",
    "日米構造協議": "にちべいこうぞうきょうぎ",
    "通商代表": "つうしょうだいひょう",
    "鉢巻き": "はちまき",
    "通産省": "つうさんしょう",
    "茨城県阿見町": "いばらきけんあみまち",
    "荒川沖店": "あらかわおきてん",
    "相模原店": "さがみはらてん",
    "店頭市場": "てんとうしじょう",
    "粗利率": "あらりりつ",
    "利幅": "りはば",
    "ウォルマート": "うぉるまーと",
    "ベインキャピタル": "べいんきゃぴたる",
    "KKR": "けーけーあーる",
    "公開買い付け": "こうかいかいつけ",
    "取締役会": "とりしまりやくかい",
    "課徴金": "かちょうきん",
    "連邦破産法": "れんぽうはさんほう",
    "社債": "しゃさい",
    "出生数": "しゅっしょうすう",
    "家電量販店": "かでんりょうはんてん",
    "PPIH": "ぴーぴーあいえいち",
    "一日がかり": "いちにちがかり",
    "池袋サンシャインシティ": "いけぶくろさんしゃいんしてぃ",
  },
  "images": {k: {"prompt": v} for k, v in images.items()},
  "segments": [
    {"id": "op", "kind": "opening", "blocks": op},
    {"id": "ch01", "kind": "chapter", "title": "ベビーベッドは二度売れない", "blocks": ch01},
    {"id": "ch02", "kind": "chapter", "title": "石の上にも三年", "blocks": ch02},
    {"id": "ch03", "kind": "chapter", "title": "10年で100店", "blocks": ch03},
    {"id": "ch04", "kind": "chapter", "title": "親会社が背負ったもの", "blocks": ch04},
    {"id": "ch05", "kind": "chapter", "title": "おもちゃは売れているのに", "blocks": ch05},
    {"id": "ch06", "kind": "chapter", "title": "新たな遊び場", "blocks": ch06},
  ],
  "ident_image": "kashihara-heli-1992",
  "credits": {"image": "credits-cart", "sources": [
    "日本トイザらス株式会社 プレスリリース",
    "パン・パシフィック・インターナショナルホールディングス IR資料・ニュースリリース（2026年）",
    "Toys \"R\" Us, Inc. 米証券取引委員会への提出書類（年次報告書・四半期報告書）",
    "東京商工リサーチ、帝国データバンク 倒産・企業情報（2018年、2026年）",
    "国立国会図書館 国会会議録検索システム（1990〜1999年）",
    "衆議院 制定法律「大規模小売店舗法の一部を改正する法律」（1991年）",
    "George H. W. Bush Presidential Library「Remarks at the Opening of Toys \"R\" Us in Kashihara, Japan」（1992年）",
    "Harvard Business School ケース教材「Toys \"R\" Us Japan」",
    "国際経済交流財団『Journal of Japanese Trade & Industry』（1991年）",
    "一般社団法人日本玩具協会 玩具市場規模",
    "厚生労働省 人口動態統計",
    "日本経済新聞、時事通信、共同通信、新潟日報",
    "UPI、Baltimore Sun、CNN",
    "ダイヤモンド・チェーンストアオンライン、流通ニュース、ITmedia、プレジデントオンライン",
  ]},
  "thumbnail": {"image": "kashihara-heli-1992", "lines": ["トイザらス", "なぜ倒産？", "大統領が来た店だったのに…"]},
  "thumbnail_variants": [
    {"image": "kidult-shelves-2026", "lines": ["おもちゃは過去最高", "なのに倒産", "トイザらスに何が？"]},
    {"image": "first-store-queue-1991", "lines": ["1000人が並んだ", "黒船", "トイザらスはなぜ倒産した？"]},
  ],
  "description": {
    "intro": [
      "1991年12月、茨城県阿見町に開いた日本1号店には、開店前から1,000人を超える行列ができました。翌1992年1月には、奈良県の橿原店の開店にアメリカのブッシュ大統領が駆けつけ、大型店の出店を縛っていた大店法を揺るがした「黒船」として、日本中の注目を集めた「トイザらス」。",
      "上陸から10年足らずで100店を超え、2007年1月期には売上高およそ1,944億円に達しましたが、その後は売上が減り続け、2019年1月期から8期連続の最終赤字に。2026年10月1日、日本トイザらスは東京地裁に民事再生法の適用を申請し、10月30日、154店がドン・キホーテを展開するPPIHグループに引き継がれました。"
    ],
    "questions": [
      "なぜ、大統領に祝福された「黒船」は、日本で行き詰まったのでしょうか。",
      "そして、おもちゃ市場が過去最高を記録した時代に、なぜトイザらスは売れなくなったのでしょうか。"
    ],
    "overview": "今回の「栄枯盛衰ファイル」では、1948年にアメリカで生まれた子ども用家具の店から、日本上陸をめぐる大店法と日米構造協議、10年で100店の急成長、アメリカ本社の巨額買収と破綻、日本の8期連続赤字、そして民事再生とドンキへの事業譲渡、アメリカでのブランド復活まで、トイザらスの歴史をたどります。",
    "comment_prompt": "子どもの頃にトイザらスでおもちゃを選んだ思い出や、家族で出かけた店の思い出があれば、ぜひコメント欄で教えてください。",
    "sources_summary": "本動画は、日本トイザらス・PPIHの発表資料、米トイザらスが米証券取引委員会に提出した年次報告書、東京商工リサーチ・帝国データバンクの企業情報、国会会議録、大統領の公式演説録、日本玩具協会・厚生労働省の統計、当時の新聞・専門メディアの報道などを参考に制作しています。",
    "main_sources": ["日本トイザらス","パン・パシフィック・インターナショナルホールディングス（PPIH）","Toys \"R\" Us, Inc.（米SEC提出書類）","東京商工リサーチ","帝国データバンク","国会会議録検索システム","George H. W. Bush Presidential Library","日本玩具協会","厚生労働省","日本経済新聞","時事通信","共同通信","UPI","ダイヤモンド・チェーンストアオンライン","プレジデントオンライン"],
    "notes": [
      "※民事再生は、事業を続けながら借金を整理する再建型の法的整理で、会社を清算する破産とは異なります。帝国データバンク・東京商工リサーチは倒産として集計しています。動画制作時点（2026年11月）で、店舗は「トイザらス」「ベビーザらス」の名前で、PPIHグループの会社が運営しています。",
      "※アメリカのトイザらスの経営破綻（2017〜2018年）と、日本トイザらスの民事再生（2026年）は別の手続きです。日本トイザらスは2018年1月期まで黒字でした。",
      "※譲渡価額およそ28億8,000万円は東京商工リサーチの報道によるものです。日本経済新聞は取得総額を100億円規模と報じていました。",
      "※店舗数は時点によって異なります（2026年6月末158店、PPIHグループへの承継154店）。",
      "※1990年代の数字の一部（売上1,000億円・64店すべて黒字、玩具店の倒産件数など）は、国会での参考人・議員の発言によるものです。"
    ],
    "reference_urls": [
      {"title": "東京商工リサーチ 日本トイザらスが民事再生法申請（2026年10月）", "url": "https://tsr-net.co.jp/news/tsr/detail/1203287_1521.html"},
      {"title": "帝国データバンク 倒産速報 日本トイザらス（2026年10月）", "url": "https://www.tdb.co.jp/report/bankruptcy/flash/5265/"},
      {"title": "東京商工リサーチ 譲渡価額などの続報（2026年10月）", "url": "https://www.tsr-net.co.jp/data/detail/1203331_1527.html"},
      {"title": "PPIH 日本トイザらスの事業譲受に関するお知らせ（2026年10月1日）", "url": "https://ppih.co.jp/ir/library/earnings/pdf/b7434043d4601e5b6a375312b8a2b18e.pdf"},
      {"title": "PPIH 事業譲渡の実行に関するお知らせ（2026年11月2日）", "url": "https://ppih.co.jp/news/pdf/news_261102_1000.pdf"},
      {"title": "George H. W. Bush Presidential Library 橿原店開店での演説（1992年1月7日）", "url": "https://www.bush41library.gov/digital-research-room/finding-aid/public-papers/remarks-opening-toys-r-us-kashihara-japan"},
      {"title": "UPI Bush salutes Toys R Us in Japan（1992年1月7日）", "url": "https://www.upi.com/Archives/1992/01/07/Bush-salutes-Toys-R-Us-in-Japan/6493967600014/"},
      {"title": "Baltimore Sun 日本1号店の開店ルポ（1991年12月20日）", "url": "https://www.baltimoresun.com/1991/12/20/toys-r-us-is-a-big-hit-in-japan-retailer-overcame-trade-obstacles/"},
      {"title": "国会会議録 新潟出店と大店法をめぐる質疑（1990年4月21日）", "url": "https://kokkai.ndl.go.jp/txt/111805261X01319900421/90"},
      {"title": "国会会議録 参考人による日本トイザらスの説明（1998年5月14日）", "url": "https://kokkai.ndl.go.jp/txt/114214062X01219980514/70"},
      {"title": "衆議院 大規模小売店舗法の一部を改正する法律（1991年）", "url": "https://www.shugiin.go.jp/Internet/itdb_housei.nsf/html/houritsu/12019910524080.htm"},
      {"title": "Toys \"R\" Us, Inc. 年次報告書（2006年度、日本事業の粗利率）", "url": "https://www.sec.gov/Archives/edgar/data/1005414/000119312507115768/d10k.htm"},
      {"title": "Toys \"R\" Us, Inc. 四半期報告書（2017年、連邦破産法11条の申請）", "url": "https://www.sec.gov/Archives/edgar/data/1005414/000100541417000047/tru10281710q.htm"},
      {"title": "東京商工リサーチ 日本トイザらスの2018年1月期決算", "url": "https://www.tsr-net.co.jp/data/detail/1189075_1527.html"},
      {"title": "日本玩具協会 玩具市場規模と人口の推移（2006〜2025年度）", "url": "https://www.toys.or.jp/pdf/2026/gangu_sijyou_15jinkou_suii_2006_2025.pdf"},
      {"title": "FOX 10 Toys R Us makes major comeback（2026年9月）", "url": "https://www.fox10phoenix.com/news/toys-r-us-makes-major-comeback-120-new-stores-opening-across-us-holiday-season"}
    ],
    "hashtags": ["トイザらス","ベビーザらス","ドンキホーテ","民事再生","黒船","大店法","おもちゃ","キダルト","平成レトロ","企業史"]
  },
}

out = Path(__file__).resolve().parent / "episode.json"
json.dump(ep, open(out, "w"), ensure_ascii=False, indent=2)
total = 0
for s in ep["segments"]:
    n = sum(len(re.sub(r"\[([^|\]]+)\|[^\]]+\]", r"\1", l)) for b in s["blocks"] for l in b["lines"])
    total += n
    print(s["id"], len(s["blocks"]), "blocks", n, "chars")
print("total", total, "chars;", len(images), "images")
