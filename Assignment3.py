import os
import sys
import json
import nltk
import pymongo
import string
from flask import Flask, render_template, request, redirect
from werkzeug import secure_filename
from collections import Counter
from pymongo import MongoClient

#Declaring Upload location and the allowed type of files
UPLOAD_FOLDER = 'C:/Users/Adam/Documents/College/Carlow IT/3rd Year/Web & Cloud Dev/Assignment3/uploads'
ALLOWED_EXTENSIONS = set(['txt'])

app = Flask(__name__)
client = MongoClient()

#Setting upload location
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Function to check that the file is .txt
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Function to check for files with the same name
def collection_check(dataBase, name):
    names = dataBase.collection_names()
    exists = None

    #If name exists in list of collections return True
    if name in names:
        exists = True
    
    return exists

@app.route('/')

@app.route('/base')
def base_page():
    return render_template('base.html')

@app.route('/uploader', methods = ['GET','POST'])
def upload_file():

    if request.method == 'POST':
        #Pulling file from html form
        f = request.files['file']
        
        #If no file selected it'll kick back to base screen
        if f.filename == '':
           return redirect('/base')
        
        #Checking if the file is .txt
        if allowed_file(f.filename):
            filename = secure_filename(f.filename)
            
            #Saving file to upload directory
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            #Creating instance of file path for opening
            fName = (os.path.join(app.config['UPLOAD_FOLDER'], filename))

            #Opening copy of file for usage
            openFile = open(fName, encoding = "latin-1")
            contents = openFile.read()

            #Selecting DB for use
            db = client["fileDB"]

            #Checking if collection exists already
            #If the file already exists it will print the results of it
            if collection_check(client["fileDB"], filename):
                data1 = list(db[filename].find())
                return render_template('uploader.html',
                                       results = data1)

            #If it doesnt exist the process of adding it to the DB will continue
            else:
                #Opening thesaurus file
                normsf = open('ea-thesaurus-lower.json', encoding = "utf8")
                norms = json.load(normsf)

                #Performing functions to get file contents in usable state
                translator = str.maketrans('','',string.punctuation)
                no_punc = contents.translate(translator)
                lower = no_punc.lower()
                tokens = nltk.word_tokenize(lower)
            
                data = Counter()

                #Getting count of words appearing in file
                for word in tokens:
                    data[word] += 1

                    #Converting data into a dict for usage
                    c = data
                x = dict(c)

                #Inserting values into it's collection
                for k,v in x.items():
                    
                    #Tries to find the words association in thesaurus
                    #If found inserts the results found
                    try:
                        db[filename].insert_one({"word": k,
                                              "value": v,
                                              "matches": norms[k][:3]})
                        
                    #Or inserts that there were no results found
                    except:
                        db[filename].insert_one({"word": k,
                                              "value": v,
                                              "matches": "not found in word association file"})

                #Creating list of collection items
                data = list(db[filename].find())
                
                #Printing the items to the html form
                return render_template('uploader.html',
                                       results = data)
            
        #If not .txt type it'll kick back to the base screen
        else:
            return redirect('/base')
                

#Displaying previous text files
@app.route('/previous', methods = ['GET','POST'])
def previous_results():
    db = client["fileDB"]
    cNames = db.collection_names()
    
    return render_template('previous.html',
                           names = cNames)

#Displaying the selected previous text file
@app.route('/previousResult', methods = ['GET', 'POST'])
def print_pResults():
    fName = request.form['button']
    db = client["fileDB"]
    data = list(db[fName].find())
    return render_template('previousResult.html',
                            name = fName,
                            results = data)
        
        
if __name__ == '__main__':
        app.secret_key = 'not_so_secret_key'
        app.run(debug = True)
