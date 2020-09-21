import os
import re
import json
from datetime import datetime
from django.http import JsonResponse
from kafehan_bot.settings import BASE_DIR
from .tlgrm_kafehan.bot import t
import kafehan.tlgrm_kafehan.handlers
import kafehan.tlgrm_kafehan.handlers.admin
from .models import Order, OnlinePay
from .tlgrm_kafehan.handlers.admin import create_online_payment, admins
from .tlgrm_kafehan.kbs import bu, b


def tg(request):
    res = json.loads(request.body)

    # with open(os.path.normpath(os.path.join(BASE_DIR, 'log/log.txt')), 'a') as f:
    #     f.write('\n'+str(datetime.now())+'\n'+json.dumps(res, indent="    ", ensure_ascii=False,)+'\n\n')

    t.webhook_handler(res)

    return JsonResponse({
        "status": 'Ok'
    }, safe=False)


def yk(request):
    res = json.loads(request.body)

    # with open(os.path.normpath(os.path.join(BASE_DIR, 'log/log-yk.txt')), 'a') as f:
    #     f.write('\n'+str(datetime.now())+'\n'+json.dumps(res, indent="    ", ensure_ascii=False,)+'\n\n')

    if 'object' in res:
        status = res['object']['status']
        pay = OnlinePay.objects.filter(id_pay=res['object']['id']).first()
        pay.status = status
        pay.save()
        order_id = int(re.match(r'Заказ №(\d+)$', res['object']['description']).group(1))
        order = Order.objects.filter(pk=order_id).first()

        if order.pk == order_id:
            if order.status.slag == 'access':
                t.clear_msg_stack(order.client.idu)
                if status == 'succeeded':
                    order.payed = True
                    order.save()
                    t.send(
                        order.client.idu,
                        '✅ Заказ №' + str(order) + ' успешно оплачен 💵 и уже готовится!♨')
                    for a in admins:
                        t.send(
                            a,
                            '✅ Заказ №' + str(order) + ' оплачен онлайн! 💵',
                            ikb=[[b('Просмотреть 👀', 'order_' + str(order))]])

                elif status == 'canceled':
                    url_pay = create_online_payment(order)

                    if url_pay:
                        t.send(
                            order.client.idu,
                            '🚷 Платёж не прошёл, сформирован новый:',
                            ikb=[
                                [bu('💲 Оплатить' + str(order.cost) + '₽', url_pay)],
                                [b('❌ Отменить заказ', 'order_cancel_' + str(order))]
                            ])

    return JsonResponse({
        "status": 'Ok, thank you!'
    }, safe=False)
