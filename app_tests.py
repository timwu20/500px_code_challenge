import app
import unittest
from unittest import mock
import flask_oauthlib
from requests.exceptions import Timeout

class AppTestCase(unittest.TestCase):

    def setUp(self):
        #print('setUp')
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()

    def tearDown(self):
        #print('tearDown')
        pass

    def test_index(self):
        rv = self.app.get('/')
        assert b'<div id="photos">' in rv.data

    @mock.patch('requests.get')
    def test_index_mock(self, mock_requests_get):
        app.cache.set('photos', None)
        mock_requests_get.side_effect = Exception('Boom')

        rv = self.app.get('/')
        assert b'Boom' in rv.data
        assert b'<div id="photos">' in rv.data

        mock_requests_get.side_effect = Timeout('Boom Timeout')
        rv = self.app.get('/')
        assert b'Boom Timeout' in rv.data
        assert b'<div id="photos">' in rv.data

    def test_login(self):
        rv = self.app.get('/login')
        assert '302' in rv.status
        assert 'https://api.500px.com/v1/oauth/authorize?oauth_token=' in rv.headers.get('Location')

    def test_oauth_authorized_messages(self):
        rv = self.app.get('/oauth-authorized', follow_redirects=True)
        assert '200' in rv.status
        assert b'You denied the request to sign in.' in rv.data

        #fake oauth_token and oauth_verifier
        rv = self.app.get('/oauth-authorized?next=http%3A%2F%2Flocalhost%3A5000%2F&oauth_token=jPjY8uDc2V529FZLiFZWReBR1iWdHT5iGsbwYuV1&oauth_verifier=4a5UStJ9bfIBr2qqnE01', follow_redirects=True)
        assert '200' in rv.status
        assert b'Something went wrong trying to login to 500px.' in rv.data

    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.authorized_response')
    def test_oauth_authorized(self, mock_authorized_response):
        #fake oauth_token and oauth_verifier
        mock_authorized_response.return_value = {'oauth_token_secret': 'QPVfnn673UIzZ6voJj9Bw7TyYfTMFnr42D5GR2QW', 'oauth_token': 'aQwYEpwFIl4rpIYG7TnRWhJpWjpU3hxWiCUM2UFo'}

        rv = self.app.get('/oauth-authorized?next=http%3A%2F%2Flocalhost%3A5000%2F&oauth_token=jPjY8uDc2V529FZLiFZWReBR1iWdHT5iGsbwYuV1&oauth_verifier=4a5UStJ9bfIBr2qqnE01', follow_redirects=True)
        
        #check that it's called without any params
        mock_authorized_response.assert_called_once_with()

        #check that session contains tokens
        with self.app.session_transaction() as sess:
            assert 'QPVfnn673UIzZ6voJj9Bw7TyYfTMFnr42D5GR2QW' in sess['500px_token']
            assert 'aQwYEpwFIl4rpIYG7TnRWhJpWjpU3hxWiCUM2UFo' in sess['500px_token']

        assert b'You were successfully signed in' in rv.data

    #fakes the login process
    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.authorized_response')
    def login(self, mock_authorized_response):
        #fake oauth_token and oauth_verifier
        mock_authorized_response.return_value = {'oauth_token_secret': 'QPVfnn673UIzZ6voJj9Bw7TyYfTMFnr42D5GR2QW', 'oauth_token': 'aQwYEpwFIl4rpIYG7TnRWhJpWjpU3hxWiCUM2UFo'}
        rv = self.app.get('/oauth-authorized?next=http%3A%2F%2Flocalhost%3A5000%2F&oauth_token=jPjY8uDc2V529FZLiFZWReBR1iWdHT5iGsbwYuV1&oauth_verifier=4a5UStJ9bfIBr2qqnE01', follow_redirects=True)
        return rv

    def test_authenticated_index(self):
        self.login()
        rv = self.app.get('/')
        assert b'Logout' in rv.data     

    def test_logout(self):
        self.login()
        rv = self.app.get('/logout', follow_redirects=True)

        assert '200' in rv.status
        assert b'You were successfully logged out' in rv.data
        with self.app.session_transaction() as sess:
            assert sess.get('500px_token', None) == None

    def test_like_not_authenticated(self):
        rv = self.app.post('/like/153435169')
        assert b'No token available' in rv.data

    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.post')
    def test_like(self, mock_post):
        rv = self.app.post('/like/153435169')
        mock_post.assert_called_once_with('photos/%s/vote' % 153435169, data={
            'vote': 1,
        })

    def test_delete_like_not_authenticated(self):
        rv = self.app.post('/delete-like/153435169')
        assert b'No token available' in rv.data

    @mock.patch('flask_oauthlib.client.OAuthRemoteApp.delete')
    def test_delete_like(self, mock_delete):
        rv = self.app.post('/delete-like/153435169')
        mock_delete.assert_called_once_with('photos/%s/vote' % 153435169)


if __name__ == '__main__':
    unittest.main()