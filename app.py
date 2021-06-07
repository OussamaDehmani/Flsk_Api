from flask import Flask,jsonify,request,json
from flask_mysqldb import MySQL,MySQLdb
import random
import numpy as np
import pandas as pd
#******************  recommendation lib*****************
from scipy.sparse import csr_matrix
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
#******************  purchased lib  *****************
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.frequent_patterns import association_rules
from mlxtend.preprocessing import TransactionEncoder

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
    print("avant")
    print(corrMatrix[movie_id])
    similar_ratings = corrMatrix[movie_id]*(rating-2.5)
    print("apres")
    print(similar_ratings)

    similar_ratings = similar_ratings.sort_values(ascending=False)
    #print(type(similar_ratings))
    return similar_ratings

def knn_s(model,mtrx,myids):
	bigdict = {}
	mydict={}
	for i in myids:
		distances,indices=model.kneighbors(mtrx[i])
		ind=indices.tolist()
		dist=distances.tolist()
		for A, B in zip(ind[0], dist[0]):
			mydict[A] = B
		Merge(bigdict, mydict)
		mydict={}
	print(bigdict)


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
	user_rated = []
	for res in rated:
		user_rated.append((res['piece_id'],res['rate']))
	similar_movies = pd.DataFrame()
	for piece_id,rating in user_rated:
		similar_movies = similar_movies.append(get_similar(piece_id,rating,corrMatrix),ignore_index = True)
	mysimilar=similar_movies.sum().sort_values(ascending=False).head(20)
	print(type(mysimilar))
	resp=mysimilar.to_dict()
	print(type(resp))
	return jsonify(resp)


#best viewed
# **********************function to get similar product based on user interction************************************
def get_similar_cliqued(piece_id,temps,corrMatrix):
    # we give the movies with same rating as our movie a good similarity 
    # and a bad one for those who has a diffrent rating than our movie

    similar_cliques = corrMatrix[piece_id]*temps
    similar_cliques = similar_cliques.sort_values(ascending=False)
    return similar_cliques

def Merge(dict1, dict2):
    return(dict1.update(dict2))

def knn_similar(model,mtrx,myids):
	bigdict = {}
	mydict={}
	for i in myids:
		distances,indices=model.kneighbors(mtrx[i])
		ind=indices.tolist()
		dist=distances.tolist()
		for A, B in zip(ind[0], dist[0]):
			mydict[A] = B
		Merge(bigdict, mydict)
		mydict={}
	return bigdict



#function for recommneded product based on cliques
@app.route('/viewed')
def viewed():

	cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	iduser= request.args.get('id')
	# cur.execute("select cliques.user_id as user_id,cliques.piece_id as piece_id,cliques.temps as temps ,pieces.subcategory_id  as subcategory_id from cliques,pieces where cliques.piece_id=pieces.id ")
	# viewed = pd.DataFrame(data=list(cur))
	# pivote1=viewed.pivot_table(values='temps', index='user_id',columns='piece_id').fillna(0)
	#corrMatrix = pivote1.corr(method='pearson')
	#print(corrMatrix)
	cur.execute("select user_id,piece_id,rate from rates ")
	viewed = pd.DataFrame(data=list(cur))
	pivote1=viewed.pivot_table(values='rate', index='user_id',columns='piece_id').fillna(0)
	mtrx=csr_matrix(pivote1.values)
	model=NearestNeighbors(metric='cosine',algorithm='brute',n_neighbors=10)
	model.fit(mtrx)
	print('resultat')
	mylist=[1,2,3]
	sm=knn_similar(model,mtrx,mylist)

		# for i,j in  zip(indices,distances):
		# 	print(i,j)
	# cur.execute("select piece_id,temps from cliques where user_id=%s",(iduser))
	# rated=cur.fetchall()
	# print(rated)
	# visited = []
	# for res in rated:
	# 	visited.append((res['piece_id'],res['temps']))
	# last_viewed = pd.DataFrame()
	# for piece_id,temps in visited:
	# 	last_viewed = last_viewed.append(get_similar_cliqued(piece_id,temps,corrMatrix),ignore_index = True)
	# print("last_viewed")
	# print(last_viewed)
	# mysimilar=last_viewed.sum().sort_values(ascending=False).head(20)
	# #print(type(mysimilar))
	# resp=mysimilar.to_dict()
	# print(resp)
	return jsonify(sm)

#insert into database
@app.route('/add')
def add():
	mycursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	for i in range(1,300):
		item=random.randint(1, 76)
		user=random.randint(1, 14)
		temps=random.randint(1500, 10000)
		mycursor.execute("INSERT INTO cliques (piece_id,user_id,temps) VALUES (%s,%s,%s)",(item,user,temps)) 
		#cur.execute("INSERT INTO cliques (piece_id,user_id,temps) VALUES (%s, %s)", (firstName, lastName))
		print('finished')


# # **********************function to get similar product based on user rating************************************
# def get_similar(movie_id,rating,corrMatrix):
#     # we give the movies with same rating as our movie a good similarity 
#     # and a bad one for those who has a diffrent rating than our movie
#     similar_ratings = corrMatrix[movie_id]*(rating-2.5)
#     similar_ratings = similar_ratings.sort_values(ascending=False)
#     #print(type(similar_ratings))
#     return similar_ratings
# #function for recommneded product based on rating
# @app.route('/')
# def index():

# 	cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
# 	iduser= request.args.get('id')
# 	cur.execute("select user_id,piece_id,rate from rates")
# 	rate = pd.DataFrame(data=list(cur))
# 	pivote=rate.pivot_table(values='rate', index='user_id',columns='piece_id').fillna(0)
# 	corrMatrix = pivote.corr(method='pearson')
# 	cur.execute("select piece_id,rate from rates where user_id=%s",(iduser))
# 	rated=cur.fetchall()
# 	#print(rated)
# 	romantic_lover = []
# 	for res in rated:
# 		romantic_lover.append((res['piece_id'],res['rate']))
# 	similar_movies = pd.DataFrame()
# 	for piece_id,rating in romantic_lover:
# 		similar_movies = similar_movies.append(get_similar(piece_id,rating,corrMatrix),ignore_index = True)
# 	mysimilar=similar_movies.sum().sort_values(ascending=False).head(20)
# 	print(type(mysimilar))
# 	resp=mysimilar.to_dict()
# 	print(type(resp))
# 	return jsonify(resp)


dataset = [['Milk', 'Onion', 'Nutmeg', 'Kidney Beans', 'Eggs', 'Yogurt'],
           ['Dill', 'Onion', 'Nutmeg', 'Kidney Beans', 'Eggs', 'Yogurt'],
           ['Milk', 'Apple', 'Kidney Beans', 'Eggs'],
           ['Milk', 'Unicorn', 'Corn', 'Kidney Beans', 'Yogurt'],
           ['Corn', 'Onion', 'Onion', 'Kidney Beans', 'Ice cream', 'Eggs']]
#pf growth algorithm
##.\venv\Scripts\activate
def find_matches(dict1):
    match_dict = {}
    base_keys = dict1.keys()
    print(base_keys)
    for key, values in dict1.items():
        for base_key in base_keys:
            if base_key in values:
            	# print(base_key,values)
            	position = val_list.index(values)
            	if base_keys[position]==dict1[base_key]
    #             match_dict.update({key: base_key})
    return match_dict


@app.route('/purchased')
def purchased():
    tr=TransactionEncoder()
    tr_array=tr.fit(dataset).transform(dataset)
    df=pd.DataFrame(tr_array,columns=tr.columns_)
    frequent=fpgrowth(df,min_support=0.5 ,use_colnames=True)
    rules=association_rules(frequent,metric='confidence', min_threshold=0.8)
    mydict={}
    for i in range(len(rules['antecedents'])):
    	if(len(rules['antecedents'][i])==1):
    		#sets=[rules['antecedents'][i], rules['consequents'][i]]
    		x=list(rules['antecedents'][i])
    		y=list(rules['consequents'][i])
    		print(x,y)
    		mydict[x[0]]=y[0]
    print('mydict befor')
    print(mydict)
    print('mydict after')
    print(find_matches(mydict))
    return jsonify(mydict)


if __name__ == '__main__':
    app.run(debug=True)