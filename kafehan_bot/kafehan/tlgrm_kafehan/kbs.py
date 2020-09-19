def b(text, cb):
    return {"text": text, "callback_data": cb}


def bt(text):
    return {"text": text}


menu = bt("Меню")
orders = bt("История заказов")
order = bt("Текущий заказ")

ikb_order = [
    [b('Добавить ещё', 'menu'), b('Изменить заказ', 'edit')],
    [b('Оформить заказ', 'access'), b('Удалить заказ', 'delete')],
]

