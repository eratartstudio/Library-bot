import asyncio
import datetime
from unittest.mock import MagicMock

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from conf import token
from help import *
from models import User, Autor, Book, Review

loop = asyncio.get_event_loop()
bot = Bot(token=token, loop=loop)
storage = MemoryStorage()
dp = Dispatcher(bot, loop=loop, storage=storage)
s = bot.send_message

chat = -1001410410976

# file_ids = {'files.jpg': None, 'answers.jpg': None, 'statistics.jpg': None}

# bot.get_updates()

'''                                     #to work with channels#
@dp.channel_post_handler()
async def post(msg: types.Message):
    print(msg)


@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def cont(msg: types.Message):
    print(msg)
'''


class AuthorState(StatesGroup):
    start = State()
    ask = State()
    name_or_surname = State()
    get_author_command = State()
    get_book_command = State()
    get_review_state = State()
    get_out_of_ten_state = State()

    watching_collection = State()
    new_action = State()


def pseudo_message(user_id, text=None, mes_id=None, data=None):
    m = MagicMock()
    m.from_user.id = user_id
    if mes_id:
        m.message.message_id = mes_id
    if data:
        m.data = data
    if text:
        m.text = text

    return m


@dp.callback_query_handler(lambda c: c.data == 'start', state=AuthorState.all_states)
async def start_callback(c: types.CallbackQuery):
    await bot.answer_callback_query(c.id)
    await bot.delete_message(c.from_user.id, c.message.message_id)
    await start_command_func(c)


@dp.message_handler(commands=['start', 's'], state='*')
async def start_command_func(msg: [types.Message, types.CallbackQuery]):
    u_id = msg.from_user.id
    get_or_add_user(msg)
    # print("start from user ", u.username)
    # print(msg.get_args())
    await AuthorState.start.set()
    await s(u_id, start_message, reply_markup=menu_reply_markup)


async def send_books_in_collection(u: User):
    if len(u.books) == 0:
        await s(u.user_id, 'Ваша полка пуста!')
    else:
        await s(u.user_id, 'На вашей полке стоят книги:', reply_markup=get_books_from_collection(0, u))
        await AuthorState.watching_collection.set()


@dp.message_handler(lambda m: m.text in text_in_buttons, state=AuthorState.start)
async def handle_buttons(msg: types.Message):
    u_id = msg.from_user.id
    u = get_user(u_id)
    text = msg.text
    if text == text_in_buttons[0]:
        await AuthorState.name_or_surname.set()
        await s(u_id, get_name_message)
        u.update(step='get_author_name')

    elif text == text_in_buttons[1]:
        pass

    elif text == text_in_buttons[2]:
        await send_books_in_collection(u)

    elif text == text_in_buttons[3]:
        pass
    else:
        pass


@dp.message_handler(commands=['addReview'])
async def add_review():
    for book in Book.objects():
        book.create_reviews()
        print(book.reviews)


@dp.message_handler(commands=['addGogols'])
async def add_gogols():
    if len(Autor.objects(surname='Гоголь')) == 0:
        Autor(name='Николай', surname='Гоголь', patronymic='Васильевич').save()
        Autor(name='Василий', surname='Гоголь', patronymic='Васильевич').save()


@dp.message_handler(commands=['addBooks'])
async def add_books():
    a = Autor.objects(name='Николай', surname='Гоголь', patronymic='Васильевич')[0]
    book = Book(autor=a, article='my first book(c)',
                url_litres='https://www.litres.ru/german-gesse/siddhartha-24506086/')
    books = a.books
    book.save()
    a.update(books=books.append(book))
    a.save()
    # Autor(name='Василий', surname='Гоголь', patronymic='Васильевич').save()


def get_autor_list(text):
    args = text.split(' ')
    autorlist = []
    for word in args:
        autor_name = list(Autor.objects(name=word))
        autor_surname = list(Autor.objects(surname=word))
        autorlist = autorlist + autor_name + autor_surname
    return autorlist


@dp.message_handler(state=AuthorState.name_or_surname)
async def get_author_by_name(msg: types.Message, state: FSMContext):
    u_id = msg.from_user.id
    autorlist = get_autor_list(msg.text)
    mark = inK()

    if len(autorlist) == 0:
        await s(u_id, 'Подобного автора не найдено')
        return

    async with state.proxy() as data:
        data['autorlist'] = autorlist

    txt = get_list_of_authors(0, autorlist)
    await AuthorState.next()

    await s(u_id, 'Авторы:', reply_markup=get_authors_markup(0, autorlist))


@dp.callback_query_handler(lambda c: 'page_' in c.data, state=AuthorState.get_author_command)
async def get_author_by_name(c: types.CallbackQuery, state: FSMContext):
    count = int(c.data.replace('page_', ''))
    async with state.proxy() as data:

        autorlist = data['autorlist']

        if count > len(autorlist):
            await bot.answer_callback_query(c.id, 'Это последняя страница', show_alert=True)
            return
        else:
            await bot.answer_callback_query(c.id, 'Переход к следующей странице')

        await bot.edit_message_reply_markup(c.from_user.id, c.message.message_id,
                                            reply_markup=get_authors_markup(count, autorlist))


@dp.callback_query_handler(state=AuthorState.get_author_command)
async def get_author_by_name(c: types.CallbackQuery, state: FSMContext):
    autor_id = c.data
    aut = Autor.objects(id=autor_id)[0]

    async with state.proxy() as data:
        data['autor'] = aut

    txt = get_list_of_books(0, aut)
    await bot.edit_message_text('Выберите книгу', c.from_user.id, c.message.message_id,
                                reply_markup=get_books_of_autor(0, aut))
    await AuthorState.get_book_command.set()


@dp.callback_query_handler(lambda c: 'page_' in c.data, state=AuthorState.watching_collection)
async def get_author_by_name(c: types.CallbackQuery, state: FSMContext):
    count = int(c.data.replace('page_', ''))
    u = get_user(c.from_user.id)

    if count > len(u.books):
        await bot.answer_callback_query(c.id, 'Это последняя страница', show_alert=True)
        return
    else:
        await bot.answer_callback_query(c.id, 'Переход к следующей странице')

    await bot.edit_message_reply_markup(c.from_user.id, c.message.message_id,
                                        reply_markup=get_books_from_collection(count, u))


@dp.callback_query_handler(lambda c: 'page_' in c.data, state=AuthorState.get_book_command)
async def get_author_by_name(c: types.CallbackQuery, state: FSMContext):
    count = int(c.data.replace('page_', ''))
    async with state.proxy() as data:

        aut = data['autor']

        if count > len(aut.books):
            await bot.answer_callback_query(c.id, 'Это последняя страница', show_alert=True)
            return
        else:
            await bot.answer_callback_query(c.id, 'Переход к следующей странице')

        await bot.edit_message_reply_markup(c.from_user.id, c.message.message_id,
                                            reply_markup=get_books_of_autor(count, aut))


@dp.callback_query_handler(state=AuthorState.get_book_command)
async def get_book_command(c: types.CallbackQuery, state: FSMContext):
    book_id = c.data
    book = get_book(book_id)
    async with state.proxy() as data:
        data['book'] = book
        u = get_user(c.from_user.id)
        if book not in u.books:
            u.books.append(book)
            u.update(books=u.books)
        else:
            await s(c.from_user.id, 'Книга уже на вашей полке, поэтому она не будет добавлена!')

    txt = get_reviews_text()
    await AuthorState.get_review_state.set()
    await bot.edit_message_text(txt, c.from_user.id, c.message.message_id, reply_markup=get_review_type_markup(book))


@dp.callback_query_handler(state=AuthorState.get_review_state)
async def get_author_by_name(c: types.CallbackQuery, state: FSMContext):
    try:
        await bot.answer_callback_query(c.id, 'Критерий выбран')
    except:
        pass
    review_type = int(c.data)
    async with state.proxy() as data:
        review = Review.objects(book=data['book'], type=review_type - 1)[0]
        data['review'] = review

        await bot.edit_message_text(get_solo_review_text(review), c.from_user.id, c.message.message_id,
                                    reply_markup=review_from_ten_markup)

    await AuthorState.next()


@dp.message_handler(state=AuthorState.get_review_state)
async def get_author_by_name(msg: types.Message, state: FSMContext):
    if msg.text.isnumeric():
        u_id = msg.from_user.id
        async with state.proxy() as data:
            review = Review.objects(book=data['book'], type=int(msg.text) - 1)[0]
            data['review'] = review

            await s(u_id, get_solo_review_text(review), reply_markup=review_from_ten_markup)

        await AuthorState.get_out_of_ten_state.set()
        print('next')
    else:
        await s(msg.from_user.id, 'Введите число')


@dp.callback_query_handler(state=AuthorState.get_out_of_ten_state)
async def get_author_by_name(c: types.CallbackQuery, state: FSMContext):
    try:
        await bot.answer_callback_query(c.id, 'Оценка выбрана')
    except:
        pass
    u_id = c.from_user.id
    mark = int(c.data)
    async with state.proxy() as data:
        review = data['review']
        review.mark[mark] += 1
        review.update(mark=review.mark)
        data['review'] = review

        await bot.edit_message_text('Оценка книги завершена', c.from_user.id, c.message.message_id)

    await AuthorState.start.set()


def get_book(u_id):
    return Book.objects(id=u_id)[0]


def get_user(u_id):
    return User.objects(user_id=u_id)[0]


@dp.message_handler(state=None)
async def handle_all_messages(msg: types.Message):
    u_id = msg.from_user.id
    get_or_add_user(msg)
    await s(u_id, f'Напишите /start для начала работы')

    await AuthorState.start.set()


def get_or_add_user(msg):
    u_id = msg.from_user.id
    u = User.objects(user_id=u_id)
    if len(u) == 0:
        u = User(user_id=u_id, username=msg.from_user.username or str(msg.from_user.id))
        u.save()

    else:
        u = u[0]
        # if user changed or deleted his username 
        u.update(username=msg.from_user.username or str(msg.from_user.id))
    return u


async def check_users_notifications():
    # notification function, can be useful in future

    users = User.objects(need_to_notify=True, notified=False)
    secs_in_day = 3600 * 24
    for user in users:
        # print("for user {} delta is {}".format(user.username,(datetime.datetime.now() - user.time_started).seconds))

        if (datetime.datetime.now() - user.time_started).seconds >= secs_in_day:
            # u_id = user.user_id
            user.update(notified=True)


def get_secs_to_hour():
    # to check notifications every hour

    needtime = datetime.datetime.now() + datetime.timedelta(hours=1)
    needtime = datetime.datetime.strptime(needtime.strftime('%Y %m %d %H'), '%Y %m %d %H')  # %M - mins
    now = datetime.datetime.now()
    delta = needtime - now
    print('До запуска осталось ', delta.seconds)
    return delta.seconds + 10


def repeat(coro, event_loop):
    asyncio.ensure_future(coro(), loop=event_loop)
    loop.call_later(3600, repeat, coro, event_loop)


if __name__ == '__main__':
    # loop.call_later(get_secs_to_hour(), repeat, check_users_notifications, loop)

    executor.start_polling(dp, loop=loop)

    pass
