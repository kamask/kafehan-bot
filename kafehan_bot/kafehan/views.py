import os
import json
from datetime import datetime
from django.http import JsonResponse
from kafehan_bot.settings import BASE_DIR
from .tlgrm_kafehan.bot import t
import kafehan.tlgrm_kafehan.handlers
import kafehan.tlgrm_kafehan.handlers.admin


def tlgrm(request):
    res = json.loads(request.body)

    with open(os.path.normpath(os.path.join(BASE_DIR, '../public/s/kafehan/log.txt')), 'a') as f:
        f.write('\n'+str(datetime.now())+'\n'+json.dumps(res, indent="    ", ensure_ascii=False,)+'\n\n')

    t.webhook_handler(res)

    return JsonResponse({
        "status": 'Ok'
    }, safe=False)
