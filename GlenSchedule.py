from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')
    #postgres://guard_postgresql_blake_user:BJbMaGCTYlccKx8KRyl76fA3E0NYoBLC@dpg-cpjnaf821fec73a0sskg-a.oregon-postgres.render.com/guard_postgresql_blake
@app.route('/<name>')
def person(name):
    try:
        return render_template(f'{name}.html')
    except:
        return "Page not found", 404

if __name__ == '__main__':
    app.run(debug=True)
