#!/usr/bin/env python3
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv
load_dotenv()

from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, Dispatcher, CallbackContext
from telegram.bot import Bot
from telegram.update import Update
from telegram.parsemode import ParseMode
from telegram.ext.dispatcher import run_async
from nltk import ngrams
from persistence import Model
from cache import Cache

# Configuration
BOTNAME = os.getenv("BOTNAME")
TOKEN = os.getenv("TOKEN")
GROUP_NAME = os.getenv("GROUPNAME")
LOG_FILE = os.getenv("LOGFILE")
PROFANITY_NGRAMS = 2

# Set up logging
root = logging.getLogger()
root.setLevel(logging.INFO)
karaliste = []

# Set up persistence
model = Model("persistence/data.db")
model.initiate()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
logger.level = logging.INFO
handler = RotatingFileHandler(LOG_FILE, maxBytes=100*1024, backupCount=10, encoding="utf8")
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

group_rules = """
**Pyturk** Python ve programlamaya dair tartışmalar yürütmek için oluşturulmuş profesyonel bir topluluktur. 
Aşağıda belirtildiği gibi paylaşım yaparsanız alanında uzman kişilere daha hızlı ulaşabilirsiniz. 

*1*. Sorularınız olduğunda olabildiğince ayrıntı vermeniz yararınıza olacaktır. "A veri tabanını kullanan var mı?", "Daha önce X paketiyle çalışmış olan var mı?" vb. sorular üstünkörü sorulardır ve bu tip sorularda yardım almanız güçleşir.
    Üstünkörü soru soranların yazma yetkileri geçici olarak ellerinden alınabilir. Sık sık üstünkörü soru soranlar grubun kalitesini korumak adına banlanırlar.

*2*. Reklam yapmak yasaktır. Whatsapp grubu, telegram grubu tanıtımı yapmak, grup amacıyla ilintili içerik bulunmayan sayfaların paylaşımını yapmak reklam olarak algılanır ve paylaşımı yapanlar gruptan uzaklaştırılırlar. Tanıtım izni almak için "/yardim mesaj içeriği" yazarak yardım isteyebilirsiniz. Yöneticilerimizden birisi sizinle iletişime geçecektir.
    
*3*. Grup üyelerinden herhangi birisine rızası dışında mesaj atmayınız veya rahatsız etmeyiniz. Rahatsızlık verenler gruptan uzaklaştırılırlar.
    
*4*. Dini, siyasi içerik paylaşmak kişilere yönelik olsun veya olmasın küfür veya hakaret etmek kesinlikle yasaktır.  
    
*Pitto* size bir çok konuda yardım etmek için burada bulunmakta. "/yardim mesaj içeriği" şeklinde Pitto'dan yardım çağırmasını isteyebilirsiniz. Yardım isteğiniz ve mesaj içeriğiniz gruptan gizlenecektir.
https://www.pyturk.com üzerinde blog yazıları yazmak isterseniz /pyturk yazarak bildirebilirsiniz. Yönetici arkadaşlarımız yardımcı olacaktır.
Beraber yapacağımız projelerle Pitto'nun daha da akıllı olacağını biliyoruz.

Hoşgeldiniz 🤗🤗
"""

def custom_lower(param:str):
    return param.replace("I", "ı").lower()

@run_async
def send_message_to_administrators(update:Update, context:CallbackContext, text:str):
    bot = context.bot
    if not check_group(context.bot, update):
        return
    for member in bot.get_chat_administrators(chat_id=update.message.chat.id):
        if member.user.username and member.user.username != BOTNAME:
            chat_id = model.get_chat(member.user.id)
            if chat_id:
                try:
                    bot.send_message(text=text, chat_id=chat_id, parse_mode=ParseMode.MARKDOWN)
                except Exception as e:
                    logging.error(e)

def remove_profanity(param:str):
    result = False
    param = " ".join(param.split()) + " "
    ngram_payloads = []
    for i in range(PROFANITY_NGRAMS):
        ngram_payloads += list(ngrams(param.split(), i+1))
    for payload in ngram_payloads[::-1]:
        payload = " ".join(payload)
        if custom_lower(payload) in karaliste:
            param_lower = custom_lower(param)
            found_index = param_lower.find(custom_lower(payload))
            if found_index>-1:
                #Found
                param_new = ""
                param_new += param[0:found_index+1]
                param_new += ("*"*(len(payload)-1))
                param_new += param[found_index+len(payload):]
                param = param_new
            result=True
    return result, param


def message(update:Update, context:CallbackContext):
    """
    """
    if not check_group(context.bot, update):
        return
    bot = context.bot
    raise ValueError
    if update.message.text:
        profanity, text_b = remove_profanity(update.message.text)
        if profanity:
            bot.delete_message(chat_id=update.message.chat.id, message_id=update.message.message_id)
            active_user = update.message.to_dict().get("from").get("id", None)
            first_name = update.message.to_dict().get("from").get("first_name", None)
            last_name = update.message.to_dict().get("from").get("last_name", None)
            send_message_to_administrators(update, context,
                                           f"[{first_name} {last_name}](tg://user?id={active_user}) kullanıcısı yasaklı mesaj için uyarıldı. \n\n\n {update.message.text}")
            bot.send_message(chat_id=update.message.chat.id, text=f"Yasaklı kelime kullanımı tespit ettim. Grup kurallarında belirtildiği üzere küfür ve hakaret içerikli mesaj gönderemezsin! 😡😡\n\n{text_b}", parse_mode="html")

def check_group(bot:Bot, update:Update):
    if update.message.chat.username != GROUP_NAME:
        bot.send_message(chat_id=update.message.chat.id, text=f"Malesef şimdilik sadece https://t.me/{GROUP_NAME} için çalışıyorum ve iş tekliflerini değerlendiriyorum.😃")
        return False
    return True

@Cache(cache_key=lambda u, c: str(u.message.chat_id), timeout=60*60)
def fetch_admins(update:Update, context:CallbackContext):
    bot = context.bot
    id_list = []
    for member in bot.get_chat_administrators(chat_id=update.message.chat.id):
        id_list.append(member.user.id)
    return id_list


def check_admin(update:Update, context:CallbackContext):
    bot = context.bot
    id_list = fetch_admins(update, context)
    if update.message.to_dict().get("from").get("id", None) not in id_list:
        logging.warning("Kullanıcı admin yetkisi kullanmaya çalışıyor. ")
        bot.send_message(text="Bu komut için yönetici olman gerekiyor.", chat_id=update.message.chat.id)
        return False
    return True


def send_message_behalf(update:Update, context:CallbackContext):
    bot = context.bot
    args = context.args
    bot.delete_message(chat_id=update.message.chat.id, message_id=update.message.message_id)
    if not check_group(context.bot, update):
        return
    if not check_admin(update, context):
        return
    bot.send_message(chat_id=update.message.chat.id, text=" ".join(args))



def register_pyturk(update:Update, context:CallbackContext):
    bot = context.bot
    bot.send_message(text="Pyturk.com'da yazmak istemen beni mutlu etti. 🤗 Başvurunu site yöneticilerine ilettim.", chat_id=update.message.chat.id)
    active_user = update.message.to_dict().get("from").get("id", None)
    first_name = update.message.to_dict().get("from").get("first_name", None)
    last_name = update.message.to_dict().get("from").get("last_name", None)
    send_message_to_administrators(update, context, f"[{first_name} {last_name}](tg://user?id={active_user}) kullanıcısı pyturk.com'da yazmak istediğini belirtti. İlgilenmek isteyebilirsin.")

def register_yardim(update:Update, context:CallbackContext):
    bot = context.bot
    bot.delete_message(chat_id=update.message.chat.id, message_id=update.message.message_id)
    if not check_group(context.bot, update):
        return
    bot.send_message(text="Yardım isteğini yöneticime ilettim, sana en kısa zamanda dönüş yapacağını söyledi.🤗", chat_id=update.message.chat.id)
    active_user = update.message.to_dict().get("from").get("id", None)
    first_name = update.message.to_dict().get("from").get("first_name", None)
    last_name = update.message.to_dict().get("from").get("last_name", None)
    send_message_to_administrators(update, context, f"[{first_name} {last_name}](tg://user?id={active_user}) kullanıcısı sana yardım isteği gönderdi. \n\n\n {' '.join(context.args)}")


def error_callback(update, context:CallbackContext):
    logger.error('Update "%s" caused error(%s): "%s"', update, type(context.error), str(context.error))
    logger.exception(context.error)

def load_karaliste():
    global karaliste
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "karaliste.txt"), "r", encoding="utf8") as f:
        karaliste = list(filter(lambda y: len(y)>0, map(lambda x: x.strip(), f.readlines())))

def new_member(update:Update, context:CallbackContext):
    bot = context.bot
    for member in update.message.new_chat_members:
        if member.username != 'PittoPyBot':
            bot.send_message(chat_id=update.message.chat.id, text=f"""
Hoşgeldin {member.first_name} 🤗
Benim adım Pitto grupta sana yardımcı olmak için buradayım. 
☝ Tam yukarıda sabitlenmiş mesajımızı okumanı tavsiye ederim. 

🔹 Bir de eğer https://www.pyturk.com üzerinde yazılar yazmak istiyorsan. /pyturk yazman yeterli.
            """)

def start(update:Update, context:CallbackContext):
    bot = context.bot
    if update.message.chat.id<0:
        bot.send_message(text="Malesef grup içerisinde bu komutu kullanamazsın. 😕", chat_id=update.message.chat.id)
    else:
        try:
            if update.message.to_dict().get("from").get("username", None):
                if model.get_chat_by_chat_id(update.message.chat.id):
                    raise Exception
                model.add_chat(update.message.chat.id, update.message.to_dict().get("from").get("id", None))
            bot.send_message(text="Tanıştığımıza memnun oldum.🥰 Gerektiğinde buradan seninle iletişim kuracağım. ", chat_id=update.message.chat.id)
        except:
            bot.send_message(text="Seni önceden tanıyor olabilir miyim? 🤨", chat_id=update.message.chat.id)

def send_rules(update:Update, context:CallbackContext):
    bot = context.bot
    args = context.args
    bot.delete_message(chat_id=update.message.chat.id, message_id=update.message.message_id)
    if not check_group(context.bot, update):
        return
    if not check_admin(update, context):
        return
    message = bot.send_message(chat_id=update.message.chat.id, text=group_rules, parse_mode=ParseMode.MARKDOWN)
    bot.pin_chat_message(chat_id=update.message.chat.id, message_id=message.message_id)

if __name__ == '__main__':
    updater = Updater(TOKEN, workers=10, use_context=True)
    dp:Dispatcher = updater.dispatcher
    dp.add_handler(CommandHandler("start", start, pass_args=True))
    dp.add_handler(CommandHandler("mesaj", send_message_behalf, pass_args=True))
    dp.add_handler(CommandHandler("pyturk", register_pyturk))
    dp.add_handler(CommandHandler("yardim", register_yardim))
    dp.add_handler(CommandHandler("kurallar", send_rules))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_member))
    dp.add_handler(MessageHandler(Filters.text, message))
    dp.add_error_handler(error_callback)
    load_karaliste()
    logger.info("Başladı")
    update_queue = updater.start_polling(timeout=30, clean=False)
    updater.idle()