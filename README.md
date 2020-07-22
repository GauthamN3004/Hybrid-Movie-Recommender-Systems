# Hybrid-Movie-Recommender-Systems
A recommender system which employs a combination of content-based and user-based collaborative filtering recommender systems to recommend a movie to the user

### Requirements
* pandas
```
pip install pandas
```
* numpy
```
pip install numpy
```
* flask
``` 
pip install flask
```
* flask_sqlalchemy
``` 
pip install flask_sqlalchemy
```
* psycopg2
```
pip install psycopg2
```
* sklearn
```
pip install sklearn
```

### How it works
There are two types of recommender systems used.
* Content-Based
* Collaborative-Filtering

Both the above recommendation systems can be implemented using simple matrix multiplication.

##### Preprocessing
The genres of the movie should be split into individual columns, in case of content-based recommendation.
A pivot table of user ratings should be created, in case of collaborative filtering.

The Content-based recommendation is used to recommend movies based on user's genre preferences. The movie ratings of the user can be multiplied with the genres of the movies rated.
The sum of each genre (column) can give the weight of each genre (the most liked genre of the user). These weights are multiplied with genres of movies that are not watched by the user and a score can be generated for each movie. The top N highest scoring movies can be recommended to the user.

The Collaborative-filtering recommendation checks the similarity of the user with other users and returns those movies which are highly rated by the others. This is also based on simple matrix multiplication. First, we find the similarity of users with each other using cosine_similarity (Cosine similarity is a metric used to measure how similar the documents are irrespective of their size. Mathematically, it measures the cosine of the angle between two vectors projected in a multi-dimensional space.). Now multiply this similarity with ratings provided by other users for those movies that are not watched. Again, a normalized score is generated for each movie and the top N movies can be recommended to the user.
