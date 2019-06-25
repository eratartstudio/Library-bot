import datetime
from pprint import pprint as pp

from aiogram import Bot , Dispatcher , executor
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State , StatesGroup
from aiogram.utils import exceptions
from mongoengine import errors

from conf import token , MAX_CONNECTIONS_TO_CONF
from help import *
from models import User , Autor , Book , Review , ReviewsToAdd , Chats

loop = asyncio.get_event_loop()
bot = Bot( token=token , loop=loop )

storage = RedisStorage2( db=5 )
dp = Dispatcher( bot , loop=loop , storage=storage )
s = bot.send_message


'''                                     #to work with channels#
@dp.channel_post_handler()
async def post(msg: types.Message):
    print(msg)


@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def cont(msg: types.Message):
    print(msg)
'''


class AuthorState( StatesGroup ) :
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

	watch_reviews_by_criterias = State()
	watch_reviews_from = State()
	watch_reviews_from_users = State()
	watch_reviews_from_web = State()

	in_conversation = State()

	adminstate = State()


@dp.message_handler( lambda message : message.text == '⬅️ Назад' , state='*' )
async def global_back_handler( msg: types.Message , state: FSMContext ) :
	await delete_temp_messages( state )
	state_now = await state.get_state()
	u_id = msg.from_user.id
	u = get_user( u_id )
	async with state.proxy() as data :
		if state_now == AuthorState.action_menu.state :
			print( 'done!' )
			# await delete_active_user_from_chat( state , u_id , msg )
			if data[ 'already_in_search' ] :
				count = data[ 'count in search' ]

				mark = get_books_by_name( count , data[ 'book_name' ] )
				await AuthorState.get_book_command.set()
				await s( msg.from_user.id , 'Получаем данные...' , reply_markup=simple_markup_back_end )
				await s( msg.from_user.id , 'Результаты поиска:' , reply_markup=mark )
			else :
				count = data[ 'count in search' ]
				await add_to_temp( await send_books_in_collection( u , count ) , data )
				await AuthorState.get_book_command.set()

		elif state_now == AuthorState.in_conversation.state :
			print( 'not good' )
			await disconnect_user_from_conversation( state )
		# equal
		# await in_conversation_back_handler_callback( msg , state )

		elif state_now == AuthorState.get_book_name.state :
			if data[ 'actions_menu' ] :
				msg.text = text_in_main[ 1 ]
			else :
				msg.text = text_in_main[ 0 ]
			await main_menu( msg , state )
		elif state_now == AuthorState.get_author_command.state :
			msg.text = text_in_add_book[ 0 ]
			await book_root_menu( msg , state )

		elif state_now == AuthorState.get_book_command.state :
			if not data[ 'already_in_search' ] :
				autorlist = data[ 'autorlist' ]
				count = data[ 'count in search' ]

				await AuthorState.get_author_command.set()
				await s( u_id , 'Авторы:' , reply_markup=get_authors_markup( count , autorlist ) )
			else :
				msg.text = text_in_add_book[ 1 ]
				await book_root_menu( msg , state )

		elif state_now == AuthorState.get_review_state.state :
			pass
		elif state_now == AuthorState.search_book.state :
			pass
		elif state_now == AuthorState.add_review_from_user.state :

			book = Book.objects( id=data[ 'book_id' ] ).first()
			await add_to_temp( await new_book_or_review( u , msg , book , need_to_add=False ,
			                                             not_first_time=not data[ 'user_books' ] ) , data )

		elif state_now == AuthorState.name_or_surname.state :

			if data[ 'actions_menu' ] :
				msg.text = text_in_main[ 1 ]
			else :
				msg.text = text_in_main[ 0 ]
			await main_menu( msg , state )

		elif state_now == AuthorState.add_new_criteria.state :

			book = Book.objects( id=data[ 'book_id' ] ).first()
			await add_to_temp( await new_book_or_review( u , msg , book , need_to_add=False ,
			                                             not_first_time=not data[ 'user_books' ] ,
			                                             from_library=data[ 'from_library' ] ) , data )

		elif state_now == AuthorState.get_out_of_ten_state.state :

			book = Book.objects( id=data[ 'book_id' ] ).first()
			await add_to_temp( await new_book_or_review( u , msg , book , False ) , data )

		elif state_now == AuthorState.watch_reviews_from.state :
			book = Book.objects( id=data[ 'book_id' ] ).first()

			await add_to_temp( await new_book_or_review( u , msg , book , need_to_add=False ,
			                                             from_library=data[ 'from_library' ] , actions=True ) , data )

		elif any( this_state == state_now for this_state in [
			AuthorState.watch_reviews_from_users.state , AuthorState.watch_reviews_from_web.state ,
			AuthorState.watch_reviews_by_criterias.state ] ) :
			print( f'user @{msg.from_user.username} watches types of reviews ' )
			await AuthorState.watch_reviews_from.set()
			await bot.send_message( u_id , 'У нас много отзывов, выберите' ,
			                        reply_markup=inline_markup_reviews )


@dp.callback_query_handler( lambda c : c.data == 'back' ,
                            state=[ AuthorState.watch_reviews_from , AuthorState.watch_reviews_from_web ,
                                    AuthorState.watch_reviews_from_users , AuthorState.watch_reviews_by_criterias ] )
async def global_back_callback_handler( c: types.CallbackQuery , state: FSMContext ) :
	await c.answer()
	state_now = await state.get_state()
	async with state.proxy() as data :
		if state_now == AuthorState.watch_reviews_from.state :
			await c.message.delete()

			book = Book.objects( id=data[ 'book_id' ] ).first()

			await add_to_temp( await new_book_or_review( get_user( c.from_user.id ) , c , book , need_to_add=False ,
			                                             from_library=data[ 'from_library' ] , actions=True ) , data )
		else :
			c.data = 'watch_reviews_from'
			await action_menu( c , state )


@dp.callback_query_handler( lambda c : 'page_' in c.data , state='*' )
async def global_paginator( c: types.CallbackQuery , state: FSMContext ) :
	state_now = await state.get_state()
	count = int( c.data.replace( 'page_' , '' ) )

	async with state.proxy() as data :
		if state_now == AuthorState.get_author_command.state :
			data[ 'count in search' ] = count
			autorlist = data[ 'autorlist' ]

			if count > len( autorlist ) :
				await bot.answer_callback_query( c.id , 'Это последняя страница' , show_alert=True )
				return
			else :
				await bot.answer_callback_query( c.id , 'Переход к следующей странице' )
			await bot.edit_message_reply_markup( c.from_user.id , c.message.message_id ,
			                                     reply_markup=get_authors_markup( count , autorlist ) )
		elif state_now == AuthorState.get_book_command.state :
			data[ 'count in search' ] = count

			if data[ 'user_books' ] :
				await bot.edit_message_reply_markup( c.from_user.id , c.message.message_id ,
				                                     reply_markup=get_books_from_collection( count ,
				                                                                             get_user(
						                                                                             c.from_user.id ) ) )
			elif not data[ 'already_in_search' ] :
				aut = data[ 'autor_id' ]
				await bot.answer_callback_query( c.id , 'Переход к следующей странице' )
				await bot.edit_message_reply_markup( c.from_user.id , c.message.message_id ,
				                                     reply_markup=get_books_of_autor( count , aut ) )
			else :
				await bot.answer_callback_query( c.id , 'Переход к следующей странице' )

				mark = get_books_by_name( count , data[ 'book_name' ] )
				data[ 'count in search' ] = count
				await bot.edit_message_reply_markup( c.from_user.id , c.message.message_id , reply_markup=mark )

		elif state_now == AuthorState.adminstate.state :

			await bot.edit_message_reply_markup( c.from_user.id , c.message.message_id ,
			                                     reply_markup=get_inline_list( count , data[ 'objs' ] ) )


async def delete_temp_messages( state: FSMContext ) :
	async with state.proxy() as data :
		if 'temp_messages' in data :
			pp( data[ 'temp_messages' ] )
			for message_id in data[ 'temp_messages' ] :
				try :
					await bot.delete_message( state.chat , message_id )
				except exceptions.MessageToDeleteNotFound :
					pass
		data[ 'temp_messages' ] = [ ]


async def add_to_temp( msg: types.Message , data=None , state=None ) :
	if not state :
		data[ 'temp_messages' ].append( msg.message_id )
	else :
		async with state.proxy() as data :
			data[ 'temp_messages' ].append( msg.message_id )


@dp.message_handler( commands=[ 'top_10_criterias' ] , state='*' )
async def top_10_addition( msg: types.Message , state: FSMContext ) :
	# u = get_user(msg.from_user.id)
	objs = list( reversed( sorted( ReviewsToAdd.objects() , key=lambda obj : obj.count ) ) )
	async with state.proxy() as data :
		data[ 'objs' ] = objs
	print( objs )
	await s( msg.from_user.id , 'Топ популярных отзывов\n' , reply_markup=get_inline_list( 0 , objs ) )
	await AuthorState.adminstate.set()


@dp.callback_query_handler( lambda c : c.data in [ 'accept' , 'decline' ] , state='*' )
async def accept_decline_callback( c: types.CallbackQuery , state: FSMContext ) :
	await c.answer()
	data = await state.get_data()
	# mark = get_accept_decline(data)
	#
	try :
		await c.message.delete()
	except exceptions.MessageToDeleteNotFound :
		pass

	u_id = c.from_user.id
	u = get_user( u_id )
	chat = Chats.objects( id=data[ 'chat_id' ] ).first()

	if c.data == 'accept' :

		if chat :
			print( f'user @{c.from_user.username} with id {c.from_user.id} accepted conversation ' )

			await s( u_id , 'Вы присоединились к обсуждению!' , reply_markup=simple_markup_back_end )
			u.connect_chat()
			if not chat.visited :
				await delete_temp_messages( FSMContext( storage , chat.creator_id , chat.creator_id ) )

				get_user( chat.creator_id ).update( waits_conversation=False , in_conversation=True )

				await s( chat.creator_id , in_contact ,
				         reply_markup=accept_decline_markup )
				# await creator_data.update(waiting_message_id=mes.message_id)

				chat.visited = True

			chat.connected_users.append( u )
			chat.save()
			await AuthorState.in_conversation.set()
		else :
			print(
					f'user @{c.from_user.username} with id {c.from_user.id} accepted conversation but chat does not exist' )
			await s( u_id , 'Чат уже не существует' )
			u.disconnect_chat()
	# await c.message.edit_text( 'Чат уже не существует' )

	elif c.data == 'decline' :
		print( f'user @{c.from_user.username} with id {c.from_user.id} declined conversation ' )
		# await disconnect_user_from_conversation( state )
		u.disconnect_chat()


@dp.callback_query_handler( lambda c : c.data == 'start' , state=AuthorState.all_states )
async def start_callback( c: types.CallbackQuery , state: FSMContext ) :
	await bot.answer_callback_query( c.id )
	await c.message.delete()
	await start_command_func( c , state )


@dp.message_handler( commands=[ 'available' ] , state='*' )
async def set_all_users_to_available_state( msg: [ types.Message , types.CallbackQuery ] ) :
	User.objects.update( in_conversation=False , waits_conversation=False )
	await s( msg.from_user.id , 'all users sets to available' )


async def start_state_init( state ) :
	await state.set_data( {
		'already_in_search' : False ,
		'user_books'        : False ,
		'from_library'      : False ,
		'count in search'   : 0 ,
		'temp_messages'     : [ ] ,
		'chat_id'           : None
		} )


@dp.message_handler( commands=[ 'start' , 's' ] , state='*' )
async def start_command_func( msg: [ types.Message , types.CallbackQuery ] , state: FSMContext ) :
	u_id = msg.from_user.id
	await start_state_init( state )

	get_or_add_user( msg )
	# delete_from_chat(u_id)

	await AuthorState.start.set()
	await s( u_id , start_message , reply_markup=menu_reply_markup )


async def send_books_in_collection( u: User , count=0 ) :
	if len( u.books ) == 0 :
		await AuthorState.start.set()
		mes = await s( u.user_id , 'Ваша полка пуста!' , reply_markup=menu_reply_markup )

	else :
		await s( u.user_id , 'Отсылаем меню...' , reply_markup=simple_markup_with_add_book_end )
		mes = await s( u.user_id , 'На вашей полке стоят книги:' , reply_markup=get_books_from_collection( count , u ) )
	return mes


@dp.message_handler( lambda m : m.text in [ '❌️ Закончить' , ] , state=AuthorState.all_states )
async def back( m: types.Message , state: FSMContext ) :
	# if user is in conversation
	await delete_temp_messages( state )

	if await state.get_state() == AuthorState.in_conversation.state :
		# remove user from conversation
		await disconnect_user_from_conversation( state , send_mes=False )
	# pass

	# data = await state.get_data()
	# book = Book.objects( id=data[ 'book_id' ] ).first()
	#
	# await add_to_temp(await new_book_or_review( get_user( m.from_user.id ) , m , book , need_to_add=False ,
	#                           from_library=data[ 'from_library' ] , actions=True )
	# user = get_user( m.from_user.id )
	# user.disconnect_chat()
	await m.delete()
	await start_command_func( m , state )


async def set_state_by_id( user_id , state ) :
	await storage.set_state( chat=user_id , user=user_id , state=state )


async def set_chat_by_id( user_id , chat_id ) :
	await storage.update_data( chat=user_id , user=user_id , chat_id=chat_id )


@dp.callback_query_handler( state=[ AuthorState.start , AuthorState.book_root ] )
async def get_search_autor_or_bookname( c: types.CallbackQuery , state: FSMContext ) :
	await c.answer()

	await c.message.delete()

	async with state.proxy() as data :
		data[ 'already_in_search' ] = False
		data[ 'user_books' ] = False

		if c.data == 'autor' :
			await AuthorState.name_or_surname.set()
			await s( c.from_user.id , get_name_message , reply_markup=simple_markup_back_end )

		elif c.data == 'title' :
			await AuthorState.get_book_name.set()
			await s( c.from_user.id , 'Напишите название книги' , reply_markup=simple_markup_back_end )


@dp.message_handler( lambda m : m.text in text_in_main ,
                     state=[ AuthorState.start , AuthorState.get_book_command , AuthorState.book_root ] )
async def main_menu( msg: types.Message , state: FSMContext ) :
	await delete_temp_messages( state )

	u_id = msg.from_user.id
	text = msg.text
	u = get_user( u_id )

	async with state.proxy() as data :

		data[ 'already_in_search' ] = False
		data[ 'user_books' ] = False
		data[ 'from_library' ] = False
		if text == text_in_main[ 0 ] :
			await AuthorState.book_root.set()
			data[ 'need_to_add' ] = True
			data[ 'actions_menu' ] = False
			await s( u_id , add_book_start , reply_markup=menu_add_book_markup )
			temp_mes = await s( u_id , 'Как искать?' , reply_markup=inline_markup_autor_nazvanie )
			data[ 'temp_messages' ].append( temp_mes.message_id )

			print( f'user @{msg.from_user.username} wants to add some book' )

		elif text == text_in_main[ 1 ] :
			data[ 'need_to_add' ] = False
			data[ 'actions_menu' ] = True
			await AuthorState.book_root.set()
			await s( u_id , add_book_start , reply_markup=menu_add_book_markup )
			temp_mes = await s( u_id , 'Как искать?' , reply_markup=inline_markup_autor_nazvanie )
			data[ 'temp_messages' ].append( temp_mes.message_id )

			print( f'user @{msg.from_user.username} wants to see some book' )

		elif text == text_in_main[ 2 ] :
			data[ 'need_to_add' ] = False
			data[ 'actions_menu' ] = True
			data[ 'user_books' ] = True
			data[ 'from_library' ] = True
			data[ 'count in search' ] = 0
			await AuthorState.get_book_command.set()
			print( f'user @{msg.from_user.username} wants to see library' )

			await add_to_temp( await send_books_in_collection( u ) , data )

		elif text == text_in_main[ 3 ] :
			pass
		else :
			pass


@dp.message_handler( lambda m : m.text in text_in_add_book , state=AuthorState.book_root )
async def book_root_menu( msg: types.Message , state: FSMContext ) :
	await delete_temp_messages( state )

	u_id = msg.from_user.id
	u = get_user( u_id )
	text = msg.text
	async with state.proxy() as data :
		data[ 'already_in_search' ] = False
		data[ 'user_books' ] = False

		if text == text_in_add_book[ 0 ] :
			await AuthorState.name_or_surname.set()
			await s( u_id , get_name_message , reply_markup=simple_markup_back_end )

		elif text == text_in_add_book[ 1 ] :
			await AuthorState.get_book_name.set()
			await s( u_id , 'Напишите название книги' , reply_markup=simple_markup_back_end )

		elif text == text_in_add_book[ 2 ] :
			data[ 'need_to_add' ] = False
			data[ 'actions_menu' ] = True
			data[ 'user_books' ] = True
			await AuthorState.get_book_command.set()
			await add_to_temp( await send_books_in_collection( u ) , data )

		elif text == text_in_add_book[ 3 ] :
			pass


@dp.message_handler( state=AuthorState.get_book_name )
async def get_book_name( msg: types.Message , state: FSMContext ) :
	async with state.proxy() as data :
		u_id = msg.from_user.id
		await delete_temp_messages( state )

		if not data[ 'already_in_search' ] :

			book_name = msg.text
			if Book.objects( article__icontains=book_name ).first() :
				# alphabetic order
				await AuthorState.get_book_command.set()
				mark = get_books_by_name( 0 , book_name )
				data[ 'count in search' ] = 0
				# save them to use in next steps / pagination
				data[ 'book_name' ] = book_name
				data[ 'already_in_search' ] = True
				await add_to_temp( await s( u_id , 'Результаты поиска:' , reply_markup=mark ) , data )
			else :
				await add_to_temp( await s( u_id , 'Ничего не найдено, попробуйте снова' ) , data )

		else :
			await add_to_temp( await s( u_id , 'Сначала закончите предыдущий поиск' ) , data )
			await bot.delete_message( msg.from_user.id , msg.message_id )


# search authors by name and surname
def get_autor_list( text ) :
	args = list( text.split( ' ' ) )
	while args.count( '' ) != 0 :
		args.remove( '' )
	autorlist = ()
	if len( args ) > 1 :
		name = args[ 0 ][ 0 ].upper() + args[ 0 ][ 1 : ]
		surname = args[ 1 ][ 0 ].upper() + args[ 1 ][ 1 : ]
		print( name , surname )
		autorlist = tuple(
				(name , surname , str( x.id )) for x in Autor.objects( name=name , surname=surname ) ) + tuple(
				(surname , name , str( x.id )) for x in Autor.objects( name=surname , surname=name ) )
	# print(autorlist)
	if not autorlist :
		for word in args :
			word = word[ 0 ].upper() + word[ 1 : ]
			autor_name = tuple( (x.name , x.surname , str( x.id )) for x in Autor.objects( name=word ) )
			autor_surname = tuple( (x.name , x.surname , str( x.id )) for x in Autor.objects( surname=word ) )
			autorlist = autorlist + autor_name + autor_surname

	autorlist = tuple( set( autorlist ) )
	return tuple( sorted( autorlist , key=lambda author : author[ 2 ] ) )


@dp.message_handler( state=AuthorState.name_or_surname )
async def get_author_by_name_mes( msg: types.Message , state: FSMContext ) :
	u_id = msg.from_user.id
	await delete_temp_messages( state )

	async with state.proxy() as data :
		# go to previous state

		autorlist = get_autor_list( msg.text )

		if len( autorlist ) == 0 :
			await s( u_id , 'Подобного автора не найдено' )
			return

		data[ 'autorlist' ] = autorlist
		data[ 'count in search' ] = 0

		await AuthorState.get_author_command.set()
		await s( u_id , 'Авторы:' , reply_markup=get_authors_markup( 0 , autorlist ) )


@dp.callback_query_handler( state=AuthorState.get_author_command )
async def get_author_command( c: types.CallbackQuery , state: FSMContext ) :
	autor_id = c.data
	# aut = Autor.objects(id=autor_id).first()
	await delete_temp_messages( state )

	async with state.proxy() as data :
		data[ 'autor_id' ] = autor_id
		data[ 'count in search' ] = 0

	await AuthorState.get_book_command.set()
	await bot.edit_message_text( 'Выберите книгу' , c.from_user.id , c.message.message_id ,
	                             reply_markup=get_books_of_autor( 0 , autor_id ) )


@dp.callback_query_handler( state=AuthorState.get_book_command )
async def get_book_command( c: types.CallbackQuery , state: FSMContext ) :
	await bot.answer_callback_query( c.id )
	await c.message.delete()
	book_id = c.data

	u = get_user( c.from_user.id )

	async with state.proxy() as data :
		try :
			book = get_book( book_id )
			print( f'user @{c.from_user.username} had chosen book {book.article}' )

			data[ 'book_id' ] = str( book.id )
			# data[ 'autor_id' ] = str( book.autor.id ) or 'None'
			need = data[ 'need_to_add' ]
			actions = data[ 'actions_menu' ]
			from_library = data[ 'from_library' ]

			await add_to_temp( await new_book_or_review( u , c , book , need_to_add=need , actions=actions ,
			                                             from_library=from_library ) , data )

		except errors.ValidationError :
			pass


# big function that sends different types of messages when the book was chosen
async def new_book_or_review( u: User , c: [ types.Message , types.CallbackQuery ] , book , need_to_add=True ,
                              actions=False , from_library=False , not_first_time=False ) :
	if type( c ) == types.CallbackQuery :
		try :
			await c.message.delete()
			await bot.delete_message( c.from_user.id , c.message.message_id - 1 )

		except :
			pass
	if actions :
		await AuthorState.action_menu.set()
		if from_library :
			await s( u.user_id , 'Получаем данные...' , reply_markup=simple_markup_back_end )
		else :
			await s( u.user_id , 'Получаем данные...' , reply_markup=simple_markup_with_another_book )
		mes = await s( u.user_id , book_done ,
		               reply_markup=get_inline_markup_with_actions( book in u.books ) )

	else :
		await AuthorState.get_review_state.set()

		mes = await s( c.from_user.id ,
		               get_review_text(
				               need_to_add=need_to_add ) if need_to_add or not_first_time else get_reviews_criteria(
				               book ) + '\nВыбери критерий для оценки' ,
		               reply_markup=simple_markup_on_criteria , parse_mode='Markdown' )
		if need_to_add and book not in u.books :
			print( 'no book.really' )
			u.books.append( book )
			u.save()

	return mes


async def delete_active_user_from_chat( state , u_id ) :
	async with state.proxy() as data :
		if await state.get_state() == AuthorState.in_conversation.state :  # if user waited
			# remove user from query
			u = get_user( u_id )
			u.disconnect_chat()
			chat = Chats.objects( id=data[ 'chat_id' ] ).first()
			if chat :
				if u_id == chat.creator_id :
					print( 'he is creator' )
					try :
						await bot.delete_message( u_id , data[ 'waiting_message_id' ] )
					except exceptions.MessageToDeleteNotFound :
						pass

					for user in chat.connected_users :
						if user.user_id != u_id :
							await s( user.user_id , 'Создатель вышел из беседы, беседа закончена' )
						user.disconnect_chat()
					chat.close()

				else :
					chat.connected_users.remove( u )
					chat.save()


@dp.message_handler( lambda m : m.text == '📔 Другая книга' ,
                     state=AuthorState.all_states )
async def msg_action( msg: types.Message , state: FSMContext ) :
	await delete_temp_messages( state )

	await AuthorState.get_book_name.set()
	msg.text = '📔 Узнать о книге'
	await main_menu( msg , state )


@dp.callback_query_handler( lambda c : c.data == 'back' , state=AuthorState.in_conversation )
async def in_conversation_back_handler_callback( c: types.CallbackQuery , state: FSMContext ) :
	# await delete_temp_messages( state )
	u_id = c.from_user.id
	if type( c ) == types.CallbackQuery :
		await c.answer()

		try :
			await c.message.delete()
			await bot.delete_message( u_id , c.message.message_id - 1 )
		except exceptions.MessageCantBeDeleted :
			pass
		except exceptions.MessageToDeleteNotFound :
			pass

	await disconnect_user_from_conversation( state )


async def close_chat_and_disconnect_users( book: Book , chat: Chats ) :
	await set_state_by_id( chat.creator_id , AuthorState.action_menu.state )

	for user in chat.connected_users :
		await s( user.user_id , 'Чат перестал существовать' )
		await set_state_by_id( user.user_id , AuthorState.action_menu.state )
		if user.user_id != chat.creator_id :
			await new_book_or_review( user , None , book , need_to_add=False ,
			                          from_library=False , actions=True )
	chat.close()


async def disconnect_user_from_conversation( state: FSMContext , send_mes=True ) :
	async with state.proxy() as data :
		u = get_user( state.user )

		# print( f'user @{c.from_user.username} with id {c.from_user.id} declined conversation ' )
		chat = Chats.objects( id=data[ 'chat_id' ] ).first()
		book = get_book( data[ 'book_id' ] )
		if chat :
			if chat.creator_id == u.user_id :
				print(
						f'user @{u.username} get BACK from conversation, conversation closed because he is creator' )
				u.disconnect_chat()
				await close_chat_and_disconnect_users( book , chat )
			else :
				chat.disconnect_user( u )
		if send_mes :
			await add_to_temp( await new_book_or_review( u , None , book , need_to_add=False ,
			                                             from_library=data[ 'from_library' ] , actions=True ) , data )
	# await AuthorState.action_menu.set()


@dp.message_handler( state=AuthorState.in_conversation , content_types=types.ContentTypes.ANY )
async def in_conversation( msg: types.Message , state: FSMContext ) :
	# await delete_temp_messages( state )

	# msg.text = f'{get_random_emodzi()}\n' + msg.text
	async with state.proxy() as data :
		chat = Chats.objects( id=data[ 'chat_id' ] ).first()
		if chat :
			pp( chat.smiles )
			smile = chat.smiles[ str( msg.from_user.id ) ]

			for user in chat.connected_users :
				if user.user_id != msg.from_user.id :
					await bot.send_chat_action( user.user_id , action='typing' )
					await resend_message_with_file( bot , msg , user.user_id , smile )


# await s( user.user_id , msg.text , parse_mode='Markdown' , reply_markup=simple_markup_back_end )


def get_available_users_with_book( u_id , book ) :
	users = User.get_available( books__contains=book , user_id__ne=int( u_id ) )
	user_count = users.count()
	return random.sample( list( users ) , k=min( MAX_CONNECTIONS_TO_CONF , user_count ) )


# return User.get_available( books__contains=book , username__in=['Netsl','GioNets'])


@dp.callback_query_handler( state=AuthorState.action_menu )
async def action_menu( c: types.CallbackQuery , state: FSMContext ) :
	# await delete_temp_messages( state )

	u_id = c.from_user.id
	msg_id = c.message.message_id
	try :
		await c.answer()
	except :
		pass

	if c.data == 'go_into_conversation' :
		await c.message.delete()
		# await bot.delete_message( u_id , msg_id )
		async with state.proxy() as data :
			# userqueue should not include users who have already in_conversation state and
			print( data[ 'book_id' ] )
			# we should optimize function that will get all "good" users to us
			user = get_user( u_id )
			user.chat_waiting()
			# if we have user that waits, then connect them, else add new user to queue

			book = get_book( data[ 'book_id' ] )
			available_users = get_available_users_with_book( u_id , book )

			new_chat = Chats( creator_id=c.from_user.id , book_id=data[ 'book_id' ] , invited_users=available_users )

			new_chat.get_emodzi()
			data[ 'chat_id' ] = str( new_chat.id )

			for user in available_users :
				await s( user.user_id , f'Вас приглашают обсудить книгу *{book.article}*' ,
				         reply_markup=accept_decline_markup , parse_mode='Markdown' )
				await state.storage.update_data( chat=user.user_id , user=user.user_id , chat_id=str( new_chat.id ) )
				user.chat_waiting()

			mes = await s( u_id , 'Идет поиск собеседника...' , reply_markup=back_inline_markup , )
			await add_to_temp( mes , data )
			await AuthorState.in_conversation.set()

			print( f'user @{c.from_user.username} waits conversation for book {book.article}' )

		task = asyncio.create_task( timeout_callback( loop , u_id , str( book.id ) ) )
		await task

	elif c.data == 'watch_reviews_from' :
		print( f'user @{c.from_user.username} watches types of reviews ' )
		await AuthorState.watch_reviews_from.set()
		await bot.edit_message_text( 'У нас много отзывов, выберите' , u_id , msg_id ,
		                             reply_markup=inline_markup_reviews )



	elif c.data == 'delete' :

		async with state.proxy() as data :
			book = Book.objects( id=data[ 'book_id' ] ).first()
			print( f'user @{c.from_user.username} deleted book {book.article}' )

			u = get_user( u_id )
			u.books.remove( book )
			u.save()
			await add_to_temp( await new_book_or_review( u , c , book , need_to_add=False , actions=True ,
			                                             from_library=data[ 'from_library' ] ) , data )


@dp.callback_query_handler( state=AuthorState.watch_reviews_from )
async def watch_reviews_from_menu( c: types.CallbackQuery , state: FSMContext ) :
	await c.answer()

	if 'watch_reviews_from_web_' in c.data :
		await AuthorState.watch_reviews_from_web.set()

		await see_reviews_from_web_paginator( c , state )


	elif 'reviews_of_users_' in c.data :
		await AuthorState.watch_reviews_from_users.set()

		print( f'user @{c.from_user.username} wants to see reviews from users' )

		await see_reviews_from_users_paginator( c , state )

	elif c.data == 'reviews_by_criterias' :
		await AuthorState.watch_reviews_by_criterias.set()

		print( f'user @{c.from_user.username} wants to see reviews by criterias' )

		async with state.proxy() as data :
			book = Book.objects( id=data[ 'book_id' ] ).first()
			await c.message.edit_text( get_reviews_criteria( book ) ,
			                           reply_markup=reviews_criteria_reply_markup , parse_mode='Markdown' )

	async with state.proxy() as data :
		await add_to_temp( c.message , data )


@dp.callback_query_handler( lambda c : 'reviews_from_web_' in c.data , state=AuthorState.watch_reviews_from_web )
async def see_reviews_from_web_paginator( c: types.CallbackQuery , state: FSMContext ) :
	await c.answer()

	async with state.proxy() as data :
		book = Book.objects( id=data[ 'book_id' ] ).first()
		# captcha
		try :
			print( f'Отзывы для юзера {c.from_user.username}' )
			reviews = book.get_impressions_bookmate()

			next = int( c.data.replace( 'watch_reviews_from_web_' , '' ) )

			if reviews :
				await bot.edit_message_text( reviews[ next ] , c.from_user.id , c.message.message_id ,
				                             reply_markup=get_book_reviews( next , reviews ) )
			else :
				await bot.edit_message_text( 'Нет отзывов с букмейта :(' , c.from_user.id , c.message.message_id ,
				                             reply_markup=back_inline_markup )

		except IndexError :
			await bot.edit_message_text( 'Нет отзывов с букмейта :(' , c.from_user.id , c.message.message_id ,
			                             reply_markup=back_inline_markup )
		except Exception as e :
			print( e )
			await bot.edit_message_text( str( e ) , c.from_user.id , c.message.message_id ,
			                             reply_markup=end_inline_markup )
			await s( c.from_user.id , 'Сообщите об ошибке @Netsl' )


@dp.callback_query_handler( lambda c : c.data == 'vote' , state=AuthorState.watch_reviews_by_criterias )
async def vote_by_criterias( c: types.CallbackQuery , state: FSMContext ) :
	print( f'user @{c.from_user.username} wants to vote by criteria' )

	async with state.proxy() as data :
		book = Book.objects( id=data[ 'book_id' ] ).first()

		await add_to_temp(
				await new_book_or_review( get_user( c.from_user.id ) , c , book , need_to_add=False , actions=False ) ,
				data )


@dp.callback_query_handler( lambda c : 'reviews_of_users_' in c.data , state=AuthorState.watch_reviews_from_users )
async def see_reviews_from_users_paginator( c: types.CallbackQuery , state: FSMContext ) :
	await c.answer()
	u_id = c.from_user.id
	next = int( c.data.replace( 'reviews_of_users_' , '' ) )

	async with state.proxy() as data :
		book = Book.objects( id=data[ 'book_id' ] ).first()

		reviews = book.reviews
		if len( reviews ) == 0 :
			await bot.edit_message_text( 'Отзывов пока нет' , u_id , c.message.message_id ,
			                             reply_markup=get_book_reviews_from_users( 0 , [ ] ) )
		else :
			await bot.edit_message_text( reviews[ next ].text , u_id , c.message.message_id ,
			                             reply_markup=get_book_reviews_from_users( next , reviews ) )


@dp.message_handler( state=AuthorState.add_new_criteria )
async def add_new_criteria( msg: types.Message , state: FSMContext ) :
	await s( msg.from_user.id , 'Спасибо!' )
	obj = ReviewsToAdd.objects( text=msg.text ).first()
	if not obj :
		obj = ReviewsToAdd( text=msg.text )
	else :
		obj.count += 1
	obj.save()


@dp.callback_query_handler( state=AuthorState.adminstate )
async def adminstate_callback( c: types.CallbackQuery , state: FSMContext ) :
	await c.answer()

	r_id = c.data
	obj = ReviewsToAdd.objects( id=r_id ).first()
	await s( c.from_user.id , 'in progress.\n' + obj.text )


@dp.message_handler( state=AuthorState.get_review_state )
async def get_review_state( msg: types.Message , state: FSMContext ) :
	if msg.text == '✅ Доб. критерий' :
		await s( msg.from_user.id , 'Отправьте критерий оценки который бы вы хотели видеть' ,
		         reply_markup=simple_markup_back_end )
		await AuthorState.add_new_criteria.set()

	elif msg.text == '✍️ Написать отзыв' :
		await s( msg.from_user.id ,
		         'Отправьте сообщение и мы сохраним его как отзыв!\nНажмите "Закончить" чтобы прервать это действие' ,
		         reply_markup=simple_markup_back_end )
		await AuthorState.add_review_from_user.set()

	elif msg.text == '🎓 Добавить книгу' :
		await main_menu( msg , state )

	elif msg.text.isnumeric() :
		async with state.proxy() as data :
			review_type = int( msg.text )
			book = Book.objects( id=data[ 'book_id' ] ).first()

			review = Review.objects( book=book , type=review_type - 1 ).first()
			print( review )
			if review_type <= 0 or not list( review ) :
				await s( msg.from_user.id , 'Выберите корректный критерий' )
				return

			if str( msg.from_user.id ) in review.voted :
				await s( msg.from_user.id ,
				         f'Вы уже оценили книгу по этому критерию. Ваша оценка: *{review.voted[str(msg.from_user.id)]}*' ,
				         parse_mode='Markdown' )
				return

			data[ 'review' ] = str( review.id )

			await s( msg.from_user.id , get_solo_review_text( review ) ,
			         reply_markup=simple_markup_back_end )

			await AuthorState.get_out_of_ten_state.set()


# await bot.answer_callback_query(c.id, callback_text)


@dp.message_handler( state=AuthorState.add_review_from_user )
async def add_review_from_user( msg: types.Message , state: FSMContext ) :
	async with state.proxy() as data :
		book = Book.objects( id=data[ 'book_id' ] ).first()

		text = '{}\n{}'.format( msg.from_user.username or 'Аноним' , msg.text )
		new = Review( type=0 , text=text , book=book )
		new.save()
		book.reviews.append( new )
		book.save()
		await s( msg.from_user.id , 'Ваш отзыв принят!' )


@dp.message_handler( lambda m : m.text.isnumeric() , state=AuthorState.get_out_of_ten_state )
async def get_author_by_name( msg: types.Message , state: FSMContext ) :
	u_id = msg.from_user.id
	mark = int( msg.text )
	async with state.proxy() as data :
		book = Book.objects( id=data[ 'book_id' ] ).first()

		review_id = data[ 'review' ]
		review = Review.objects( id=review_id ).first()
		review.mark[ mark ] += 1
		review.voted[ str( msg.from_user.id ) ] = mark
		review.save()

		await add_to_temp( await new_book_or_review( u=get_user( u_id ) , c=msg , book=book , need_to_add=False ,
		                                             not_first_time=True ) , data )


def get_book( book_id ) :
	return Book.objects( id=book_id ).first()


def get_user( u_id ) :
	return User.objects( user_id=u_id ).first()


@dp.message_handler( state=None )
async def handle_all_messages( msg: types.Message ) :
	u_id = msg.from_user.id
	get_or_add_user( msg )
	await s( u_id , f'Напишите /start для начала работы' )

	await AuthorState.start.set()


def get_or_add_user( msg ) :
	u_id = msg.from_user.id
	u = User.objects( user_id=u_id )
	if len( u ) == 0 :
		u = User( user_id=u_id , username=msg.from_user.username or str( msg.from_user.id ) )
		u.save()

	else :
		u = u[ 0 ]
		# if user changed or deleted his username
		u.update( username=msg.from_user.username or str( msg.from_user.id ) )
	return u


async def timeout_callback( loop , user_id , book_id ) :
	end_time = loop.time() + 300
	while True :
		print( datetime.datetime.now() )
		if (loop.time() + 1) >= end_time :
			break
		await asyncio.sleep( 150 )
	print( 'timer done, let\'t start connecting them!' )
	user = get_user( user_id )

	if user.waits_conversation and not user.in_conversation :
		my_chat = Chats.objects( creator_id=user_id ).first()
		my_chat.time_out()

		while True :
			chatslist = get_waiting_chats( book_id , user_id )
			pp( list( x.creator_id for x in chatslist ) )
			user = get_user( user_id )
			my_chat = Chats.objects( creator_id=user_id ).first()

			if not user.waits_conversation or user.in_conversation or not my_chat :
				print( 'func closed' )
				break
			if len( chatslist ) >= 4 :
				available_users = list( get_user( chat.creator_id ) for chat in chatslist )

				book = get_book( book_id )

				for chat in chatslist :
					await close_chat_and_disconnect_users( book , chat )

				await close_chat_and_disconnect_users( book , my_chat )

				new_chat = Chats( creator_id=user_id , book_id=book_id , invited_users=available_users )

				new_chat.get_emodzi()
				await set_chat_by_id( user_id , str( new_chat.id ) )

				await AuthorState.in_conversation.set()
				for u in available_users :
					await set_chat_by_id( u.user_id , str( new_chat.id ) )
					u_state = FSMContext( storage , u.user_id , u.user_id )
					await delete_temp_messages( u_state )
					mes = await s( u.user_id , f'Вас приглашают обсудить книгу *{book.article}*' ,
					               reply_markup=accept_decline_markup , parse_mode='Markdown' )
					await add_to_temp( mes , state=u_state )
					user.chat_waiting()
				await asyncio.create_task( timeout_callback( loop , user_id , book_id ) )
				break
			await asyncio.sleep( 10 )
			print( 'still waiting' )


def get_waiting_chats( book_id , creator_id ) :
	return Chats.get_not_visited( book_id=book_id , creator_id__ne=creator_id )[ :5 ]


if __name__ == '__main__' :
	executor.start_polling( dp , loop=loop )
