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
from sklearn.metrics.pairwise import cosine_similarity


all_movies = pd.read_csv("movies_with_genre.csv")
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
        

def content_based():
    my_movies = movies.query.filter_by(user_id = session["user_id"]).all()
    m_ids = []
    m_rats = []
    avg_rating = all_ratings.groupby("movieId").mean()["rating"]
    count_rating = all_ratings.groupby("movieId").count()["rating"]
    for i in my_movies:
        m_ids.append(i.movie_id)
        m_rats.append(i.rating)

    watched = all_movies.loc[all_movies["movieId"].isin(m_ids)]
    not_watched = all_movies.loc[~all_movies["movieId"].isin(m_ids)]
    watched = watched.reset_index(drop=True)
    for i in range(watched.shape[0]):
        this_id = watched["movieId"][i]
        index = m_ids.index(this_id)
        rating = m_rats[index]
        for j in range(7,watched.shape[1]):
            watched.iloc[i,j]*= (rating-3)

    gen_mat = watched.iloc[:,7:]
    gen_data = gen_mat.sum(axis = 0)
    for j in gen_data.index:
        not_watched[j] *=gen_data[j]

    score = not_watched.iloc[:,7:].sum(axis=1)
    score = (score - score.min())/(score.max()-score.min())
    nw_ratings = not_watched["avg_rating"]
    nw_ratings = (nw_ratings - nw_ratings.min())/(nw_ratings.max()-nw_ratings.min())
    score = score*10 + nw_ratings*5
    not_watched["score"] = score.tolist()
    data = not_watched.sort_values(by = "score",ascending = False)
    data = data.head(9)[["title","genres","poster_img","imdbId"]]
    new_data = []
    for i in range(data.shape[0]):
        another = []
        another.append(data.iloc[i,0])
        another.append(data.iloc[i,1])
        another.append(data.iloc[i,2])
        imdb = data.iloc[i,3]
        while(len(str(imdb))<7):
            imdb = '0'+str(imdb)
        link = "https://www.imdb.com/title/tt"+str(imdb)
        another.append(link)
        new_data.append(another)
    return new_data

def standardize(row):
    return (row - row.mean())/(row.max()-row.min())

def user_based():
    user_movie_id = []
    user_rating = []
    user_id = []
    my_movies = movies.query.filter_by(user_id = session["user_id"]).all()
    for i in my_movies:
        user_movie_id.append(i.movie_id)
        user_rating.append(i.rating)
        user_id.append(1000000)
    
    my_rating = pd.DataFrame({'userId' : user_id, 'movieId': user_movie_id,'rating' : user_rating})
    num_movies = my_rating.shape[0]
    new_rating = pd.concat([all_ratings,my_rating],axis=0,ignore_index=True)
    rat_pivot = new_rating.pivot(index = "userId",columns = "movieId",values = "rating")
    user_movie_ratings = rat_pivot[user_movie_id]
    user_movie_ratings = user_movie_ratings.fillna(0)
    user_movie_ratings = user_movie_ratings.apply(standardize)
    user_similarity = cosine_similarity(user_movie_ratings)
    user_similarity = pd.DataFrame(user_similarity,columns = rat_pivot.index,index = rat_pivot.index)
    my_row = user_similarity.iloc[-1,:]
    my_row = my_row.sort_values(ascending = False)
    most_similar = my_row.iloc[1:11]
    most_similar_user = most_similar.index.to_list()
    most_similar_score = list(my_row.iloc[1:11].values)
    not_watched = rat_pivot.drop(columns = user_movie_id)
    not_watched = not_watched.T[most_similar_user]
    not_watched = not_watched[not_watched.isnull().sum(axis=1) <= int(num_movies/2)]
    my_dict=dict()
    for i in range(len(most_similar_user)):
        my_dict[most_similar_user[i]] = most_similar_score[i]
    for i in most_similar_user:
        not_watched[i]*=my_dict[i]
    score = []
    for i in range(not_watched.shape[0]):
        s1 = 0
        s2 = 0
        for j in range(not_watched.shape[1]):
            if(np.isnan(not_watched.iloc[i,j])):
                continue
            else:
                s1 = s1+not_watched.iloc[i,j]
                s2 = s2 + my_dict[not_watched.columns[j]]
                
        s1 = s1/s2
        score.append(s1)
    not_watched['score'] = score
    not_watched = not_watched.sort_values(by = "score",ascending = False)
    nw = not_watched.iloc[:12,0].index.tolist()
    not_watched = all_movies.loc[all_movies["movieId"].isin(nw)]
    data = not_watched[["title","genres","poster_img","imdbId"]]
    new_data = []
    for i in range(not_watched.shape[0]):
        another = []
        another.append(data.iloc[i,0])
        another.append(data.iloc[i,1])
        another.append(data.iloc[i,2])
        imdb = data.iloc[i,3]
        while(len(str(imdb))<7):
            imdb = '0'+str(imdb)
        link = "https://www.imdb.com/title/tt"+str(imdb)
        another.append(link)
        new_data.append(another)
    return new_data

@app.route("/recommend",methods = ["GET","POST"])
def recommend():
    if(session["loggedin"] != True):
        flash("This page requires you to login !",category= "error")
        return redirect(url_for('login'))
    cb_data = content_based()
    ub_data = user_based()
    return render_template("recommend.html",cb_data = cb_data,ub_data = ub_data)

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