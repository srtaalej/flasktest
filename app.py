from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user
import requests
import os
from dotenv import load_dotenv
import random

load_dotenv()

app = Flask(__name__)

# Tells flask-sqlalchemy what database to connect to
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
# Enter a secret key
app.config["SECRET_KEY"] = "ENTER YOUR SECRET KEY"
# Initialize flask-sqlalchemy extension
db = SQLAlchemy()
 
# LoginManager is needed for our application
# to be able to log in and out users
login_manager = LoginManager()
login_manager.init_app(app)

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True,
                         nullable=False)
    password = db.Column(db.String(250),
                         nullable=False)
    
class TrackRecommendations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)

 
 
# Initialize app with extension
db.init_app(app)
# Create database within app context
 
with app.app_context():
    db.create_all()
    
@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(user_id)

@app.route('/register', methods=["GET", "POST"])
def register():
  # If the user made a POST request, create a new user
    if request.method == "POST":
        user = Users(username=request.form.get("username"),
                     password=request.form.get("password"))
        # Add the user to the database
        db.session.add(user)
        # Commit the changes made
        db.session.commit()
        # Once user account created, redirect them
        # to login route (created later on)
        return redirect(url_for("signin"))
    # Renders sign_up template if user made a GET request
    return render_template("register.html")

@app.route("/signin", methods=["GET", "POST"])
def signin():
    # If a post request was made, find the user by
    # filtering for the username
    if request.method == "POST":
        user = Users.query.filter_by(
            username=request.form.get("username")).first()
        # Check if the password entered is the
        # same as the user's password
        if user.password == request.form.get("password"):
            # Use the login_user method to log in the user
            login_user(user)
            return redirect(url_for("index"))
        # Redirect the user back to the home
        # (we'll create the home route in a moment)
    return render_template("signin.html")

@app.route("/pick", methods=["GET", "POST"])
def pick():
    recommendations = TrackRecommendations.query.all()
    rec_urls = [rec.url for rec in recommendations]
    
    if request.method == "POST":
        db.session.query(TrackRecommendations).delete()
        db.session.commit()
        artist_ids = ['6M2wZ9GZgrQXHCFfjv46we', '5pKCCKE2ajJHZ9KAiaK11H', '0hCNtLu0JehylgoiP8L4Gh', '06HL4z0CvFAxyc27GXpf02', '3LZZPxNDGDFVSIPqf4JuEf']
        artist_choice = random.choice(artist_ids)
        
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",    
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET")
        }
        response = requests.post(url, headers=headers, data=data)
        res = response.json()
        access_token = res['access_token']
        print(access_token)
        genre1 = request.form.get("genre1")
        genre2 = request.form.get("genre2")
        genre3 = request.form.get("genre3")
            
        print(genre1, genre2, genre3)
        
        rec_url = "https://api.spotify.com/v1/recommendations/"
        rec_params = {
            "seed_artists": artist_choice,
            "seed_genres": f"{genre1},{genre2},{genre3}",
            "seed_tracks": "0c6xIDDpzE81m2q797ordA"
        }
        rec_headers = {
            "Authorization": f"Bearer {access_token}"
        }

        rec_res = requests.get(rec_url, headers=rec_headers, params=rec_params).json()
        
        spotify_urls = []
        for track in rec_res['tracks']:
            spotify_url = track.get('external_urls', {}).get('spotify')
            if spotify_url and "/track" in spotify_url:
                spotify_urls.append(spotify_url)
                
        for url in spotify_urls:
            new_track = TrackRecommendations(url=url)
            db.session.add(new_track)
            db.session.commit()
        print(spotify_urls)
        
    if not rec_urls:
        return render_template("pick.html", message="No recommendations yet")
    else:
        return render_template("pick.html", recommendations=rec_urls)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")

if __name__ == '__main__':
	app.run(debug=True, host="0.0.0.0")
 
 