import csv
from os.path import dirname
from datetime import datetime

from mock import patch
from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq
import test_utils
from devmo.tests import create_profile

from django.contrib.auth.models import User

from devmo.models import Calendar, Event, UserProfile, UserDocsActivityFeed
from devmo.helpers import devmo_url
from devmo import urlresolvers
from devmo.models import Calendar, Event, UserProfile

from dekicompat.tests import (mock_post_mindtouch_user, mock_put_mindtouch_user)
from dekicompat.backends import DekiUser, DekiUserBackend


APP_DIR = dirname(dirname(__file__))
MOZILLA_PEOPLE_EVENTS_CSV = '%s/fixtures/Mozillapeopleevents.csv' % APP_DIR
USER_DOCS_ACTIVITY_FEED_XML = ('%s/fixtures/user_docs_activity_feed.xml' %
                               APP_DIR)
XSS_CSV = '%s/fixtures/xss.csv' % APP_DIR
BAD_DATE_CSV = '%s/fixtures/bad_date.csv' % APP_DIR


class TestCalendar(test_utils.TestCase):
    fixtures = ['devmo_calendar.json']

    def setUp(self):
        self.cal = Calendar.objects.get(shortname='devengage_events')
        self.event = Event(date="2011-06-17", conference="Web2Day",
                           location="Nantes, France",
                           people="Christian Heilmann",
                           description="TBD", done="no", calendar=self.cal)
        self.event.save()

    def test_reload_bad_url_does_not_delete_data(self):
        self.cal.url = 'bad'
        success = self.cal.reload()
        ok_(success == False)
        ok_(Event.objects.all()[0].conference == 'Web2Day')
        self.cal.url = 'http://test.com/testcalspreadsheet'
        success = self.cal.reload()
        ok_(success == False)
        ok_(Event.objects.all()[0].conference == 'Web2Day')

    def test_reload_from_csv_data(self):
        self.cal.reload(data=csv.reader(open(MOZILLA_PEOPLE_EVENTS_CSV, 'rb')))
        # check total
        assert_equal(33, len(Event.objects.all()))
        # spot-check
        ok_(Event.objects.get(conference='StarTechConf'))

    def test_reload_from_csv_data_blank_end_date(self):
        self.cal.reload(data=csv.reader(open(MOZILLA_PEOPLE_EVENTS_CSV, 'rb')))
        event = Event.objects.get(conference='Monash University')
        ok_(event)
        eq_(event.date, event.end_date)

    def test_reload_end_date_determines_done(self):
        self.cal.reload(data=csv.reader(open(MOZILLA_PEOPLE_EVENTS_CSV, 'rb')))
        # no matter what done column says, events should be done
        # by virtue of the end date
        event = Event.objects.get(conference='Confoo')
        ok_(event)
        eq_(True, event.done)
        event = Event.objects.get(conference='TECH4AFRICA')
        ok_(event)
        eq_(False, event.done)

    def test_bad_date_column_skips_row(self):
        self.cal.reload(data=csv.reader(open(BAD_DATE_CSV, 'rb')))
        # check total - should still have the good row
        assert_equal(1, len(Event.objects.all()))
        # spot-check
        ok_(Event.objects.get(conference='StarTechConf'))

    def test_html_santiziation(self):
        self.cal.reload(data=csv.reader(open(XSS_CSV, 'rb')))
        # spot-check
        eq_('&lt;script&gt;alert("ruh-roh");&lt;/script&gt;Brendan Eich',
            Event.objects.get(conference="Texas JavaScript").people)


class TestUserProfile(test_utils.TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        pass

    @mock_put_mindtouch_user
    def test_websites(self):
        """A list of websites can be maintained on a UserProfile"""
        user = User.objects.get(username='testuser')
        profile = UserProfile.objects.get(user=user)

        # Property should start off as an empty dict()
        sites = profile.websites
        eq_({}, sites)

        # Assemble a set of test sites.
        test_sites = dict(
            website='http://example.com',
            twitter='http://twitter.com/lmorchard',
            github='http://github.com/lmorchard',
            stackoverflow='http://stackoverflow.com/users/lmorchard',
        )

        # Try a mix of assignment cases for the websites property
        sites['website'] = test_sites['website']
        sites['bad'] = 'bad'
        del sites['bad']
        profile.websites['twitter'] = test_sites['twitter']
        profile.websites.update(dict(
            github=test_sites['github'],
            stackoverflow=test_sites['stackoverflow'],
        ))

        # Save and make sure a fresh fetch works as expected
        profile.save()
        p2 = UserProfile.objects.get(user=user)
        eq_(test_sites, p2.websites)

        # One more set-and-save to be sure this survives a round-trip
        test_sites['google'] = 'http://google.com'
        p2.websites['google'] = test_sites['google']
        p2.save()
        p3 = UserProfile.objects.get(user=user)
        eq_(test_sites, p3.websites)

    @attr('docs_activity')
    def test_user_docs_activity_url(self):
        """Can build the API URL for a user docs activity feed"""
        username = "Sheppy"
        url = UserDocsActivityFeed(username=username).feed_url_for_user()
        ok_(url.endswith('/@api/deki/users/=%s/feed?format=raw' % username))

    @attr('bug689203')
    def test_activity_url_bug689203(self):
        try:
            username = u"She\xeappy"
            url = UserDocsActivityFeed(username=username).feed_url_for_user()
        except KeyError, e:
            ok_(False, "No KeyError should be thrown")

    @attr('docs_activity')
    @patch('devmo.models.UserDocsActivityFeed.fetch_user_feed')
    def test_user_docs_activity(self, fetch_user_feed):
        fetch_user_feed.return_value = (open(USER_DOCS_ACTIVITY_FEED_XML, 'r')
                                        .read())
        feed = UserDocsActivityFeed(username="Sheppy")
        items = feed.items

        eq_(100, len(items))

        for item in items:

            ok_(hasattr(item, 'rc_id'))
            ok_(hasattr(item, 'rc_comment'))
            ok_(hasattr(item, 'rc_title'))
            ok_(hasattr(item, 'rc_timestamp'))

            ok_(isinstance(item.rc_timestamp, datetime))
            ok_(type(item.rc_revision) is int)

            if 'EDIT' == item.rc_type:
                ok_(item.edit_url is not None)
            if 'NEW' == item.rc_type:
                ok_(item.history_url is None)
                ok_(item.diff_url is None)
            if 'MOVE' == item.rc_type:
                eq_(item.rc_moved_to_title, item.current_title)

    @attr('docs_activity')
    def test_irc_nickname(self):
        """We've added IRC nickname as a profile field. Make sure it shows up."""
        user = User.objects.get(username='testuser')
        profile_from_db = UserProfile.objects.get(user=user)
        ok_(hasattr(profile_from_db, 'irc_nickname'))
        eq_('testuser', profile_from_db.irc_nickname)

    def test_unicode_email_gravatar(self):
        """Bug 689056: Unicode characters in email addresses shouldn't break
        gravatar URLs"""
        user = User.objects.get(username='testuser')
        user.email = u"Someguy Dude\xc3\xaas Lastname"
        try:
            profile = UserProfile.objects.get(user=user)
            g = profile.gravatar
        except UnicodeEncodeError:
            ok_(False, "There should be no UnicodeEncodeError")

    def test_locale_timezone_fields(self):
        """We've added locale and timezone fields. Verify defaults."""
        user = User.objects.get(username='testuser')
        profile_from_db = UserProfile.objects.get(user=user)
        ok_(hasattr(profile_from_db, 'locale'))
        ok_(profile_from_db.locale == 'en-US')
        ok_(hasattr(profile_from_db, 'timezone'))
        ok_(str(profile_from_db.timezone) == 'US/Pacific')

    def test_mindtouch_timezone(self):
        user = User.objects.get(username='testuser')
        profile = UserProfile.objects.get(user=user)
        eq_("-08:00", profile.mindtouch_timezone)

    def test_mindtouch_language(self):
        user = User.objects.get(username='testuser')
        profile = UserProfile.objects.get(user=user)
        eq_("en", profile.mindtouch_language)
