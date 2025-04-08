# app.py - Güncellenmiş Sürüm
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import uuid

# Uygulama Konfigürasyonu
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'quiz.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)  # Daha güvenli rastgele anahtar

db = SQLAlchemy(app)

# --- Veritabanı Modelleri ---
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(100), nullable=False)
    option_b = db.Column(db.String(100), nullable=False)
    option_c = db.Column(db.String(100), nullable=False)
    option_d = db.Column(db.String(100), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    topic = db.Column(db.String(100), nullable=False)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.String(36), nullable=False)  # UUID için
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# --- Yardımcı Fonksiyonlar ---
def get_user_session():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

def calculate_score(questions, answers):
    return sum(1 for q in questions if answers.get(f'q{q.id}') == q.correct_answer)

# --- Rotalar ---
@app.route('/')
def index():
    topics = db.session.query(Question.topic).distinct().all()
    return render_template('index.html', topics=[t[0] for t in topics])

@app.route('/quiz')
def quiz():
    topic = request.args.get('topic')
    questions = Question.query.filter_by(topic=topic).all() if topic else Question.query.all()
    return render_template('quiz.html', questions=questions)

@app.route('/submit', methods=['POST'])
def submit_quiz():
    user_id = get_user_session()
    questions = Question.query.all()
    
    # Skor Hesaplama
    user_answers = request.form
    score = calculate_score(questions, user_answers)
    
    # Veritabanına Kaydet
    new_result = Result(score=score, user_id=user_id)
    db.session.add(new_result)
    db.session.commit()
    
    return redirect(url_for('results'))

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    user_results = Result.query.filter_by(user_id=user_id)

    latest_result = user_results.order_by(Result.timestamp.desc()).first()
    if latest_result is None:
        latest_score = 0  # veya "Henüz sınav çözmediniz." gibi mesaj da olur
    else:
        latest_score = latest_result.score

    best_result = user_results.order_by(Result.score.desc()).first()
    if best_result is None:
        best_user_score = 0
    else:
        best_user_score = best_result.score

    overall_best_result = Result.query.order_by(Result.score.desc()).first()
    if overall_best_result is None:
        overall_best = 0
    else:
        overall_best = overall_best_result.score

    return render_template('results.html', latest_score=latest_score, best_user_score=best_user_score, overall_best=overall_best)
# --- Veritabanı İlk Yükleme ---
def initialize_database():
    with app.app_context():
        db.create_all()
        
        if Question.query.count() == 0:
            questions = [
                Question(
                    text="Flask'da route tanımlamak için hangi dekoratör kullanılır?",
                    option_a="@app.get", option_b="@app.post",
                    option_c="@app.route", option_d="@app.endpoint",
                    correct_answer="c", topic="Flask"
                ),
                Question(
                    text="Discord.py'de mesajları dinlemek için hangi decorator kullanılır?",
                    option_a="@client.event", option_b="@client.command",
                    option_c="@client.listen", option_d="@client.message",
                    correct_answer="a", topic="Discord.py"
                ),
                Question(
                    text="Python’da bir sözlükten anahtar ile değer silmek için hangi metot kullanılır?",
                    option_a="remove()", option_b="pop()",
                    option_c="delete()", option_d="clear()",
                    correct_answer="b", topic="Python"
                ),
                Question(
                    text="HTML'de bağlantı (link) oluşturmak için hangi etiket kullanılır?",
                    option_a="<a>", option_b="<link>",
                    option_c="<href>", option_d="<url>",
                    correct_answer="a", topic="HTML"
                ),
                Question(
                    text="SQL’de bir tablodan veri silmek için hangi komut kullanılır?",
                    option_a="REMOVE", option_b="DELETE",
                    option_c="ERASE", option_d="DROP",
                    correct_answer="b", topic="SQL"
                ),
            ]
            db.session.bulk_save_objects(questions)
            db.session.commit()

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)