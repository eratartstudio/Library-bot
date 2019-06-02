import asyncio
import datetime

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from conf import token
from help import *
from models import User, Autor, Book, Review, ReviewsToAdd, UserQueue

loop = asyncio.get_event_loop()
bot = Bot(token=token, loop=loop)
storage = MemoryStorage()
dp = Dispatcher(bot, loop=loop, storage=storage)
s = bot.send_message

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
    book_root = State()
    ask = State()
    name_or_surname = State()
    get_author_command = State()
    get_book_command = State()
    get_review_state = State()  # menu for actions while add
    add_new_criteria = State()
    get_out_of_ten_state = State()

    search_book = State()
    get_book_name = State()

    add_review_from_user = State()
    action_menu = State()

    see_reviews = State()
    see_reviews_from_web = State()

    in_conversation = State()

    adminstate = State()


@dp.message_handler(commands=['top_10_criterias'], state='*')
async def top_10_addition(msg: types.Message, state: FSMContext):
    # u = get_user(msg.from_user.id)
    objs = list(reversed(sorted(ReviewsToAdd.objects(), key=lambda obj: obj.count)))
    async with state.proxy() as data:
        data['objs'] = objs
    print(objs)
    await s(msg.from_user.id, 'Топ популярных отзывов\n', reply_markup=get_inline_list(0, objs))
    await AuthorState.adminstate.set()


@dp.callback_query_handler(lambda c: c.data == 'start', state=AuthorState.all_states)
async def start_callback(c: types.CallbackQuery):
    await bot.answer_callback_query(c.id)
    await bot.delete_message(c.from_user.id, c.message.message_id)
    await start_command_func(c)


@dp.message_handler(commands=['start', 's'], state='*')
async def start_command_func(msg: [types.Message, types.CallbackQuery]):
    u_id = msg.from_user.id
    get_or_add_user(msg)
    # delete_from_chat(u_id)
    await AuthorState.start.set()
    await s(u_id, start_message, reply_markup=menu_reply_markup)


async def send_books_in_collection(u: User, count=0):
    if len(u.books) == 0:
        await s(u.user_id, 'Ваша полка пуста!')
    else:
        await s(u.user_id, 'Отсылаем меню...', reply_markup=simple_markup_with_add_book_end)
        await s(u.user_id, 'На вашей полке стоят книги:', reply_markup=get_books_from_collection(count, u))


@dp.message_handler(lambda m: m.text in ['Назад', '❌️ Закончить', ], state=AuthorState.all_states)
async def back(m: types.Message, state: FSMContext):
    # if user is in conversation
    if await state.get_state() == AuthorState.in_conversation.state:
        # remove user from conversation
        delete_from_chat(m.from_user.id)
    await m.delete()
    await start_command_func(m)


@dp.message_handler(lambda m: m.text in text_in_main,
                    state=[AuthorState.start, AuthorState.get_book_command, AuthorState.book_root])
async def main_menu(msg: types.Message, state: FSMContext):
    u_id = msg.from_user.id
    text = msg.text
    u = get_user(u_id)

    async with state.proxy() as data:

        data['already_in_search'] = False
        data['user_books'] = False
        data['from_library'] = False
        if text == text_in_main[0]:
            await AuthorState.book_root.set()
            data['need_to_add'] = True
            data['actions_menu'] = False
            await s(u_id, add_book_start, reply_markup=menu_add_book_markup)

        elif text == text_in_main[1]:
            data['need_to_add'] = False
            data['actions_menu'] = True
            await AuthorState.book_root.set()
            await s(u_id, add_book_start, reply_markup=menu_add_book_markup)

        elif text == text_in_main[2]:
            data['need_to_add'] = False
            data['actions_menu'] = True
            data['user_books'] = True
            data['from_library'] = True
            data['count in search'] = 0
            await AuthorState.get_book_command.set()
            await send_books_in_collection(u)

        elif text == text_in_main[3]:
            pass
        else:
            pass


@dp.message_handler(lambda m: m.text in text_in_add_book, state=AuthorState.book_root)
async def book_root_menu(msg: types.Message, state: FSMContext):
    u_id = msg.from_user.id
    u = get_user(u_id)
    text = msg.text
    async with state.proxy() as data:
        data['already_in_search'] = False
        data['user_books'] = False

        if text == text_in_add_book[0]:
            await AuthorState.name_or_surname.set()
            await s(u_id, get_name_message, reply_markup=simple_markup_back_end)

        elif text == text_in_add_book[1]:
            await AuthorState.get_book_name.set()
            await s(u_id, 'Напишите название книги', reply_markup=simple_markup_back_end)

        elif text == text_in_add_book[2]:
            data['need_to_add'] = False
            data['actions_menu'] = True
            data['user_books'] = True
            await AuthorState.get_book_command.set()
            await send_books_in_collection(u)

        elif text == text_in_add_book[3]:
            pass


@dp.message_handler(state=AuthorState.get_book_name)
async def get_book_name(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        u_id = msg.from_user.id

        if not data['already_in_search']:
            if msg.text == '⬅️ Назад':
                # go to previous state
                if data['actions_menu']:
                    msg.text = text_in_main[1]
                else:
                    msg.text = text_in_main[0]
                await main_menu(msg, state)
                return

            book_name = msg.text
            # mas is result of searching title of books, represented as tuples of (article,book_id)
            mas = ()
            for book in Book.objects:
                if book_name.lower() in book.article.lower():
                    mas += ((book.article, book.id),)

            if mas:
                # alphabetic order
                mas = sorted(mas, key=lambda b: b[0])
                await AuthorState.get_book_command.set()
                mark = get_books_by_name(0, mas)
                data['count in search'] = 0
                # save them to use in next steps / pagination
                data['books_in_search'] = mas

                data['book_name'] = book_name
                data['already_in_search'] = True
                await s(u_id, 'Результаты поиска:', reply_markup=mark)
            else:

                await s(u_id, 'Ничего не найдено, попробуйте снова')

        else:
            await s(u_id, 'Сначала закончите предыдущий поиск')
            await bot.delete_message(msg.from_user.id, msg.message_id)


# @dp.message_handler(commands=['addReview'])
# async def add_review():
#     for book in Book.objects():
#         book.create_reviews()
#         print(book.reviews)


# search authors by name and surname
def get_autor_list(text):
    args = list(text.split(' '))
    while args.count('') != 0:
        args.remove('')

    autorlist = []
    if len(args) > 1:
        name = args[0][0].upper() + args[0][1:]
        surname = args[1][0].upper() + args[1][1:]
        print(name, surname)
        autorlist = list(Autor.objects(name=name, surname=surname)) + list(Autor.objects(name=surname, surname=name))
        print(autorlist)
    if not autorlist:
        for word in args:
            word = word[0].upper() + word[1:]
            autor_name = list(Autor.objects(name=word))
            autor_surname = list(Autor.objects(surname=word))
            autorlist = autorlist + autor_name + autor_surname
    # sorted in alphabetic order
    return sorted(list(set(autorlist)), key=lambda author: author.surname)


@dp.message_handler(state=AuthorState.name_or_surname)
async def get_author_by_name_mes(msg: types.Message, state: FSMContext):
    u_id = msg.from_user.id
    async with state.proxy() as data:
        # go to previous state
        if msg.text == '⬅️ Назад':
            if msg.text == '⬅️ Назад':
                if data['actions_menu']:
                    msg.text = text_in_main[1]
                else:
                    msg.text = text_in_main[0]
                await main_menu(msg, state)
                return

        autorlist = get_autor_list(msg.text)

        if len(autorlist) == 0:
            await s(u_id, 'Подобного автора не найдено')
            return

        data['autorlist'] = autorlist
        data['count in search'] = 0

        await AuthorState.get_author_command.set()
        await s(u_id, 'Авторы:', reply_markup=get_authors_markup(0, autorlist))


@dp.callback_query_handler(lambda c: 'page_' in c.data, state=AuthorState.get_author_command)
async def get_author_by_name_callback(c: types.CallbackQuery, state: FSMContext):
    count = int(c.data.replace('page_', ''))
    async with state.proxy() as data:
        data['count in search'] = count
        autorlist = data['autorlist']

        if count > len(autorlist):
            await bot.answer_callback_query(c.id, 'Это последняя страница', show_alert=True)
            return

        else:
            await bot.answer_callback_query(c.id, 'Переход к следующей странице')

        await bot.edit_message_reply_markup(c.from_user.id, c.message.message_id,
                                            reply_markup=get_authors_markup(count, autorlist))


@dp.callback_query_handler(state=AuthorState.get_author_command)
async def get_author_command(c: types.CallbackQuery, state: FSMContext):
    autor_id = c.data
    aut = Autor.objects(id=autor_id).first()
    async with state.proxy() as data:
        data['autor'] = aut
        data['count in search'] = 0

    await AuthorState.get_book_command.set()
    await bot.edit_message_text('Выберите книгу', c.from_user.id, c.message.message_id,
                                reply_markup=get_books_of_autor(0, aut))


@dp.message_handler(state=AuthorState.get_author_command)
async def back_handler(msg: types.Message, state: FSMContext):
    if msg.text == '⬅️ Назад':
        msg.text = text_in_add_book[0]
        await book_root_menu(msg, state)


@dp.message_handler(state=AuthorState.get_book_command)
async def back_handler(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if msg.text == '⬅️ Назад':
            if not data['already_in_search']:
                u_id = msg.from_user.id
                autorlist = data['autorlist']
                count = data['count in search']

                await AuthorState.get_author_command.set()
                await s(u_id, 'Авторы:', reply_markup=get_authors_markup(count, autorlist))
            else:
                msg.text = text_in_add_book[1]
                await book_root_menu(msg, state)
                print('eaaaaa')


@dp.callback_query_handler(lambda c: 'page_' in c.data, state=AuthorState.get_book_command)
async def get_book_command(c: types.CallbackQuery, state: FSMContext):
    print('get_book_command')
    count = int(c.data.replace('page_', ''))

    async with state.proxy() as data:
        data['count in search'] = count

        if data['user_books']:
            await bot.edit_message_reply_markup(c.from_user.id, c.message.message_id,
                                                reply_markup=get_books_from_collection(count, get_user(c.from_user.id)))

        elif not data['already_in_search']:
            aut = data['autor']
            await bot.answer_callback_query(c.id, 'Переход к следующей странице')
            await bot.edit_message_reply_markup(c.from_user.id, c.message.message_id,
                                                reply_markup=get_books_of_autor(count, aut))
        else:
            await bot.answer_callback_query(c.id, 'Переход к следующей странице')

            mark = get_books_by_name(count, data['books_in_search'])
            data['count in search'] = count
            await bot.edit_message_reply_markup(c.from_user.id, c.message.message_id, reply_markup=mark)


@dp.callback_query_handler(state=AuthorState.get_book_command)
async def get_book_command(c: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(c.id)

    book_id = c.data
    book = get_book(book_id)
    u = get_user(c.from_user.id)

    async with state.proxy() as data:
        data['book'] = book
        data['autor'] = book.autor
        need = data['need_to_add']
        actions = data['actions_menu']
        from_library = data['from_library']
        if need:
            data['books_in_search'] = []

    await new_book_or_review(u, c, book, need_to_add=need, actions=actions, from_library=from_library)


# big function that sends different types of messages when the book was chosen
async def new_book_or_review(u: User, c: [types.Message, types.CallbackQuery], book: Book, need_to_add=True,
                             actions=False, from_library=False, not_first_time=False):
    if type(c) == types.CallbackQuery:
        try:
            await bot.delete_message(c.from_user.id, c.message.message_id)
        except:
            pass

    if actions:
        await AuthorState.action_menu.set()
        if from_library:
            await s(c.from_user.id, 'Получаем данные...', reply_markup=simple_markup_back_end)
        else:
            await s(c.from_user.id, 'Получаем данные...', reply_markup=simple_markup_with_another_book)
        print(book.id in [x.id for x in u.books])
        await s(c.from_user.id, book_done,
                reply_markup=get_inline_markup_with_actions(book.id in [x.id for x in u.books]))

    else:

        if need_to_add and [x.id for x in u.books].count(book.id) == 0:
            u.books.append(book)
            u.save()
        await AuthorState.get_review_state.set()

        await s(c.from_user.id,
                get_review_text(need_to_add=need_to_add) if need_to_add or not_first_time else get_reviews_criteria(
                    book) + '\nВыбери критерий для оценки',
                reply_markup=simple_markup_on_criteria, parse_mode='Markdown')

        if need_to_add and [x.id for x in u.books].count(book.id) == 0:
            u.books.append(book)
            u.save()


@dp.message_handler(lambda m: m.text in ['📔 Другая книга', '⬅️ Назад'],
                    state=[AuthorState.action_menu, AuthorState.in_conversation])
async def msg_action(msg: types.Message, state: FSMContext):
    u_id = msg.from_user.id
    if msg.text == '⬅️ Назад':
        async with state.proxy() as data:
            if await state.get_state() == AuthorState.in_conversation.state:  # if user waited
                # remove user from query
                delete_from_chat(u_id)

            if data['already_in_search']:
                count = data['count in search']

                mark = get_books_by_name(count, data['books_in_search'])
                await msg.delete()
                await bot.delete_message(msg.from_user.id, msg.message_id - 2)
                await bot.delete_message(msg.from_user.id, msg.message_id - 1)

                await AuthorState.get_book_command.set()
                await s(msg.from_user.id, 'Получаем данные...', reply_markup=simple_markup_back_end)
                await s(msg.from_user.id, 'Результаты поиска:', reply_markup=mark)
            else:
                count = data['count in search']
                await send_books_in_collection(get_user(msg.from_user.id), count)
                await AuthorState.get_book_command.set()
                print('Библиотеку не обработал')

    elif msg.text == '📔 Другая книга':
        await AuthorState.get_book_name.set()
        msg.text = '📔 Узнать о книге'
        await main_menu(msg, state)


@dp.callback_query_handler(state=AuthorState.in_conversation)
async def in_conversation(c: types.CallbackQuery, state: FSMContext):
    u_id = c.from_user.id
    async with state.proxy() as data:

        if c.data == 'accept':
            await c.message.edit_text('Вы присоединились к обсуждению!')
            u = UserQueue.objects(book=data['book'], u_id=u_id).first()
            u.in_chat = True
            u.save()
            await AuthorState.in_conversation.set()
        elif c.data == 'decline':
            await c.answer()
            await c.message.edit_text('Возвращаемся назад!')
            delete_from_chat(u_id)
            await AuthorState.action_menu.set()
            await new_book_or_review(get_user(c.from_user.id), c, data['book'], need_to_add=False,
                                     from_library=data['from_library'], actions=True)
        elif c.data == 'back':
            await c.answer('Возвращаемся назад!')

            await new_book_or_review(get_user(c.from_user.id), c, data['book'], need_to_add=False,
                                     from_library=data['from_library'], actions=True)


@dp.message_handler(state=AuthorState.in_conversation)
async def in_conversation(msg: types.Message, state: FSMContext):
    msg.text = f'@{msg.from_user.username}\n' + msg.text
    async with state.proxy() as data:
        chat_users = UserQueue.objects(book=data['book'], in_chat=True)
        for user in chat_users:
            if user.u_id != msg.from_user.id:
                await s(user.u_id, msg.text, parse_mode='Markdown', reply_markup=simple_markup_back_end)


@dp.callback_query_handler(state=AuthorState.action_menu)
async def action_menu(c: types.CallbackQuery, state: FSMContext):
    u_id = c.from_user.id
    msg_id = c.message.message_id
    try:
        await bot.answer_callback_query(c.id)
    except:
        pass

    if c.data == 'go_into_conversation':
        await bot.delete_message(u_id, msg_id)

        async with state.proxy() as data:
            user_conts = UserQueue.objects(book=data['book'])
            # if we have user that waits, then connect them, else add new user to queue
            await AuthorState.in_conversation.set()

            if not list(user_conts):
                # print(state.chat,state.user,)
                await s(u_id, 'Идет поиск собеседника...', reply_markup=back_inline_markup, )

            else:
                mes = await s(u_id, in_contact, reply_markup=accept_decline)
                data['last_message'] = mes.message_id
                user_conts = UserQueue.objects(book=data['book'], in_chat=False)
                await AuthorState.in_conversation.set()

                if len(user_conts) == 1:
                    user_cont = user_conts.first()
                    user_cont_state = dp.current_state(user=user_cont.u_id, chat=user_cont.u_id)
                    await user_cont_state.set_state(AuthorState.in_conversation.state)
                    data_two = await user_cont_state.get_data()
                    mes = await s(user_cont.u_id, in_contact, reply_markup=accept_decline)
                    data_two['last_message'] = mes.message_id
                    await user_cont_state.set_data(data_two)

                else:
                    for user_cont in user_conts:
                        # remove all "old" users from query
                        if (datetime.datetime.now() - datetime.datetime(user_cont.date)).seconds >= 300:
                            user_cont_state = dp.current_state(user=user_cont.u_id, chat=user_cont.u_id)
                            await user_cont_state.set_state(AuthorState.action_menu.state)
                            data_two = await user_cont_state.get_data()
                            await bot.edit_message_text('У нас много отзывов, выберите', user_cont.u_id,
                                                        data_two['last_message'],
                                                        reply_markup=inline_markup_reviews)
            # after check after user to query
            queue_user = UserQueue(book=data['book'], u_id=u_id)
            queue_user.save()

    elif c.data == 'watch_reviews_from':
        await bot.edit_message_text('У нас много отзывов, выберите', u_id, msg_id, reply_markup=inline_markup_reviews)

    elif 'watch_reviews_from_web_' in c.data:
        async with state.proxy() as data:
            book = Book.objects(id=data['book'].id).first()
            data['book'] = book
            # captcha
            try:
                if not list(book.litres_reviews):
                    temp = await s(u_id, 'Подгружаем отзывы, пожалуйста подождите :)')
                    print(book.autor.name, book.article)
                    book.get_review_list_litres()
                    book = Book.objects(id=data['book'].id).first()
                    data['book'] = book
                    await temp.delete()

                next = int(c.data.replace('watch_reviews_from_web_', ''))
                if book.litres_reviews:
                    await bot.edit_message_text(book.litres_reviews[next], c.from_user.id, c.message.message_id,
                                                reply_markup=get_book_reviews(next, book))
                else:
                    await bot.edit_message_text('Нет отзывов с литреса :(', c.from_user.id, c.message.message_id,
                                                reply_markup=back_inline_markup)

            except Exception as e:
                # print(e)
                await bot.edit_message_text(str(e), c.from_user.id, c.message.message_id,
                                            reply_markup=end_inline_markup)

    elif 'reviews_of_users_' in c.data:
        next = int(c.data.replace('reviews_of_users_', ''))

        async with state.proxy() as data:
            book = Book.objects(id=data['book'].id).first()
            data['book'] = book
            reviews = book.reviews
            if len(reviews) == 0:
                await bot.edit_message_text('Отзывов пока нет', u_id, c.message.message_id,
                                            reply_markup=get_book_reviews_from_users(0, []))
            else:
                await bot.edit_message_text(reviews[next].text, u_id, c.message.message_id,
                                            reply_markup=get_book_reviews_from_users(next, reviews))

    elif c.data == 'reviews_by_criterias':
        async with state.proxy() as data:
            await bot.edit_message_text(get_reviews_criteria(data['book']), u_id, msg_id,
                                        reply_markup=get_reviews_criteria_reply_markup(), parse_mode='Markdown')

    elif c.data == 'vote':
        async with state.proxy() as data:
            await new_book_or_review(get_user(c.from_user.id), c, data['book'], need_to_add=False, actions=False)

    elif c.data == 'back_to_reviews_list':
        c.data = 'watch_reviews_from'
        await action_menu(c, state)

    elif c.data == 'back':
        async with state.proxy() as data:
            await new_book_or_review(get_user(c.from_user.id), c, data['book'], need_to_add=False,
                                     from_library=data['from_library'], actions=True)

    elif c.data == 'delete':
        async with state.proxy() as data:
            book = Book.objects(id=data['book'].id).first()
            u = get_user(u_id)
            u.books.remove(book)
            u.save()
            await new_book_or_review(u, c, book, need_to_add=False, actions=True, from_library=data['from_library'])
            data['book'] = book


@dp.message_handler(state=AuthorState.add_new_criteria)
async def add_new_criteria(msg: types.Message, state: FSMContext):
    if msg.text == '⬅️ Назад':
        # back to previous message
        async with state.proxy() as data:
            await new_book_or_review(get_user(msg.from_user.id), msg, data['book'], need_to_add=False,
                                     not_first_time=not data['user_books'])
            return

    await s(msg.from_user.id, 'Спасибо!')
    obj = ReviewsToAdd.objects(text=msg.text)
    if len(obj) == 0:
        obj = ReviewsToAdd(text=msg.text)
    else:
        obj = obj[0]
        obj.count += 1
    obj.save()


@dp.callback_query_handler(state=AuthorState.adminstate)
async def adminstate_callback(c: types.CallbackQuery, state: FSMContext):
    await c.answer()
    if 'page_' in c.data:
        counter = int(c.data.replace('page_', ''))
        async with state.proxy() as data:
            await bot.edit_message_reply_markup(c.from_user.id, c.message.message_id,
                                                reply_markup=get_inline_list(counter, data['objs']))
    else:
        r_id = c.data
        obj = ReviewsToAdd.objects(id=r_id).first()
        await s(c.from_user.id, 'in progress.\n' + obj.text)


@dp.message_handler(state=AuthorState.get_review_state)
async def get_review_state(msg: types.Message, state: FSMContext):
    if msg.text == '✅ Доб. критерий':
        await s(msg.from_user.id, 'Отправьте критерий оценки который бы вы хотели видеть',
                reply_markup=simple_markup_back_end)
        await AuthorState.add_new_criteria.set()

    elif msg.text == '✍️ Написать отзыв':
        await s(msg.from_user.id,
                'Отправьте сообщение и мы сохраним его как отзыв!\nНажмите "Закончить" чтобы прервать это действие',
                reply_markup=simple_markup_back_end)
        await AuthorState.add_review_from_user.set()

    elif msg.text == '🎓 Добавить книгу':
        await main_menu(msg, state)

    elif msg.text.isnumeric():
        async with state.proxy() as data:
            review_type = int(msg.text)
            review = Review.objects(book=data['book'], type=review_type - 1).first()
            print(review)
            if review_type <= 0 or not list(review):
                await s(msg.from_user.id, 'Выберите корректный критерий')
                return

            if str(msg.from_user.id) in review.voted:
                await s(msg.from_user.id,
                        f'Вы уже оценили книгу по этому критерию. Ваша оценка: *{review.voted[str(msg.from_user.id)]}*',
                        parse_mode='Markdown')
                return

            data['review'] = review

            await s(msg.from_user.id, get_solo_review_text(review),
                    reply_markup=simple_markup_back_end)

            await AuthorState.get_out_of_ten_state.set()

        # await bot.answer_callback_query(c.id, callback_text)


@dp.message_handler(state=AuthorState.add_review_from_user)
async def add_review_from_user(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if msg.text == '⬅️ Назад':
            # back to previous state
            await new_book_or_review(get_user(msg.from_user.id), msg, data['book'], need_to_add=False,
                                     not_first_time=not data['user_books'])
            return

        text = '{}\n{}'.format(msg.from_user.username or 'Аноним', msg.text)
        book = data['book']
        new = Review(type=0, text=text, book=data['book'])
        new.save()
        book.reviews.append(new)
        book.save()
        data['book'] = book
        await s(msg.from_user.id, 'Ваш отзыв принят!')


@dp.message_handler(lambda m: m.text.isnumeric(), state=AuthorState.get_out_of_ten_state)
async def get_author_by_name(msg: types.Message, state: FSMContext):
    u_id = msg.from_user.id
    mark = int(msg.text)
    async with state.proxy() as data:
        if msg.text == '⬅️ Назад':
            # back to previous state
            await new_book_or_review(get_user(msg.from_user.id), msg, data['book'], False)
            return

        review = data['review']
        review.mark[mark] += 1
        review.voted[str(msg.from_user.id)] = mark
        review.save()
        data['review'] = review

        await new_book_or_review(u=get_user(u_id), c=msg, book=data['book'], need_to_add=False, not_first_time=True)


def get_book(u_id):
    return Book.objects(id=u_id).first()


def get_user(u_id):
    return User.objects(user_id=u_id).first()


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

