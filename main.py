from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from os import environ

from sqlalchemy import desc
from sqlalchemy.orm import backref

app = Flask(__name__)
# in environ variables create a variable name DB_CONNECTION and set it to
# mysql+pymysql://<username>:<password>@<db>/JobInsights
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DB_CONNECTION')
# app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONNECTION

db = SQLAlchemy(app)


class Companies(db.Model):
    company_id = db.Column(db.INTEGER, primary_key=True)  # Primary Key (Unique ID for db)
    company_name = db.Column(db.TEXT, nullable=False)  # Text entered by user

    def __repr__(self):
        return '<%r>' % self.company_id


class Company_top_ngrams(db.Model):
    company_id = db.Column(db.INTEGER, db.ForeignKey('companies.company_id'), primary_key=True)
    companies = db.relationship("Companies", backref=backref("companies_ngrams", uselist=False))
    ngram_type = db.Column(db.TEXT)
    ngram = db.Column(db.TEXT, primary_key=True, nullable=False)
    count = db.Column(db.INTEGER)



class Postings(db.Model):
    posting_id = db.Column(db.TEXT, primary_key=True, nullable=False)
    job_title = db.Column(db.TEXT, nullable=False)
    company_id = db.Column(db.INTEGER, db.ForeignKey('companies.company_id'))
    companies = db.relationship("Companies", backref=backref("companies", uselist=False))
    job_description = db.Column(db.TEXT, nullable=False)
    cleaned_job_description = db.Column(db.TEXT, nullable=True)
    date_scraped = db.Column(db.DATE)

    def __repr__(self):
        return '<%r>' % self.posting_id


class Unigrams(db.Model):
    unigram = db.Column(db.TEXT, primary_key=True, nullable=False)
    count = db.Column(db.INTEGER, nullable=False)

    def __repr__(self):
        return '<%r>' % self.unigram


class Unigrams_postings(db.Model):
    # FOREIGN KEY ( unigram ) REFERENCES unigrams ( unigram )
    # unigram = db.Column(db.TEXT, primary_key=True, nullable=False)
    unigram = db.Column(db.TEXT, db.ForeignKey('unigrams.unigram'), primary_key=True)
    unigrams = db.relationship("Unigrams", backref=backref("unigrams", uselist=False))
    # FOREIGN KEY (posting_id) REFERENCES postings ( posting_id )
    posting_id = db.Column(db.INTEGER, db.ForeignKey('postings.posting_id'), primary_key=True)
    postings = db.relationship("Postings", backref=backref("unigrams_postings", uselist=False))

    def __repr__(self):
        return '<%r>' % self.unigram


class Bigrams(db.Model):
    bigram = db.Column(db.TEXT, primary_key=True, nullable=False)
    count = db.Column(db.INTEGER, nullable=False)

    def __repr__(self):
        return '<%r>' % self.bigram


class Bigrams_postings(db.Model):
    # FOREIGN KEY ( bigram ) REFERENCES bigrams ( bigram )
    bigram = db.Column(db.TEXT, db.ForeignKey('bigrams.bigram'), primary_key=True, nullable=False)
    bigrams = db.relationship("Bigrams", backref=backref("bigrams", uselist=False))
    # FOREIGN KEY (posting_id) REFERENCES postings ( posting_id )
    posting_id = db.Column(db.INTEGER, db.ForeignKey('postings.posting_id'), primary_key=True)
    postings = db.relationship("Postings", backref=backref("bigrams_postings", uselist=False))

    def __repr__(self):
        return '<%r>' % self.bigram


class Bigrams_unigrams(db.Model):
    # FOREIGN KEY ( bigram ) REFERENCES bigrams ( bigram )
    bigram = db.Column(db.TEXT, db.ForeignKey('bigrams.bigram'), primary_key=True, nullable=False)
    bigrams = db.relationship("Bigrams", backref=backref("bigrams_unigrams", uselist=False))
    # FOREIGN KEY (posting_id) REFERENCES postings ( posting_id )
    unigram = db.Column(db.TEXT, db.ForeignKey('unigrams.unigram'), primary_key=True)
    unigrams = db.relationship("Unigrams", backref=backref("unigrams_bigrams", uselist=False))

    def __repr__(self):
        return '<%r>' % self.bigram


class Trigrams(db.Model):
    trigram = db.Column(db.TEXT, primary_key=True, nullable=False)
    count = db.Column(db.INTEGER, nullable=False)

    def __repr__(self):
        return '<%r>' % self.trigram


class Trigrams_postings(db.Model):
    trigram = db.Column(db.TEXT, db.ForeignKey('trigrams.trigram'), primary_key=True, nullable=False)
    trigrams = db.relationship("Trigrams", backref=backref("trigrams", uselist=False))
    # FOREIGN KEY (posting_id) REFERENCES postings ( posting_id )
    posting_id = db.Column(db.INTEGER, db.ForeignKey('postings.posting_id'), primary_key=True)
    postings = db.relationship("Postings", backref=backref("trigrams_postings", uselist=False))

    def __repr__(self):
        return '<%r>' % self.trigram


class Trigrams_unigrams(db.Model):
    trigram = db.Column(db.TEXT, db.ForeignKey('trigrams.trigram'), primary_key=True, nullable=False)
    trigrams = db.relationship("Trigrams", backref=backref("trigrams_unigrams", uselist=False))
    # FOREIGN KEY (unigram) REFERENCES unigrams ( unigram )
    unigram = db.Column(db.TEXT, db.ForeignKey('unigrams.unigram'), primary_key=True)
    unigrams = db.relationship("Unigrams", backref=backref("unigrams_trigrams", uselist=False))

    def __repr__(self):
        return '<%r>' % self.trigram


# tmp = Company_top_ngrams.query.all()
# print(tmp)
# for row in tmp:
#     print(row)
#


@app.route('/')
@app.route('/home')
def home():  # put application's code here
    return render_template('index.html')


@app.route('/companies', methods=['GET'])
@app.route('/companies/<int:page>', methods=['GET'])
def companies(page=1):
    per_page = 10
    return render_template('companies.html', companies= Companies.query.order_by(Companies.company_name)
                           .paginate(page, per_page, error_out=False))


@app.route('/company/<company_id>', methods=['GET'])
def company(company_id):
    return render_template('company.html', n_grams=Company_top_ngrams.query
                           .filter(Company_top_ngrams.company_id == company_id),
                           company=Companies.query.filter(Companies.company_id == company_id).limit(1).all())

    # return render_template('company.html',
    #                        postings=Postings.query.filter(Postings.company_id == company_id).all(),
    #                        company=Companies.query.filter(Companies.company_id == company_id).limit(1).all())


@app.route('/postings', methods=['GET'])
@app.route('/postings/<int:page>', methods=['GET'])
def postings(page=1):
    per_page = 10
    return render_template('postings.html', postings=Postings.query.paginate(page, per_page, error_out=False))


@app.route('/unigrams', methods=['GET'])
@app.route('/unigrams/<int:page>', methods=['GET'])
def unigrams(page=1):
    per_page = 10
    return render_template('unigrams.html',
                           unigrams=Unigrams.query.order_by(desc(Unigrams.count)).paginate(page, per_page,
                                                                                           error_out=False))


@app.route('/unigram/<unigram>', methods=['GET'])
def unigram(unigram):
    return render_template('unigram.html',
                           postings=Postings.query.filter(Postings.posting_id == Unigrams_postings.posting_id).filter(
                               Unigrams_postings.unigram == unigram),
                           unigram=unigram)


@app.route('/unigrams-postings', methods=['GET'])
def unigrams_postings():
    return render_template('unigrams-postings.html', unigrams_postings=Unigrams_postings.query.all())


@app.route('/bigrams', methods=['GET'])
@app.route('/bigrams/<int:page>', methods=['GET'])
def bigrams(page=1):
    per_page = 10
    return render_template('bigrams.html', bigrams=Bigrams.query.order_by(desc(Bigrams.count)).paginate(page, per_page,
                                                                                                        error_out=False))


@app.route('/bigram/<bigram>', methods=['GET'])
def bigram(bigram):
    return render_template('bigram.html',
                           postings=Postings.query.filter(Postings.posting_id == Bigrams_postings.posting_id).filter(
                               Bigrams_postings.bigram == bigram),
                           unigrams=Bigrams_unigrams.query.filter(Bigrams_unigrams.bigram == bigram),
                           bigram=bigram)


@app.route('/trigrams', methods=['GET'])
@app.route('/trigrams/<int:page>', methods=['GET'])
def trigrams(page=1):
    per_page = 10
    return render_template('trigrams.html',
                           trigrams=Trigrams.query.order_by(desc(Trigrams.count)).paginate(page, per_page,
                                                                                           error_out=False))


@app.route('/trigram/<trigram>', methods=['GET'])
def trigram(trigram):
    return render_template('trigram.html',
                           postings=Postings.query.filter(Postings.posting_id == Trigrams_postings.posting_id).filter(
                               Trigrams_postings.trigram == trigram),
                           unigrams=Trigrams_unigrams.query.filter(Trigrams_unigrams.trigram == trigram).all(),
                           trigram=trigram)


@app.route('/ui_test')
def ui_test():
    return render_template('ui_test.html')

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)

