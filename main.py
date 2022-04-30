from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from typing import Callable
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os


TMDB_API = os.environ['TMDB_API']
TMDB_ENDPOINT = "https://api.themoviedb.org/3/search/movie"
TMDB_DETAILS_ENDPOINT = "https://api.themoviedb.org/3/movie/"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Movie_Library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


class MySQLAlchemy(SQLAlchemy):
    Column: Callable
    String: Callable
    Integer: Callable
    Float: Callable
    Model: Callable


app.config['SECRET_KEY'] = os.environ['SEC_KEY']
Bootstrap(app)

db = MySQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Integer, nullable=False)
    year = db.Column(db.String(4))
    description = db.Column(db.String(400))
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(400))
    img_url= db.Column(db.String(400))

    def __repr__(self):
        return f'<Movie {self.title}'

db.create_all()

#Create record
# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
#
# db.session.add(new_movie)
# db.session.commit()


class EditForm(FlaskForm):
    rating = StringField(label="Your rating out of 10", validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class AddMovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


@app.route("/")
def home():
    all_movies = db.session.query(Movie).order_by(Movie.rating.desc()).all()
    i = 1
    for movie in all_movies:
        movie.ranking = i
        i += 1
    db.session.commit()
    return render_template("index.html", all_movies=all_movies)


@app.route("/delete")
def del_movie():
    movie_title = request.args.get('title')
    movie_to_delete = Movie.query.filter_by(title=movie_title).first()
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/edit", methods=["GET", "POST"])
def edit():
    edit_form = EditForm()
    movie_title = request.args.get('title')
    movie = Movie.query.filter_by(title=movie_title).first()
    if edit_form.validate_on_submit():
        movie.rating = edit_form.rating.data
        movie.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return render_template("edit.html", movie=movie.title, form=edit_form)


@app.route("/add", methods=["GET", "POST"])
def add():
    movie_form = AddMovieForm()
    if movie_form.validate_on_submit():
        title = movie_form.title.data
        parameters = {
            "api_key": TMDB_API,
            "query": title,
        }
        response = requests.get(TMDB_ENDPOINT, params=parameters)
        search_result = response.json()
        movie_list = search_result["results"]
        return render_template('select.html', movie_list=movie_list)

    return render_template('add.html', form=movie_form)


@app.route("/get_movie", methods=["GET", "POST"])
def get_movie():
    id = request.args.get('id')
    response = requests.get(f"{TMDB_DETAILS_ENDPOINT}{id}?api_key={TMDB_API}")
    movie_data = response.json()
    title = movie_data["original_title"]
    img_url = "https://image.tmdb.org/t/p/w500/" + movie_data["poster_path"]
    release_date = movie_data["release_date"]
    year = release_date[0:3]
    description = movie_data["overview"]

    new_movie = Movie(
        title=title,
        year=year,
        description=description,
        img_url=img_url,
    )

    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', title=title))


if __name__ == '__main__':
    app.run(debug=True)
