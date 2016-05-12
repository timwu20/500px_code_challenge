from flask import Flask
app = Flask(__name__)

# for sessions
app.secret_key = b'\xdf\xf6\xfd\xb8\xdcI\xa85n\x10\x03\x88\x12\\\xc1\xb4\x80\x8f\x18@\x83{\xe1\xa5'


from flask_oauthlib.client import OAuth
from flask import session, redirect, url_for, request, flash, render_template

CONSUMER_KEY = '6cHA4hgqzBWhVEQXMtdVdjIPZTT9N7zi7Cw3wGjR'
CONSUMER_SECRET = 'SWVn3TDH6d0GjBRoe1eySab3H52JJ4ipDGjCVnGi'

base_url = 'https://api.500px.com/v1/'

oauth = OAuth()

_500px = oauth.remote_app('500px',
    base_url=base_url,
    request_token_url=base_url + 'oauth/request_token',
    access_token_url=base_url + 'oauth/access_token',
    authorize_url=base_url + 'oauth/authorize',
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
)

@_500px.tokengetter
def get_500px_token(token=None):
	return session.get('500px_token')

@app.route('/')
def index():
	if get_500px_token():
		flash('hello logged in user')
	else:
	    flash( 'Hello World! Please login' )

	return render_template('index.html')

@app.route('/login')
def login():
    return _500px.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route('/oauth-authorized')
def oauth_authorized():
    next_url = request.args.get('next') or url_for('index')
    resp = _500px.authorized_response()

    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['500px_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )

    flash('You were successfully signed in')
    return redirect(next_url)

if __name__ == '__main__':
    app.run(debug=True)