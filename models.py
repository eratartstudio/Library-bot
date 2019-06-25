import datetime

import mongoengine
import random
import requests as re
from bs4 import BeautifulSoup
from mongoengine import queryset_manager

from conf import url , db_name , emodzi_list

mongoengine.connect( db_name , host=url )


def get_html( url ) :
	response = re.get( url )
	return response.text


class User( mongoengine.Document ) :
	# id = mongoengine.ReferenceField(Posts,primary_key=True)
	user_id = mongoengine.IntField()
	username = mongoengine.StringField()
	phone = mongoengine.StringField()
	books = mongoengine.ListField( mongoengine.ReferenceField( 'Book' , reverse_delete_rule=mongoengine.DO_NOTHING ) )
	# orders = mongoengine.StringField()
	time_started = mongoengine.DateTimeField( default=datetime.datetime.now() )
	in_conversation = mongoengine.BooleanField( default=False )
	waits_conversation = mongoengine.BooleanField( default=False )

	@queryset_manager
	def get_available( doc_cls , queryset ) :

		return queryset.filter( in_conversation=False , waits_conversation=False )

	def chat_waiting( self ) :
		self.in_conversation = False
		self.waits_conversation = True
		self.save()

	def connect_chat( self ) :
		self.in_conversation = True
		self.waits_conversation = False
		self.save()

	def disconnect_chat( self ) :
		self.in_conversation = False
		self.waits_conversation = False
		self.save()

	def get_litres_reviews_library( self ) :
		for book in self.books :
			if not book.litres_reviews_ids :
				book.get_review_list_litres()


class Review( mongoengine.Document ) :
	type = mongoengine.IntField()
	text = mongoengine.StringField()
	book = mongoengine.ReferenceField( 'Book' , reverse_delete_rule=mongoengine.DO_NOTHING )
	mark = mongoengine.ListField( default=[ 0 for x in range( 11 ) ] )
	voted = mongoengine.DictField()


class Book( mongoengine.Document ) :
	meta = {
		'strict' : False
		}

	url = mongoengine.StringField()
	article = mongoengine.StringField()
	autor = mongoengine.ReferenceField( 'Autor' , reverse_delete_rule=mongoengine.DO_NOTHING )
	reviews = mongoengine.ListField( mongoengine.ReferenceField( 'Review' , reverse_delete_rule=mongoengine.CASCADE ) )
	url_litres = mongoengine.StringField()
	url_bookmate = mongoengine.StringField()
	litres_reviews = mongoengine.ListField()
	all_reviews = mongoengine.ListField()
	bookmate_parsed = mongoengine.BooleanField( default=False )

	def get_impressions_bookmate( self ) :

		if not self.bookmate_parsed :
			url_proto = f'https://ru.bookmate.com/api/v5/books/{self.url_bookmate.split("/")[-1]}/impressions'  # {book_uuid}
			response = re.get( url=url_proto )
			data = response.json()
			title_of_impression = f'📖{self.article}\n'

			self.all_reviews += list(
					title_of_impression + impression[ 'content' ] for impression in data[ 'impressions' ] if
					impression[ 'content' ].replace( ' ' , '' ) )
			self.bookmate_parsed = True
			self.save()
		return self.all_reviews

	def form_link_litres( self ) :
		small_url = 'https://www.litres.ru'

		search_url = 'https://www.litres.ru/pages/rmd_search_arts/?q={}'.format(
				(self.autor.name + ' ' + self.article).replace( ' ' , '+' ) )

		html = get_html( search_url )
		soup = BeautifulSoup( html , 'lxml' )
		book_ent = soup.select( 'div.art-item__name' )
		for obj in book_ent :
			if obj[ 'class' ] == [ 'art-item__name' ] and self.article in obj.contents[ 0 ][ 'title' ] :
				return small_url + obj.contents[ 0 ][ 'href' ]

	def get_review_text( self , list_ ) :
		text = f'📖{self.article}\n'
		reviews = [ ]

		for child in list_ :
			child = str( child )
			# print(child[:3],child[-4:])
			if child[ :3 ] == '<p>' and child[ -4 : ] == '</p>' and not '<i>' in child :
				text += '\n' + child[ 3 :-4 ]
		# elif '<i>' in child:
		#     text = child[child.find('<i>')+3:child.find('</i>')]  + '\n' + text
		text = text.replace( '<br/>' , '\n' )
		return text

	def get_review_list_litres( self ) :
		if not self.url_litres :
			url_litres = self.form_link_litres()
			url_to_search = url_litres + 'otzivi/page-4/'
			self.update( url_litres=url_litres )
		else :
			url_to_search = self.url_litres + 'otzivi/page-4/'

		html = get_html( url_to_search )
		print( url_to_search )
		# print('is it captcha?\n',html)
		soup = BeautifulSoup( html , 'lxml' )
		# for i in
		reviews = [ ]
		for x in soup.select( 'div.recense_content' ) :
			# print(x.findChildren())
			reviews.append( self.get_review_text( x.findChildren() ) )

		self.update( litres_reviews=reviews )
		# self.litres_reviews = reviews
		# self.save()
		return Book.objects( id=self.id ).first()

	def create_reviews( self ) :
		if len( Review.objects( book=self ) ) == 0 :
			list_of_reviews = [ 'Легко читается' , 'Требует усилий / тяжело читается' , 'Интересный сюжет' ,
			                    'Держит внимание до конца' ]
			for i , val in enumerate( list_of_reviews ) :
				text = '{}. {}'.format( i + 1 , val )
				review = Review( type=i , text=text , book=self )
				review.save()
				self.update( reviews=self.reviews.append( review ) )


class Autor( mongoengine.Document ) :
	url = mongoengine.StringField()
	name = mongoengine.StringField()
	surname = mongoengine.StringField()
	patronymic = mongoengine.StringField()
	books = mongoengine.ListField( mongoengine.ReferenceField( Book , reverse_delete_rule=mongoengine.DO_NOTHING ) ,
	                               reverse_delete_rule=mongoengine.DO_NOTHING )
	url_litres = mongoengine.StringField()
	url_bookmate = mongoengine.StringField()

	def add_book( self , book: Book ) :
		self.books.append( book )
		self.save()


class ReviewsToAdd( mongoengine.Document ) :
	count = mongoengine.IntField()
	text = mongoengine.ListField()


class Chats( mongoengine.Document ) :
	creator_id = mongoengine.IntField()
	invited_users = mongoengine.ListField()
	connected_users = mongoengine.ListField()
	book_id = mongoengine.StringField()
	smiles = mongoengine.DictField()  # associate id with emodzi
	creation_date = mongoengine.DateField( default=datetime.datetime.now() )
	visited = mongoengine.BooleanField( default=False )
	out_of_time = mongoengine.BooleanField( default=False )

	def close( self ) :
		for user in self.invited_users :
			user.disconnect_chat()
		self.delete()

	def disconnect_user( self , user ) :
		user.disconnect_chat()
		if user in self.connected_users :
			self.connected_users.remove( user )
		self.save()

	def get_emodzi( self ) :
		smile_list = random.sample( emodzi_list , k=len( self.invited_users ) + 1 )
		for ind , user in enumerate( self.invited_users ) :
			self.smiles[ str( user.user_id ) ] = smile_list[ ind ]

		self.smiles[ str( self.creator_id ) ] = smile_list[ -1 ]

		self.save()
		return self.smiles

	def time_out( self ) :
		self.out_of_time = True
		self.save()

	@queryset_manager
	def get_not_visited( doc_cls , queryset ) :

		return queryset.filter( visited=False , out_of_time=True )
