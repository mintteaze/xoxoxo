import os
import os
import sys
from random import randint

import flask_login
import requests
import urllib3
from PIL import Image
from flask import Flask, render_template, make_response, jsonify, redirect
from flask_caching import Cache
from flask_login import LoginManager, login_user, logout_user, login_required
from waitress import serve

from data import db_session
from data.category import Category
from data.comments import Comment
from data.kind import Kind
from data.objects import Object
from data.region import Region
from data.users import User
from forms.comment import AddCommentForm
from forms.object import FindObjectForm
from forms.user import RegisterForm, LoginForm

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
app.config['SECRET_KEY'] = 'NJwadok12LMKF3KMlmcd232v_key'
login_manager = LoginManager()
login_manager.init_app(app)
urllib3.disable_warnings()


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@login_manager.user_loader
def load_user(user_id):
    from data import db_session
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/')
def main_page():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if db_sess.query(User).filter(User.nick == form.nick.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пользователь с таким ником уже зарегистрирован")
        user = User(
            email=form.email.data,
            nick=form.nick.data,
            is_admin=0
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/show')
def show_objects():
    db_sess = db_session.create_session()
    objects = db_sess.query(Object).all()
    obj = [objects[randint(1, len(objects))] for _ in range(10)]
    return render_template('show_objects.html', obj=obj)


@app.route('/<int:object_id>', methods=['GET', 'POST'])
def get_object(object_id):
    db_sess = db_session.create_session()
    obj = db_sess.query(Object).get(object_id)
    form = AddCommentForm()
    comments = db_sess.query(Comment).filter(Comment.obj_id == object_id).all()
    if form.validate_on_submit():
        comment = Comment(
            text=form.text.data,
            obj_id=form.obj_id.data,
            creater_id=flask_login.current_user.id
        )
        db_sess.add(comment)
        db_sess.commit()
        return redirect(f'/{object_id}')
    if obj:
        coords = obj.coords
        if coords:
            get_photo(coords[1:-1])
        if obj.photo:
            try:
                res = requests.get(obj.photo, verify=False).content
                with open('static/photo/obj.png', 'wb') as file:
                    file.write(res)
                im = Image.open("static/photo/obj.png")
                out = im.resize((512, 512))
                out.save("static/photo/object.png")
            except:
                if os.path.isfile('static/photo/object.png'):
                    os.remove('static/photo/object.png')
                if os.path.isfile('static/photo/obj.png'):
                    os.remove('static/photo/obj.png')
        reg = db_sess.query(Region).get(obj.region)
        cat = db_sess.query(Category).get(obj.category)
        kind = db_sess.query(Kind).get(obj.kind)
        return render_template('object.html', obj=obj, comments=comments, region=reg.name, cat=cat.name, kind=kind.name,
                               form=form)
    return jsonify({'error': 'object not found'})


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = FindObjectForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit():
        if bool(form.name.data) and bool(form.reester_number.data) and form.region.data \
                and form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.reester_number == form.reester_number.data,
                                               Object.region == form.region.data,
                                               Object.category == form.category.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and bool(form.reester_number.data) and form.region.data \
                and form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.reester_number == form.reester_number.data,
                                               Object.region == form.region.data,
                                               Object.category == form.category.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and not bool(form.reester_number.data) and form.region.data \
                and form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.region == form.region.data,
                                               Object.category == form.category.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and not bool(form.reester_number.data) and not form.region.data \
                and form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.category == form.category.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and not bool(form.reester_number.data) and not form.region.data \
                and not form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and not bool(form.reester_number.data) and not form.region.data \
                and not form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and not bool(form.reester_number.data) and not form.region.data \
                and form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.category == form.category.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and not bool(form.reester_number.data) and form.region.data \
                and not form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.region == form.region.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and bool(form.reester_number.data) and not form.region.data \
                and not form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.reester_number == form.reester_number.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and not bool(form.reester_number.data) and not form.region.data \
                and not form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and not bool(form.reester_number.data) and form.region.data \
                and not form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.region == form.region.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and not bool(form.reester_number.data) and form.region.data \
                and form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.region == form.region.data,
                                               Object.category == form.category.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and bool(form.reester_number.data) and not form.region.data \
                and not form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.reester_number == form.reester_number.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and bool(form.reester_number.data) and not form.region.data \
                and form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.reester_number == form.reester_number.data,
                                               Object.category == form.category.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and bool(form.reester_number.data) and not form.region.data \
                and form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.reester_number == form.reester_number.data,
                                               Object.category == form.category.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and bool(form.reester_number.data) and form.region.data \
                and not form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.reester_number == form.reester_number.data,
                                               Object.region == form.region.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and bool(form.reester_number.data) and form.region.data \
                and not form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.reester_number == form.reester_number.data,
                                               Object.region == form.region.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif not bool(form.name.data) and bool(form.reester_number.data) and form.region.data \
                and form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.reester_number == form.reester_number.data,
                                               Object.region == form.region.data,
                                               Object.category == form.category.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and not bool(form.reester_number.data) and not form.region.data \
                and not form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and not bool(form.reester_number.data) and not form.region.data \
                and form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.category == form.category.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and not bool(form.reester_number.data) and not form.region.data \
                and form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.category == form.category.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and not bool(form.reester_number.data) and form.region.data \
                and not form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.region == form.region.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and not bool(form.reester_number.data) and form.region.data \
                and not form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.region == form.region.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and not bool(form.reester_number.data) and form.region.data \
                and form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.region == form.region.data,
                                               Object.category == form.category.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and not bool(form.reester_number.data) and form.region.data \
                and form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.region == form.region.data,
                                               Object.category == form.category.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and bool(form.reester_number.data) and not form.region.data \
                and not form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.reester_number == form.reester_number.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and bool(form.reester_number.data) and not form.region.data \
                and not form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.reester_number == form.reester_number.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and bool(form.reester_number.data) and not form.region.data \
                and form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.reester_number == form.reester_number.data,
                                               Object.category == form.category.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and bool(form.reester_number.data) and not form.region.data \
                and form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.reester_number == form.reester_number.data,
                                               Object.category == form.category.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and bool(form.reester_number.data) and form.region.data \
                and not form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.reester_number == form.reester_number.data,
                                               Object.region == form.region.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and bool(form.reester_number.data) and form.region.data \
                and not form.category.data and form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.reester_number == form.reester_number.data,
                                               Object.region == form.region.data,
                                               Object.kind == form.kind.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        elif bool(form.name.data) and bool(form.reester_number.data) and form.region.data \
                and form.category.data and not form.kind.data:
            obj = db_sess.query(Object).filter(Object.name.like(f"%{form.name.data}%"),
                                               Object.reester_number == form.reester_number.data,
                                               Object.region == form.region.data,
                                               Object.category == form.category.data,
                                               Object.unesco == form.unesco.data,
                                               Object.is_value == form.is_value.data).all()
        else:
            obj = None
        cache.set('obj', obj)
        return redirect('/objects')
    return render_template('search.html', form=form)


@app.route('/objects', methods=['GET', 'POST'])
def objects():
    obj = cache.get('obj')
    return render_template('objects.html', obj=obj)


def get_photo(sel):
    geocoder_request = \
        f"http://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b&geocode={sel}&format=json"
    response = requests.get(geocoder_request)
    if response:
        toponym_coodrinates = \
            response.json()["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"].split()

    map_request = \
        f"http://static-maps.yandex.ru/1.x/?ll={toponym_coodrinates[0]},{toponym_coodrinates[1]}&spn=0.005,0.005&l=map&pt={toponym_coodrinates[0]},{toponym_coodrinates[1]},comma"
    response = requests.get(map_request)

    if not response:
        print("Ошибка выполнения запроса:")
        print(map_request)
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)

    map_file = "static/photo/map.png"
    with open(map_file, "wb") as file:
        file.write(response.content)


def add_coords():
    db_sess = db_session.create_session()
    obj = db_sess.query(Object).filter(Object.full_address != '', Object.coords == '').all()
    for i in obj:
        try:
            address = str('+'.join(i.full_address.split(', '))).replace(' ', '+')
            geocoder_request = f"https://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b&geocode={address}&format=json"
            response = requests.get(geocoder_request)
            if response:
                json_response = response.json()
                pos = (
                    json_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'])
                coords = ('[' + str(', '.join(pos.split())) + ']')
                print(f"{i.id}) {i.name} - {coords}")
                i.coords = coords
                db_sess.add(i)
                db_sess.commit()
        except Exception as e:
            print(f"{i.id} --- {e}")


@app.route('/29')
def p29():
    return render_template('29.html')


@app.route('/51')
def p51():
    return render_template('51.html')


@app.route('/83')
def p83():
    return render_template('83.html')


@app.route('/87')
def p87():
    return render_template('87.html')


@app.route('/10')
def p10():
    return render_template('10.html')


@app.route('/11')
def p11():
    return render_template('11.html')


@app.route('/14')
def p14():
    return render_template('14.html')


@app.route('/24')
def p24():
    return render_template('24.html')


@app.route('/89')
def p89():
    return render_template('89.html')


def main():
    db_session.global_init('culture.db')
    port = int(os.environ.get("PORT", 5000))
    app.run(port=5000, host='0.0.0.0')
    serve(app, port=port, host='0.0.0.0', threads=100)


@app.route('/aof')
def aof():
    return render_template('aof.html')


if __name__ == '__main__':
    main()
