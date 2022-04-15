from django.shortcuts import HttpResponse, render
from django.views.decorators.csrf import csrf_exempt
from apps.accounts.models import TGUser, UserBot
from apps.product.models import Product, Category
from apps.order.models import Order, OrderProduct, OrderStatus, F
from django.utils.translation import gettext as _
from apps.core.utils.service import BASE_URL, GeoAPI
from geopy.geocoders import Nominatim
import telebot
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton, \
    InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto

BOT_TOKEN = ""
BOT_NAME = ""
bot = telebot.TeleBot(BOT_TOKEN)
bot_channel_id = 0


LOCATOR = Nominatim(user_agent="weboasis9002@gmail.com")

# https://api.telegram.org/bot{TOKEN}/setWebhook?url={domain}/bot?bot_name={bot_name}


@csrf_exempt
def update_bot(request, bot_name):
    try:
        user_bot = UserBot.objects.get(bot_name=bot_name)
        global BOT_TOKEN
        global BOT_NAME
        global bot_channel_id
        BOT_TOKEN = user_bot.bot_token
        BOT_NAME = user_bot.bot_name
        bot_channel_id = user_bot.channel_id
        if request.method == 'POST':
            json_string = request.body.decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return HttpResponse('OK', {"success": True})
    except UserBot.DoesNotExist:
        return HttpResponse('Error', {"success": False})


class Controller:
    def __init__(self, telegram_id=None, first_name=None, last_name=None, username=None, phone=None, text=None,
                 product_id=None, secret_key=None, message_id=None,
                 order_product_id=None, latitude=None, longitude=None, channel_id=None):
        self.telegram_id = telegram_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.phone = phone
        self.text = text
        self.product_id = product_id
        self.secret_key = secret_key
        self.message_id = message_id
        self.order_product_id = order_product_id
        self.latitude = latitude
        self.longitude = longitude
        self.channel_id = channel_id
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.bot_name = BOT_NAME
        self.lang = "uz"

    def start(self):
        self.signup()
        # language = self.get_merchant().language
        # if language in ["uz", "oz", "ru"]:
        #     self.lang = language.lower()
        self.bot.send_message(self.telegram_id, "Привет", reply_markup=self.category())

    def signup(self):
        user, _ = TGUser.objects.get_or_create(telegram_id=self.telegram_id)
        user.first_name = self.first_name
        user.last_name = self.last_name
        user.username = self.username
        user.phone = self.phone
        user.step = 1
        user.save()

    def category(self):
        array = []
        key = ReplyKeyboardMarkup(True, False, row_width=2)
        # print("CATEGORY > self.bot_name.........", self.bot_name)
        category = Category.objects.filter(user__bot_name=self.bot_name, parent_category__isnull=True)
        # print("CATEGORY > category.........", category)
        for i in category:
            array.append(KeyboardButton(i.title))
        order = KeyboardButton(_('Мой закази'))
        feedback = KeyboardButton(_('Оставит отзыв'))
        key.add(order, feedback)
        key.add(*array)
        return key

    def subcategory(self):
        array = []
        key = ReplyKeyboardMarkup(True, False, row_width=2)
        subcategory = Category.objects.filter(
            user__bot_name=self.bot_name, parent_category__title__icontains=self.text, parent_category__isnull=False,
        )
        # print("CATEGORY > category.........", subcategory, self.text)
        for cat in subcategory:
            array.append(KeyboardButton(cat.title))
        back = KeyboardButton(_("⬅️назад"))
        key.add(back)
        key.add(*array)
        return key

    def send_channel_order(self):
        line, text = self.order_product_key()
        order = Order.objects.get(tg_user__telegram_id=self.telegram_id, status=OrderStatus.NEW)
        order.status = OrderStatus.PROCESSING
        order.save()
        key = InlineKeyboardMarkup()
        checkout = InlineKeyboardButton(text=_("✅ Оформить"), callback_data='checkout_id' + str(order.pk))
        cancel = InlineKeyboardButton(text=_('❌ Отменить'), callback_data='cancel_id' + str(order.pk))
        status = InlineKeyboardButton(text=_("Статус: ") + str(order.get_status_display()), callback_data='status')
        key.add(checkout, cancel)
        key.add(status)
        text += _('\nВаш телефон: ') + str(order.phone)
        self.bot.send_message(bot_channel_id, text, reply_markup=key, parse_mode='HTML')
        # self.bot.send_message(self.telegram_id, text, reply_markup=key, parse_mode='HTML')

    def product(self):
        products = Product.objects.filter(user__bot_name=self.bot_name, category__title__icontains=self.text)
        print("Products......", products)
        line = InlineKeyboardMarkup()
        for item in products:
            secret_key = f"1%{item.price}%{item.pk}"  # quantity % 105$ % pk // 1%105%1
            plus = InlineKeyboardButton(text='➕', callback_data='+' + secret_key)
            minus = InlineKeyboardButton(text='➖', callback_data='-' + secret_key)
            buy = InlineKeyboardButton(text=_("добовит 🛒"), callback_data='buy' + secret_key)
            quantity = InlineKeyboardButton(text='1', callback_data='*' + secret_key)
            total = InlineKeyboardButton(text=str(item.price) + _(" сум"), callback_data='total')
            line.add(plus, quantity, minus)
            line.add(total)
            line.add(buy)
            url = f"{BASE_URL}{item.image.url}"
            print("URL......", url, total)
            self.bot.send_photo(self.telegram_id, url, reply_markup=line)

    def check_subcategory(self):
        qs = Category.objects.filter(parent_category__title__icontains=self.text, parent_category__isnull=False)
        if qs.exists():
            return True
        else:
            return False

    def check_product(self):
        # print("check_product.......", self.text)
        qs = Product.objects.filter(category__title__icontains=self.text)
        if qs.exists():
            return True
        else:
            return False

    def control_quantity(self, secret_key, count, price):
        line = InlineKeyboardMarkup()
        plus = InlineKeyboardButton(text='➕', callback_data='+' + secret_key)
        minus = InlineKeyboardButton(text='➖', callback_data='-' + secret_key)
        buy = InlineKeyboardButton(text=_('добовит 🛒'), callback_data='buy' + secret_key)
        quantity = InlineKeyboardButton(text=str(count), callback_data='*' + secret_key)
        total = InlineKeyboardButton(text=str(price) + _(' сум'), callback_data='total')
        line.add(plus, quantity, minus)
        line.add(total)
        line.add(buy)
        self.bot.edit_message_reply_markup(self.telegram_id, self.message_id, reply_markup=line)

    def plus_quantity_product(self):
        text = self.secret_key.split('%')  # quantity and price and product_id
        product = Product.objects.get(pk=int(text[2]))
        quantity_plus = int(text[0]) + 1
        total_price = quantity_plus * product.price
        secret_key = f"{quantity_plus}%{product.price}%{product.pk}"
        self.control_quantity(secret_key=secret_key, count=quantity_plus, price=total_price)

    def minus_quantity_product(self):
        text = self.secret_key.split('%')  # quantity and price and product_id
        if int(text[0]) == 1:
            return False
        else:
            product = Product.objects.get(pk=int(text[2]))
            quantity_plus = int(text[0]) - 1
            total_price = quantity_plus * product.price
            secret_key = f"{quantity_plus}%{product.price}%{product.pk}"
            self.control_quantity(secret_key=secret_key, count=quantity_plus, price=total_price)

    def buy_product(self):
        text = self.secret_key.split('%')
        print("buy_product > text", text)
        order = self.new_order()
        print("buy_product > order", order, order.id)
        product = Product.objects.get(pk=int(text[2]))
        qs = OrderProduct.objects.filter(order_id=order.id, product_id=product.id)
        print("QS>.......>>>", qs)
        quantity = int(text[0])
        if qs.exists():
            total = 0
            for item in qs:
                total += item.quantity * item.product.price
            order.total += total
            order.save()
            qs.update(quantity=F("quantity") + quantity)
        else:
            order.total += quantity * product.price
            order.save()
            OrderProduct.objects.create(order_id=order.id, quantity=quantity, product=product)

    def validation_number(self):
        if len(self.text) == 10:
            code = ['99', '94', '93', '92', '90', '98', '97', '71', '72']
            text = self.text.split()
            if text[0] in code:
                try:
                    int(text[1])
                    return True
                except Exception as e:
                    print("Exception > validation_number", e.args)
                    return False
        else:
            return False


    def user(self):
        return TGUser.objects.get(telegram_id=self.telegram_id)

    def home_page(self):
        user = TGUser.objects.get(telegram_id=self.telegram_id)
        user.step = 1
        user.save()
        self.bot.send_message(self.telegram_id, _('Главный меню '), reply_markup=self.category())

    def order_delete(self):
        self.new_order().delete()

    def cancel_order(self):
        order = Order.objects.get(pk=int(self.order_product_id))
        order.status = OrderStatus.CANCEL
        order.save()
        self.bot.send_message(order.tg_user.telegram_id, _('Ваш заказ отменен 😢'))

    def finished_order(self):
        order = Order.objects.get(id=int(self.order_product_id))
        order.status = OrderStatus.FINISHED
        order.save()
        order.create_tezbor_parcel()
        self.bot.send_message(order.tg_user.telegram_id, _('📌 Ваш заказ почти готов скора будет к вам доставлена'))

    def checkout(self):
        order_item = OrderProduct.objects.filter(order=self.new_order())
        if not order_item:
            self.bot.answer_callback_query(self.message_id, text=_('Ваш корзина пустой'))
        else:
            user = TGUser.objects.get(telegram_id=self.telegram_id)
            if user.step == 9:
                user.step = 5
                user.save()
                self.contact()

    def contact(self):
        text = _('<b>Пожалуста отравите контакт или напишите номер.</b> \n<i>пример :90 1234567‼</i>️')
        key = ReplyKeyboardMarkup(True, False)
        key.add(KeyboardButton(_('Отправить контакт 📲'), request_contact=True))
        key.add(KeyboardButton(_('⬅️назад ')))
        self.bot.send_message(self.telegram_id, text, reply_markup=key, parse_mode='HTML')

    def location(self):
        text = _('<b>Отправьте локация или выбирайте свой регион</b>')
        key = ReplyKeyboardMarkup(True, False)
        key.add(KeyboardButton(_('📍 Отправить локация'), request_location=True))
        regions = {
            "Тошкент шахри", "Тошкент вилояти", "Қорақалпоғистон", "Андижон", "Бухоро", "Жиззах",
            "Қашқадарё", "Навоий", "Наманган", "Самарқанд", "Сурхондарё", "Сирдарё", "Фарғона", "Хоразм"
        }
        for region in regions:
            key.add(KeyboardButton(_(region)))
        key.add(KeyboardButton(_('⬅️назад ')))
        self.bot.send_message(self.telegram_id, text, reply_markup=key, parse_mode='HTML')

    def save_contact(self):
        tg_user = TGUser.objects.get(telegram_id=self.telegram_id)
        if tg_user.step == 5:
            order = Order.objects.get(
                user_bot__bot_name=self.bot_name, tg_user__telegram_id=self.telegram_id, status=OrderStatus.NEW)
            order.phone = self.phone
            order.save()
            self.bot.send_message(self.telegram_id, _('✅ Ваш номер успешно сохранено'))
            tg_user.step = 6
            tg_user.phone = self.phone
            tg_user.save()
            self.location()

    def save_location(self):
        tg_user = TGUser.objects.get(telegram_id=self.telegram_id)
        print(f"X{self.latitude}\nY{self.longitude}")
        if tg_user.step == 6 or tg_user.step == 50:
            order = Order.objects.get(
                user_bot__bot_name=self.bot_name, tg_user__telegram_id=self.telegram_id, status=OrderStatus.NEW)
            order.latitude = self.latitude
            order.longitude = self.longitude
            geo_api = GeoAPI(location=(self.latitude, self.longitude))
            print("GeoAPI ... ", geo_api)
            region, raw_address = geo_api.get_address()
            order.region = region
            order.address = raw_address
            order.save()
            self.bot.send_message(
                self.telegram_id, _('✅ Ваш локация успешно сохранено '), reply_markup=ReplyKeyboardRemove()
            )
            tg_user.step = 7
            tg_user.save()
            self.success_order()

    def save_reply_message_id(self):
        tg_user = TGUser.objects.get(telegram_id=self.telegram_id)
        tg_user.step = 20
        tg_user.text = self.text
        tg_user.save()

    def order_update_status(self, status, order_id):
        order = Order.objects.get(pk=int(order_id))
        order.status = status
        order.save()
        key = InlineKeyboardMarkup()
        checkout = InlineKeyboardButton(text=_('✅ Оформить'), callback_data='checkout_id' + str(order.pk))
        cancel = InlineKeyboardButton(text=_('❌ отменить'), callback_data='cancel_id' + str(order.pk))
        status_btn = InlineKeyboardButton(text=_("Статус: ") + order.status, callback_data='status')
        key.add(checkout, cancel)
        key.add(status_btn)
        self.bot.edit_message_reply_markup(self.channel_id, self.message_id, reply_markup=key)

    def leave_feedback(self):
        tg_user = TGUser.objects.get(telegram_id=self.telegram_id)
        tg_user.step = 8
        tg_user.save()
        key = ReplyKeyboardMarkup(True, False)
        key.row(_("⬅️назад"))
        self.bot.send_message(self.telegram_id, _('Пожалуйста напишите что нибудь отзыв! 💬'), reply_markup=key)

    def send_leave_feedback(self):
        reply_key = 'reply' + str(self.telegram_id) + '%' + str(self.message_id)
        key = InlineKeyboardMarkup()
        reply = InlineKeyboardButton(text=_('Ответить '), callback_data=str(reply_key))
        self.text += f"\n telegram_id: {self.telegram_id}"
        key.add(reply)
        self.bot.send_message(bot_channel_id, self.text, reply_markup=key)
        self.bot.send_message(self.telegram_id, _('Ваш отзыв успешно отправлено ☑️'), reply_markup=self.category())

    def send_replay_message(self):
        self.bot.send_message(self.telegram_id, _('Напишите ответ что нибудь 💬'))

    def send_admin_send_reply_message(self):
        tg_user = TGUser.objects.get(telegram_id=self.telegram_id)
        text = tg_user.text.split('%')
        self.bot.send_message(int(text[0]), reply_to_message_id=int(text[1]), text=self.text)
        self.bot.send_message(self.telegram_id, _('Ваше сообщение отправлено ✅'))
        tg_user.step = 1
        tg_user.text = None
        tg_user.save()

    def main(self):
        tg_user = TGUser.objects.get(telegram_id=self.telegram_id)
        print("main......", tg_user, tg_user.step, type(tg_user.step))
        if tg_user.step == 1:
            check = self.check_subcategory()
            print("check......", check)
            if check:
                tg_user.step = 2
                tg_user.text = self.text
                tg_user.save()
                self.bot.send_message(self.telegram_id, self.text, reply_markup=self.subcategory())
            else:
                tg_user.step = 1
                tg_user.text = self.text
                tg_user.save()
                self.product()
        elif tg_user.step == 2:
            if self.check_product():
                tg_user.text = self.text
                tg_user.save()
                self.product()
            else:
                key = ReplyKeyboardMarkup(True, False, row_width=2)
                key.add(KeyboardButton(_('⬅️назад ')))
                self.bot.send_message(self.telegram_id, _('Товар не найден'), reply_markup=key)
        elif tg_user.step == 5:
            if self.validation_number():
                self.phone = self.text
                self.save_contact()
                tg_user.step = 6
                tg_user.save()
            else:
                text = _('❌ <b>Вы неправильно отправили номер.</b> <i>пример :99 8158172</i>')
                self.bot.send_message(self.telegram_id, text)
        elif tg_user.step == 6:
            order = Order.objects.get(
                user_bot__bot_name=self.bot_name, tg_user__telegram_id=self.telegram_id, status=OrderStatus.NEW)
            order.region = self.text
            order.latitude = None
            order.longitude = None
            order.save()

            text = _('<b>Отправьте локация или напишите адрес.</b> \n<i>пример: Яшнобод Кадишва 6 дом</i>')
            key = ReplyKeyboardMarkup(True, False)
            key.add(KeyboardButton(_('📍 Отправить локация'), request_location=True))
            self.bot.send_message(self.telegram_id, text, reply_markup=key, parse_mode='HTML')
            tg_user.step = 50
            tg_user.save()
        elif tg_user.step == 50:
            order = Order.objects.get(
                user_bot__bot_name=self.bot_name, tg_user__telegram_id=self.telegram_id, status=OrderStatus.NEW)
            order.address = self.text
            order.save()
            line, text = self.order_product_key()
            self.bot.send_message(self.telegram_id, _('Ваш адрес успешно сохранено'),
                                  reply_markup=ReplyKeyboardRemove())
            text += f"\n\n<b>📞 {_('номер: ')}{order.phone}\n{_('🚩 регион: ')}{order.region}\n{_('📌 адрес: ')}{order.address}\n\n{_('Вы подтверждаете свой заказ?')}</b>"
            key = InlineKeyboardMarkup()
            yes = InlineKeyboardButton(text='✅', callback_data='yes')
            no = InlineKeyboardButton(text='❌', callback_data='no')
            key.add(no, yes)
            self.bot.send_message(self.telegram_id, text, reply_markup=key, parse_mode='HTML')
            tg_user.step = 7
            tg_user.save()
        elif tg_user.step == 8:
            self.send_leave_feedback()
            tg_user.step = 1
            tg_user.save()
        elif tg_user.step == 20:
            self.send_admin_send_reply_message()

    def back_step(self):
        tg_user = TGUser.objects.get(telegram_id=self.telegram_id)
        if tg_user.step == 6:
            self.contact()
            tg_user.step = 5
            tg_user.save()
        elif tg_user.step == 5:
            line, text = self.order_product_key()
            tg_user.step = 9
            tg_user.save()
            key = ReplyKeyboardMarkup(True, False)
            key.add(KeyboardButton(_('Главный меню')))
            self.bot.send_message(self.telegram_id, _('Корзина 🛒'), reply_markup=key)
            self.bot.send_message(self.telegram_id, text, reply_markup=line, parse_mode='HTML')
        elif tg_user.step == 2:
            tg_user.step = 1
            tg_user.save()
            self.bot.send_message(self.telegram_id, _('Главный меню'), reply_markup=self.category())
        elif tg_user.step == 8:
            tg_user.step = 1
            tg_user.save()
            self.bot.send_message(self.telegram_id, _('Главный меню'), reply_markup=self.category())


@bot.message_handler(commands=['start'])
def start(message):
    print("START > message > chat.....", message)
    Controller(
        telegram_id=message.chat.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    ).start()

