"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user1 = User.signup('User-Test1', 'user1@fake-email.com', 'test-password', 'https://cdn-icons-png.flaticon.com/512/21/21104.png')
        user1id = 2
        user1.id = user1id

        user2 = User.signup('User-Test2', 'user2@fake-email.com', 'blabla#bla', None)
        user2id = 3
        user2.id = user2id

        db.session.commit()

        user1 = User.query.get(user1id)
        user2 = User.query.get(user2id)

        self.user1 = user1
        self.user1id = user1id

        self.user2 = user2
        self.user2id = user2id

        self.client = app.test_client()


    def tearDown(self) -> None:
        result = super().tearDown()
        db.session.rollback()
        return result

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


    ####### Tests for the following features #######################

    def test_user_follows(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user2.following), 0)
        self.assertEqual(len(self.user2.followers), 1)
        self.assertEqual(len(self.user1.followers), 0)
        self.assertEqual(len(self.user1.following), 1)

        self.assertEqual(self.user1.following[0].id, self.user2.id)
        self.assertEqual(self.user2.followers[0].id, self.user1.id)

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_followed_by(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))


########### Tests for signup feature ############################

    def test_valid_signup(self):
        user_test = User.signup('testuser', 'testuser@fake-email.com', 'anypassword', None)
        user_test_id = 4
        user_test.id = user_test_id
        db.session.commit()

        user_test = User.query.get(user_test_id)
        self.assertIsNotNone(user_test)
        self.assertEqual(user_test.username, 'testuser')
        self.assertEqual(user_test.email, 'testuser@fake-email.com')
        ##since password should be hashed, test if password is NOT equal to what user entered###
        self.assertNotEqual(user_test.password, 'anypassword')

        ## Test if hashed password using Bcrypt starts with $2b$ ##
        self.assertTrue(user_test.password.startswith('$2b$'))

    def test_invalid_username_signup(self):
        invalid_user = User.signup(None, 'test@testing.com', 'password', None)
        user_id = 55
        invalid_user.id = user_id
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        invalid_user = User.signup('invalid', None, 'password', None)
        user_id = 56
        invalid_user.id = user_id
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password(self):
        with self.assertRaises(ValueError) as context:
            User.signup('invalid', 'testing@test.com', None, None)

        with self.assertRaises(ValueError) as context:
            User.signup('invalid', 'testing@test.com', '', None)

    
    ###### Authentication Tests #######################

    def test_valid_authentication(self):
        u = User.authenticate(self.user1.username, 'password')
        self.assertIsNotNone(u)
        self.assertEqual(self.user1.id, self.user1id)

    def test_invalid_username(self):
        self.assertFalse(User.authenticate('badusername', 'password'))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.user1.username, 'wrongpassword'))

    