import asyncio

import random
from aiogram import types

from conf import emodzi_list
from models import Review , Autor , User , ReviewsToAdd , Book

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


def get_random_emodzi() :
	return random.choice( emodzi_list )


async def resend_message_with_file( bot , msg , id_to_send , smile ) :
	if 'photo' in msg :
		# mes['photo']x
		print( msg[ 'photo' ][ len( msg.photo ) - 1 ].__dict__ )
		args = {
			'chat_id'      : id_to_send ,
			'photo'        : msg.photo[ len( msg.photo ) - 1 ][ 'file_id' ] ,
			'caption'      : smile + '\n' + msg[ 'caption' ] if msg[ 'caption' ] else smile ,
			'reply_markup' : simple_markup_back_end
			}
		mes = await bot.send_photo( **args )
		print( 'photo detected' )

	elif 'document' in msg :
		args = {
			'chat_id'      : id_to_send ,
			'document'     : msg.document.file_id ,
			'caption'      : smile + '\n' + msg[ 'caption' ] if msg[ 'caption' ] else smile ,
			'reply_markup' : simple_markup_back_end

			}
		mes = await bot.send_document( **args )
		print( 'document detected' )

	elif 'video' in msg :
		args = {
			'chat_id'      : id_to_send ,
			'video'        : msg.video.file_id ,
			'caption'      : smile + '\n' + msg[ 'caption' ] if msg[ 'caption' ] else smile ,
			'reply_markup' : simple_markup_back_end

			}
		mes = await bot.send_video( **args )
		print( 'video detected' )

	elif 'video_note' in msg :
		args = {
			'chat_id'      : id_to_send ,
			'video_note'   : msg.video_note.file_id ,
			'reply_markup' : simple_markup_back_end

			}
		await bot.send_message( id_to_send , f'video from {smile}' )
		mes = await bot.send_video_note( **args )
		print( 'video detected' )

	elif 'sticker' in msg :
		args = {
			'chat_id'      : id_to_send ,
			'sticker'      : msg.sticker.file_id ,
			'reply_markup' : simple_markup_back_end

			}
		await bot.send_message( id_to_send , f'sticker from {smile}' )

		mes = await bot.send_sticker( **args )

	elif 'reply_to_message' in msg :
		msg = msg.reply_to_message
		if 'photo' in msg :
			# mes['photo']x
			print( msg[ 'photo' ][ len( msg.photo ) - 1 ].__dict__ )
			args = {
				'chat_id'      : id_to_send ,
				'photo'        : msg.photo[ len( msg.photo ) - 1 ][ 'file_id' ] ,
				'caption'      : smile + '\n' + msg[ 'caption' ] if msg[ 'caption' ] else smile ,
				'reply_markup' : simple_markup_back_end

				}
			mes = await bot.send_photo( **args )
			print( 'photo detected' )

		elif 'document' in msg :
			args = {
				'chat_id'      : id_to_send ,
				'document'     : msg.document.file_id ,
				'caption'      : smile + '\n' + msg[ 'caption' ] if msg[ 'caption' ] else smile ,
				'reply_markup' : simple_markup_back_end

				}
			mes = await bot.send_document( **args )
			print( 'document detected' )

		elif 'video' in msg :
			args = {
				'chat_id'      : id_to_send ,
				'video'        : msg.video.file_id ,
				'caption'      : smile + '\n' + msg[ 'caption' ] if msg[ 'caption' ] else smile ,
				'reply_markup' : simple_markup_back_end

				}
			mes = await bot.send_video( **args )
			print( 'video detected' )

		elif 'voice' in msg :
			# print( msg.to_python() )
			args = {
				'chat_id'      : id_to_send ,
				'voice'        : msg.voice.file_id ,
				'parse_mode'   : 'Markdown' ,
				'reply_markup' : simple_markup_back_end ,
				'caption'      : smile + '\n' + msg[ 'caption' ] if msg[ 'caption' ] else smile ,

				}
			await bot.send_voice( **args )

		elif 'video_note' in msg :
			args = {
				'chat_id'      : id_to_send ,
				'video_note'   : msg.video_note.file_id ,
				'reply_markup' : simple_markup_back_end

				}
			mes = await bot.send_video_note( **args )
			print( 'video detected' )
			await bot.send_message( id_to_send , f'video from {smile}' )

		elif 'sticker' in msg :
			args = {
				'chat_id'      : id_to_send ,
				'sticker'      : msg.sticker.file_id ,
				'reply_markup' : simple_markup_back_end

				}
			await bot.send_message( id_to_send , f'sticker from {smile}' )

			mes = await bot.send_sticker( **args )

		else :
			args = {
				'chat_id'      : id_to_send ,
				'text'         : smile + '\n' + msg.text ,

				'parse_mode'   : 'Markdown' ,
				'reply_markup' : simple_markup_back_end

				}
			mes = await bot.send_message( **args )

	elif 'text' in msg :
		args = {
			'chat_id'      : id_to_send ,
			'text'         : smile + '\n' + msg.text ,
			'parse_mode'   : 'Markdown' ,
			'reply_markup' : simple_markup_back_end

			}
		mes = await bot.send_message( **args )

	elif 'voice' in msg :
		# print(	msg.to_python())
		args = {
			'chat_id'      : id_to_send ,
			'voice'        : msg.voice.file_id ,
			'parse_mode'   : 'Markdown' ,
			'reply_markup' : simple_markup_back_end ,
			'caption'      : smile + '\n' + msg[ 'caption' ] if msg[ 'caption' ] else smile ,

			}
		await bot.send_voice( **args )
	else :
		# pp( msg.__dict__ )
		args = {
			'chat_id'      : id_to_send ,
			'text'         : smile + '\n' + msg.text ,
			'parse_mode'   : 'Markdown' ,
			'reply_markup' : simple_markup_back_end

			}
		mes = await bot.send_message( **args )


def get_accept_decline() :
	return inK( inB( 'Начать' , data=f'accept' ) , inB( 'Отмена' , data=f'decline' ) , row_width=1 )


def get_decline() :
	return inK( inB( 'Отмена' , data=f'decline' ) )


def get_max_mark( marks ) :
	maxcount = 0
	index = 0
	for mark , count in enumerate( marks ) :
		if count >= maxcount :
			maxcount = count
			index = mark

	return index , maxcount


def get_solo_review_text( review: Review ) :
	mark , maxcount = get_max_mark( review.mark )
	m = pre_text_solo_review.format( review.text , mark , maxcount )
	return m


def get_reviews_criteria_reply_markup() :
	mark = inK()
	mark.row( inB( 'Проголосовать' , data='vote' ) )
	mark.row( inB( 'Назад' , data='back' ) )
	return mark


def get_reviews_criteria( book ) :
	i = 0
	review = Review.objects( type=i , book=book ).first()
	mes = f'📖{book.article}\n'
	while review :
		mark , maxcount = get_max_mark( review.mark )

		mes += f'{review.text} *{mark}/10* ({maxcount} оценок)\n'
		i += 1
		try :
			review = Review.objects( type=i , book=book ).first()
		except :
			break
	# print(i,query)
	# mes += '\nВыбери критерий для оценки'
	return mes


def get_review_text( need_to_add=False ) :
	mes = pre_text_add_book if need_to_add else pre_text_review
	i = 0
	query = Review.objects( type=i ).first()

	while query :
		mes += f'\n{query.text}'
		i += 1
		try :
			query = Review.objects( type=i ).first()
		except :
			break
	# print(i,query)
	mes += '\nВыбери критерий для оценки'
	return mes


def get_reviews_text() :
	mes = pre_text_review
	i = 0
	query = Review.objects( type=i ).first()

	while query :
		mes += f'\n{query.text}'
		i += 1
		try :
			query = Review.objects( type=i ).first()
		except :
			break
	# print(i,query)
	mes += '\nВыбери критерий для оценки'
	return mes


def get_list_of_authors( count , autors ) :
	msg = ''
	# print(autors)
	for autor in autors[ count :count + 8 ] :
		# print(autor)
		msg += f'{count + 1}. {autor.name} {autor.surname} {autor.patronymic}\nВыбрать автора /autor_{autor.id}\n'
		count += 1

	return msg


def get_list_of_books( count , autor ) :
	msg = ''
	# print(autors)
	for book in autor.books[ count :count + 8 ] :
		# print(autor)
		msg += f'{count + 1}. {book.article}\nВыбрать книгу /book_{book.id}\n'
		count += 1

	return msg


def simple_keyboard( *buttons , row_width=2 , one_time_keyboard=True ) :
	mark = types.ReplyKeyboardMarkup( row_width=row_width , one_time_keyboard=one_time_keyboard , resize_keyboard=True )

	mark.add( *buttons )

	return mark


def simple_button( text , request_contact=False , request_location=False ) :
	return types.KeyboardButton( text , request_contact , request_location )


def inK( *buttons , row_width=3 ) :
	mark = types.InlineKeyboardMarkup( row_width=row_width )
	for button in buttons :
		mark.add( button )
	return mark


def inB( text , url=None , data=None ) :
	return types.InlineKeyboardButton( text=text , url=url , callback_data=data )


def getAddBookReply() :
	mark = simple_keyboard( one_time_keyboard=False )

	mark.row( simple_button( '🎓 Автор' ) , simple_button( '📔 Название' ) )
	mark.row( simple_button( '📚 Моя библиотека' ) , simple_button( '💬 Помощь' ) )
	return mark


def getMenuReply() :
	mark = simple_keyboard( one_time_keyboard=False )

	mark.row( simple_button( '🎓 Добавить книгу' ) , simple_button( '📔 Узнать о книге' ) )
	mark.row( simple_button( '📚 Моя библиотека' ) , simple_button( '💬 Помощь' ) )
	return mark


menu_reply_markup = getMenuReply()
menu_add_book_markup = getAddBookReply()


def get_review_type_markup( book ) :
	reviews = Review.objects( book=book )
	mark = inK()
	for x in range( 1 , len( reviews ) + 1 ) :
		mark.row( inB( str( x ) , data=str( x ) ) )

	mark.row( inB( '✍️ Написать свой' , data='new_review_text' ) ,
	          inB( '✅ Доб. критерий' , data='add_criteria_on_book' ) )

	mark.row( inB( '🎓 Добавить книгу' , data='add_book' ) )

	mark.row( inB( '❌️ Закончить' , data='start' ) )

	# print(mark.__dict__)
	return mark


def get_end_inline_markup() :
	mark = inK()
	mark.row( inB( '❌️ Закончить' , data='start' ) )
	return mark


def get_back_inline_markup() :
	mark = inK()
	mark.row( inB( '❌️ Закончить' , data='back' ) )
	return mark


def get_authors_markup( count , autorlist ) :
	mark = inK()
	for i , autor in enumerate( autorlist[ count :count + 8 ] ) :
		mark.row( inB( '{}. {} {}'.format( count + i + 1 , autor[ 0 ] , autor[ 1 ] ) , data=autor[ 2 ] ) )
	if count + 8 < len( autorlist ) :
		mark.row( inB( '>>' , data=f'page_{count + 8}' ) )
	if count >= 8 :
		mark.row( inB( '<<' , data=f'page_{count - 8}' ) )
	mark.row( inB( 'X' , data='start' ) )
	return mark


def get_books_from_collection( count , u: User ) :
	mark = inK()
	books_list = list( reversed( u.books ) )
	for i , book in enumerate( books_list[ count :count + 8 ] ) :
		mark.row( inB( '{}. {}'.format( count + i + 1 , book.article ) , data=str( book.id ) ) )
	if count + 8 < len( u.books ) :
		mark.row( inB( '>>' , data=f'page_{count + 8}' ) )
	if count >= 8 :
		mark.row( inB( '<<' , data=f'page_{count - 8}' ) )
	mark.row( inB( 'X' , data='start' ) )
	return mark


def get_books_of_autor( count , aut_id ) :
	aut = Autor.objects( id=aut_id ).first()
	print( aut )
	print( aut.books )
	mark = inK()
	aut.books = list( sorted( aut.books , key=lambda book_inside : book_inside.article ) )
	aut.save()
	for i , book in enumerate( aut.books[ count :count + 8 ] ) :
		mark.row( inB( '{}. {}'.format( count + i + 1 , book.article ) , data=str( book.id ) ) )
	if count + 8 < len( aut.books ) :
		mark.row( inB( '>>' , data=f'page_{count + 8}' ) )
	if count >= 8 :
		mark.row( inB( '<<' , data=f'page_{count - 8}' ) )
	mark.row( inB( 'X' , data='start' ) )
	return mark


def get_review_from_ten_markup() :
	mark = inK()
	for x in range( 1 , 11 ) :
		mark.row( inB( str( x ) , data=str( x ) ) )

	return mark


def get_simple_markup_with_add_book_end() :
	return simple_keyboard( simple_button( '🎓 Добавить книгу' ) , simple_button( '❌️ Закончить' ) ,
	                        one_time_keyboard=False )


def get_simple_markup_with_another_book() :
	return simple_keyboard( simple_button( '📔 Другая книга' ) , simple_button( '⬅️ Назад' ) , one_time_keyboard=False )


def get_simple_markup_on_criteria() :
	mark = simple_keyboard( one_time_keyboard=False )

	mark.row( simple_button( '✍️ Написать отзыв' ) , simple_button( '✅ Доб. критерий' ) )

	mark.row( simple_button( '🎓 Добавить книгу' ) , simple_button( '❌️ Закончить' ) )

	return mark


def get_books_by_name( count , book_name ) :
	mas = Book.objects( article__icontains=book_name ).order_by( 'article' )[ count :count + 8 ]

	mark = inK()
	for book in mas :
		mark.row( inB( book.article , data=str( book.id ) ) )
	if count + 8 < Book.objects( article__icontains=book_name ).count() :
		mark.row( inB( '>>' , data=f'page_{count + 8}' ) )
	if count >= 8 :
		mark.row( inB( '<<' , data=f'page_{count - 8}' ) )

	mark.row( inB( '❌️ Закончить' , data='start' ) )
	return mark


def get_book_reviews( count , reviews ) :
	mark = inK()
	if count + 1 < len( reviews ) :
		mark.row( inB( '>>' , data=f'watch_reviews_from_web_{count + 1}' ) )
	if count >= 1 :
		mark.row( inB( '<<' , data=f'watch_reviews_from_web_{count - 1}' ) )
	mark.row( inB( '❌️ Закончить' , data='back' ) )
	return mark


def get_book_reviews_from_users( count , reviews ) :
	mark = inK()
	if count + 1 < len( reviews ) :
		mark.row( inB( '>>' , data=f'reviews_of_users_{count + 1}' ) )
	if count >= 1 :
		mark.row( inB( '<<' , data=f'reviews_of_users_{count - 1}' ) )

	mark.row( inB( '❌️ Закончить' , data='back' ) )
	return mark


def get_simple_markup_back_end() :
	mark = simple_keyboard( one_time_keyboard=False )

	mark.row( simple_button( '⬅️ Назад' ) , simple_button( '❌️ Закончить' ) )

	return mark


def get_simple_markup_end() :
	mark = simple_keyboard( one_time_keyboard=False )

	mark.row( simple_button( '❌️ Закончить' ) )

	return mark


def get_inline_markup_with_actions( delete=False ) :
	mark = inK()

	mark.row( inB( '📣 Отзывы' , data=f'watch_reviews_from' ) )
	mark.row( inB( '💬 Обсудить' , data='go_into_conversation' ) )
	if delete :
		mark.row( inB( '🗑 Удалить' , data='delete' ) )
	else :
		mark.row( inB( '⏹ Закончить' , data='start' ) )

	return mark


def get_inline_list( count , list_of_objects: [ ReviewsToAdd ] ) :
	mark = inK()
	for obj in list_of_objects[ count :count + 8 ] :
		# print(obj.text)
		mark.row( inB( '{} - {}'.format( obj.count , obj.text ) , data=str( obj.id ) ) )

	if count + 8 < len( list_of_objects ) :
		mark.row( inB( '>>' , data=f'page_{count + 8}' ) )
	if count >= 8 :
		mark.row( inB( '<<' , data=f'page_{count - 8}' ) )
	mark.row( inB( '❌️ Закончить' , data='start' ) )
	return mark


def get_inline_markup_reviews() :
	mark = inK()
	mark.row( inB( '💻 Отзывы с bokmate.ru, litres.ru и т.д.' , data=f'watch_reviews_from_web_0' ) )
	mark.row( inB( '💬 Отзывы наших пользователей' , data='reviews_of_users_0' ) )
	mark.row( inB( '📝 Отзывы по критериям' , data='reviews_by_criterias' ) )
	mark.row( inB( 'Назад' , data='back' ) )

	return mark


def get_inline_markup_autor_nazvanie() :
	mark = inK()
	mark.row( inB( 'По автору' , data='autor' ) , inB( 'По названию' , data='title' ) )
	return mark


inline_markup_autor_nazvanie = get_inline_markup_autor_nazvanie()
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
accept_decline_markup = get_accept_decline()
reviews_criteria_reply_markup = get_reviews_criteria_reply_markup()
text_in_main = [ ]

decline_markup = get_decline()

for row in menu_reply_markup[ 'keyboard' ] :
	for button in row :
		text_in_main.append( button.text )

text_in_add_book = [ ]

for row in menu_add_book_markup[ 'keyboard' ] :
	for button in row :
		text_in_add_book.append( button.text )


class Timer :
	def __init__( self , timeout , callback ) :
		self._timeout = timeout
		self._callback = callback
		self._task = asyncio.ensure_future( self._job() )

	async def _job( self ) :
		await asyncio.sleep( self._timeout )
		await self._callback()

	def cancel( self ) :
		self._task.cancel()


async def timeout_callback() :
	await asyncio.sleep( 0.1 )
	print( 'echo!' )

# import datetime
# from pprint import pprint
#
# begin_searching = datetime.datetime.now()
# while True:
# 	pprint((datetime.datetime.now()-begin_searching).seconds)
