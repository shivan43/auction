from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auctions.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    auctions = db.relationship('Auction', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Auction model
class Auction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    start_bid = db.Column(db.Float, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    highest_bid = db.Column(db.Float, default=0.0)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/auctions', methods=['GET'])
@login_required
def view_auctions():
    auctions = Auction.query.filter_by(owner_id=current_user.id).all()
    return render_template('auctions.html', auctions=auctions)

@app.route('/auctions/create', methods=['GET', 'POST'])
@login_required
def create_auction():
    if request.method == 'POST':
        item = request.form['item']
        start_bid = float(request.form['start_bid'])
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d %H:%M:%S')
        new_auction = Auction(item=item, start_bid=start_bid, end_date=end_date, owner_id=current_user.id)
        db.session.add(new_auction)
        db.session.commit()
        flash('Auction created successfully.', 'success')
        return redirect(url_for('view_auctions'))
    return render_template('create_auction.html')

@app.route('/auctions/<int:auction_id>/update', methods=['GET', 'POST'])
@login_required
def update_auction(auction_id):
    auction = Auction.query.get(auction_id)
    if auction.owner_id != current_user.id:
        flash('You are not authorized to update this auction.', 'error')
        return redirect(url_for('view_auctions'))
    if request.method == 'POST':
        auction.item = request.form['item']
        auction.start_bid = float(request.form['start_bid'])
        auction.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d %H:%M:%S')
        db.session.commit()
        flash('Auction updated successfully.', 'success')
        return redirect(url_for('view_auctions'))
    return render_template('update_auction.html', auction=auction)

@app.route('/auctions/<int:auction_id>/delete', methods=['POST'])
@login_required
def delete_auction(auction_id):
    auction = Auction.query.get(auction_id)
    if auction.owner_id != current_user.id:
        flash('You are not authorized to delete this auction.', 'error')
        return redirect(url_for('view_auctions'))
    db.session.delete(auction)
    db.session.commit()
    flash('Auction deleted successfully.', 'success')
    return redirect(url_for('view_auctions'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
