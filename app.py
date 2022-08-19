#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from pickle import UNICODE
from tokenize import String
from itertools import groupby
from operator import attrgetter
from unittest.case import _AssertRaisesContext
from sqlalchemy import func
import numpy as np

import unicodedata
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.types import ARRAY
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from config import *
from sqlalchemy.dialects.postgresql import ARRAY

from flask_migrate import Migrate
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI']=SQLALCHEMY_DATABASE_URI
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'
   

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=True)
    city = db.Column(db.String(120), nullable=True)
    state = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(120), nullable=True)
    genres = db.Column(db.String(), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=True)
    image_link = db.Column(db.String(500), nullable=True)
    website_link = db.Column(db.String(500), nullable=True)
    # seeking_talent=db.Column(db.Boolean())
    seeking_description = db.Column(db.Text, nullable=True)
    seeking_talent = db.Column(db.Boolean, nullable=True, default=False)
    upcoming_shows_count = db.Column(db.Integer, nullable=True, default=0)
    past_shows_count = db.Column(db.Integer,nullable=True, default=0)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=True)
    city = db.Column(db.String(120), nullable=True)
    state = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(120), nullable=True)
    genres = db.Column(db.String(), nullable=False)

    # genres = db.Column(ARRAY(db.String), default=[])
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)
    seeking_description = db.Column(db.String, nullable=True)
    website_link = db.Column(db.String(120), nullable=True)
    seeking_venue = db.Column(db.Boolean, nullable=True, default=False)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = "shows"
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    start_time = db.Column(db.DateTime(timezone=True))
    artist = db.relationship("Artist",
                             backref=db.backref("shows",
                                                cascade="all, delete-orphan"))
    venue = db.relationship("Venue",
                            backref=db.backref("shows",
                                               cascade="all, delete-orphan"))
    artist_id = db.Column(db.Integer,
                          db.ForeignKey('Artist.id'),
                          nullable=False)
    future = db.Column(db.Boolean, nullable=False, default=True)


db.create_all()

migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data=[]

    data_query=db.session.query(Venue.city,Venue.state).group_by(Venue.state,Venue.city).all()
    def append_venues(venue):
        data[-1]["venues"].append({"id":venue[0],"name":venue[1],"upcoming_shows_count":venue[2]})

    def venue_list(lists):
        lists_venue=db.session.query(Venue.id,Venue.name,Venue.upcoming_shows_count).filter(Venue.city==lists[0],Venue.state==lists[1]).all()
        data.append({"city":lists[0],"state":[lists[1]],"venues":[]})
        # map(append_venues,lists_venue)
       
        [append_venues(venue) for venue in lists_venue]
   
    [venue_list(lists) for lists in data_query]
    # map(venue_list,data_query)
    # data_query = db.session.query(Venue.city,
    #                         Venue.state).group_by(Venue.state,
    #                                               Venue.city).all()
    # data = []
    # for lists in data_query:
    #     list_vnu = db.session.query(Venue.id, Venue.name,
    #                               Venue.upcoming_shows_count).filter(
    #                                   Venue.city == lists[0],
    #                                   Venue.state == lists[1]).all()
    #     data.append({"city": lists[0], "state": lists[1], "venues": []})
    #     for venue in list_vnu:
    #         data[0]["venues"].append({
    #             "id": venue[0],
    #             "name": venue[1],
    #             "num_upcoming_shows": venue[2]
    #         })

    return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  query_result=Venue.query.filter(Venue.name.contains(request.form['search_term'])).all()
  results_response={"count":len(query_result),"data":[]}
  def response(V):
    results_response["data"].append({"id":V.id,"name":V.name,"upcoming_shows_count":V.upcoming_shows_count})
  [response(v) for v in query_result]


  return render_template('pages/search_venues.html', results=results_response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
    
    venue_response=Venue.query.get(venue_id)
    previous_shows=[]
    future_shows=[]
    shows_result=venue_response.shows
    def show_info(show):
        show_list={"artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)}
        if (show.upcoming):
            future_shows.append(show_list)
        else:
            previous_shows.append(show_list)
    [show_info(shows) for shows in shows_result]
    
    data_venue=  {
        "id": venue_response.id,
        "name": venue_response.name,
        "genres": venue_response.genres.split(','),
        "address": venue_response.address,
        "city": venue_response.city,
        "state": venue_response.state,
        "phone": venue_response.phone,
        "website_link": venue_response.website_link,
        "facebook_link": venue_response.facebook_link,
        "seeking_talent": venue_response.seeking_talent,
        "seeking_description": venue_response.seeking_description,
        "image_link": venue_response.image_link}
    data_shows={
        "past_shows": previous_shows,
        "upcoming_shows": future_shows,
        "past_shows_count": len(previous_shows),
        "upcoming_shows_count": len(future_shows)
    }
    data =data_venue.update(data_shows)
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  data=request.form

  Venue.name = data['name']
  Venue.city = data['city']
  Venue.state = data['state']
  Venue.address = data['address']
  Venue.phone = data['phone']
  Venue.facebook_link = data['facebook_link']
  Venue.genres = data['genres']
  Venue.website_link = data['website_link']
  Venue.image_link = data['image_link']

  venue=Venue(**data)
  try:
    db.session.add(venue)
    db.session.commit()
  

    # on successful db insert, flash success
    flash('Venue ' + data['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
  # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + data['name']+ ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
        
    except:
        db.session.rollback()
        
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
    return redirect(url_for('index'))
 
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data =[]
  # queyd = Artist.query.all()
  # for list in queyd:
  #       data.append({"id": list[0], "name": list[1]})


  # queyd=db.session.query(Artist.id,Artist.name).group_by(Artist.id,Artist.name).all()
  # def append_artist(artist):
  #       data[-1]["venues"].append({"id":artist[0],"name":artist[1],"upcoming_shows_count":artist[2]})
  # [append_artist(artist) for artist in queyd]
  # queyd = db.session.query(Artist).all()
  # for list in queyd:
  #           data["data"].append({"id":list.id,"name":list.name})
  # print(data)
  # queyd = Artist.query.all()
  # data =[]
  # for list in queyd:
  #       data.append({"id": list[0], "name": list[1]})
  data=Artist.query.with_entities(Artist.id, Artist.name).all()



  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  artists_result=Artist.query.filter(Artist.name.contains(request.form['search_term'])).all()
  artists_response={"count":len(artists_result),"data":[]}
  def response(resp):
    artists_response["data"].append({"id":resp.id,"name":resp.name,"upcoming_shows_count":resp.num_upcoming_shows})
  [response(results) for results in artists_result]
  return render_template('pages/search_artists.html', results=artists_response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist_response=Artist.query.get(artist_id)
  previous_shows=[]
  future_shows=[]
  shows_result=artist_response.shows
  def show_info(show):
    show_list={"venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": str(show.start_time)}
    if (show.upcoming):
        future_shows.append(show_list)
    else:
        previous_shows.append(show_list)
    [show_info(shows) for shows in shows_result]

  data_artist = {
        "id": artist_response.id,
        "name": artist_response.name,
        "genres": artist_response.genres.split(','),
        "city": artist_response.city,
        "state": artist_response.state,
        "phone": artist_response.phone,
        "website": artist_response.website_link,
        "facebook_link": artist_response.facebook_link,
        "seeking_venue": artist_response.seeking_venue,
        "seeking_description": artist_response.seeking_description,
        "image_link": artist_response.image_link}

  data_shows={
    "past_shows": previous_shows,
    "upcoming_shows": future_shows,
    "past_shows_count": len(previous_shows),
    "upcoming_shows_count": len(future_shows)
    }
  data =data_artist.update(data_shows)
  print(data)


  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    
    form = ArtistForm()
    artist=Artist.query.get(artist_id)

    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    data=request.form
    artist=Artist.query.get(artist_id)
    artist=Artist(**data)
    try:
        db.session.update(artist)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
        

    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue=Venue.query.get(venue_id)

  
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    data=request.form
    venue=Artist.query.get(venue_id)
    venue=Artist(**data)
    try:
        db.session.add(venue)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  data=request.form
  Artist.name = data['name']
  Artist.city = data['city']
  Artist.state = data['state']
  Artist.genres = data['genres']
  Artist.phone = data['phone']
  Artist.facebook_link = data['facebook_link']
  Artist.image_link = data['image_link']
  artist=Artist(**data)
  try:
      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + artist.name +
            ' could not be listed.')
  finally:
      db.session.close()

  # on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows_list = Show.query.all()
  data = []
  def shows_coming(show_info):
    if (show_info.upcoming):
      data.append({
          "venue_id": show_info.venue_id,
          "venue_name": show_info.venue.name,
          "artist_id": show_info.artist_id,
          "artist_name": show_info.artist.name,
          "artist_image_link": show_info.artist.image_link,
          "start_time": str(show_info.start_time)
      })

  [shows_coming(shows) for shows in shows_list]
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  data=request.form
  Show.artist_id = data['artist_id']
  Show.venue_id = data['venue_id']
  dateAndTime = data['start_time'].split(' ')
  Date_List = dateAndTime[0].split('-')
  Date_List += dateAndTime[1].split(':')
  for i in range(len(Date_List)):
      Date_List[i] = int(Date_List[i])
  Show.start_time = datetime(Date_List[0], Date_List[1], Date_List[2], Date_List[3],
                                  Date_List[4], Date_List[5])
  now = datetime.now()
  Show.future = (now < Show.start_time)
  show=Show(**data)
  try:
      db.session.add(show)
      # update venue and artist table
      sh_artist = Artist.query.get(Show.artist_id)
      sh_venue = Venue.query.get(Show.venue_id)
      if (Show.upcoming):
          sh_artist.upcoming_shows_count += 1
          sh_venue.upcoming_shows_count += 1
      else:
          sh_artist.past_shows_count += 1
          sh_venue.past_shows_count += 1
      # on successful db insert, flash success
      db.session.commit()
      flash('Show was successfully listed!')
  except:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      flash(
          'Show could not be listed. please make sure that your ids are correct'
      )
  finally:
      db.session.close()

  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
