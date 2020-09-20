import traceback
from ksk_util.dump import add_dump_txt as dump_add

import re
from urllib.request import Request, urlopen
import json


class TBot:
    message_handlers = dict()
    re_message_handlers = list()
    callback_handlers = dict()
    re_callback_handlers = list()
    poll_handlers = dict()
    location_handler_func = None
    pre_checkout_handler_func = None

    prev_msg_ids = dict()
    msg_ids_for_delete = dict()
    users = dict()

    def __init__(self, token, history=False):
        self.token = token
        self.history = history

    def webhook_handler(self, res):

        def search_handler(handlers, re_handlers):
            finded = False
            if data in handlers:
                if callable(handlers[data]):
                    handlers[data](uid, mid)
                else:
                    private_list = handlers[data][1]
                    if uid in private_list:
                        handlers[data][0](uid, mid)
                    else:
                        self.delete(uid, mid)
                        self.send(uid, 'Ты не избранный!')
                finded = True
            else:
                for h in re_handlers:
                    match = re.match(h[0], data)
                    if match:
                        if callable(h[1]):
                            h[1](uid, mid, match.groups())
                        else:
                            if uid in h[1][1]:
                                h[1][0](uid, mid, match.groups())
                            else:
                                self.delete(uid, mid)
                                self.send(uid, 'Ты не избранный!')
                        finded = True
                        break
            return finded

        if 'message' in res:
            user = res['message']['from']
            uid = user['id']
            mid = res['message']['message_id']
            if 'text' in res['message']:
                data = res['message']['text']
                self.users[uid] = user
                self.clear_msg_stack(uid)
                if not self.history and not search_handler(self.message_handlers, self.re_message_handlers):
                    self.delete(uid, mid)
                    self.send(uid, 'Ошибка ввода')
            elif 'location' in res['message']:
                self.clear_msg_stack(uid)
                self.location_handler_func(uid, mid, res['message']['location'])

        elif 'callback_query' in res:
            user = res['callback_query']['from']
            uid = user['id']
            mid = res['callback_query']['message']['message_id']
            data = res['callback_query']['data']
            self.users[uid] = user
            self.clear_msg_stack(uid)
            search_handler(self.callback_handlers, self.re_callback_handlers)
        elif 'poll_answer' in res:
            user = res['poll_answer']['user']
            uid = user['id']
            data = res['poll_answer']['option_ids']
            self.users[uid] = user
            self.clear_msg_stack(uid)
            if uid in self.poll_handlers:
                handler = self.poll_handlers[uid]
                del(self.poll_handlers[uid])
                handler(uid, data)
        elif 'pre_checkout_query' in res:
            self.pre_checkout_handler_func(res['pre_checkout_query'])
        else:
            return True

    def message_handler(self, data, private=None):
        def wrapper(func):
            def f(*args, **kwargs):
                func(*args, **kwargs)
            self.message_handlers[data] = (f, private,) if private else f
        return wrapper

    def re_message_handler(self, data, private=None):
        def wrapper(func):
            def f(*args, **kwargs):
                func(*args, **kwargs)
            self.re_message_handlers.append((data, ((f, private,) if private else f),))
        return wrapper

    def callback_handler(self, data, private=None):
        def wrapper(func):
            def f(*args, **kwargs):
                func(*args, **kwargs)
            self.callback_handlers[data] = (f, private,) if private else f
        return wrapper

    def re_callback_handler(self, data, private=None):
        def wrapper(func):
            def f(*args, **kwargs):
                func(*args, **kwargs)
            self.re_callback_handlers.append((data, ((f, private,) if private else f),))
        return wrapper

    def location_handler(self):
        def wrapper(func):
            def f(*args, **kwargs):
                func(*args, **kwargs)
            self.location_handler_func = f
        return wrapper

    def pre_checkout_handler(self):
        def wrapper(func):
            def f(*args, **kwargs):
                func(*args, **kwargs)
            self.pre_checkout_handler_func = f
        return wrapper

    def clear_msg_stack(self, uid):
        if not self.history and uid in self.prev_msg_ids:
            for m in self.prev_msg_ids[uid]:
                self.delete(uid, m)
            del (self.prev_msg_ids[uid])

    def request(self, method, data):
        url = 'https://api.telegram.org/bot' + self.token + '/' + method
        try:
            res = urlopen(Request(url, json.dumps(data).encode('utf-8'), {'Content-Type': 'application/json; charset utf-8'}))
            return json.loads(res.read())
        except Exception as e:
            # dump_add(e)
            # dump_add(traceback.format_exc())
            return None

    def get_user_photo(self, uid):
        res = self.request('getUserProfilePhotos', {'user_id': uid})
        if res['result']['photos']:
            fid = res['result']['photos'][0][-1]['file_id']
            res = self.get_file(fid)
        else:
            res = None
        return res

    def get_file(self, fid):
        res = self.request('getFile', {'file_id': fid})
        return 'https://api.telegram.org/file/bot' + self.token + '/' + res['result']['file_path']

    def get_prev_sended_msg_id(self, uid):
        if uid in self.prev_msg_ids:
            return self.prev_msg_ids[uid]
        else:
            return None

    def get_tg_user(self, uid):
        return self.users[uid]

    def send(self, uid, text, kb=None, ikb=None, photo=None, markdown=False, safe=False):
        data = {'chat_id': uid}
        if photo:
            data['caption'] = text
            data['photo'] = photo
        else:
            data['text'] = text
        if markdown:
            data['parse_mode'] = 'Markdown'
        if kb or ikb:
            data['reply_markup'] = dict()
            if kb:
                data['reply_markup']['resize_keyboard'] = True
                data['reply_markup']['keyboard'] = kb
            if ikb:
                data['reply_markup']['inline_keyboard'] = ikb

        res = self.request('send' + ('Photo' if photo else 'Message'), data)

        midd = res['result']['message_id'] if res else None
        if not safe:
            if uid not in self.prev_msg_ids:
                self.prev_msg_ids[uid] = list()
            self.prev_msg_ids[uid].append(midd)
        return midd

    def send_location(self, uid, lat, long, safe=False):
        data = {
            'chat_id': uid,
            'latitude': lat,
            'longitude': long
        }

        res = self.request('sendLocation', data)

        midd = res['result']['message_id'] if res else None
        if not safe:
            if uid not in self.prev_msg_ids:
                self.prev_msg_ids[uid] = list()
            self.prev_msg_ids[uid].append(midd)
        return midd

    def send_invoice(self, uid, data):
        data_default = {
            "chat_id": uid,
            "title": "Продукт",
            "description": "Описание",
            "payload": "test",
            "provider_token": "381764678:TEST:19331",
            "start_parameter": "test",
            "currency": "RUB",
            "prices": [
                {
                    "label": "product",
                    "amount": 9900
                }
            ]
        }
        data_default.update(data)
        res = self.request('sendInvoice', data_default)

        midd = res['result']['message_id'] if res else None

        if uid not in self.prev_msg_ids:
            self.prev_msg_ids[uid] = list()
        self.prev_msg_ids[uid].append(midd)
        return midd

    def poll(self, uid, question, options, cb, safe=False):
        self.poll_handlers[uid] = cb
        data = {
            'chat_id': uid,
            'question': question,
            'options': options,
            'is_anonymous': False
        }
        res = self.request('sendPoll', data)
        midd = res['result']['message_id'] if res else None
        if not safe:
            if uid not in self.prev_msg_ids:
                self.prev_msg_ids[uid] = list()
            self.prev_msg_ids[uid].append(midd)
        return midd

    def delete(self, uid, mid):
        self.request('deleteMessage', {'chat_id': uid, 'message_id': mid})
