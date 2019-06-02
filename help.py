from aiogram import types

from models import Review, Autor, User, ReviewsToAdd, UserQueue

start_message = '''
Привет!🖖 Я бот который сделан для таких людей как ты, людей которые любят читать 📚 Расскажи мне какие книги ты уже прочитал и твои самые любимые жанры 😉 
'''

get_name_message = 'Напиши мне его Имя и Фамилию ✍️'
notification = 'notified!'

pre_text_add_book = '''
Книга добавлена! Поделись со мной своими впечатлениями о книге 🙏
'''

pre_text_review = '''
Оценка добавлена! Поделись еще своими впечатлениями о книге 🙏
'''
pre_text_solo_review = '''
{}
Оценка {}/10 ({}) отзывов
Оцени по этому критерию от 1 до 10
'''

pre_review_criteria = '''
{} Оценка {}/10 ({}) отзывов
Оцени по этому критерию от 1 до 10
'''

add_book_start = 'Добавь книгу по Автору или Названию'

book_done = 'Книга выбрана. Что хотите сделать?'

in_contact = 'Собеседник найден! Начать обсуждение?'


def get_accept_decline():
    return inK(inB('Начать', data='accept'), inB('Отмена', data='decline'), row_width=1)


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
    m = pre_text_solo_review.format(review.text, mark, maxcount)
    return m


def get_reviews_criteria_reply_markup():
    mark = inK()
    mark.row(inB('Проголосовать', data='vote'))
    mark.row(inB('Назад', data='back_to_reviews_list'))
    return mark


def get_reviews_criteria(book):
    i = 0
    review = Review.objects(type=i, book=book).first()
    mes = f'📖{book.article}\n'
    while review:
        mark, maxcount = get_max_mark(review.mark)

        mes += f'{review.text} *{mark}/10* ({maxcount} оценок)\n'
        i += 1
        try:
            review = Review.objects(type=i, book=book).first()
        except:
            break
        # print(i,query)
    # mes += '\nВыбери критерий для оценки'
    return mes


def get_review_text(need_to_add=False):
    mes = pre_text_add_book if need_to_add else pre_text_review
    i = 0
    query = Review.objects(type=i).first()

    while query:
        mes += f'\n{query.text}'
        i += 1
        try:
            query = Review.objects(type=i).first()
        except:
            break
        # print(i,query)
    mes += '\nВыбери критерий для оценки'
    return mes


def get_reviews_text():
    mes = pre_text_review
    i = 0
    query = Review.objects(type=i).first()

    while query:
        mes += f'\n{query.text}'
        i += 1
        try:
            query = Review.objects(type=i).first()
        except:
            break
        # print(i,query)
    mes += '\nВыбери критерий для оценки'
    return mes


def get_list_of_authors(count, autors):
    msg = ''
    # print(autors)
    for autor in autors[count:count + 8]:
        # print(autor)
        msg += f'{count + 1}. {autor.name} {autor.surname} {autor.patronymic}\nВыбрать автора /autor_{autor.id}\n'
        count += 1

    return msg


def get_list_of_books(count, autor):
    msg = ''
    # print(autors)
    for book in autor.books[count:count + 8]:
        # print(autor)
        msg += f'{count + 1}. {book.article}\nВыбрать книгу /book_{book.id}\n'
        count += 1

    return msg


def simple_keyboard(*buttons, row_width=2, one_time_keyboard=True):
    mark = types.ReplyKeyboardMarkup(row_width=row_width, one_time_keyboard=one_time_keyboard, resize_keyboard=True)

    mark.add(*buttons)

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


def getAddBookReply():
    mark = simple_keyboard(one_time_keyboard=False)

    mark.row(simple_button('🎓 Автор'), simple_button('📔 Название'))
    mark.row(simple_button('📚 Моя библиотека'), simple_button('💬 Помощь'))
    return mark


def getMenuReply():
    mark = simple_keyboard(one_time_keyboard=False)

    mark.row(simple_button('🎓 Добавить книгу'), simple_button('📔 Узнать о книге'))
    mark.row(simple_button('📚 Моя библиотека'), simple_button('💬 Помощь'))
    return mark


menu_reply_markup = getMenuReply()
menu_add_book_markup = getAddBookReply()


def get_review_type_markup(book):
    reviews = Review.objects(book=book)
    mark = inK()
    for x in range(1, len(reviews) + 1):
        mark.row(inB(str(x), data=str(x)))

    mark.row(inB('✍️ Написать свой', data='new_review_text'), inB('✅ Доб. критерий', data='add_criteria_on_book'))

    mark.row(inB('🎓 Добавить книгу', data='add_book'))

    mark.row(inB('❌️ Закончить', data='start'))

    # print(mark.__dict__)
    return mark


def get_end_inline_markup():
    mark = inK()
    mark.row(inB('❌️ Закончить', data='start'))
    return mark


def get_back_inline_markup():
    mark = inK()
    mark.row(inB('❌️ Закончить', data='back'))
    return mark


def get_authors_markup(count, autorlist):
    mark = inK()
    for i, autor in enumerate(autorlist[count:count + 8]):
        mark.row(inB('{}. {} {}'.format(count + i + 1, autor.name, autor.surname), data=str(autor.id)))

    mark.row(inB('>>', data=f'page_{count + 8}'))
    mark.row(inB('X', data='start'))
    return mark


def get_books_from_collection(count, u: User):
    mark = inK()
    for i, book in enumerate(u.books[count:count + 8]):
        mark.row(inB('{}. {}'.format(count + i + 1, book.article), data=str(book.id)))
    if count + 8 < len(u.books):
        mark.row(inB('>>', data=f'page_{count + 8}'))
    mark.row(inB('X', data='start'))
    return mark


def get_books_of_autor(count, aut: Autor):
    mark = inK()
    aut.books = aut.books.order_by('article')
    aut.save()
    for i, book in enumerate(aut.books[count:count + 8]):
        mark.row(inB('{}. {}'.format(count + i + 1, book.article), data=str(book.id)))

    mark.row(inB('>>', data=f'page_{count + 8}'))
    mark.row(inB('X', data='start'))
    return mark


def get_review_from_ten_markup():
    mark = inK()
    for x in range(1, 11):
        mark.row(inB(str(x), data=str(x)))

    return mark


def get_simple_markup_with_add_book_end():
    return simple_keyboard(simple_button('🎓 Добавить книгу'), simple_button('❌️ Закончить'), one_time_keyboard=False)


def get_simple_markup_with_another_book():
    return simple_keyboard(simple_button('📔 Другая книга'), simple_button('⬅️ Назад'), one_time_keyboard=False)


def get_simple_markup_on_criteria():
    mark = simple_keyboard(one_time_keyboard=False)

    mark.row(simple_button('✍️ Написать отзыв'), simple_button('✅ Доб. критерий'))

    mark.row(simple_button('🎓 Добавить книгу'), simple_button('❌️ Закончить'))

    return mark


def get_books_by_name(count, books_in_search):
    mark = inK()
    for article, index in books_in_search[count:count + 8]:
        mark.row(inB(article, data=str(index)))
    if count + 8 < len(books_in_search):
        mark.row(inB('>>', data=f'page_{count + 8}'))

    mark.row(inB('❌️ Закончить', data='start'))
    return mark


def get_book_reviews(count, book):
    mark = inK()
    if count + 1 < len(book.litres_reviews):
        mark.row(inB('>>', data=f'watch_reviews_from_web_{count + 1}'))

    mark.row(inB('❌️ Закончить', data='back_to_reviews_list'))
    return mark


def get_book_reviews_from_users(count, reviews):
    mark = inK()
    if count + 1 < len(reviews):
        mark.row(inB('>>', data=f'reviews_of_users_{count + 1}'))

    mark.row(inB('❌️ Закончить', data='back_to_reviews_list'))
    return mark


def get_simple_markup_back_end():
    mark = simple_keyboard(one_time_keyboard=False)

    mark.row(simple_button('⬅️ Назад'), simple_button('❌️ Закончить'))

    return mark


def get_simple_markup_end():
    mark = simple_keyboard(one_time_keyboard=False)

    mark.row(simple_button('❌️ Закончить'))

    return mark


def get_inline_markup_with_actions(delete=False):
    mark = inK()

    mark.row(inB('📣 Отзывы', data=f'watch_reviews_from'))
    mark.row(inB('💬 Обсудить', data='go_into_conversation'))
    if delete:
        mark.row(inB('🗑 Удалить', data='delete'))
    else:
        mark.row(inB('⏹ Закончить', data='start'))

    return mark


def get_inline_list(count, list_of_objects: [ReviewsToAdd]):
    mark = inK()
    for obj in list_of_objects[count:count + 8]:
        # print(obj.text)
        mark.row(inB('{} - {}'.format(obj.count, obj.text), data=str(obj.id)))

    if count + 8 < len(list_of_objects):
        mark.row(inB('>>', data=f'page_{count + 8}'))
    mark.row(inB('❌️ Закончить', data='start'))
    return mark


def get_inline_markup_reviews():
    mark = inK()
    mark.row(inB('💻 Отзывы с bokmate.ru, litres.ru и т.д.', data=f'watch_reviews_from_web_0'))
    mark.row(inB('💬 Отзывы наших пользователей', data='reviews_of_users_0'))
    mark.row(inB('📝 Отзывы по критериям', data='reviews_by_criterias'))
    mark.row(inB('Назад', data='back'))

    return mark


def delete_from_chat(user_id):
    for obj in UserQueue.objects(u_id=user_id):
        obj.delete()


simple_markup_end = get_simple_markup_end()
simple_markup_back_end = get_simple_markup_back_end()
inline_markup_with_actions = get_inline_markup_with_actions()
inline_markup_reviews = get_inline_markup_reviews()
simple_markup_on_criteria = get_simple_markup_on_criteria()
simple_markup_with_add_book_end = get_simple_markup_with_add_book_end()
simple_markup_with_another_book = get_simple_markup_with_another_book()
review_from_ten_markup = get_review_from_ten_markup()
end_inline_markup = get_end_inline_markup()
back_inline_markup = get_back_inline_markup()
accept_decline = get_accept_decline()
text_in_main = []

for row in menu_reply_markup['keyboard']:
    for button in row:
        text_in_main.append(button.text)

text_in_add_book = []

for row in menu_add_book_markup['keyboard']:
    for button in row:
        text_in_add_book.append(button.text)
