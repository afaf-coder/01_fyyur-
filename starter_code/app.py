#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import datetime
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from sqlalchemy import func
from flask_migrate import Migrate
import phonenumbers
from wtforms.validators import ValidationError

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
from forms import ArtistForm, VenueForm, ShowForm

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500), nullable=True)
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
      return self.city

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500), nullable=True)
    shows = db.relationship('Show', backref='artist', lazy=True)

class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  startTime = db.Column(db.DateTime, nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

def phone_validation(number):
  parsed_num = phonenumbers.parse(number, "US")
  if not phonenumbers.is_valid_number(parsed_num):
    raise ValidationError('Invalid phone number.')

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
  city_state_pair = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  print(city_state_pair)
  data=[]
  for pair in city_state_pair:
    venues = Venue.query.filter(Venue.city==pair[1]).all()
    venues_data = []
    for venue in venues:
      venues_data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(Show.query.filter(Show.venue_id==venue.id).filter(Show.startTime>datetime.now()).all())
      })
    data.append({
      "city":pair[1],
      "state": pair[2],
      "venues": venues_data
    })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term')
    result = Venue.query.filter(Venue.name.ilike('%'+search_term+'%')).all()
    data = []
    for venue in result:
      upcoming_shows = Show.query.filter(Show.venue_id == venue.id).filter(Show.startTime > datetime.now()).all()
      data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(upcoming_shows) 
      })

    response = {
        "count": len(result),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = Venue.query.get(venue_id)

  if not venue:
      return render_template('errors/404.html')

  venue_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).all()

  current_time = datetime.now()
  past_shows = []
  upcoming_shows = []

  for show in venue_shows:
      if show.start_time < current_time:
          past_shows.append({
              "artist_id": show.artist_id,
              "artist_name": show.artist.name,
              "artist_image_link": show.artist.image_link,
              "start_time": show.start_time.strftime(' %y-%m-%d  %H:%M:%S ')
          })
      else:
          upcoming_shows.append({
              "artist_id": show.artist_id,
              "artist_name": show.artist.name,
              "artist_image_link": show.artist.image_link,
              "start_time": show.start_time.strftime(' %y-%m-%d  %H:%M:%S ')
          })

  data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
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
    error=False
    try:
        name = request.form.get('name')
        city = request.form.get('city')
        state = request.form.get('state')
        address = request.form.get('address')
        phone = request.form.get("phone")
        genres = request.form.get("genres")
        seeking_talent = request.form.get("seeking_talent") == "y"
        seeking_description = request.form.get("seeking_description ")
        image_link = request.form.get(" image_link ")
        website = request.form.get(" website ")
        facebook_link = request.form.get('facebook_link')
        venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres,seeking_talent =seeking_talent,
                     seeking_description=seeking_description, image_link = image_link ,website =website , facebook_link=facebook_link)
        db.session.add(venue)
        db.session.commit()
    except Exception as e :
        print(e)
        error= True
        db.session.rollback()
    finally:
        db.session.close()
        if error:
            flash('error')
        else:
            flash('venue added')
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error=False
    try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.commit()
    except Exception as e :
        print(e)
        error= True
        db.session.rollback()
    finally:
        db.session.close()
        if error:
            flash('error')
        else:
            flash('venue deleted')
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    result = Artist.query.filter(Artist.name.ilike(f"%{request.form.get('search_term')}%")).all()
    response = {
        "count": len(result),
        "data": result
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  if not artist:
      return render_template('errors/404.html')

  artist_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).all()

  current_time = datetime.now()
  past_shows = []
  upcoming_shows = []


  for show in artist_shows:
      if show.start_time < current_time:
          past_shows.append({
              "venue_id": show.venue_id,
              "venue_name": show.venue.name,
              "venue_image_link": show.venue.image_link,
              "start_time": show.start_time.strftime(' %y-%m-%d  %H:%M:%S ')
          })
      else:
          upcoming_shows.append({
              "venue_id": show.venue_id,
              "venue_name": show.venue.name,
              "venue_image_link": show.venue.image_link,
              "start_time": show.start_time.strftime(' %y-%m-%d  %H:%M:%S ')
          })


  data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  form = ArtistForm()
  artist = Artist.query.filter_by(id=artist_id).first()
  form.genres.default = artist.genres
  form.state.default = artist.state
  form.process()
  form.name.data = artist.name
  form.city.data = artist.city
  form.phone.data = artist.phone
  form.address.data = artist.address
  form.website.data = artist.website
  form.facebook_link.data = artist.facebock_link
  form.seeking_talent.data = artist.seeking_talent
  form.sseeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  try:
      artistForm = ArtistForm()
      artist = Artist.query.filter_by(id=artist_id).first()
      phone_validation(artistForm.phone.data)
      artist.name = artistForm.name.data
      artist.city = artistForm.city.data
      artist.state =artistForm.state.data
      artist.phone = artistForm.phone.data
      artist.genres = artistForm.genres.data
      artist.website = artistForm.website.data
      artist.facebook_link = artistForm.facebook_link.data
      artist.seeking_venue = artistForm.seeking_venue.data
      artist.seeking_desc = artistForm.seeking_desc.data
      artist.image_link = artistForm.image_link.data

      db.session.commit()
  except:
      error = True
      db.session.rollback()
      flash('An error in Artist ' + request.form['name'] + ' was not  updated.')
  finally:
      db.session.close()
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).first()
  form.genres.default = venue.genres
  form.state.default = venue.state
  form.process()
  form.name.data = venue.name
  form.city.data = venue.city_name
  form.phone.data = venue.phone
  form.address.data = venue.address
  form.website.data = venue.website
  form.facebook_link.data = venue.facebock_link
  form.seeking_talent.data = venue.seeking_talent
  form.sseeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  try:
      venueForm = VenueForm()
      venue = Venue.query.filter_by(id=venue_id).first()
      phone_validation(venueForm.phone.data)
      venue.name = venueForm.name.data
      venue.city_name = venueForm.city.data
      venue.state = venueForm.state.data
      venue.phone = venueForm.phone.data
      venue.address = venueForm.address.data
      venue.genres = venueForm.genres.data
      venue.website = venueForm.website.data
      venue.facebook_link = venueForm.facebook_link.data
      venue.seeking_talent = venueForm.seeking_talent.data
      venue.seeking_desc = venueForm.seeking_desc.data
      venue.image_link = venueForm.image_link.data

      db.session.commit()
  except:
      error = True
      db.session.rollback()
      flash('An error in Venue ' + request.form['name'] + ' was not  updated.')
  finally:
      db.session.close()
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error=False
    try:
      artist = Artist(
        name=request.form.get('name'),
        city =request.form.get('city'),
        state= request.form.get('state'),
        phone=request.form.get('phone'),
        genres=request.form.get('genres'),
        seeking_venue=request.form.get('seeking_venue')=="y",
        seeking_description=request.form.get('seeking_description '),
        image_link=request.form.get('image_link'),
        website=request.form.get('website'),
        facebook_link=request.form.get('facebook_link')
      )
      db.session.add(artist)
      db.session.commit()
    except:
        error=True
        db.session.rollback()
    finally:
        db.session.close()
        if error:
            flash('error')
        else:
            flash('artist added')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.join(Venue).join(Artist).all()
  data = []
  for show in shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name, 
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.startTime)
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error=False
    try:
      show = Show(
        artist_id=request.form.get('artist_id'),
        venue_id =request.form.get('venue_id'),
        startTime= request.form.get('start_time'),
      )
      db.session.add(show)
      db.session.commit()
    except:
        error=True
        db.session.rollback()
    finally:
        db.session.close()
        if error:
            flash('error')
        else:
            flash('show added')
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
