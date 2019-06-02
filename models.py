import datetime

import mongoengine
import requests as re
from bs4 import BeautifulSoup

from conf import url, db_name

mongoengine.connect(db_name, host=url)


def get_html(url):
    response = re.get(url)
    return response.text


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

    def get_litres_reviews_library(self):
        for book in self.books:
            if not book.litres_reviews_ids:
                book.get_review_list_litres()


class Review(mongoengine.Document):
    type = mongoengine.IntField()
    text = mongoengine.StringField()
    book = mongoengine.ReferenceField('Book', reverse_delete_rule=mongoengine.DO_NOTHING)
    mark = mongoengine.ListField(default=[0 for x in range(11)])
    voted = mongoengine.DictField()


class ReviewsToAdd(mongoengine.Document):
    text = mongoengine.StringField()
    count = mongoengine.IntField(default=1)


class Book(mongoengine.Document):
    meta = {'strict': False}

    url = mongoengine.StringField()
    article = mongoengine.StringField()
    autor = mongoengine.ReferenceField('Autor', reverse_delete_rule=mongoengine.DO_NOTHING)
    reviews = mongoengine.ListField(mongoengine.ReferenceField('Review', reverse_delete_rule=mongoengine.CASCADE))
    url_litres = mongoengine.StringField()
    url_bookmate = mongoengine.StringField()
    litres_reviews = mongoengine.ListField()

    def form_link_litres(self):
        small_url = 'https://www.litres.ru'

        search_url = 'https://www.litres.ru/pages/rmd_search_arts/?q={}'.format(
            (self.autor.name + ' ' + self.article).replace(' ', '+'))

        html = get_html(search_url)
        soup = BeautifulSoup(html, 'lxml')
        book_ent = soup.select('div.art-item__name')
        for obj in book_ent:
            if obj['class'] == ['art-item__name'] and self.article in obj.contents[0]['title']:
                return small_url + obj.contents[0]['href']

    def get_review_text(self, list_):
        text = f'📖{self.article}\n'
        reviews = []

        for child in list_:
            child = str(child)
            # print(child[:3],child[-4:])
            if child[:3] == '<p>' and child[-4:] == '</p>' and not '<i>' in child:
                text += '\n' + child[3:-4]
            # elif '<i>' in child:
            #     text = child[child.find('<i>')+3:child.find('</i>')]  + '\n' + text
        text = text.replace('<br/>', '\n')
        return text

    def get_review_list_litres(self):
        if not self.url_litres:
            url_litres = self.form_link_litres()
            url_to_search = url_litres + 'otzivi/page-4/'
            self.update(url_litres=url_litres)
        else:
            url_to_search = self.url_litres + 'otzivi/page-4/'

        html = get_html(url_to_search)
        print(url_to_search)
        # print('is it captcha?\n',html)
        soup = BeautifulSoup(html, 'lxml')
        # for i in
        reviews = []
        for x in soup.select('div.recense_content'):
            # print(x.findChildren())
            reviews.append(self.get_review_text(x.findChildren()))

        self.update(litres_reviews=reviews)
        # self.litres_reviews = reviews
        # self.save()
        return Book.objects(id=self.id).first()

    def create_reviews(self):
        if len(Review.objects(book=self)) == 0:
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


class UserQueue(mongoengine.Document):
    u_id = mongoengine.IntField()
    book = mongoengine.ReferenceField(Book, reverse_delete_rule=mongoengine.DO_NOTHING)
    in_chat = mongoengine.BooleanField(default=False)
    date = mongoengine.DateField(default=datetime.datetime.now())
