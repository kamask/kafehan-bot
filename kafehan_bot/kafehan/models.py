from django.db import models


class Client(models.Model):
    idu = models.IntegerField(unique=True, verbose_name='Идентификатор')
    first_name = models.CharField(max_length=255, blank=True, verbose_name='Имя')
    last_name = models.CharField(max_length=255, blank=True, verbose_name='Фамилия')
    username = models.CharField(max_length=255, blank=True, verbose_name='Ник')
    number = models.CharField(max_length=255, blank=True, verbose_name='Телефонный номер', null=True)
    photo = models.ImageField(
        upload_to='kafehan/clients/photo/%Y/%m/%d',
        default='kafehan/clients/photo/no_photo.png',
        verbose_name='Фото'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return str(self.idu)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['username']


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Название категории')
    order = models.IntegerField(verbose_name='Порядок', blank=True, default=1)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order']


class Product(models.Model):
    title = models.CharField(max_length=255, unique=True, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, verbose_name='Категория')
    weight = models.CharField(max_length=255, verbose_name='Вес', blank=True)
    cost = models.IntegerField(verbose_name='Стоимость')
    visible = models.BooleanField(default=True, verbose_name='Отображать')
    photo = models.ImageField(
        blank=True,
        upload_to='kafehan/product/photo/%Y/%m/%d',
        default='',
        verbose_name='Фото'
    )

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['title']


class OrderStatus(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Статус')
    slag = models.CharField(max_length=255, unique=True, verbose_name='slag')

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Статус'
        verbose_name_plural = 'Статусы'
        ordering = ['name']


class OrderType(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Способ')
    slag = models.CharField(max_length=255, unique=True, verbose_name='slag')

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Способ получения'
        verbose_name_plural = 'Способы получения'
        ordering = ['name']


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    client = models.ForeignKey('Client', on_delete=models.CASCADE, verbose_name='Клиент')
    number = models.CharField(max_length=255, blank=True, verbose_name='Телефонный номер', null=True)
    status = models.ForeignKey('OrderStatus', on_delete=models.CASCADE, verbose_name='Статус')
    type = models.ForeignKey('OrderType', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Способ получения')
    comment = models.TextField(blank=True, verbose_name='Коментарий', null=True)
    address = models.TextField(blank=True, verbose_name='Адрес', null=True)
    table = models.ForeignKey('Table', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Стол')
    dateOrder = models.DateTimeField(verbose_name='Дата заказа', blank=True, null=True)
    dateAccess = models.DateTimeField(verbose_name='Дата подтверждения', blank=True, null=True)
    dateDone = models.DateTimeField(verbose_name='Дата выполнения', blank=True, null=True)
    dateCanceled = models.DateTimeField(verbose_name='Дата отмены', blank=True, null=True)
    update_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата обновления')
    pay = models.ForeignKey('OrderPayType', on_delete=models.CASCADE, verbose_name='Способ оплаты', blank=True, null=True)
    cost = models.IntegerField(verbose_name='Сумма', default=0)
    payed = models.BooleanField(default=False, verbose_name='Оплачено')
    canceled = models.IntegerField(verbose_name='Отменён', null=True)

    def __str__(self):
        return str(self.pk)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class OrderList(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, verbose_name='Заказ')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name='Продукт')
    count = models.IntegerField(verbose_name='Количество')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return str(self.product)

    class Meta:
        verbose_name = 'Продукт в заказе'
        verbose_name_plural = 'Продукты в заказе'
        ordering = ['order']


class Table(models.Model):
    num = models.IntegerField(verbose_name='Номер стола')
    photo = models.ImageField(
        null=True,
        upload_to='kafehan/product/photo/%Y/%m/%d',
        verbose_name='Фото'
    )

    def __str__(self):
        return str(self.num)

    class Meta:
        verbose_name = 'Стол'
        verbose_name_plural = 'Столы'
        ordering = ['num']


class OrderPayType(models.Model):
    name = models.CharField(max_length=255, verbose_name='Способ')
    slag = models.CharField(max_length=255, verbose_name='slag')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Способ оплаты'
        verbose_name_plural = 'Способы оплаты'


class AdminKafeHan(models.Model):
    uid = models.ForeignKey('Client', on_delete=models.CASCADE, verbose_name='Пользователь')

    def __str__(self):
        return str(self.uid)

    class Meta:
        verbose_name = 'Админ кафе'
        verbose_name_plural = 'Админ кафе'
