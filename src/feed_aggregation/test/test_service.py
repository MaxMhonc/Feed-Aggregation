import json
from lxml import html
from twisted.trial.unittest import SynchronousTestCase
from twisted.internet import defer
from treq.testing import StubTreq
from .. import FeedAggregation
from .._service import Feed, Channel, Item

FEEDS = (Feed("http://feed-1.invalid/rss.xml",
              Channel(title="First feed", link="http://feed-1/",
                      items=(Item(title="First item", link="#first"),))),
         Feed("http://feed-2.invald/rss.xml",
              Channel(title="Second feed", link="http://feed-2/",
                      items=(Item(title="Second item", link="#second"),))),
         )


class FeedAggregationTests(SynchronousTestCase):

    def setUp(self):
        self.client = StubTreq(FeedAggregation(FEEDS).resource())

    @defer.inlineCallbacks
    def get(self, url):
        response = yield self.client.get(url)
        self.assertEqual(response.code, 200)
        content = yield response.content()
        defer.returnValue(content)

    def test_renderHTML(self):
        content = self.successResultOf(self.get(u"http://test.invalid/"))
        parsed = html.fromstring(content)
        self.assertEqual(parsed.xpath(u'/html/body/div/table/tr/th/a/text()'),
                         [u"First feed", u"Second feed"])
        self.assertEqual(parsed.xpath('/html/body/div/table/tr/th/a/@href'),
                         [u"http://feed-1/", u"http://feed-2/"])
        self.assertEqual(parsed.xpath('/html/body/div/table/tr/td/a/text()'),
                         [u"First item", u"Second item"])
        self.assertEqual(parsed.xpath('/html/body/div/table/tr/td/a/@href'),
                         [u"#first", u"#second"])

    def test_renderJSON(self):
        content = self.successResultOf(self.get(
            u"http://test.invalid/?json=true"))

        parsed = json.loads(content)
        self.assertEqual(
            parsed,
            {
                u"feeds": [
                    {
                        u"title": u"First feed",
                        u"link": u"http://feed-1/",
                        u"items": [
                            {u"title": u"First item", u"link": u"#first"}
                        ]
                    },
                    {
                        u"title": u"Second feed",
                        u"link": u"http://feed-2/",
                        u"items": [
                            {u"title": u"Second item",
                             u"link": u"#second"}
                        ]
                    }
                ]
            }
        )
