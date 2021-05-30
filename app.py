from flask import Flask,jsonify,request,json
from flask_mysqldb import MySQL,MySQLdb
import random
import pandas as pd
from scipy.sparse import csr_matrix

app = Flask(__name__)
##.\venv\Scripts\activate
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ecommerce'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

 
mysql = MySQL(app)

print('connected')



@app.route('/test')
def index1():
	iduser= request.args.get('id')
	cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cur.execute("select piece_id,rate from rates where user_id=%s",(iduser))
	data=cur.fetchall()
	pieces=[]
	content={}
	for result in data:
		content={'id':result['piece_id'],'rate':result['rate']}
		pieces.append(content)
		content={}
	return jsonify(pieces)

# **********************function to get similar product based on user rating************************************
def get_similar(movie_id,rating,corrMatrix):
    # we give the movies with same rating as our movie a good similarity 
    # and a bad one for those who has a diffrent rating than our movie
    similar_ratings = corrMatrix[movie_id]*(rating-2.5)
    similar_ratings = similar_ratings.sort_values(ascending=False)
    #print(type(similar_ratings))
    return similar_ratings
#function for recommneded product based on rating
@app.route('/')
def index():

	cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	iduser= request.args.get('id')
	cur.execute("select user_id,piece_id,rate from rates")
	rate = pd.DataFrame(data=list(cur))
	pivote=rate.pivot_table(values='rate', index='user_id',columns='piece_id').fillna(0)
	corrMatrix = pivote.corr(method='pearson')
	cur.execute("select piece_id,rate from rates where user_id=%s",(iduser))
	rated=cur.fetchall()
	#print(rated)
	romantic_lover = []
	for res in rated:
		romantic_lover.append((res['piece_id'],res['rate']))
	similar_movies = pd.DataFrame()
	for piece_id,rating in romantic_lover:
		similar_movies = similar_movies.append(get_similar(piece_id,rating,corrMatrix),ignore_index = True)
	mysimilar=similar_movies.sum().sort_values(ascending=False).head(20)
	print(type(mysimilar))
	resp=mysimilar.to_dict()
	print(type(resp))
	return jsonify(resp)

#best viewed
@app.route('/view')
def index1():
	iduser= request.args.get('id')
	cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cur.execute("select piece_id,rate from cliques where user_id=%s",(iduser))
	data=cur.fetchall()
	pieces=[]
	content={}
	for result in data:
		content={'id':result['piece_id'],'rate':result['rate']}
		pieces.append(content)
		content={}
	return jsonify(pieces)

if __name__ == '__main__':
    app.run(debug=True)