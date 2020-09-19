import os
import locale
import re
from datetime import datetime
from urllib.request import urlopen

from kafehan.models import *
from kafehan.tlgrm_kafehan import txt, kbs
from kafehan.tlgrm_kafehan.bot import t
from kafehan.tlgrm_kafehan.kbs import b, bt
from kafehan_bot.settings import MEDIA_ROOT
from ksk_util.dump import add_dump_txt

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

mid_kb = dict()
msg_wait = dict()


@t.message_handler('/start')
def start(uid, mid):
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    user = Client.objects.filter(idu=uid).first()
    admins = [i.uid.idu for i in AdminKafeHan.objects.all()]

    if not user:
        udata = t.get_tg_user(uid)
        user = Client(
            idu=uid,
            username=udata.get('username', ''),
            first_name=udata.get('first_name', ''),
            last_name=udata.get('last_name', '')
        )
        photo_url = t.get_user_photo(uid)

        if photo_url:
            now = datetime.now()
            photo_dir_path = f'kafehan/clients/photo/{now.year}/{now.month}/{now.day}/'
            if not os.path.exists(os.path.join(MEDIA_ROOT, photo_dir_path)):
                os.makedirs(os.path.join(MEDIA_ROOT, photo_dir_path))
            photob = urlopen(photo_url).read()
            with open(os.path.join(MEDIA_ROOT, photo_dir_path + str(uid) + '.jpg'), 'wb') as f:
                f.write(photob)
            user.photo = photo_dir_path + str(uid) + '.jpg'

    user.save()

    t.send(
        uid,
        'Приветствуем! Найдите для себя самое вкусное блюдо, и мы будем радовать Вас им каждый день!',
        safe=True)

    kb = (([[b('Текущий заказ', 'order')]] if order else [])
          + [[kbs.menu], [kbs.orders]]
          + ([[bt('Администрирование')]] if uid in admins else []))
    global mid_kb
    mid_kb[uid] = t.send(
        uid,
        'Кстати Вам нужно знать, что Вы наш самый лучший клиент!',
        kb=kb, safe=True)
    t.send(uid, txt.main, photo='https://py.sha88.ru/s/kafehan/natur.png')
    t.delete(uid, mid)


@t.message_handler('Меню')
def menu(uid, mid):
    t.delete(uid, mid)
    cats = Category.objects.all()
    ikb = [[b(str(i), "cat_" + str(i.pk))] for i in cats]
    t.send(uid, 'Выберите раздел:', ikb=ikb)


@t.message_handler('История заказов')
def orders(uid, mid):
    t.delete(uid, mid)
    orders = Order.objects.filter(client__idu=uid).exclude(status__slag='start')
    text = 'На данный момент в истории нет заказов.' if not len(orders) else 'История заказов:'
    wait = orders.filter(status__slag='wait_access')
    access = orders.filter(status__slag='access')
    done = orders.filter(status__slag='done')
    canceled = orders.filter(status__slag='canceled')
    ikb = [[]]
    if wait:
        ikb += [[b('Ждут подтверждения', 'orders_wait_access')]]
    if access:
        ikb += [[b('Подтверждённые', 'orders_access')]]
    if done:
        ikb += [[b('Завершённые', 'orders_done')]]
    if canceled:
        ikb += [[b('Отменены', 'orders_canceled')]]
    t.send(uid, text, ikb=ikb)


@t.message_handler('Текущий заказ')
def current_order(uid, mid):
    t.delete(uid, mid)
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    if order:
        text = 'Заказ №' + str(order.pk) + '\n\n'
        prod_list = OrderList.objects.filter(order=order)
        i = 0
        for p in prod_list:
            i += 1
            text += f'{i}.) {p.product.title}\_\_{str(p.count)}шт.\_\_{str(p.product.cost * p.count)}₽\n'
        text += f'\n*Итого: {order.cost}₽*'
        t.send(uid, text, markdown=True, ikb=kbs.ikb_order)
    else:
        t.send(uid, 'У Вас нет текущего заказа.')


@t.callback_handler('menu')
def cb_menu(uid, mid):
    t.delete(uid, mid)
    cats = Category.objects.all()
    ikb = [[b(str(i), "cat_" + str(i.pk))] for i in cats]
    t.send(uid, 'Выберите раздел:', ikb=ikb)


@t.re_callback_handler(r'cat_(\d+)$')
def catalog(uid, mid, data):
    t.delete(uid, mid)
    cats = Category.objects.all()
    cat = cats.filter(pk=data[0]).first()
    other_cats = cats.exclude(pk=data[0])
    prods = cat.product_set.all()
    ikb = [[b(str(i), "cat_" + str(i.pk))] for i in other_cats]

    t.send(uid, 'Выбран раздел - ' + str(cat), ikb=ikb)
    for p in prods:
        if p.visible:
            description = "_" + p.description + "_\n"
            text = (f'\n*{p.title}*{(" / (" + p.weight + ")") if p.weight else ""}\n'
                    f'{description if p.description else ""}\nСтоимость: {p.cost}₽\n')
            t.send(
                uid, text,
                photo=('https://py.sha88.ru/' + p.photo.url) if p.photo else None,
                markdown=True, ikb=[[b('Добавить в заказ', 'prod_' + str(p.pk))]])
    t.send(uid, 'Выбран раздел - ' + str(cat), ikb=ikb)


@t.re_callback_handler(r'prod_(\d+)$')
def product(uid, mid, data):
    t.delete(uid, mid)
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    p = Product.objects.filter(pk=data[0]).first()
    has = None
    if order:
        has = OrderList.objects.filter(order=order, product=p).first()
    description = "_" + p.description + "_\n"
    text = (f'\n*{p.title}*{(" / (" + p.weight + ")") if p.weight else ""}\n'
            f'{description if p.description else ""}Стоимость: {p.cost}₽\n')
    if has:
        text += (f"\nВ заказе №{str(order)} добавлено {has.count}шт.\n\n"
                 f"*Напишите цифрами колличество на которое нужно изменить*")
    else:
        text += "\n*Напишите цифрами колличество которое нужно добавить в заказ*"

    ikb = [[b('Удалить из заказа', 'prodDelete_' + str(has.pk))] if has else []] + [
        [b('Меню - ' + str(p.category), 'cat_' + str(p.category.pk))]
    ]

    midd = t.send(uid, text,
                  photo=('https://py.sha88.ru/' + p.photo.url) if p.photo else None,
                  ikb=ikb, markdown=True)

    msg_wait[uid] = 'add_' + str(midd) + '_' + str(p.pk)
    if has:
        msg_wait[uid] += '_' + str(has.pk)


def order_calc(uid):
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    prod_list = OrderList.objects.filter(order=order)
    summ = 0
    for p in prod_list:
        summ += p.product.cost * p.count
    order.cost = summ
    order.save()


@t.re_message_handler(r'(.+)')
def in_msg(uid, mid, data):
    t.delete(uid, mid)
    if uid in msg_wait:
        data_wait = msg_wait[uid].split('_')
        if uid in msg_wait:
            data_wait = msg_wait[uid].split('_')
            if data_wait[0] == 'add':
                if data[0].isdigit() and int(data[0]) > 0:
                    del (msg_wait[uid])
                    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
                    user = Client.objects.filter(idu=uid).first()
                    prod = Product.objects.filter(pk=int(data_wait[2])).first()
                    if not order:
                        status = OrderStatus.objects.filter(slag='start').first()
                        order = Order(client=user, status=status)
                        order.save()
                        kb = ([[b('Текущий заказ', 'order')]] if order else []) + [[kbs.menu], [kbs.orders]]
                        global mid_kb
                        t.delete(uid, mid_kb[uid])

                        mid_kb[uid] = t.send(
                            uid,
                            'Кстати Вам нужно знать, что Вы наш самый лучший клиент!',
                            kb=kb, safe=True)

                    has = None
                    if len(data_wait) == 3:
                        OrderList.objects.create(order=order, product=prod, count=int(data[0]))
                    elif len(data_wait) == 4:
                        has = OrderList.objects.filter(pk=int(data_wait[3])).first()
                        has.count = int(data[0])
                        has.save()
                    order_calc(uid)
                    text = (f'{prod.title} {data[0]}шт. {str(prod.cost * int(data[0]))}₽\n'
                            f'{"добавлено в заказ" if not has else "изменено в заказе"} №{str(order)}')
                    t.send(uid, text)
                    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
                    text = 'Заказ №' + str(order.pk) + '\n\n'
                    prod_list = OrderList.objects.filter(order=order)
                    i = 0
                    for p in prod_list:
                        i += 1
                        text += f'{i}.) {p.product.title}\_\_{str(p.count)}шт.\_\_{str(p.product.cost * p.count)}₽\n'
                    text += f'\n*Итого: {order.cost}₽*'
                    t.send(uid, text, markdown=True, ikb=kbs.ikb_order)
                else:
                    t.send(uid, 'Введите число порций, которое хотите добавить в заказ!')
            elif data_wait[0] == 'delevery':
                del (msg_wait[uid])
                order = Order.objects.filter(client__idu=uid, status__slag='start').first()
                order.address = data[0]
                order.save()
                poll_select_pay_type(uid)
            elif data_wait[0] == 'comment':
                del(msg_wait[uid])
                order = Order.objects.filter(client__idu=uid, status__slag='start').first()
                order.comment = data[0]
                order.save()
                access_order(uid)
            elif data_wait[0] == 'tel':
                del(msg_wait[uid])
                order = Order.objects.filter(client__idu=uid, status__slag='start').first()
                user = Client.objects.filter(idu=uid).first()
                user.number = data[0]
                order.number = data[0]
                user.save()
                order.save()
                wait_access(uid)
        else:
            t.send(uid, 'Не ожидается текст для ввода')


@t.location_handler()
def location(uid, mid, loc):
    if uid in msg_wait and msg_wait[uid] == 'delevery':
        del (msg_wait[uid])
        t.delete(uid, mid)
        order = Order.objects.filter(client__idu=uid, status__slag='start').first()
        order.address = f'loc|{loc["latitude"]}|{loc["longitude"]}'
        order.save()
        poll_select_pay_type(uid)


@t.re_callback_handler(r'prodDelete_(\d+)$')
def prod_delete(uid, mid, data):
    t.delete(uid, mid)
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    order_list = OrderList.objects.filter(order=order)
    if len(order_list) == 1:
        kb = [[kbs.menu], [kbs.orders]]
        global mid_kb
        midd = mid_kb.get(uid, False)
        if midd:
            t.delete(uid, midd)

            mid_kb[uid] = t.send(
                uid,
                'Кстати Вам нужно знать, что Вы наш самый лучший клиент!',
                kb=kb, safe=True)

        t.send(uid, f'В заказе №{str(order)} больше не осталось блюд, поэтому он был удалён.')
        if order:
            order.delete()
    else:
        p = order_list.filter(pk=data[0]).first()
        p.delete()
        order_calc(uid)
        t.send(uid, f'{p.product.title} удалено из заказа №' + str(order))


@t.callback_handler('edit')
def edit_order(uid, mid):
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    prod_list = OrderList.objects.filter(order=order)
    kb = [[]]
    for p in prod_list:
        kb += [[b(p.product.title + ' ' + str(p.count) + 'шт.', 'prod_' + str(p.product.pk))]]
    t.send(uid, 'Выберите нужный пункт', ikb=kb)


@t.callback_handler('delete')
def delete_order(uid, mid):
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    t.send(uid, 'Заказ №' + str(order) + ' удалён.')
    kb = [[kbs.menu], [kbs.orders]]
    global mid_kb
    midd = mid_kb.get(uid, False)

    if midd:
        t.delete(uid, midd)
        mid_kb[uid] = t.send(
            uid,
            'Кстати Вам нужно знать, что Вы наш самый лучший клиент!',
            kb=kb, safe=True)

    if order:
        order.delete()


@t.callback_handler('skip_comment')
def skip_comment(uid, mid):
    del (msg_wait[uid])
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    order.comment = ""
    order.save()
    access_order(uid)


def get_comment(uid):
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    text = 'нужно накрыть на стол' if order.type.slag == 'table' else 'хотите получить заказ'

    t.send(uid,
           'Вы можете написать комментарий к закзау, а также время к которому ' + text,
           ikb=[[b('Пропустить', 'skip_comment')]])
    msg_wait[uid] = 'comment'


def poll_select_pay_type(uid):
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    pay_types = OrderPayType.objects.all()
    opt_pay = [i.name for i in pay_types]
    opt_pay_slag = [i.slag for i in pay_types]

    def cb_pay_type(uid, data):
        order.pay = OrderPayType.objects.filter(slag=opt_pay_slag[data[0]]).first()
        order.save()
        get_comment(uid)

    t.poll(uid, 'Выберите способ оплаты ', opt_pay, cb_pay_type)


@t.callback_handler('access')
def access(uid, mid):
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()

    types = OrderType.objects.all()

    opt = [i.name for i in types]
    opt_slag = [i.slag for i in types]

    def cb(uid, data):
        order.type = OrderType.objects.filter(slag=opt_slag[data[0]]).first()
        order.save()

        if order.type.slag == 'kassa':
            poll_select_pay_type(uid)
        elif order.type.slag == 'delevery':
            msg_wait[uid] = 'delevery'
            t.send(uid, 'Напишите адрес для доставки или отправьте геопозицию')
        elif order.type.slag == 'table':
            tables = Table.objects.all()
            t.send(uid, 'Выберите желаемый стол')
            for tb in tables:
                t.send(
                    uid,
                    'Стол №' + str(tb.num),
                    photo='https://py.sha88.ru' + tb.photo.url,
                    ikb=[[b('Выбрать', 'table_' + str(tb.num))]])

    t.poll(uid, 'Выберите способ получения', opt, cb)


@t.re_callback_handler(r'table_(\d+)$')
def select_table(uid, mid, data):
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    order.table = Table.objects.filter(num=int(data[0])).first()
    order.save()
    poll_select_pay_type(uid)


@t.callback_handler('select_number_user')
def select_number_user(uid, mid):
    del (msg_wait[uid])
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    user = Client.objects.filter(idu=uid).first()
    order.number = user.number
    order.save()
    wait_access(uid)


def access_order(uid):
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    user = Client.objects.filter(idu=uid).first()
    delevery_cost = int(re.search(r'\+(\d+)', OrderType.objects.filter(slag='delevery').first().name).group(1))

    if order.type.slag == 'kassa':
        if order.address:
            order.address = None
        if order.table:
            order.table = None
    if order.type.slag == 'delevery':
        if order.table:
            order.table = None
    if order.type.slag == 'table':
        if order.address:
            order.address = None

    order_calc(uid)
    if order.type.slag == 'delevery':
        order.cost = order.cost + delevery_cost
        order.save()
    text = 'Заказ №' + str(order.pk) + '\n\n'
    prod_list = OrderList.objects.filter(order=order)
    i = 0
    for p in prod_list:
        i += 1
        text += f'{i}.) {p.product.title}\_\_{str(p.count)}шт.\_\_{str(p.product.cost * p.count)}₽\n'
    if order.type.slag == 'delevery':
        text += f'\nДоствка - {str(delevery_cost)}₽\n'
    text += f'''
*Итого: {order.cost}₽*

Получение: {order.type}
'''

    if order.type.slag == 'delevery':
        text += '\nАдрес доставки: ' + ('Геопозиция' if order.address[:3] == 'loc' else order.address)
    if order.type.slag == 'table':
        text += '\nСтол номер: ' + str(order.table.num)

    text += f"""
Комментарий: {order.comment if order.comment else 'Без комментариев'}
Оплата: {order.pay.name}

*Для подтверждения заказа напишите Ваш номер телефона*
    """

    ikb = [[b('Использовать ' + user.number, 'select_number_user')]] if user.number else None
    msg_wait[uid] = 'tel'
    t.send(uid, text, ikb=ikb, markdown=True)
    if order.address and order.address[:3] == 'loc':
        loc = order.address.split('|')
        t.send_location(uid, loc[1], loc[2])


def wait_access(uid):
    admins = [i.uid.idu for i in AdminKafeHan.objects.all()]
    order = Order.objects.filter(client__idu=uid, status__slag='start').first()
    order_status = OrderStatus.objects.filter(slag='wait_access').first()
    order.status = order_status
    order.dateOrder = datetime.now()
    order.save()
    kb = [[kbs.menu], [kbs.orders]]
    global mid_kb
    midd = mid_kb.get(uid, False)

    if midd:
        t.delete(uid, midd)
        mid_kb[uid] = t.send(
            uid,
            'Кстати Вам нужно знать, что Вы наш самый лучший клиент!',
            kb=kb, safe=True)

    t.send(
        uid,
        ('Ожидайте подтверждения, заказ перемещён в историю'
         + (', после подтверждения Вы сможете оплатить заказ онлайн' if order.pay.slag == 'online' else '')))

    for a in admins:
        t.send(a, 'Новый заказ:', ikb=[[b(f'№{str(order)} - {str(order.cost)}₽', 'order_' + str(order))]])


@t.re_callback_handler(r'orders_((wait_access|access|done|canceled))$')
def orders_list(uid, mid, data):
    orders = Order.objects.filter(client__idu=uid, status__slag=data[0])
    ikb = [[]]

    if data[0] == 'wait_access':
        text = 'Ждут подтверждения:'
    elif data[0] == 'access':
        text = 'Подтверждённые:'
    elif data[0] == 'canceled':
        text = 'Отменены:'
    else:
        text = 'Завершённые:'

    for o in orders:
        if data[0] == 'wait_access':
            date = o.dateOrder
        elif data[0] == 'access':
            date = o.dateAccess
        elif data[0] == 'canceled':
            date = o.dateCanceled
        else:
            date = o.dateDone

        ikb += [[b(f'№{str(o.pk)}) {str(date.strftime("%d%B%Yг. %H:%M"))} - {str(o.cost)}₽', 'order_' + str(o.pk))]]
    t.send(uid, text, ikb=ikb)


@t.re_callback_handler(r'order_(\d+)$')
def order_one(uid, mid, data):
    order = Order.objects.filter(pk=data[0]).first()
    admins = [i.uid.idu for i in AdminKafeHan.objects.all()]
    status = order.status
    payed = 'оплачено' if order.payed else 'НЕоплачено'
    delevery_cost = int(re.search(r'\+(\d+)', OrderType.objects.filter(slag='delevery').first().name).group(1))

    text = 'Заказ №' + str(order.pk) + '\n\n'
    prod_list = OrderList.objects.filter(order=order)
    i = 0
    for p in prod_list:
        i += 1
        text += f'{i}.) {p.product.title}\_\_{str(p.count)}шт.\_\_{str(p.product.cost * p.count)}₽\n'
    if order.type.slag == 'delevery':
        text += f'\nДоствка - {str(delevery_cost)}₽\n'
    text += f'''
*Итого: {order.cost}₽*

Получение: {order.type}
    '''

    if order.type.slag == 'delevery':
        text += '\nАдрес доставки: ' + ('Геопозиция' if order.address[:3] == 'loc' else order.address)
    if order.type.slag == 'table':
        text += '\nСтол номер: ' + str(order.table.num)

    text += f"""
Комментарий: {order.comment if order.comment else 'Без комментариев'}
Оплата: {order.pay.name}
Телефон: {order.number}
        """

    ikb = [[]]
    if status.slag in ['access', 'wait_access']:
        ikb += [[b('Отменить заказ', 'order_cancel_'+str(order))]]
    if status.slag == 'done' and uid == order.client.idu:
        ikb += [[b('Повторить заказ', 'order_repeat_' + str(order))]]
    if status.slag == 'canceled':
        ikb += [[b('Повторить', 'order_repeat_' + str(order))]]

    if uid in admins:
        if order.dateOrder:
            text += '\nДата заказа: ' + order.dateOrder.strftime("%d%B%Yг. %H:%M")
        if order.dateAccess:
            text += '\nДата подтверждения: ' + order.dateAccess.strftime("%d%B%Yг. %H:%M")
        if order.dateDone:
            text += '\nДата завершения: ' + order.dateDone.strftime("%d%B%Yг. %H:%M")
        if order.dateCanceled:
            text += '\nДата отмены: ' + order.dateCanceled.strftime("%d%B%Yг. %H:%M")

        text += f"""
Статус: {status.name} {'клиентом' if status.slag == 'canceled' and order.canceled == order.client.idu else ''}
Оплата: {payed}

\nПользователь:
    id: {str(order.client)}
    login: {order.client.username if order.client.username else 'отсутствует'}
    Имя: {order.client.first_name if order.client.first_name else 'отсутствует'}
    Фамилия: {order.client.last_name if order.client.last_name else 'отсутствует'}
    Зарегистрирован: {order.client.created_at.strftime("%d%B%Yг. %H:%M")}
        """
        if status.slag == 'wait_access':
            ikb += [[b('Подтвердить заказ', 'order_access_' + str(order))]]
        if status.slag == 'access' and not order.payed:
            ikb += [[b('Принять оплату', 'order_payed_' + str(order))]]
        if status.slag != 'done':
            ikb += [[b('Обновить', 'order_' + str(order))]]
        if status.slag == 'access' and order.payed:
            ikb += [[b('Завершить заказ', 'order_done_' + str(order))]]

    photo = 'https://py.sha88.ru' + order.client.photo.url if order.client.photo and uid in admins else None

    t.send(uid, text, ikb=ikb, markdown=True, photo=photo)
    if order.address and order.address[:3] == 'loc':
        t.send_location(uid, order.address.split('|')[1], order.address.split('|')[2])
