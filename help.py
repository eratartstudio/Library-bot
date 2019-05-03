from aiogram import types

from models import Review

start_message = '''
Привет!🖖 Я бот который сделан для таких людей как ты, людей которые любят читать 📚 Расскажи мне какие книги ты уже прочитал и твои самые любимые жанры 😉 
'''

get_name_message = 'Напиши мне его Имя и Фамилию ✍️'
notification = 'notified!'

pre_text_review = '''
Книга добавлена! Поделись со мной своими впечатлениями о книге 🙏
'''

pre_text_solo_review = '''
{}. {}
Оценка {}/10 ({}) отзывов
Оцени по этому критерию от 1 до 10
'''


def get_max_mark(marks):
    maxcount = 0
    index = 0
    for mark, count in enumerate(marks):
        if count >= maxcount:
            maxcount = count
            index = mark

    return index, maxcount


def get_solo_review_text(review: Review):
    mark, maxcount = get_max_mark(review.mark)
    pre_text_solo_review.format(review.type, review.text, mark, maxcount)
    return pre_text_solo_review


def get_reviews_text():
    mes = pre_text_review
    i = 1
    query = Review.objects(type=i)

    while (list(query) != []):
        mes += f'\n{i}. {query[0].text}'
        i += 1
        query = Review.objects(type=i)
        # print(i,query)
    mes += '\nВыбери критерий для оценки'
    return mes


def get_list_of_authors(count, autors):
    msg = ''
    print(autors)
    for autor in autors[count:count + 8]:
        print(autor)
        msg += f'{count + 1}. {autor.name} {autor.surname} {autor.patronymic}\nВыбрать автора /autor_{autor.id}\n'
        count += 1

    return msg


def get_list_of_books(count, autor):
    msg = ''
    # print(autors)
    for book in autor.books[count:count + 8]:
        print(autor)
        msg += f'{count + 1}. {book.article}\nВыбрать книгу /book_{book.id}\n'
        count += 1

    return msg


def simple_keyboard(*buttons, row_width=3, one_time_keyboard=True):
    mark = types.ReplyKeyboardMarkup(row_width=row_width, one_time_keyboard=one_time_keyboard, resize_keyboard=True)
    for button in buttons:
        mark.add(button)

    return mark


def simple_button(text, request_contact=False, request_location=False):
    return types.KeyboardButton(text, request_contact, request_location)


def inK(*buttons, row_width=3):
    mark = types.InlineKeyboardMarkup(row_width=row_width)
    for button in buttons:
        mark.add(button)
    return mark


def inB(text, url=None, data=None):
    return types.InlineKeyboardButton(text=text, url=url, callback_data=data)


def getMenuReply():
    mark = simple_keyboard(one_time_keyboard=False)
    mark.row(simple_button('🎓 Автор'), simple_button('📔 Название'))
    mark.row(simple_button('📚 Моя библиотека'), simple_button('💬 Помощь'))
    return mark


# shit

menu_reply_markup = getMenuReply()

text_in_buttons = []

for row in menu_reply_markup['keyboard']:
    for button in row:
        text_in_buttons.append(button.text)
