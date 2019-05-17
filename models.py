import datetime

import mongoengine

from conf import url, db_name

mongoengine.connect(db_name, host=url)


class User(mongoengine.Document):
    # id = mongoengine.ReferenceField(Posts,primary_key=True)
    mes_id = mongoengine.IntField()
    user_id = mongoengine.IntField()
    username = mongoengine.StringField()
    invited = mongoengine.ListField()
    from_user = mongoengine.IntField()
    phone = mongoengine.StringField()
    need_to_notify = mongoengine.BooleanField(default=True)
    notified = mongoengine.BooleanField(default=False)
    books = mongoengine.ListField(mongoengine.ReferenceField('Book', reverse_delete_rule=mongoengine.DO_NOTHING))
    # orders = mongoengine.StringField()
    self_url = mongoengine.StringField()
    time_started = mongoengine.DateTimeField(default=datetime.datetime.now())
    step = mongoengine.StringField(default="start")


class Review(mongoengine.Document):
    type = mongoengine.IntField()
    text = mongoengine.StringField()
    book = mongoengine.ReferenceField('Book', reverse_delete_rule=mongoengine.DO_NOTHING)
    mark = mongoengine.ListField(default=[0 for x in range(11)])
    voted = mongoengine.DictField()


class Book(mongoengine.Document):
    url = mongoengine.StringField()
    article = mongoengine.StringField()
    autor = mongoengine.ReferenceField('Autor', reverse_delete_rule=mongoengine.DO_NOTHING)
    reviews = mongoengine.ListField(mongoengine.ReferenceField('Review', reverse_delete_rule=mongoengine.CASCADE))
    url_litres = mongoengine.StringField()
    url_bookmate = mongoengine.StringField()

    def create_reviews(self):
        list_of_reviews = ['Легко читается', 'Требует усилий / тяжело читается', 'Интересный сюжет',
                           'Держит внимание до конца']
        for i, val in enumerate(list_of_reviews):
            text = '{}. {}'.format(i + 1, val)
            review = Review(type=i, text=text, book=self)
            review.save()
            self.update(reviews=self.reviews.append(review))


class Autor(mongoengine.Document):
    url = mongoengine.StringField()
    name = mongoengine.StringField()
    surname = mongoengine.StringField()
    patronymic = mongoengine.StringField()  # Отчество
    books = mongoengine.ListField(mongoengine.ReferenceField(Book, reverse_delete_rule=mongoengine.CASCADE),
                                  reverse_delete_rule=mongoengine.DO_NOTHING)
    url_litres = mongoengine.StringField()
    url_bookmate = mongoengine.StringField()
