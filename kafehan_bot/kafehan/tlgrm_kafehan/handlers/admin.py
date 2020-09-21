import re
import json
import uuid
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth


from config import YK_SHOP_ID, YK_SHOP_API_TOKEN
from kafehan.models import *
from kafehan.tlgrm_kafehan import kbs
from kafehan.tlgrm_kafehan.bot import t
from kafehan.tlgrm_kafehan.kbs import b, bu
from ksk_util.dump import add_dump_txt
from . import order_calc

admins = [i.uid.idu for i in AdminKafeHan.objects.all()]


@t.message_handler('🔓 Администрирование', admins)
def administration(uid, mid):
    t.delete(uid, mid)
    orders = Order.objects.exclude(status__slag='start')
    wait = orders.filter(status__slag='wait_access')
    access = orders.filter(status__slag='access')
    done = orders.filter(status__slag='done')
    canceled = orders.filter(status__slag='canceled')

    ikb = [[]]
    if wait:
        ikb += [[b('☑ Ожидают подтверждения', 'admin_orders_wait_access')]]
    if access:
        ikb += [[b('✔ Подтверждены', 'admin_orders_access')]]
    if done:
        ikb += [[b('✅ Завершены', 'admin_orders_done')]]
    if canceled:
        ikb += [[b('🚫 Отменены', 'admin_orders_canceled')]]
    t.send(uid, '🔓 Администрирование:', ikb=ikb)


@t.re_callback_handler(r'admin_orders_((wait_access|access|done|canceled))$', admins)
def admin_orders(uid, mid, data):
    orders = Order.objects.filter(status__slag=data[0])
    if data[0] in ['done', 'canceled']:
        orders = orders[:20]
    ikb = [[]]
    if data[0] == 'wait_access':
        text = '☑ Ждут подтверждения:'
    elif data[0] == 'access':
        text = '✔ Подтверждённые:'
    elif data[0] == 'canceled':
        text = '🚫 Отменены:'
    else:
        text = '✅ Завершённые:'
    for o in orders:
        order_calc(o)
        if data[0] == 'wait_access':
            date = o.dateOrder.strftime("%d%B%Yг. %H:%M") if o.dateOrder else ''
        elif data[0] == 'access':
            date = o.dateAccess.strftime("%d%B%Yг. %H:%M") if o.dateAccess else ''
        elif data[0] == 'canceled':
            date = o.dateCanceled.strftime("%d%B%Yг. %H:%M") if o.dateCanceled else ''
        else:
            date = o.dateDone.strftime("%d%B%Yг. %H:%M") if o.dateDone else ''
        ikb += [[b(f'№{str(o.pk)}) {str(date)} - {str(o.cost)}₽', 'order_' + str(o))]]

    t.send(uid, text, ikb=ikb)


@t.re_callback_handler(r'order_cancel_(\d+)$')
def order_canceled(uid, mid, data):
    order = Order.objects.filter(pk=data[0]).first()
    order.status = OrderStatus.objects.filter(slag='canceled').first()
    order.dateCanceled = datetime.now()
    order.canceled = uid
    order.save()
    if uid != order.client.idu and uid in admins:
        t.send(order.client.idu, '⛔ Заказ №' + str(order) + ' отменён администратором!')
    if uid == order.client.idu:
        for a in admins:
            t.send(a, '⛔ Заказ №' + str(order) + ' отменён клиентом!')
    t.send(uid, '⛔ Заказ №' + str(order) + ' отменён!')


@t.re_callback_handler(r'order_repeat_(\d+)$')
def repeat_order(uid, mid, data):
    client = Order.objects.filter(pk=data[0]).first().client
    if Order.objects.filter(client__idu=client.idu, status__slag='start').first():
        t.send(
            uid,
            '⛔ Существует текущий заказ, отмените его или подтвердите. '
            'Затем Вы сможете повторить любой завершённый или отменённый заказ.')
        return
    order = Order(client=client, status=OrderStatus.objects.filter(slag='start').first())
    order.save()
    summ = 0
    for p in OrderList.objects.filter(order=data[0]):
        OrderList.objects.create(order=order, product=p.product, count=p.count)
        summ += p.product.cost * p.count
    order.cost = summ
    order.save()
    text = '📋 Заказ №' + str(order.pk) + '\n\n'
    prod_list = OrderList.objects.filter(order=order)
    i = 0
    for p in prod_list:
        i += 1
        text += f'{i}.) {p.product.title}\_\_{str(p.count)}шт.\_\_{str(p.product.cost * p.count)}₽\n'
    from . import mid_kb
    text += f'\n💰 *Итого: {order.cost}₽*'
    kb = ([[b('📌 Текущий заказ', 'order')]] if order else []) + [[kbs.menu], [kbs.orders]]
    if uid == order.client.idu:
        t.delete(uid, mid_kb[uid])
        mid_kb[uid] = t.send(
            uid,
            'Кстати Вам нужно знать, что Вы наш самый лучший клиент🤴🏻!',
            kb=kb, safe=True)
        t.send(uid, text, markdown=True, ikb=kbs.ikb_order)
    else:
        t.send(uid, 'Заказ повторён, клиенту отправлено уведомление.')
        t.delete(order.client.idu, mid_kb[order.client.idu])
        mid_kb[order.client.idu] = t.send(
            order.client.idu,
            'Кстати Вам нужно знать, что Вы наш самый лучший клиент🤴🏻!',
            kb=kb, safe=True)
        t.send(order.client.idu, '🖊 Администратором повторён ваш заказ, подтвердите или измените его.')
        t.send(order.client.idu, text, markdown=True, ikb=kbs.ikb_order)


@t.re_callback_handler(r'order_access_(\d+)', admins)
def order_access_one(uid, mid, data):
    order = Order.objects.filter(pk=data[0]).first()
    order.status = OrderStatus.objects.filter(slag='access').first()
    order.dateAccess = datetime.now()
    order.save()

    text = (f' ❕ До либо во время получения заказа, необходимо перевести {str(order.cost)}₽ на карту '
            'Сбербанк Visa 4276 3800 1966 5251 с комментарием: ' + str(order)
            + '.\nПолучатель: Бозорбоев Мухаммадюнус Юлдашбой.')

    t.send(
        order.client.idu,
        f'✅ Ваш заказ №{str(order)} подтверждён!'
        + (text if order.pay.slag == 'perevod' else ''))

    if order.pay.slag == 'online':
        delevery_cost = int(re.search(r'\+(\d+)', OrderType.objects.filter(slag='delevery').first().name).group(1))

        text = '📋 Заказ №' + str(order) + '\n\n'
        prod_list = OrderList.objects.filter(order=order)
        i = 0
        for p in prod_list:
            i += 1
            text += f'{i}.) {p.product.title}\_\_{str(p.count)}шт.\_\_{str(p.product.cost * p.count)}₽\n'
        if order.type.slag == 'delevery':
            text += f'\nДоствка - {str(delevery_cost)}₽\n'
        text += f'''
        💰 *Итого: {order.cost}₽*

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

        url_pay = create_online_payment(order)

        if url_pay:
            t.send(
                order.client.idu,
                '❕ Для оплаты онлайн Вы будете перенаправлены на сайт платёжной системы.',
                ikb=[
                    [bu('💳 Оплатить ' + str(order.cost) + '₽', url_pay)],
                    [b('🚫 Отменить заказ', 'order_cancel_' + str(order))]
                ])

    t.send(uid, f'☑ Заказ №{str(order)} подтверждён!', ikb=[[b('👀 Просмотреть', 'order_' + str(order))]])


def create_online_payment(order):
    try:
        res = requests.post(
            'https://payment.yandex.net/api/v3/payments',
            headers={
                'Idempotence-Key': str(uuid.uuid4()),
                'Content-Type': 'application/json; charset utf-8',
            },
            data=json.dumps({
                "amount": {
                    "value": order.cost,
                    "currency": "RUB"
                },
                "capture": True,
                "confirmation": {
                    "type": "redirect",
                    "return_url": "t.me/kafeHanBot"
                },
                "description": 'Заказ №' + str(order)
            }).encode('utf-8'),
            auth=HTTPBasicAuth(YK_SHOP_ID, YK_SHOP_API_TOKEN)).json()
    except Exception as e:
        # dump_add(e)
        # dump_add(traceback.format_exc())
        res = None

    if res and 'confirmation' in res:
        OnlinePay.objects.create(id_pay=res['id'], status=res['status'], order=order, cost=order.cost)
        res = res['confirmation']['confirmation_url']
    return res


@t.pre_checkout_handler()
def pre_checkout(data):
    t.request('answerPreCheckoutQuery', {
        'pre_checkout_query_id': data['id'],
        'ok': True
    })


@t.re_callback_handler(r'order_payed_(\d+)$', admins)
def order_payed(uid, mid, data):
    order = Order.objects.filter(pk=data[0]).first()
    order.payed = True
    order.save()
    for a in admins:
        t.send(a, '✔ Заказ №' + str(order) + ': оплата принята!', ikb=[[b('Просмотреть', 'order_' + str(order))]])
    t.send(order.client.idu, '✔ Заказ №' + str(order) + ': оплачен!')


@t.re_callback_handler(r'order_done_(\d+)$', admins)
def order_payed(uid, mid, data):
    order = Order.objects.filter(pk=data[0]).first()
    order.status = OrderStatus.objects.filter(slag='done').first()
    order.dateDone = datetime.now()
    order.save()
    for a in admins:
        t.send(a, '✔ Заказ №' + str(order) + ': завершён!', ikb=[[b('👀 Просмотреть', 'order_' + str(order))]])
    t.send(order.client.idu, '✔ Заказ №' + str(order) + ': завершён!\n🍲 Приятного аппетита!\n🙋 ‍Будем рады видеть Вас снова!')
