from flask import Flask
app = Flask(__name__)

# for sessions
app.secret_key = b'\xdf\xf6\xfd\xb8\xdcI\xa85n\x10\x03\x88\x12\\\xc1\xb4\x80\x8f\x18@\x83{\xe1\xa5'

from flask import session, redirect, url_for, request, flash, render_template, jsonify
from flask_oauthlib.client import OAuth
import requests
from werkzeug.contrib.cache import SimpleCache

cache = SimpleCache()

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
    params = {
        'feature': 'popular',
        'rpp': 100,
        'image_size': 4,
        'consumer_key': CONSUMER_KEY,
    }
    r = requests.get('https://api.500px.com/v1/photos', params=params)

    photos = cache.get('photos')
    if not photos:
        app.logger.debug('photos not found in cache, fetching from 500px')
        try: 
            # will throw exception if not 200
            r.raise_for_status()

            data = r.json()
            if 'photos' in data:
                photos = data['photos']
                app.logger.debug('filled cache with photos')
                cache.set('photos', photos, timeout=60)
            else:
                raise Exception('No photos found in data')

        except Exception as e:
            flash ('Something went wrong getting photos from 500px: %s' % e, 'negative')
            photos = []
    else:
        app.logger.debug('photos fetched from cache')

    context = {
            'photos': photos,
            'authenticated': False if not get_500px_token() else get_500px_token(),
        }
    return render_template('index.html', **context)

@app.route('/like/<photo_id>', methods=['POST'])
def like(photo_id):
    r = _500px.post('photos/%s/vote' % photo_id, data={
        'vote': 1,
    })

    json = r.data

    #purge index cache
    cache.delete('photos')

    return jsonify( **json )

@app.route('/delete-like/<photo_id>', methods=['POST'])
def delete_like(photo_id):
    r = _500px.delete('photos/%s/vote' % photo_id)

    json = r.data

    #purge index cache
    cache.delete('photos')
    
    return jsonify( **json )


@app.route('/login')
def login():
    return _500px.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route('/logout')
def logout():
    next_url = request.args.get('next') or url_for('index')
    session.pop('500px_token', None)
    flash('You were successfully logged out', 'positive')
    return redirect(next_url)


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

    flash('You were successfully signed in', 'positive')
    return redirect(next_url)

if __name__ == '__main__':
    app.run(debug=True)