from flask import Flask,render_template,flash,request,redirect,url_for,session,Response
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Float
from passlib.hash import sha256_crypt
import pandas as pd
import numpy as np
import psycopg2
import json
from wtforms import TextField, SubmitField, IntegerField, validators


all_movies = pd.read_csv("movies.csv")
all_ratings = pd.read_csv("ratings.csv")

class Add(FlaskForm):
    movie = TextField('Movie Name',[validators.Required('enter valid movie')],id = 'city_autocomplete')
    submit = SubmitField('Submit')

app = Flask(__name__)
app.secret_key = ""


env = "dev"
if env == "dev":
    app.debug=True
    app.config['SQLALCHEMY_DATABASE_URI'] = ""

else:
    app.debug=True
    app.config['SQLALCHEMY_DATABASE_URI'] = ""


db = SQLAlchemy(app)

class users(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(50),nullable = False, unique = True)
    password = db.Column(db.String(300),nullable = False)
    movie = db.relationship('movies',backref = 'user',lazy = True)

    def __repr__(self):
        return f"users('{self.username}','{self.id}')"

class movies(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'),nullable = False)
    movie_id = db.Column(db.Integer,nullable = False)
    rating = db.Column(db.Float,nullable = False)
    

    def __repr__(self):
        return f"movie('{self.user_id}','{self.movie_id}','{self.rating}')"

@app.route('/')
def start():
    session["username"] = "no one here !!"
    session["loggedin"] = False
    session["user_id"] = -1
    return redirect(url_for("login"))

@app.route('/login/',methods = ['POST','GET'])
def login():
    if(session["loggedin"]== True):
        return redirect(url_for("home"))
    if(request.method == 'POST'):
        uname = request.form["username"]
        pw = request.form["password"]
        users_data = users.query.filter_by(username=uname).all()
        if(len(users_data)==1):
            users_data = users_data[0]
            if(sha256_crypt.verify(pw,users_data.password)):
                session["loggedin"] = True
                session["username"] = uname
                session["user_id"] = users_data.id
                return redirect(url_for('home'))

            else:
                flash("Wrong Username or Password !",category='error')
                return render_template("login.html")

        else:
            flash("Wrong Username or Password !",category='error')
            return render_template("login.html")
    return render_template("login.html")

@app.route('/register/',methods = ['POST','GET'])
def register():
    if request.method == "POST":
        uname = request.form['username']
        passw = request.form['pass']
        re_password = request.form['re_pass']

        users_data = users.query.filter_by(username=uname).all()
        if(len(users_data)==1):
            flash("Username already exists !")
            return render_template("register.html")
        if passw == re_password:
            user1 = users(username = uname)
            name = user1.username
            pw = sha256_crypt.encrypt(passw)
            user1 = users(username = name,password = pw)
            db.session.add(user1)
            db.session.commit()

            flash("You have successfully registered !","success")
            return redirect(url_for('login'))
        else:
            flash("The passwords do not match !","error")
            return render_template("register.html")

    return render_template("register.html")

@app.route('/home/')
def home():
    if(session["loggedin"] == True):
        print(all_movies.columns)
        my_movies = movies.query.filter_by(user_id = session["user_id"]).all()

        if(len(my_movies) == 0):
            flash("No movies rated yet !!",category = "error")
            l=0
            return render_template("home.html",movies = my_movies,n = l,total = len(my_movies))
        else:
            movie_data = []
            for i in my_movies:
                data = []
                imdb = list(all_movies.loc[all_movies["movieId"] == i.movie_id]["imdbId"])[0]
                while(len(str(imdb))<7):
                    imdb = '0'+str(imdb)
                link = "https://www.imdb.com/title/tt"+str(imdb)
                data.append(i.movie_id)
                data.append(list(all_movies.loc[all_movies["movieId"] == i.movie_id]["title"])[0])
                data.append(list(all_movies.loc[all_movies["movieId"] == i.movie_id]["poster_img"])[0])
                data.append(i.rating)
                data.append(link)
                movie_data.append(data)
            l = int(len(my_movies)/3)+1
            return render_template("home.html",movies = movie_data,n = l,total = len(my_movies))

    else:
        flash("This page requires you to login !",category= "error")
        return redirect(url_for('login'))


@app.route('/_autocomplete', methods=['GET'])
def autocomplete():
    movies = list(all_movies["title"]) 
    return Response(json.dumps(movies), mimetype='application/json')

@app.route("/delete/",methods = ["GET","POST"])
def delete():
    if(session["loggedin"] != True):
        flash("This page first requires you to login !",category= "error")
        return redirect(url_for('login'))
    if(request.method == "POST" and request.form["delete"]!= ""):
        del_id = request.form["delete"]
        del_movie = movies.query.filter_by(user_id = session["user_id"],movie_id = del_id)
        print(del_movie)
        for d in del_movie:
            db.session.delete(d)
        db.session.commit()
        flash("Movie Rating Deleted !",category= "success")
        return redirect(url_for('add_movies'))

@app.route("/add_movies",methods = ["GET","POST"])
def add_movies():
    if(session["loggedin"] != True):
        flash("This page first requires you to login !",category= "error")
        return redirect(url_for('login'))
    form = Add()

    my_movie_list = movies.query.filter_by(user_id = session["user_id"]).all()
    print(my_movie_list)
    rating = []
    movie = []
    for m in my_movie_list:
        k = []
        m_title = all_movies.loc[all_movies["movieId"] == m.movie_id]["title"].tolist()[0]
        k.append(m.movie_id)
        k.append(m_title)
        k.append(m.rating)
        movie.append(k)
    movie.sort(key=lambda x:x[1])

    if(form.is_submitted()):
        result = request.form
        my_movie = result["movie"]
        my_rating = request.form["rating"]
        find_movie_id =  all_movies.loc[all_movies["title"]== my_movie]["movieId"]
        if(len(list(find_movie_id)) == 0):
            flash("There is no such movie ! Please enter again !",category= "error")
            return render_template("add_movies.html",movie_list = movie)
        else:
            movie_id = list(find_movie_id)[0]
        this_movie = movies.query.filter_by(user_id = session["user_id"],movie_id = movie_id).all()
        if(len(this_movie)>0):
            flash("You have already rated this movie !",category= "error")
            return redirect(url_for("add_movies",movie_list = movie))
        else:
            my_movie_rating = movies(user_id = session["user_id"],movie_id = movie_id,rating = my_rating)
            db.session.add(my_movie_rating)
            db.session.commit()
            flash("Movie Rating added Successfully !",category= "success")
            return redirect(url_for('add_movies',movie_list = movie))

    else:
        return render_template("add_movie.html",form=form,movie_list = movie)
        

    return render_template("add_movie.html",form=form,movie_list = movie)
        



@app.route("/logout")
def logout():
    if(session["loggedin"] != True):
        flash("This page requires you to login !",category= "error")
        return redirect(url_for('login'))
    session.pop("loggedin",False)
    session.pop("username","")
    flash("You have successfully Logged Out!",category="success")
    return redirect(url_for('start'))


if __name__ == "__main__":
    app.run(debug = True)