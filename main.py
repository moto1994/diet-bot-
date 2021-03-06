from flask import Flask, request, abort
import os
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

import re
import pickle
import random
import sqlite3

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
f = open("./lawson_list.txt","rb")
list_row = pickle.load(f)
f02 = open("./seven_list.txt","rb")
list_row02 = pickle.load(f02)

#基礎代謝を計算する関数
def base_energy(tall, weight, age, sex):
    if sex == 1:
        result = 13.397 * weight + 4.799 * tall - 5.677 * age + 88.362
        return result
    else:
        result = 9.247 * weight + 3.098 * tall - 4.33 * age + 447.593
    
    result = (result * 1.75) -1000
    return round(result)

#朝と昼・夜のカロリーを計算
def create_before(aim_kcal):
    return int(aim_kcal * 0.2)
def create_after(aim_kcal):    
    return int(aim_kcal * 0.4)

#メニューをランダムに選ぶ関数
def make_menu(aim_num, conv_list):
    menu = []
    x = 0
    #目標カロリーのプラマイ100kcalになるまでループ
    for i in range(150):
        i = random.choice(conv_list)
        if aim_num -100 <= x <= aim_num + 100:
            return menu
            break
        if i[0] + x <= aim_num + 100:
            x += i[0]
            menu.append(i)
        else:
            continue      



@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    word = event.message.text
    if word in ["ローソン"]:
        #朝と昼・夜の基礎代謝データを呼び出し
        profile = line_bot_api.get_profile(event.source.user_id)
        user_id = profile.user_id
        conn = sqlite3.connect('database.sqlite3')
        c = conn.cursor()
        c.execute('SELECT * FROM user WHERE id=?', (user_id,))
        list1 = c.fetchone()
        before_noon = list1[1]
        after_noon = list1[2]
        conn.commit()
        conn.close()
        today_morning = make_menu(before_noon, list_row)
        today_lunch = make_menu(after_noon, list_row)
        today_dinner= make_menu(after_noon, list_row)
        today_menu = []
        for i in today_morning:
            today_menu .append( "\n朝ご飯は" + str(i))
        for i in today_lunch:
            today_menu.append("\n昼ご飯は" + str(i))
        for i in today_dinner:
            today_menu.append("\n夜ご飯は" + str(i))
        reply = ','.join(today_menu)

        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply))

    elif word in ["セブン"]:
        #朝と昼・夜の基礎代謝データを呼び出し
        profile = line_bot_api.get_profile(event.source.user_id)
        user_id = profile.user_id
        conn = sqlite3.connect('database.sqlite3')
        c = conn.cursor()
        c.execute('SELECT * FROM user WHERE id=?', (user_id,))
        list1 = c.fetchone()
        before_noon = list1[1]
        after_noon = list1[2]
        conn.commit()
        conn.close()
        today_morning = make_menu(before_noon, list_row02)
        today_lunch = make_menu(after_noon, list_row02)
        today_dinner= make_menu(after_noon, list_row02)
        today_menu = []
        for i in today_morning:
            today_menu .append( "\n朝ご飯は" + str(i))
        for i in today_lunch:
            today_menu.append("\n昼ご飯は" + str(i))
        for i in today_dinner:
            today_menu.append("\n夜ご飯は" + str(i))
        reply = ','.join(today_menu)

        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply))

    elif word in ["設定"]:
        setup_text = """以下のフォーマットで入力してください\
        
        登録。身長-体重-年齢-性別（１男性　or　2女性）
        ＊全て半角数字をご使用してください
        ＊例　　　　登録。168-68-24-1
        """
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=setup_text))

    elif 0 <= word.find('登録。') :
        #受けとったデータを身長、体重、年齢、性別に分ける
        #それをbase_energyに渡す
        personal_data = event.message.text
        personal_data = personal_data.replace("登録。", "")
        personal_data = personal_data.replace("-", ",")
        personal_data = personal_data.split(',')
        tall = int(personal_data[0])
        weight = int(personal_data[1])
        age = int(personal_data[2])
        sex = int(personal_data[3])
        aim_kcal = base_energy(tall, weight, age, sex)
        #各食ごとのカロリーを算出
        #データベースに書き込み
        profile = line_bot_api.get_profile(event.source.user_id)
        prof_dict = {}
        prof_dict["id"] = profile.user_id
        prof_dict["before_noon"] = create_before(aim_kcal)
        prof_dict["after_noon"] = create_after(aim_kcal)
        conn = sqlite3.connect('database.sqlite3')
        c = conn.cursor()
        c.execute('insert into user(id, before_noon, after_noon) values(:id, :before_noon, :after_noon);', prof_dict)
        conn.commit()
        conn.close()

        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="設定は完了したよ"))

    else:
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ローソンかセブンか設定と入力してください"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    app.run()