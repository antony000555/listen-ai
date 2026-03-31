import pandas as pd
import random
import os

base_negative_scenarios = [
    '學校網路真的爛到想哭', '學餐又貴又難吃', '選課系統根本是垃圾', '室友每天半夜不睡覺打遊戲', 
    '行政效率慢到不可思議', '公車老是遲到', '宿舍洗衣機又壞了', '圖書館位置永遠被佔用', 
    '期末考範圍根本在搞人', '教授上課都在念投影片', '冷氣卡又被吃掉', '校園角落到了晚上黑漆漆的', 
    '系辦態度有夠差', '腳踏車又被偷了', '必修課被當，人生無望', '下雨天校園就會積水', 
    '報告分組遇到雷雷隊友', '校方不聽學生意見', '宿舍熱水忽冷忽熱', '機車停車位根本找不到',
    '體育課強制考游泳真的討厭','又被教授點名上台超級丟臉','校慶活動無聊到爆','社團迎新還要繳一堆錢',
    '影印部阿姨臉超級臭','這學期通識又沒抽到','宿舍網路鎖得超級嚴格','學校餐廳又漲價了',
    '選修課停開竟然沒通知','操場跑道又在施工','廁所衛生紙又沒了','校車司機開車有夠急',
    '教授說期末報告要上萬字，根本刁難','宿舍抽籤機率也太低了吧','每天爬那長斜坡真的要人命','學校又發無意義的問卷',
    '獎學金申請手續超級繁瑣','校方網站設計超不直覺','系學會費到底花去哪了','成績出來了真的慘不忍睹',
    '又被路上的野狗追','圖書館冷氣強到像冰庫','教室椅子超難坐','通識課教授評分超主觀',
    '宿舍管理員總是管東管西','選課完全黑箱作業','打工的薪水被學校拖欠','學校都不維護公共設施',
    '體育館器材破爛不堪','每到考試週就沒有讀書位','做專題做到要肝硬化','這堂課根本是廢課'
]

base_neutral_scenarios = [
    '請問一下學餐營業到幾點？', '這學期的行事曆出來了嗎？', '有人知道這堂課的評分方式嗎？', '禮拜三的校車時刻表在哪看？',
    '明天的課程改在線上進行。', '今天圖書館開放到晚上十點。', '想請問有人撿到一串鑰匙嗎？', '體育館本週維護暫停開放。',
    '請問有沒有人修過林教授的課？', '下週就是期中考週了。', '學校即將舉辦校慶活動。', '宿舍今天下午要進行消毒。',
    '行政大樓三樓是教務處。', '有人想一起團購教科書嗎？', '選課結果今天會公布。', '本學期的退選日期到這個月底。',
    '請問搭公車到火車站要多久？', '新生訓練在下週一舉行。', '校園內請勿騎乘私人電動車。', '大家期末報告都做完了嗎？',
    '請問學務處的辦公時間？','有哪位同學能借我筆記？','明天社團有迎新茶會','有人在操場遺失水壺嗎',
    '校長會出席明天的畢業典禮','這是本學期的課表','請問通識課的加簽單去哪裡拿？','今晚是校園演唱會',
    '學校附近有什麼推薦的店嗎？','計中電腦目前都可以正常使用。','圖書借閱期限快到了','請記得繳交宿舍費',
    '明天有校外參訪活動','教授把講義放上網路學園了','請問一下，大一英文要怎麼抵免？','本週五全校停課一天',
    '聽說下學期會有新的通識課','選課系統將於明日關閉','校園志工招募中','學生證補辦需要幾個工作天？',
    '有人知道機車停車證怎麼申請嗎？','今天天氣蠻舒服的','學校公布了最新的防疫規定','系上將舉辦企業參訪',
    '請問二手書交易版在哪裡？','下週有就業博覽會','社團評鑑將在週末進行','圖書館借閱數量上限是幾本？',
    '保健室有提供冰敷袋嗎？','有人要一起合租套房嗎？','今天學餐的菜單跟昨天一樣','這門課的期末考是開書考'
]

prefixes = ['', '真的想問', '大家覺得', '認真說，', '唉，', '有人跟我一樣覺得', '說實話，', '其實', '到底為什麼']
suffixes_negative = ['', '...真的是受夠了。', ' ==', ' QQ', '，要瘋了。', '，有沒有搞錯啊？', '，心好累。']
suffixes_neutral = ['', '？', '，謝謝大家。', '。', '？有人能解答嗎？', '，麻煩了。']

def get_200_unique(scenarios, suffix_list, max_len=200):
    unique_set = set()
    while len(unique_set) < max_len:
        s = random.choice(scenarios)
        p = random.choice(prefixes)
        suf = random.choice(suffix_list)
        res = p + s + suf
        if len(res) > 5:
            unique_set.add(res)
    return list(unique_set)

distinct_negative = get_200_unique(base_negative_scenarios, suffixes_negative, 200)
distinct_neutral = get_200_unique(base_neutral_scenarios, suffixes_neutral, 200)

print(f"Generated {len(distinct_negative)} distinct negative sentences and {len(distinct_neutral)} neutral.")

def expand_to_limit(sentences, target_size, noise_list):
    res = list(sentences)
    while len(res) < target_size:
        base = random.choice(sentences)
        noise = random.choice(noise_list)
        new_sent = base + noise
        if new_sent not in res:
            res.append(new_sent)
    return res

expanded_negative = expand_to_limit(distinct_negative, 600, [' （無奈', '，唉唉', '，氣死我了', ' 凸-_-凸', ' 真的超煩', ' 傻眼'])
expanded_neutral = expand_to_limit(distinct_neutral, 600, [' （求問', ' 感謝大大', ' 推', ' 幫推', ' 謝謝', ' 拜託了大家'])

df_new_neg = pd.DataFrame({'content': expanded_negative, 'SENTIMENT': 'negative'})
df_new_neu = pd.DataFrame({'content': expanded_neutral, 'SENTIMENT': 'neutral'})

df_orig = pd.read_csv('sentiment_result.csv')
df_orig['SENTIMENT'] = df_orig['SENTIMENT'].str.lower().fillna('neutral')

# Downsample positive identically to 600
df_pos = df_orig[df_orig['SENTIMENT'] == 'positive'].sample(600, random_state=42)

df_final = pd.concat([df_pos, df_new_neg, df_new_neu], ignore_index=True)
df_final.to_csv('sentiment_result_augmented.csv', index=False, encoding='utf-8-sig')

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

X = df_final['content']
y = df_final['SENTIMENT']

vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
X_tfidf = vectorizer.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_tfidf, y, test_size=0.2, stratify=y, random_state=42)

clf = LinearSVC(random_state=42, class_weight='balanced', dual=False, C=1.0)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print('\n=== Evaluation (200 Distinct -> 600 Extrapolated per class) ===')
print(classification_report(y_test, y_pred))

joblib.dump(clf, 'svm_model.pkl')
joblib.dump(vectorizer, 'tfidf_vectorizer.pkl')
print('Done!')