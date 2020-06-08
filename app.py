#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    genres = db.Column(db.ARRAY(db.String(120)))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False, nullable=True)
    seeking_description = db.Column(db.Text)
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self): # Add to class if you want print debugging statements
        return f'<Venue: {self.id} {self.name}>'


class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False, nullable=True)
    seeking_description = db.Column(db.Text)
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f'<Venue: {self.id} {self.name}>'


class Show(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    venue_id  = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, default= datetime.today())


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def fix_json_array(obj, attr):
    arr = getattr(obj, attr)
    if isinstance(arr, list) and len(arr) > 1 and arr[0] == '{':
        arr = arr[1:-1]
        arr = ''.join(arr).split(",")
        setattr(obj,attr, arr)



def format_datetime(value, format='medium'):
  date = value   # was dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#----------------------------------------------------------------------------#
#  Venues
#----------------------------------------------------------------------------#

@app.route('/venues')
def venues():
  areas = Venue.query.distinct('city','state').all()
  def format_data(area):
    venues = Venue.query.filter_by(city=area.city,state=area.state).all()
    def format_venues(venue):
      shows = venue.shows
      upcoming_shows = [show for show in shows if show.start_time >= datetime.today()]
      return {
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(upcoming_shows)
      }
    return {
      "city": area.city,
      "state": area.state,
      "venues": list(map(lambda venue: format_venues(venue=venue), venues))
    }
  data = list(map(lambda area: format_data(area=area), areas))

  return render_template('pages/venues.html', areas=data)


#  Search Venue
#  ----------------------------------------------------------------
@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term').lower()
  search= "%{}%".format(search_term)
  data = Venue.query.filter(Venue.name.ilike(search)).all()
  count = Venue.query.filter(Venue.name.ilike(search)).count()

  def format_search(venue):
      return {
        "id": venue.id,
        "name": venue.name,
      }

  response = {
    "data":list(map(lambda d: format_search(venue=d), data)),
    "count":count}

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


#  Show Venue
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Fixing genres display
  record = Venue.query.get(venue_id)
  fix_json_array(record, "genres")
    # Getting basic
  data = Venue.query.get(venue_id)
  venue = Venue.query.filter_by(id=venue_id).first()
  shows = Show.query.filter_by(artist_id=venue_id).all()
    # Counting past and upcoming shows
  past_shows = upcoming_shows = []
  count_past = count_upcoming = 0
  for show in shows:
      if show.start_time < datetime.today():
          count_past += 1
      elif show.start_time >= datetime.today():
          count_upcoming += 1
    # Getting upcoming shows
  upcoming_shows=db.session.query(Show).filter(Show.start_time >= datetime.today().date()).filter_by(venue_id=venue_id).all()

  def get_upcoming_shows(show):
      return {
        "artist_image_link": show.artist.image_link,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "start_time": show.start_time,
      }
    # Getting past shows
  past_shows=db.session.query(Show).filter(Show.start_time < datetime.today().date()).filter_by(venue_id=venue_id).all()

  def get_past_shows(show):
      return {
        "artist_image_link": show.artist.image_link,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "start_time": show.start_time,
      }
    # Displaying all data
  data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "city": venue.city,
        "state": venue.state,
        "address": venue.address,
        "phone": venue.phone,
        "website_link": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": list(map(lambda d: get_past_shows(show=d), past_shows)),
        "upcoming_shows": list(map(lambda d: get_upcoming_shows(show=d), upcoming_shows)),
        "past_shows_count": count_past,
        "upcoming_shows_count": count_upcoming
    }

  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        form = VenueForm()
        venue1 = Venue(name = form.name.data, city = form.city.data, state = form.state.data, address = form.address.data, phone = form.phone.data, genres = form.genres.data, facebook_link = form.facebook_link.data)
        db.session.add(venue1)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except: flash('An error occurred. Venue could not be listed.')
    return render_template('pages/home.html', form=form)


#  Delete Venue
#  ----------------------------------------------------------------
@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
  venue_to_delete = Venue.query.get(venue_id)
  try:
      db.session.delete(venue_to_delete)
      db.session.commit()
      flash('Deleted!')
  except:
      flash('There was a problem deleting that venue')
  return redirect('/')


#  Edit Venue GET
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm()
  form.name.data = venue.name
  form.state.data = venue.state
  form.city.data = venue.city
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.website.data = venue.website
  form.genres.data = venue.genres
  form.facebook_link.data = venue.facebook_link
  return render_template('forms/edit_venue.html', form=form, venue=venue)


#  Edit Venue POST
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm()
  venue.name = form.name.data
  venue.state = form.state.data
  venue.city = form.city.data
  venue.address = form.address.data
  venue.phone = form.phone.data
  venue.website = form.website.data
  venue.genres = form.genres.data
  venue.facebook_link = form.facebook_link.data
  db.session.commit()
  return redirect(url_for('show_venue', venue_id=venue_id))


#----------------------------------------------------------------------------#
#  Artists
#----------------------------------------------------------------------------#
@app.route('/artists')
def artists():
  data=Artist.query.all()
  return render_template('pages/artists.html', artists=data)


#  Search Artist
#  ----------------------------------------------------------------
@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term').lower()
  search= "%{}%".format(search_term)
  data = Artist.query.filter(Artist.name.ilike(search)).all()
  count = Artist.query.filter(Artist.name.ilike(search)).count()

  def format_search(artist):
      return {
        "id": artist.id,
        "name": artist.name,
      }
  response = {
    "data":list(map(lambda d: format_search(artist=d), data)),
    "count":count}

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


#  Show Artist
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # Fixing genres display
  record = Artist.query.get(artist_id)
  fix_json_array(record, "genres")
    # Getting basic
  data = Artist.query.get(artist_id)
  artist = Artist.query.filter_by(id=artist_id).first()
  shows = Show.query.filter_by(venue_id=artist_id).all()
    # Counting past and upcoming shows
  past_shows = upcoming_shows = []
  count_past = count_upcoming = 0
  for show in shows:
      if show.start_time < datetime.today():
          count_past += 1
      elif show.start_time >= datetime.today():
          count_upcoming += 1
    # Getting upcoming shows
  upcoming_shows=db.session.query(Show).filter(Show.start_time >= datetime.today().date()).filter_by(artist_id=artist_id).all()
  def get_upcoming_shows(show):
      return {
        "venue_image_link": show.venue.image_link,
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "start_time": show.start_time,
      }
    # Getting past shows
  past_shows=db.session.query(Show).filter(Show.start_time < datetime.today().date()).filter_by(artist_id=artist_id).all()
  def get_past_shows(show):
      return {
        "venue_image_link": show.venue.image_link,
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "start_time": show.start_time,
      }
    # Displaying all data
  data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website_link": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": list(map(lambda d: get_past_shows(show=d), past_shows)),
        "upcoming_shows": list(map(lambda d: get_upcoming_shows(show=d), upcoming_shows)),
        "past_shows_count": count_past,
        "upcoming_shows_count": count_upcoming
    }
  return render_template('pages/show_artist.html', artist=data)


#  Update Artist GET
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist=Artist.query.get(artist_id)
  form = ArtistForm()
  form.name.data = artist.name
  form.state.data = artist.state
  form.city.data = artist.city
  form.phone.data = artist.phone
  form.website.data = artist.website
  form.genres.data = artist.genres
  form.facebook_link.data = artist.facebook_link
  return render_template('forms/edit_artist.html', form=form, artist=artist)


#  Update Artist POST
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist=Artist.query.get(artist_id)
  form = ArtistForm()
  artist.name = form.name.data
  artist.state = form.state.data
  artist.city = form.city.data
  artist.phone = form.phone.data
  artist.website = form.website.data
  artist.genres = form.genres.data
  artist.facebook_link = form.facebook_link.data
  db.session.commit()
  return redirect(url_for('show_artist', artist_id=artist_id))

#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
      form = ArtistForm()
      artist1 = Artist(name = form.name.data, city = form.city.data, state = form.state.data, phone = form.phone.data, genres = form.genres.data, facebook_link = form.facebook_link.data)
      db.session.add(artist1)
      db.session.commit()
      flash('Artist ' + form.name.data + ' was successfully listed!')
  except:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  return render_template('pages/home.html', form=form)


#----------------------------------------------------------------------------#
#  Shows
#----------------------------------------------------------------------------#

@app.route('/shows')
def shows():
        # Shows all
  shows=db.session.query(Show).all()
        # Shows just upcoming Shows
  shows=db.session.query(Show).outerjoin(Venue, Venue.id == Show.venue_id).filter(Show.start_time >= datetime.today().date()).order_by(Venue.id).all()
  return render_template('pages/shows.html', shows=shows)   # First show from html, second froum route


#  Create Show
#  ----------------------------------------------------------------
@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
      form = ShowForm()
      show = Show(artist_id = form.artist_id.data, venue_id = form.venue_id.data, start_time = form.start_time.data)
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed!')
  except: flash('An error occurred. Show could not be listed.')
  return render_template('pages/home.html', form=form)


#----------------------------------------------------------------------------#
#  For errors
#----------------------------------------------------------------------------#

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
