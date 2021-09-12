import json
import random

from flask import Flask, render_template, redirect, request, Markup
import config
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)


# 机器人语言库
#机器人语录库，或者叫知识库的映射，它映射到数据库的一个表上，你可以通过这个类进行操作
class Robot(db.Model):
    #注意：此处对应数据库的表名
    __tablename__ = "robot_content"
    #以下对应表中各字段  primary_key是主键的设定，autoincrement是自增的设定
    # nullable 设定非空属性
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    keyword = db.Column(db.String(200), nullable=False)
    content = db.Column(db.String(200), nullable=False)


# 会话语言库（同上一样）

class Man(db.Model):
    __tablename__ = "man_content"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    robot_content = db.Column(db.String(200), nullable=False)
    man_content = db.Column(db.String(200), nullable=False)


# api会话

class Dialogue(db.Model):
    __tablename__ = "dialogue"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    robot_content = db.Column(db.String(200), nullable=False)
    man_content = db.Column(db.String(200), nullable=False)

#执行操作
db.create_all()

#这个是关于http协议映射的，‘’中的是映射后缀
@app.route('/')
def index():
    #返回一种操作，这个操作在这里是跳转页面的意思
    return render_template("index.html")

# 声明映射，并指定数据提交格式POST和GET
@app.route('/chat_robot', methods=["POST", "GET"])
# 创建函数，函数名为chat_robot
def chat_robot():
    # 判断接收的数据是post还是get，如果是post这进行：后的代码块。
    if request.method == "POST":
        #声明一个变量叫man_content,用来放前台的表格传进来的数据。在python中request.values.get是获取post传来的数据的方法。
        man_content = request.values.get("content")
        #声明一个变量叫robot_content，用来放数据库返回的数据。
        #query是对用户输入数据处理的函数并结合了对数据库的模糊查询。
        robot_content = query(man_content)
        #将用户数据和数据库返回数据提交到缓存表中，作用是用来存放聊天记录的
        add_man_content(man_content, robot_content)
        #声明一个变量，将缓存数据一一列举成数组的形式
        content = list_man_content()
        data = []  # 放HTML文件的数组
        # 循环体，历遍缓存表数据。
        for i in content:
            # 添加入data数组中
            data.append(
                "<div class='man_msg'><div class='man_img'></div><span class='man_content'>" + i[2] +
                "</span></div>")
            data.append(
                "<div class='robot_msg'><div class='robot_img'></div><span class='robot_content'>" + i[1] +
                "</span></div>")
        # 跳转页面，传递数据
        return render_template("chat_robot.html", data=data)
    # 如果不是post传来的数据则运行下面得代码块
    else:
        delete_man_content()
        return render_template("chat_robot.html")


@app.route('/apr_chat_robot', methods=["POST", "GET"])
def apr_chat_robot():
    if request.method == "POST":
        man_content = request.values.get("content")
        api_content = api(man_content)
        add_content(man_content, api_content)
        content = list_content()
        data = []  # 放HTML文件
        '''robot = Markup(
            "<div class='robot_msg'><div class='robot_img'></div><span class='robot_content'>") + api_content + Markup(
            "</span></div>")
        man = Markup(
            "<div class='man_msg'><div class='man_img'></div><span class='man_content'>") + man_content + Markup(
            "</span></div>")'''
        for i in content:
            data.append(
                "<div class='man_msg'><div class='man_img'></div><span class='man_content'>" + i[1] +
                "</span></div>")
            data.append(
                "<div class='robot_msg'><div class='robot_img'></div><span class='robot_content'>" + i[2] +
                "</span></div>")
        return render_template("apr_chat_robot.html", data=data)
    else:
        delete_content()
        return render_template("apr_chat_robot.html")


@app.route('/xunlian', methods=["POST", "GET"])
def xunlian():
    if request.method == "POST":
        man_content = request.values.get("man_content")
        robot_content = request.values.get("robot_content")
        add = Robot(keyword=man_content, content=robot_content)
        db.session.add(add)
        db.session.commit()
        data = "小鑫学会了~谢谢主人！"
        return render_template("xunlian.html", data=data)
    else:
        return render_template("xunlian.html")


def add_content(man_content, robot_content):
    add_content = Dialogue(man_content=man_content, robot_content=robot_content)
    db.session.add(add_content)
    db.session.commit()


def list_content():
    content = db.session.execute(' select * from dialogue order by id asc ')
    content = list(content)
    return content


def delete_content():
    Dialogue.query.filter().delete()
    db.session.commit()


def api(man_content):
    url = "http://api.qingyunke.com/api.php?key=free&appid=0&msg=" + man_content
    r = requests.get(url)
    text = json.loads(r.text)
    content = text["content"].replace('{', '<')
    content = content.replace('}', '>')
    return content


# 处理字符串，使用关键字查询
def query(man_content):
    content = db.session.execute("select * from robot_content where keyword like '%%" + man_content + "%%'")
    content = list(content)
    content_len = len(content)
    if content_len != 0:
        content_len = content_len - 1
        # random是生成随机数的工具
        i = random.randint(0, content_len)
        return content[i][2]
    else:
        content = "抱歉，我不会，你可以教教小鑫吗？"
        return content


def add_man_content(man_content, robot_content):
    add_content = Man(man_content=man_content, robot_content=robot_content)
    db.session.add(add_content)
    db.session.commit()


def list_man_content():
    content = db.session.execute(' select * from man_content order by id asc ')
    content = list(content)
    return content


def delete_man_content():
    Man.query.filter().delete()
    db.session.commit()


if __name__ == '__main__':
    app.debug = True
    app.run()
