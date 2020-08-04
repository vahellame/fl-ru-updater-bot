# -*- coding: utf-8 -*-

import json
import logging
import re

import psycopg2
import requests
import telebot

from bs4 import BeautifulSoup
from psycopg2.extras import Json
from psycopg2.extras import RealDictCursor
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler

from config import TELEGRAM_API_TOKEN, POSTGRES_CONNECTION_PARAMS
from threading import Thread
from contextlib import closing


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

start_keyboard = [
    [InlineKeyboardButton("Выбрать специализацию", callback_data="choose_root_specialization")],
    [InlineKeyboardButton("Связаться с разработчиком", url="vcard.is/vahellame")]
]
root_keyboard = [
    [InlineKeyboardButton("Разработка сайтов", callback_data="razrabotka-sajtov"),
     InlineKeyboardButton("Тексты", callback_data="teksty")],

    [InlineKeyboardButton("Дизайн и Арт", callback_data="dizajn"),
     InlineKeyboardButton("Программирование", callback_data="programmirovanie")],

    [InlineKeyboardButton("Аудио/Видео", callback_data="audio-video"),
     InlineKeyboardButton("Аутсорсинг и консалтинг", callback_data="konsalting")],

    [InlineKeyboardButton("Реклама и Маркетинг", callback_data="reklama-marketing"),
     InlineKeyboardButton("Разработка игр", callback_data="razrabotka-igr")],

    [InlineKeyboardButton("Переводы", callback_data="perevody"),
     InlineKeyboardButton("Анимация и флеш", callback_data="animatsiya-multiplikatsiya")],

    [InlineKeyboardButton("Фотография", callback_data="fotografiya"),
     InlineKeyboardButton("3D Графика", callback_data="3d-Grafika")],

    [InlineKeyboardButton("Инжиниринг", callback_data="inzhiniring"),
     InlineKeyboardButton("Обучение и консультации", callback_data="obuchenie")],

    [InlineKeyboardButton("Оптимизация (SEO)", callback_data="optimizatsiya-seo"),
     InlineKeyboardButton("Архитектура/Интерьер", callback_data="arkhitektura-interer")],

    [InlineKeyboardButton("Полиграфия", callback_data="poligrafiya"),
     InlineKeyboardButton("Менеджмент", callback_data="menedzhment")],

    [InlineKeyboardButton("Мобильные приложения", callback_data="mobilnye-prilozheniya"),
     InlineKeyboardButton("Сети и инфосистемы", callback_data="seti-i-informatsionnye-sistemy")],

    [InlineKeyboardButton("Назад", callback_data="back|root")]
]
user_project_types_default_status = {
    "razrabotka-sajtov": {
        "copywriter-razrabotka-sajtov": False,
        "web-programmist-razrabotka-sajtov": False,
        "web-dizajner-razrabotka-sajtov": False,
        "html-verstalschik": False,
        "sajt-pod-kljuch": False,
        "kontent-menedzher-razrabotka-sajtov": False,
        "landing": False,
        "rukovoditel-menedzher-internet-proektov-razrabotka-sajtov": False,
        "internet-magazinyi": False,
        "qa-testirovanie-razrabotka-sajtov": False,
        "dorabotka-saytov": False,
        "razrabotchik-cms": False,
        "proektirovanie": False,
        "wordpress": False,
        "adaptivnyiy-dizayn": False,
        "yuzabiliti-analiz": False,
        "flash-dizajner-razrabotchik-razrabotka-sajtov": False,
        "razrabotchik-wap-pda-sajtov": False,
        "no_speciality": False
    },
    "teksty": {
        "copywriter-teksty": False,
        "specialist-rasshifrovka-audio-video-zapisej": False,
        "korrektor": False,
        "kontent-menedzher-teksty": False,
        "rerajter": False,
        "specialist-napisanie-statej": False,
        "specialist-skanirovanie-raspoznavanie": False,
        "specialist-po-postingu": False,
        "specialist-napisanie-tekstov-rechej-raportov": False,
        "specialist-napisanie-referatov-kursovyh-diplomov-teksty": False,
        "specialist-napisanie-stihov-poem-esse": False,
        "tekstyi-na-inostrannyih-yazyikah": False,
        "specialist-sozdanie-subtitrov": False,
        "specialist-nejming-razrabotka-sloganov": False,
        "specialist-napisanie-scenariev-teksty": False,
        "specialist-napisanie-rezume": False,
        "specialist-napisanie-novostej-press-relizov": False,
        "specialist-napisanie-tz-help-manualov": False,
        "no_speciality": False
    },
    "dizajn": {
        "web-dizajner-verstalschik-dizajn": False,
        "dizajner-logotipov": False,
        "illustrator-art": False,
        "dizajner-poligrafii-dizajn": False,
        "dizajner-bannerov-dizajn": False,
        "chastnyj-dizajner-interjera-dizajn": False,
        "hudozhnik-vektornoj-grafiki": False,
        "dizajner-firmennogo-stilja": False,
        "dizajner-prezentacij": False,
        "2d-animator-art": False,
        "hudozhnik-2d-personazhej-art": False,
        "dizajner-upakovki-dizajn": False,
        "hudozhnik": False,
        "dizajner-naruzhnoj-reklamy": False,
        "hudozhnik-ikonok": False,
        "hand-made": False,
        "landshaftnyj-dizajner-landshafta-dizajn": False,
        "dizayn-interfeysov-prilojeniy": False,
        "3d-illustrator-art": False,
        "hudozhnik-3d-personazhej-art": False,
        "dizajner-trikotazh-tekstil": False,
        "kontsept-art": False,
        "dizajner-interfejsov": False,
        "tehnicheskij-dizajner": False,
        "hudozhnik-piksel-arta-art": False,
        "promyshlennyj-dizajner": False,
        "infografika": False,
        "hudozhnik-komiksov": False,
        "hudozhnik-graffiti": False,
        "dizajner-vystavochnyh-stendov": False,
        "dizajner-mashinnoj-vyshivki": False,
        "razrabotchik-shriftov-dizajn": False,
        "kartograf": False,
        "hudozhnik-ajerografija": False,
        "no_speciality": False
    },
    "programmirovanie": {
        "web-programmist-programmirovanie": False,
        "prikladnoj-programmist": False,
        "qa-testirovanie-programmirovanie": False,
        "1c-programmist": False,
        "programmist-baz-dannyh": False,
        "programmist-igr-programmirovanie": False,
        "sistemnyj-administrator": False,
        "razrabotka-chat-botov": False,
        "sistemnyj-administrator-programmirovanie": False,
        "parsing-dannyih": False,
        "programmist-sotovye-telefony-kpk": False,
        "razrabotka-CRM-i-ERP": False,
        "plaginyi_stsenarii_utilityi": False,
        "specialist-zaschita-informacii": False,
        "razrabotchik-vstraivaemyh-sistem": False,
        "specialist-web-proektirovanie": False,
        "interaktivnyie-prilojeniya": False,
        "upravlenie-proektami-razrabotki": False,
        "makrosyi-dlya-igr-programmirovanie": False,
        "blockchain": False,
        "no_speciality": False
    },
    "audio-video": {
        "videomontazher": False,
        "specialist-po-muzyke-zvukam-audio": False,
        "diktor": False,
        "videodizajner-audio": False,
        "audiomontazher": False,
        "videooperator": False,
        "specialist-sozdanie-subtitrov-text": False,
        "videoprezentatsii": False,
        "rejissura": False,
        "videoinfografika": False,
        "kasting": False,
        "svadebnyj-videooperator": False,
        "raskadrovki": False,
        "no_speciality": False
    },
    "konsalting": {
        "vvod-i-obrabotka-dannyih_teksta": False,
        "konsultant-perevodchik": False,
        "buhgalter-konsultant": False,
        "jurist-konsultant": False,
        "repetitory-prepodavateli-konsalting": False,
        "marketolog": False,
        "konsultant-razrabotka-sajtov": False,
        "dizajner-konsultant": False,
        "obrabotka-zakazov": False,
        "programmist-konsultant": False,
        "obrabotka-pisem": False,
        "biznes-konsultant": False,
        "virtualnyiy-assistent": False,
        "obslujivanie-klientov-i-podderjka": False,
        "tehnicheskaya-podderjka": False,
        "finansovyi-konsultant": False,
        "seo-konsultant": False,
        "podderjka-po-telefonu": False,
        "kadrovyiy-uchet-i-zarplata": False,
        "statisticheskiy-analiz": False,
        "specialist-erp-sistemy": False,
        "obrabotka-platejey": False,
        "usability-konsultant": False,
        "no_speciality": False
    },
    "reklama-marketing": {
        "SMM-marketing-v-sotssetyah": False,
        "specialist-kontekstnaja-reklama-reklama": False,
        "specialist-sbor-obrabotka-informacii": False,
        "prodaji-i-generatsiya-lidov": False,
        "kreativ": False,
        "specialist-reklamnye-koncepcii": False,
        "pr-menedzher": False,
        "telemarketing-i-prodaji-po-telefonu": False,
        "issledovaniya-ryinka-i-oprosyi": False,
        "organizator-meroprijatij": False,
        "specialist-biznes-plany": False,
        "marketolog-analitik": False,
        "smo-reklama": False,
        "specialist-mediaplanirovanie": False,
        "promo-personal": False,
        "no_speciality": False
    },
    "razrabotka-igr": {
        "illustrator-razrabotka-igr": False,
        "specialist-3d-modelirovanie-razrabotka-igr": False,
        "2d-animator-razrabotka-igr": False,
        "programmist-igr-razrabotka-igr": False,
        "testirovanie-igr-QA": False,
        "3d-animator-razrabotka-igr": False,
        "hudozhnik-piksel-arta-razrabotka-igr": False,
        "ozvuchivanie-igr": False,
        "unity": False,
        "makrosyi-dlya-igr-razrabotka-igr": False,
        "flash-flex-programmist-razrabotka-igr": False,
        "razrabotchik-koncepta-eskizov": False,
        "videoroliki": False,
        "no_speciality": False
    },
    "perevody": {
        "perevod-tekstov-obschey-tematiki": False,
        "perevodchik-tehnicheskij": False,
        "perevodchik-hudozhestvennyh-tekstov-literatury": False,
        "redaktirovanie-perevodov": False,
        "lokalizatsiya-po-saytov-i-igr": False,
        "specialist-po-korrespondencii": False,
        "ustnyiy-perevod": False,
        "no_speciality": False
    },
    "animatsiya-multiplikatsiya": {
        "dizajner-bannerov-animacija": False,
        "dizajner-bannerov-flash": False,
        "specialist-po-muzyke-zvukam-animacija": False,
        "2d-animator-animacija": False,
        "hudozhnik-2d-personazhej-animacija": False,
        "3d-animator-animacija": False,
        "hudozhnik-3d-personazhej-animacija": False,
        "geym-art": False,
        "flash-dizajner-razrabotchik-flash": False,
        "flash-flex-programmist-flash": False,
        "specialist-scenarii-dlja-animacii": False,
        "2d-animator-flash": False,
        "dizajner-flash-grafiki": False,
        "specialist-raskadrovka": False,
        "razrabotchik-virtualnye-tury": False,
        "no_speciality": False
    },
    "fotografiya": {
        "retusher": False,
        "hudozhestvennyj-fotograf": False,
        "reklamnyj-fotograf": False,
        "fotograf-modelej": False,
        "fotograf-reporter": False,
        "svadebnyj-fotograf-na-svadbu": False,
        "fotograf-interjerov": False,
        "promyshlennaya-fotosyemka": False,
        "no_speciality": False
    },
    "3d-Grafika": {
        "specialist-3d-modelirovanie-3d-grafika": False,
        "chastnyj-dizajner-interjera-3d-grafika": False,
        "videodizajner-3d-grafika": False,
        "3d-animator-3d-grafika": False,
        "3d-illustrator-3d-grafika": False,
        "hudozhnik-3d-personazhej-3d-grafika": False,
        "dizajner-eksterjerov": False,
        "vizualizator-predmetov": False,
        "no_speciality": False
    },
    "inzhiniring": {
        "chertezhnik": False,
        "inzhener-mashinostroenija": False,
        "inzhener-konstruktor": False,
        "inzhener-elektrik": False,
        "inzhener-slabotochnyh-setej-avtomatizacii": False,
        "smetyi": False,
        "inzhener-otoplenie-ventiljacija": False,
        "razrabotka-radioelektronnyih-sistem": False,
        "inzhener-vodosnabzhenija-kanalizacii": False,
        "inzhener-tehnolog": False,
        "gazosnabjenie": False,
        "no_speciality": False
    },
    "obuchenie": {
        "specialist-napisanie-referatov-kursovyh-diplomov-obuchenie": False,
        "repetitory-prepodavateli-obuchenie": False,
        "psiholog": False,
        "inostrannyie-yazyiki": False,
        "tehnicheskie-distsiplinyi": False,
        "doshkolnoe-obrazovanie": False,
        "gumanitarnyie-distsiplinyi": False,
        "konsultant-puteshestvija": False,
        "stilist": False,
        "no_speciality": False
    },
    "optimizatsiya-seo": {
        "specialist-kontekstnaja-reklama-seo": False,
        "seo-optimizator": False,
        "seo-copywriter": False,
        "smo-seo": False,
        "prodavec-ssylok": False,
        "sem": False,
        "no_speciality": False
    },
    "arkhitektura-interer": {
        "chastnyj-dizajner-interjera-arhitektura-interier": False,
        "chastnyj-arhitektor": False,
        "vizualizator": False,
        "landshaftnyj-dizajner-landshafta-interier": False,
        "specialist-makety": False,
        "no_speciality": False
    },
    "poligrafiya": {
        "dizajner-poligrafii-poligrafija": False,
        "dizajner-upakovki-poligrafija": False,
        "verstalschik-poligrafii": False,
        "specialist-dopechatnaja-podgotovka": False,
        "verstka-elektronnyih-izdaniy": False,
        "razrabotchik-shriftov-poligrafija": False,
        "no_speciality": False
    },
    "menedzhment": {
        "rukovoditel-menedzher-internet-proektov-menedzhment": False,
        "menedzher-po-prodazham": False,
        "hr-menedzher-po-personalu-rekruter": False,
        "upravlenie-onlayn-reputatsiey": False,
        "kreativnyj-art-direktor": False,
        "no_speciality": False
    },
    "mobilnye-prilozheniya": {
        "Google-Android": False,
        "iOS": False,
        "dizayn": False,
        "prototipirovanie": False,
        "Windows-Phone": False,
        "no_speciality": False
    },
    "seti-i-informatsionnye-sistemy": {
        "setevoe-administrirovanie": False,
        "administrirovanie-baz-dannyih": False,
        "ERP-i-CRM-integratsii": False,
        "no_speciality": False
    }
}

bot = telebot.TeleBot(TELEGRAM_API_TOKEN)

with open("project_types_names.json", "r", encoding='utf-8') as file:
    project_types_names = json.load(file)


def find_dict_key(d, key):
    keys = list(d)

    for k in keys:
        if key in d[k]:
            return k


def execute_sql(sql_query, connection_params):
    with closing(psycopg2.connect(cursor_factory=RealDictCursor,
                                  dbname=connection_params["dbname"],
                                  user=connection_params["user"],
                                  password=connection_params["password"],
                                  host=connection_params["host"],
                                  port=connection_params["port"],
                                  )) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            try:
                records = cursor.fetchall()
                result = []
                for record in records:
                    result.append(dict(record))
                return result
            except psycopg2.ProgrammingError:
                pass


def prepare_speciality_keyboard(kb_buttons, kb_status, specialization):
    kb = []
    kb_buttons_list = list(kb_buttons)

    while len(kb_buttons_list) > 2:
        buttons_x = kb_buttons_list[:2]
        kb.append(buttons_x)
        kb_buttons_list = kb_buttons_list[2:]
    kb.append(kb_buttons_list)

    for i in range(len(kb)):
        l_2 = len(kb[i])
        for j in range(l_2):
            specialty_link = kb[i][j]
            if kb_status[specialty_link]:
                specialty_status = "✅"
            else:
                specialty_status = ""
            kb[i][j] = InlineKeyboardButton(specialty_status + kb_buttons[specialty_link], callback_data=specialty_link)

    if kb_status["no_speciality"]:
        specialty_status = "✅"
    else:
        specialty_status = ""
    kb.append([InlineKeyboardButton(specialty_status + "Без специальности",
                                    callback_data="no_speciality|" + specialization)])
    kb.append([InlineKeyboardButton("Назад", callback_data="choose_root_specialization")])

    kb.insert(0,
              [InlineKeyboardButton("Выбрать все", callback_data="select_all+|" + specialization),
               InlineKeyboardButton("Убрать все", callback_data="select_all-|" + specialization)]
              )
    return kb


def start(update, context):
    user = update.message.from_user

    res = execute_sql(f"SELECT * FROM users WHERE telegram_id={user.id}", POSTGRES_CONNECTION_PARAMS)
    if len(res) == 0:
        execute_sql(f"INSERT into users(telegram_id, project_types) \
                      VALUES ({user.id}, {Json(user_project_types_default_status)})", POSTGRES_CONNECTION_PARAMS)

    logger.info("User %s started the conversation.", user.first_name)

    keyboard = start_keyboard
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        "Привет, я бот fl.ru. Я умею присылать проекты по выбранным тобой специализациям",
        reply_markup=reply_markup
    )

    return "s_start"


def b_back_root(update, context):
    query = update.callback_query
    query.answer()
    keyboard = start_keyboard
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Привет, я бот fl.ru. Я умею присылать проекты по выбранным тобой специализациям",
        reply_markup=reply_markup
    )
    return "s_start"


def b_choose_root_specialization(update, context):
    query = update.callback_query
    query.answer()
    keyboard = root_keyboard
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Выбери специализацию",
        reply_markup=reply_markup
    )
    return "s_choose_root_specialization"


def b_specialization(update, context):
    query = update.callback_query
    query.answer()

    specialization = query.data

    telegram_id = query.from_user["id"]
    user = execute_sql(f"SELECT * FROM users WHERE telegram_id={telegram_id}", POSTGRES_CONNECTION_PARAMS)[0]

    kb_buttons = project_types_names[specialization]["local_types"]
    kb_status = user["project_types"][specialization]
    keyboard = prepare_speciality_keyboard(kb_buttons, kb_status, specialization)

    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        text=project_types_names[specialization]["name"],
        reply_markup=reply_markup
    )

    return specialization


def b_speciality(update, context):
    query = update.callback_query
    query.answer()

    specialty = query.data
    specialization = find_dict_key(user_project_types_default_status, specialty)
    telegram_id = query.from_user["id"]

    user = execute_sql(f"SELECT * FROM users WHERE telegram_id={telegram_id}", POSTGRES_CONNECTION_PARAMS)[0]
    user_project_types = user["project_types"]
    user_project_types[specialization][specialty] = not user_project_types[specialization][specialty]

    execute_sql(f"UPDATE users SET project_types={Json(user_project_types)} \
                  WHERE telegram_id={telegram_id}", POSTGRES_CONNECTION_PARAMS)

    kb_buttons = project_types_names[specialization]["local_types"]
    kb_status = user_project_types[specialization]

    keyboard = prepare_speciality_keyboard(kb_buttons, kb_status, specialization)
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        text=project_types_names[specialization]["name"],
        reply_markup=reply_markup
    )

    return specialization


def b_speciality_select_all(update, context):
    query = update.callback_query
    query.answer()

    select_all_type, specialization = query.data.split("|")
    telegram_id = query.from_user["id"]

    user = execute_sql(f"SELECT * FROM users WHERE telegram_id={telegram_id}", POSTGRES_CONNECTION_PARAMS)[0]
    user_project_types = user["project_types"]

    if select_all_type == "select_all+":
        for speciality in user_project_types[specialization]:
            user_project_types[specialization][speciality] = True
    elif select_all_type == "select_all-":
        for speciality in user_project_types[specialization]:
            user_project_types[specialization][speciality] = False

    execute_sql(f"UPDATE users SET project_types={Json(user_project_types)} \
                      WHERE telegram_id={telegram_id}", POSTGRES_CONNECTION_PARAMS)

    kb_buttons = project_types_names[specialization]["local_types"]
    kb_status = user_project_types[specialization]

    keyboard = prepare_speciality_keyboard(kb_buttons, kb_status, specialization)
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        text=project_types_names[specialization]["name"],
        reply_markup=reply_markup
    )

    return specialization


def b_speciality_no_speciality(update, context):
    query = update.callback_query
    query.answer()

    _, specialization = query.data.split("|")
    telegram_id = query.from_user["id"]

    user = execute_sql(f"SELECT * FROM users WHERE telegram_id={telegram_id}", POSTGRES_CONNECTION_PARAMS)[0]
    user_project_types = user["project_types"]

    user_project_types[specialization]["no_speciality"] = not user_project_types[specialization]["no_speciality"]

    execute_sql(f"UPDATE users SET project_types={Json(user_project_types)} \
                      WHERE telegram_id={telegram_id}", POSTGRES_CONNECTION_PARAMS)

    kb_buttons = project_types_names[specialization]["local_types"]
    kb_status = user_project_types[specialization]

    keyboard = prepare_speciality_keyboard(kb_buttons, kb_status, specialization)
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        text=project_types_names[specialization]["name"],
        reply_markup=reply_markup
    )

    return specialization


def main():
    updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            "s_start": [CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$")],

            "s_choose_root_specialization": [
                CallbackQueryHandler(b_specialization, pattern="^razrabotka-sajtov$"),
                CallbackQueryHandler(b_specialization, pattern="^teksty$"),
                CallbackQueryHandler(b_specialization, pattern="^dizajn$"),
                CallbackQueryHandler(b_specialization, pattern="^programmirovanie$"),
                CallbackQueryHandler(b_specialization, pattern="^audio-video$"),
                CallbackQueryHandler(b_specialization, pattern="^konsalting$"),
                CallbackQueryHandler(b_specialization, pattern="^reklama-marketing$"),
                CallbackQueryHandler(b_specialization, pattern="^razrabotka-igr$"),
                CallbackQueryHandler(b_specialization, pattern="^perevody$"),
                CallbackQueryHandler(b_specialization, pattern="^animatsiya-multiplikatsiya$"),
                CallbackQueryHandler(b_specialization, pattern="^fotografiya$"),
                CallbackQueryHandler(b_specialization, pattern="^3d-Grafika$"),
                CallbackQueryHandler(b_specialization, pattern="^inzhiniring$"),
                CallbackQueryHandler(b_specialization, pattern="^obuchenie$"),
                CallbackQueryHandler(b_specialization, pattern="^optimizatsiya-seo$"),
                CallbackQueryHandler(b_specialization, pattern="^arkhitektura-interer$"),
                CallbackQueryHandler(b_specialization, pattern="^poligrafiya$"),
                CallbackQueryHandler(b_specialization, pattern="^menedzhment$"),
                CallbackQueryHandler(b_specialization, pattern="^mobilnye-prilozheniya$"),
                CallbackQueryHandler(b_specialization, pattern="^seti-i-informatsionnye-sistemy$"),

                CallbackQueryHandler(b_back_root, pattern="^back|root$"),
            ],

            "razrabotka-sajtov": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|razrabotka-sajtov$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|razrabotka-sajtov$"),

                CallbackQueryHandler(b_speciality, pattern="^copywriter-razrabotka-sajtov$"),
                CallbackQueryHandler(b_speciality, pattern="^web-programmist-razrabotka-sajtov$"),
                CallbackQueryHandler(b_speciality, pattern="^web-dizajner-razrabotka-sajtov$"),
                CallbackQueryHandler(b_speciality, pattern="^html-verstalschik$"),
                CallbackQueryHandler(b_speciality, pattern="^sajt-pod-kljuch$"),
                CallbackQueryHandler(b_speciality, pattern="^kontent-menedzher-razrabotka-sajtov$"),
                CallbackQueryHandler(b_speciality, pattern="^landing$"),
                CallbackQueryHandler(b_speciality, pattern="^rukovoditel-menedzher-internet-proektov-razrabotka-sajtov$"),
                CallbackQueryHandler(b_speciality, pattern="^internet-magazinyi$"),
                CallbackQueryHandler(b_speciality, pattern="^qa-testirovanie-razrabotka-sajtov$"),
                CallbackQueryHandler(b_speciality, pattern="^dorabotka-saytov$"),
                CallbackQueryHandler(b_speciality, pattern="^razrabotchik-cms$"),
                CallbackQueryHandler(b_speciality, pattern="^proektirovanie$"),
                CallbackQueryHandler(b_speciality, pattern="^wordpress$"),
                CallbackQueryHandler(b_speciality, pattern="^adaptivnyiy-dizayn$"),
                CallbackQueryHandler(b_speciality, pattern="^yuzabiliti-analiz$"),
                CallbackQueryHandler(b_speciality, pattern="^flash-dizajner-razrabotchik-razrabotka-sajtov$"),
                CallbackQueryHandler(b_speciality, pattern="^razrabotchik-wap-pda-sajtov$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|razrabotka-sajtov$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "teksty": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|teksty$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|teksty$"),

                CallbackQueryHandler(b_speciality, pattern="^copywriter-teksty$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-rasshifrovka-audio-video-zapisej$"),
                CallbackQueryHandler(b_speciality, pattern="^korrektor$"),
                CallbackQueryHandler(b_speciality, pattern="^kontent-menedzher-teksty$"),
                CallbackQueryHandler(b_speciality, pattern="^rerajter$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-napisanie-statej$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-skanirovanie-raspoznavanie$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-po-postingu$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-napisanie-tekstov-rechej-raportov$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-napisanie-referatov-kursovyh-diplomov-teksty$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-napisanie-stihov-poem-esse$"),
                CallbackQueryHandler(b_speciality, pattern="^tekstyi-na-inostrannyih-yazyikah$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-sozdanie-subtitrov$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-nejming-razrabotka-sloganov$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-napisanie-scenariev-teksty$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-napisanie-rezume$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-napisanie-novostej-press-relizov$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-napisanie-tz-help-manualov$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|teksty$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "dizajn": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|dizajn$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|dizajn$"),

                CallbackQueryHandler(b_speciality, pattern="^web-dizajner-verstalschik-dizajn$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-logotipov$"),
                CallbackQueryHandler(b_speciality, pattern="^illustrator-art$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-poligrafii-dizajn$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-bannerov-dizajn$"),
                CallbackQueryHandler(b_speciality, pattern="^chastnyj-dizajner-interjera-dizajn$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-vektornoj-grafiki$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-firmennogo-stilja$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-prezentacij$"),
                CallbackQueryHandler(b_speciality, pattern="^2d-animator-art$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-2d-personazhej-art$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-upakovki-dizajn$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-naruzhnoj-reklamy$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-ikonok$"),
                CallbackQueryHandler(b_speciality, pattern="^hand-made$"),
                CallbackQueryHandler(b_speciality, pattern="^dizayn-interfeysov-prilojeniy$"),
                CallbackQueryHandler(b_speciality, pattern="^landshaftnyj-dizajner-landshafta-dizajn$"),
                CallbackQueryHandler(b_speciality, pattern="^3d-illustrator-art$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-3d-personazhej-art$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-trikotazh-tekstil$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-interfejsov$"),
                CallbackQueryHandler(b_speciality, pattern="^tehnicheskij-dizajner$"),
                CallbackQueryHandler(b_speciality, pattern="^kontsept-art$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-piksel-arta-art$"),
                CallbackQueryHandler(b_speciality, pattern="^promyshlennyj-dizajner$"),
                CallbackQueryHandler(b_speciality, pattern="^infografika$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-komiksov$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-graffiti$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-vystavochnyh-stendov$"),
                CallbackQueryHandler(b_speciality, pattern="^razrabotchik-shriftov-dizajn$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-mashinnoj-vyshivki$"),
                CallbackQueryHandler(b_speciality, pattern="^kartograf$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-ajerografija$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|dizajn$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "programmirovanie": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|programmirovanie$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|programmirovanie$"),

                CallbackQueryHandler(b_speciality, pattern="^web-programmist-programmirovanie$"),
                CallbackQueryHandler(b_speciality, pattern="^prikladnoj-programmist$"),
                CallbackQueryHandler(b_speciality, pattern="^qa-testirovanie-programmirovanie$"),
                CallbackQueryHandler(b_speciality, pattern="^1c-programmist$"),
                CallbackQueryHandler(b_speciality, pattern="^programmist-baz-dannyh$"),
                CallbackQueryHandler(b_speciality, pattern="^programmist-igr-programmirovanie$"),
                CallbackQueryHandler(b_speciality, pattern="^sistemnyj-administrator$"),
                CallbackQueryHandler(b_speciality, pattern="^razrabotka-chat-botov$"),
                CallbackQueryHandler(b_speciality, pattern="^sistemnyj-administrator-programmirovanie$"),
                CallbackQueryHandler(b_speciality, pattern="^parsing-dannyih$"),
                CallbackQueryHandler(b_speciality, pattern="^programmist-sotovye-telefony-kpk$"),
                CallbackQueryHandler(b_speciality, pattern="^razrabotka-CRM-i-ERP$"),
                CallbackQueryHandler(b_speciality, pattern="^plaginyi_stsenarii_utilityi$"),
                CallbackQueryHandler(b_speciality, pattern="^razrabotchik-vstraivaemyh-sistem$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-zaschita-informacii$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-web-proektirovanie$"),
                CallbackQueryHandler(b_speciality, pattern="^interaktivnyie-prilojeniya$"),
                CallbackQueryHandler(b_speciality, pattern="^upravlenie-proektami-razrabotki$"),
                CallbackQueryHandler(b_speciality, pattern="^makrosyi-dlya-igr-programmirovanie$"),
                CallbackQueryHandler(b_speciality, pattern="^blockchain$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|programmirovanie$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "audio-video": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|audio-video$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|audio-video$"),

                CallbackQueryHandler(b_speciality, pattern="^videomontazher$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-po-muzyke-zvukam-audio$"),
                CallbackQueryHandler(b_speciality, pattern="^diktor$"),
                CallbackQueryHandler(b_speciality, pattern="^audiomontazher$"),
                CallbackQueryHandler(b_speciality, pattern="^videodizajner-audio$"),
                CallbackQueryHandler(b_speciality, pattern="^videooperator$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-sozdanie-subtitrov-text$"),
                CallbackQueryHandler(b_speciality, pattern="^videoprezentatsii$"),
                CallbackQueryHandler(b_speciality, pattern="^videoinfografika$"),
                CallbackQueryHandler(b_speciality, pattern="^rejissura$"),
                CallbackQueryHandler(b_speciality, pattern="^kasting$"),
                CallbackQueryHandler(b_speciality, pattern="^svadebnyj-videooperator$"),
                CallbackQueryHandler(b_speciality, pattern="^raskadrovki$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|audio-video$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "reklama-marketing": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|reklama-marketing$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|reklama-marketing$"),

                CallbackQueryHandler(b_speciality, pattern="^SMM-marketing-v-sotssetyah$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-kontekstnaja-reklama-reklama$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-sbor-obrabotka-informacii$"),
                CallbackQueryHandler(b_speciality, pattern="^prodaji-i-generatsiya-lidov$"),
                CallbackQueryHandler(b_speciality, pattern="^kreativ$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-reklamnye-koncepcii$"),
                CallbackQueryHandler(b_speciality, pattern="^pr-menedzher$"),
                CallbackQueryHandler(b_speciality, pattern="^telemarketing-i-prodaji-po-telefonu$"),
                CallbackQueryHandler(b_speciality, pattern="^issledovaniya-ryinka-i-oprosyi$"),
                CallbackQueryHandler(b_speciality, pattern="^marketolog-analitik$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-biznes-plany$"),
                CallbackQueryHandler(b_speciality, pattern="^organizator-meroprijatij$"),
                CallbackQueryHandler(b_speciality, pattern="^smo-reklama$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-mediaplanirovanie$"),
                CallbackQueryHandler(b_speciality, pattern="^promo-personal$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|reklama-marketing$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "konsalting": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|konsalting$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|konsalting$"),

                CallbackQueryHandler(b_speciality, pattern="^vvod-i-obrabotka-dannyih_teksta$"),
                CallbackQueryHandler(b_speciality, pattern="^buhgalter-konsultant$"),
                CallbackQueryHandler(b_speciality, pattern="^konsultant-perevodchik$"),
                CallbackQueryHandler(b_speciality, pattern="^jurist-konsultant$"),
                CallbackQueryHandler(b_speciality, pattern="^repetitory-prepodavateli-konsalting$"),
                CallbackQueryHandler(b_speciality, pattern="^marketolog$"),
                CallbackQueryHandler(b_speciality, pattern="^konsultant-razrabotka-sajtov$"),
                CallbackQueryHandler(b_speciality, pattern="^obrabotka-zakazov$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-konsultant$"),
                CallbackQueryHandler(b_speciality, pattern="^programmist-konsultant$"),
                CallbackQueryHandler(b_speciality, pattern="^biznes-konsultant$"),
                CallbackQueryHandler(b_speciality, pattern="^virtualnyiy-assistent$"),
                CallbackQueryHandler(b_speciality, pattern="^obrabotka-pisem$"),
                CallbackQueryHandler(b_speciality, pattern="^obslujivanie-klientov-i-podderjka$"),
                CallbackQueryHandler(b_speciality, pattern="^tehnicheskaya-podderjka$"),
                CallbackQueryHandler(b_speciality, pattern="^finansovyi-konsultant$"),
                CallbackQueryHandler(b_speciality, pattern="^seo-konsultant$"),
                CallbackQueryHandler(b_speciality, pattern="^podderjka-po-telefonu$"),
                CallbackQueryHandler(b_speciality, pattern="^kadrovyiy-uchet-i-zarplata$"),
                CallbackQueryHandler(b_speciality, pattern="^statisticheskiy-analiz$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-erp-sistemy$"),
                CallbackQueryHandler(b_speciality, pattern="^obrabotka-platejey$"),
                CallbackQueryHandler(b_speciality, pattern="^usability-konsultant$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|konsalting$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "razrabotka-igr": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|razrabotka-igr$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|razrabotka-igr$"),

                CallbackQueryHandler(b_speciality, pattern="^illustrator-razrabotka-igr$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-3d-modelirovanie-razrabotka-igr$"),
                CallbackQueryHandler(b_speciality, pattern="^2d-animator-razrabotka-igr$"),
                CallbackQueryHandler(b_speciality, pattern="^programmist-igr-razrabotka-igr$"),
                CallbackQueryHandler(b_speciality, pattern="^testirovanie-igr-QA$"),
                CallbackQueryHandler(b_speciality, pattern="^3d-animator-razrabotka-igr$"),
                CallbackQueryHandler(b_speciality, pattern="^unity$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-piksel-arta-razrabotka-igr$"),
                CallbackQueryHandler(b_speciality, pattern="^ozvuchivanie-igr$"),
                CallbackQueryHandler(b_speciality, pattern="^makrosyi-dlya-igr-razrabotka-igr$"),
                CallbackQueryHandler(b_speciality, pattern="^flash-flex-programmist-razrabotka-igr$"),
                CallbackQueryHandler(b_speciality, pattern="^razrabotchik-koncepta-eskizov$"),
                CallbackQueryHandler(b_speciality, pattern="^videoroliki$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|razrabotka-igr$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "perevody": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|perevody$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|perevody$"),

                CallbackQueryHandler(b_speciality, pattern="^perevod-tekstov-obschey-tematiki$"),
                CallbackQueryHandler(b_speciality, pattern="^perevodchik-tehnicheskij$"),
                CallbackQueryHandler(b_speciality, pattern="^perevodchik-hudozhestvennyh-tekstov-literatury$"),
                CallbackQueryHandler(b_speciality, pattern="^redaktirovanie-perevodov$"),
                CallbackQueryHandler(b_speciality, pattern="^lokalizatsiya-po-saytov-i-igr$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-po-korrespondencii$"),
                CallbackQueryHandler(b_speciality, pattern="^ustnyiy-perevod$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|perevody$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "animatsiya-multiplikatsiya": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|animatsiya-multiplikatsiya$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|animatsiya-multiplikatsiya$"),

                CallbackQueryHandler(b_speciality, pattern="^dizajner-bannerov-flash$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-bannerov-animacija$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-po-muzyke-zvukam-animacija$"),
                CallbackQueryHandler(b_speciality, pattern="^2d-animator-animacija$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-2d-personazhej-animacija$"),
                CallbackQueryHandler(b_speciality, pattern="^3d-animator-animacija$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-3d-personazhej-animacija$"),
                CallbackQueryHandler(b_speciality, pattern="^flash-dizajner-razrabotchik-flash$"),
                CallbackQueryHandler(b_speciality, pattern="^geym-art$"),
                CallbackQueryHandler(b_speciality, pattern="^flash-flex-programmist-flash$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-scenarii-dlja-animacii$"),
                CallbackQueryHandler(b_speciality, pattern="^2d-animator-flash$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-flash-grafiki$"),
                CallbackQueryHandler(b_speciality, pattern="^razrabotchik-virtualnye-tury$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-raskadrovka$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|animatsiya-multiplikatsiya$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "fotografiya": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|fotografiya$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|fotografiya$"),

                CallbackQueryHandler(b_speciality, pattern="^retusher$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhestvennyj-fotograf$"),
                CallbackQueryHandler(b_speciality, pattern="^reklamnyj-fotograf$"),
                CallbackQueryHandler(b_speciality, pattern="^fotograf-modelej$"),
                CallbackQueryHandler(b_speciality, pattern="^fotograf-reporter$"),
                CallbackQueryHandler(b_speciality, pattern="^svadebnyj-fotograf-na-svadbu$"),
                CallbackQueryHandler(b_speciality, pattern="^fotograf-interjerov$"),
                CallbackQueryHandler(b_speciality, pattern="^promyshlennaya-fotosyemka$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|fotografiya$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "3d-Grafika": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|3d-Grafika$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|3d-Grafika$"),

                CallbackQueryHandler(b_speciality, pattern="^specialist-3d-modelirovanie-3d-grafika$"),
                CallbackQueryHandler(b_speciality, pattern="^chastnyj-dizajner-interjera-3d-grafika$"),
                CallbackQueryHandler(b_speciality, pattern="^videodizajner-3d-grafika$"),
                CallbackQueryHandler(b_speciality, pattern="^3d-animator-3d-grafika$"),
                CallbackQueryHandler(b_speciality, pattern="^3d-illustrator-3d-grafika$"),
                CallbackQueryHandler(b_speciality, pattern="^hudozhnik-3d-personazhej-3d-grafika$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-eksterjerov$"),
                CallbackQueryHandler(b_speciality, pattern="^vizualizator-predmetov$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|3d-Grafika$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "inzhiniring": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|inzhiniring$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|inzhiniring$"),

                CallbackQueryHandler(b_speciality, pattern="^chertezhnik$"),
                CallbackQueryHandler(b_speciality, pattern="^inzhener-mashinostroenija$"),
                CallbackQueryHandler(b_speciality, pattern="^inzhener-konstruktor$"),
                CallbackQueryHandler(b_speciality, pattern="^inzhener-elektrik$"),
                CallbackQueryHandler(b_speciality, pattern="^inzhener-slabotochnyh-setej-avtomatizacii$"),
                CallbackQueryHandler(b_speciality, pattern="^smetyi$"),
                CallbackQueryHandler(b_speciality, pattern="^inzhener-otoplenie-ventiljacija$"),
                CallbackQueryHandler(b_speciality, pattern="^razrabotka-radioelektronnyih-sistem$"),
                CallbackQueryHandler(b_speciality, pattern="^inzhener-vodosnabzhenija-kanalizacii$"),
                CallbackQueryHandler(b_speciality, pattern="^inzhener-tehnolog$"),
                CallbackQueryHandler(b_speciality, pattern="^gazosnabjenie$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|inzhiniring$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "obuchenie": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|obuchenie$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|obuchenie$"),

                CallbackQueryHandler(b_speciality, pattern="^specialist-napisanie-referatov-kursovyh-diplomov-obuchenie$"),
                CallbackQueryHandler(b_speciality, pattern="^repetitory-prepodavateli-obuchenie$"),
                CallbackQueryHandler(b_speciality, pattern="^psiholog$"),
                CallbackQueryHandler(b_speciality, pattern="^inostrannyie-yazyiki$"),
                CallbackQueryHandler(b_speciality, pattern="^tehnicheskie-distsiplinyi$"),
                CallbackQueryHandler(b_speciality, pattern="^doshkolnoe-obrazovanie$"),
                CallbackQueryHandler(b_speciality, pattern="^gumanitarnyie-distsiplinyi$"),
                CallbackQueryHandler(b_speciality, pattern="^konsultant-puteshestvija$"),
                CallbackQueryHandler(b_speciality, pattern="^stilist$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|obuchenie$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "optimizatsiya-seo": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|optimizatsiya-seo$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|optimizatsiya-seo$"),

                CallbackQueryHandler(b_speciality, pattern="^specialist-kontekstnaja-reklama-seo$"),
                CallbackQueryHandler(b_speciality, pattern="^seo-optimizator$"),
                CallbackQueryHandler(b_speciality, pattern="^seo-copywriter$"),
                CallbackQueryHandler(b_speciality, pattern="^smo-seo$"),
                CallbackQueryHandler(b_speciality, pattern="^sem$"),
                CallbackQueryHandler(b_speciality, pattern="^prodavec-ssylok$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|optimizatsiya-seo$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "arkhitektura-interer": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|arkhitektura-interer$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|arkhitektura-interer$"),

                CallbackQueryHandler(b_speciality, pattern="^chastnyj-dizajner-interjera-arhitektura-interier$"),
                CallbackQueryHandler(b_speciality, pattern="^chastnyj-arhitektor$"),
                CallbackQueryHandler(b_speciality, pattern="^vizualizator$"),
                CallbackQueryHandler(b_speciality, pattern="^landshaftnyj-dizajner-landshafta-interier$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-makety$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|arkhitektura-interer$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "poligrafiya": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|poligrafiya$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|poligrafiya$"),

                CallbackQueryHandler(b_speciality, pattern="^dizajner-poligrafii-poligrafija$"),
                CallbackQueryHandler(b_speciality, pattern="^dizajner-upakovki-poligrafija$"),
                CallbackQueryHandler(b_speciality, pattern="^verstalschik-poligrafii$"),
                CallbackQueryHandler(b_speciality, pattern="^specialist-dopechatnaja-podgotovka$"),
                CallbackQueryHandler(b_speciality, pattern="^verstka-elektronnyih-izdaniy$"),
                CallbackQueryHandler(b_speciality, pattern="^razrabotchik-shriftov-poligrafija$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|poligrafiya$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "menedzhment": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|menedzhment$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|menedzhment$"),

                CallbackQueryHandler(b_speciality, pattern="^rukovoditel-menedzher-internet-proektov-menedzhment$"),
                CallbackQueryHandler(b_speciality, pattern="^menedzher-po-prodazham$"),
                CallbackQueryHandler(b_speciality, pattern="^hr-menedzher-po-personalu-rekruter$"),
                CallbackQueryHandler(b_speciality, pattern="^upravlenie-onlayn-reputatsiey$"),
                CallbackQueryHandler(b_speciality, pattern="^kreativnyj-art-direktor$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|menedzhment$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "mobilnye-prilozheniya": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|mobilnye-prilozheniya$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|mobilnye-prilozheniya$"),

                CallbackQueryHandler(b_speciality, pattern="^Google-Android$"),
                CallbackQueryHandler(b_speciality, pattern="^iOS$"),
                CallbackQueryHandler(b_speciality, pattern="^dizayn$"),
                CallbackQueryHandler(b_speciality, pattern="^prototipirovanie$"),
                CallbackQueryHandler(b_speciality, pattern="^Windows-Phone$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|mobilnye-prilozheniya$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

            "seti-i-informatsionnye-sistemy": [
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all+|seti-i-informatsionnye-sistemy$"),
                CallbackQueryHandler(b_speciality_select_all, pattern="^select_all-|seti-i-informatsionnye-sistemy$"),

                CallbackQueryHandler(b_speciality, pattern="^setevoe-administrirovanie$"),
                CallbackQueryHandler(b_speciality, pattern="^administrirovanie-baz-dannyih$"),
                CallbackQueryHandler(b_speciality, pattern="^ERP-i-CRM-integratsii$"),

                CallbackQueryHandler(b_speciality_no_speciality, pattern="^no_speciality|seti-i-informatsionnye-sistemy$"),
                CallbackQueryHandler(b_choose_root_specialization, pattern="^choose_root_specialization$"),
            ],

        },
        fallbacks=[CommandHandler("start", start)]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


def fetch_projects_links_from_file():
    with open("projects.txt", "r") as f:
        project_links = f.readlines()

    for i in range(len(project_links)):
        project_links[i] = project_links[i][:-1]

    return project_links


def clean_projects_file():
    with open("projects.txt", "r") as f:
        project_links = f.readlines()
    if len(project_links) > 100:
        project_links = project_links[:40]
    with open("projects.txt", "w") as f:
        for project_link in project_links:
            f.write(f"{project_link}\n")


def fetch_projects_links_from_site():
    root_resp = requests.get("https://www.fl.ru/projects/")
    root_soup = BeautifulSoup(root_resp.text, 'lxml')

    root_soup_project_links = []
    for a in root_soup.find_all('a', href=True):
        link = str(a['href'])
        if "/projects/" in link and ".html" in link:
            root_soup_project_links.append(link)
    return root_soup_project_links


def add_new_projects_to_file(new_projects_links):
    with open("projects.txt", "a") as f:
        for project_link in new_projects_links:
            f.write(f"{project_link}\n")


def notify_users(new_projects_links):
    users = execute_sql(f"SELECT * FROM users", POSTGRES_CONNECTION_PARAMS)

    for project_link in new_projects_links:
        project_types = []

        project_resp = requests.get("https://www.fl.ru" + project_link)
        project_soup = BeautifulSoup(project_resp.text, 'lxml')

        for a in project_soup.find_all('a', href=True):
            link = str(a['href'])
            if "/freelancers/" in link and len(link) > 13:
                project_types.append(link)

        title = project_soup.find_all(class_="b-page__title")[0].text[5:]

        budget = project_soup.find_all(
            class_="b-layout__txt b-layout__txt_fontsize_18 b-layout__txt_fontsize_13_iphone")
        if len(budget) != 0:
            budget = re.findall(r'\d+', budget[0].text)[0]
        else:
            budget = "не указан"

        text = project_soup.find_all(class_="b-layout__txt b-layout__txt_padbot_20")[0].text[13:-7]

        if len(project_types) == 1:
            project_types.append("no_speciality")

        for i in range(2):
            project_types[i] = project_types[i].split("/")
            project_types[i] = list(filter(None, project_types[i]))
            if "freelancers" in project_types[i]:
                project_types[i].remove("freelancers")
            project_types[i] = project_types[i][0]

        specialization, speciality = project_types[0], project_types[1]

        for user in users:
            if user["project_types"][specialization][speciality]:
                message = f"{title}\n\n{text}\n\nБюджет: {budget}\n\nhttps://www.fl.ru{project_link}"
                bot.send_message(user["telegram_id"], message)


def parse_and_send_projects():
    while True:
        file_projects_links = fetch_projects_links_from_file()
        if len(file_projects_links) > 40:
            clean_projects_file()
        site_projects_links = fetch_projects_links_from_site()

        new_projects_links = list(set(site_projects_links) - set(file_projects_links))

        if len(new_projects_links) > 0:
            add_new_projects_to_file(new_projects_links)
            notify_users(new_projects_links)


if __name__ == '__main__':
    # t_parse_and_send_projects = Thread(target=parse_and_send_projects, daemon=True)
    # t_parse_and_send_projects.start()
    main()
