# -*- coding: utf-8 -*-
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler
from config import TELEGRAM_API_TOKEN


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update, context):
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    keyboard = [
        [InlineKeyboardButton("Выбрать специализацию", callback_data="choose_root_specialization")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Привет, я бот fl.ru. Я умею присылать проекты по выбранным тобой специализациям",
        reply_markup=reply_markup
    )
    return "start"


def f_choose_root_specialization(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("Специализация 1", callback_data="specialization_1"),
         InlineKeyboardButton("Специализация 2", callback_data="specialization_2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Выбери специализацию",
        reply_markup=reply_markup
    )
    return "s_choose_root_specialization"


def f_spec_1(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("Специальность 1_1", callback_data="specialty_1_1"),
         InlineKeyboardButton("Специальность 1_2", callback_data="specialty_1_2")],

        [InlineKeyboardButton("Назад", callback_data="choose_root_specialization")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Специализация 1",
        reply_markup=reply_markup
    )
    return "s_specialization_1"


def f_spec_1_1(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("Специальность 1_1", callback_data="specialty_1_1"),
         InlineKeyboardButton("Специальность 1_2", callback_data="specialty_1_2")],

        [InlineKeyboardButton("Назад", callback_data="choose_root_specialization")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Специализация 1",
        reply_markup=reply_markup
    )
    return "s_specialization_1"


def f_spec_1_2(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("Специальность 1_1", callback_data="specialty_1_1"),
         InlineKeyboardButton("Специальность 1_2", callback_data="specialty_1_2")],

        [InlineKeyboardButton("Назад", callback_data="choose_root_specialization")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Специализация 1",
        reply_markup=reply_markup
    )
    return "s_specialization_1"


def f_spec_2(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("Специальность 2_1", callback_data="specialty_2_1"),
         InlineKeyboardButton("Специальность 2_2", callback_data="specialty_2_2")],

        [InlineKeyboardButton("Назад", callback_data="choose_root_specialization")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Специализация 2",
        reply_markup=reply_markup
    )
    return "s_specialization_2"


def f_spec_2_1(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("Специальность 2_1", callback_data="specialty_2_1"),
         InlineKeyboardButton("Специальность 2_2", callback_data="specialty_2_2")],

        [InlineKeyboardButton("Назад", callback_data="choose_root_specialization")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Специализация 2",
        reply_markup=reply_markup
    )
    return "s_specialization_2"


def f_spec_2_2(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("Специальность 2_1", callback_data="specialty_2_1"),
         InlineKeyboardButton("Специальность 2_2", callback_data="specialty_2_2")],

        [InlineKeyboardButton("Назад", callback_data="choose_root_specialization")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Специализация 2",
        reply_markup=reply_markup
    )
    return "s_specialization_2"



# def four(update, context):
#     query = update.callback_query
#     query.answer()
#     keyboard = [
#         [InlineKeyboardButton("2", callback_data=str(TWO)),
#          InlineKeyboardButton("4", callback_data=str(FOUR))]
#     ]
#     print(query.from_user["id"])
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     query.edit_message_text(
#         text="Fourth CallbackQueryHandler, Choose a route",
#         reply_markup=reply_markup
#     )
#     return FIRST


def end(update, context):
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over"""
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="See you next time!"
    )
    return ConversationHandler.END


def main():
    updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            "start": [CallbackQueryHandler(f_choose_root_specialization, pattern="^choose_root_specialization$")],
            "s_choose_root_specialization": [
                CallbackQueryHandler(f_spec_1, pattern="^specialization_1$"),
                CallbackQueryHandler(f_spec_2, pattern="^specialization_2$")
            ],
            "s_specialization_1": [
                CallbackQueryHandler(f_spec_1_1, pattern="^specialty_1_1$"),
                CallbackQueryHandler(f_spec_1_2, pattern="^specialty_1_2$"),
                CallbackQueryHandler(f_choose_root_specialization, pattern="^choose_root_specialization$")
            ],
            "s_specialization_2": [
                CallbackQueryHandler(f_spec_2_1, pattern="^specialty_2_1$"),
                CallbackQueryHandler(f_spec_2_2, pattern="^specialty_2_2$"),
                CallbackQueryHandler(f_choose_root_specialization, pattern="^choose_root_specialization$")
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
