from flask import Flask, redirect, url_for, render_template, request
import sqlite3

app = Flask(__name__)

class Post:
    def __init__(self, uID, uname, content, tag=None):
        self.uID = uID
        self.uname = uname
        self.content = content
        if tag:
            self.tags = self.parseTags(tag)
        else:
            self.tags = None

    def parseTags(self, tags):
        ret = []
        for tag in tags:
            ret.append("".join(tag))
        return ret

@app.route('/')
def index():
    return render_template('index.html', status="Welcome! Please Login.")

userID = ""
@app.route('/login', methods=['POST'])
def login():
    uID, pw = request.form['uID'], request.form['pw']
    
    conn = sqlite3.connect("social_media.db")
    query = '''SELECT UserID, Password FROM User WHERE
            UserID = ?'''
    res = conn.execute(query, (uID,)).fetchone()
    conn.close()
    
    if res == None: # no such user
        return render_template('index.html', status="Error: Invalid User ID")
    elif res[1] != pw: # wrong password
        return render_template('index.html', status="Error: Incorrect Password")
    else: # correct
        global userID 
        userID = uID
        return redirect(url_for('posts',user=uID))

@app.route('/posts', methods=['POST'])
@app.route('/posts/<user>', methods=['GET','POST'])
def posts(user=None):
    conn = sqlite3.connect("social_media.db")
    
    if request.method == "POST":
        uname = request.form["uname"]
        query = '''SELECT 
                Post.UserID, User.Name, Post.PostText, Post.PostID
                FROM Post INNER JOIN User 
                ON Post.UserID = User.UserID 
                WHERE User.Name = ?'''
        results = conn.execute(query, (uname,)).fetchall()

    else: # GET
        query = '''SELECT 
                Post.UserID, User.Name, Post.PostText, Post.PostID
                FROM Post INNER JOIN User 
                ON Post.UserID = User.UserID 
                WHERE Post.UserID = ?'''
        results = conn.execute(query, (user,)).fetchall()

    posts = []
    for res in results:
        uID, uname, content, pID = res[0], res[1], res[2], res[3]

        query = '''SELECT Tag.Tag FROM Post 
        INNER JOIN PostTag ON PostTag.PostID = Post.PostID
        INNER JOIN Tag ON PostTag.TagID = Tag.TagID
        WHERE Post.PostID = ?'''
        tags = conn.execute(query, (pID,)).fetchall()
        
        posts.append(Post(uID, uname, content, tags))
    conn.close()
    
    return render_template('posts.html', posts=posts)
        
@app.route('/upload',methods=["GET","POST"])
def upload():
    if request.method == "GET":
        return render_template('upload.html')
    else: # posts
        conn = sqlite3.connect("social_media.db")
        content, tags = request.form["content"], request.form["tags"]

        # create post
        global userID
        conn.execute('''INSERT INTO 
        Post(UserID,PostText) VALUES (?,?)''', (userID, content))
        pID = conn.execute('''SELECT PostID 
        FROM Post WHERE PostText = ?''', (content,)).fetchone()[0]
        
        # get/ create tags
        if tags:
            for tag in tags.strip().split(", "):
                res = conn.execute('''SELECT TagID 
                FROM Tag WHERE Tag.Tag = ?''', (tag[1:],)).fetchone()
                
                if res == None: # tag nonexistent - add new tag
                    conn.execute('''INSERT INTO 
                    Tag(Tag) VALUES (?)''', (tag[1:],))
                    
                    res = conn.execute('''SELECT TagID 
                    FROM Tag WHERE Tag.Tag = ?''', (tag[1:],)).fetchone()
                tID = res[0]

                # create PostTags
                conn.execute('''INSERT INTO PostTag(PostID, TagID) 
                VALUES (?,?)''', (pID,tID))
        
        conn.commit()
        conn.close()
        return redirect(url_for('posts',user=userID))

app.run(host='0.0.0.0', port=81)
