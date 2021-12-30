import attr
import treq
import feedparser
from klein import Klein, Plating
from twisted.web.template import tags as t, slot


@attr.s(frozen=True)
class Channel:
    title = attr.ib()
    link = attr.ib()
    items = attr.ib()


@attr.s(frozen=True)
class Item:
    title = attr.ib()
    link = attr.ib()


@attr.s(frozen=True)
class Feed:
    _source = attr.ib()
    _channel = attr.ib()

    def asJSON(self):
        return attr.asdict(self._channel)

    def asHTML(self):
        header = t.th(t.a(href=self._channel.link)(self._channel.title))
        return t.table(t.tr(header))(
            [t.tr(t.td(t.a(href=item.link)(item.title))) for item in
             self._channel.items])


@attr.s
class FeedAggregation:
    _feeds = attr.ib()
    _app = Klein()
    _plating = Plating(
        tags=t.html(
            t.head(t.title('Feed Aggregator 2.0')),
            t.body(slot(Plating.CONTENT))
        )
    )

    def resource(self):
        return self._app.resource()

    @_plating.routed(
        _app.route('/'),
        t.div(render='feeds:list')(slot('item')),
    )
    def root(self, request):
        jsonRequested = request.args.get(b'json')

        def convert(feed):
            return feed.asJSON() if jsonRequested else feed.asHTML()

        return {'feeds': [convert(feed) for feed in self._feeds]}


@attr.s
class FeedRetrieval:
    _treq = attr.ib()

    def retrieve(self, url):
        feedDeferred = self._treq.get(url)
        feedDeferred.addCallback(treq.content)
        feedDeferred.addCallback(feedparser.parse)

        def toFeed(parsed):
            feed = parsed[u'feed']
            entries = parsed[u'entries']
            channel = Channel(feed[u'title'], feed[u'link'],
                              tuple(Item(e[u'title'], e[u'link'])
                                    for e in entries))
            return Feed(url, channel)

        feedDeferred.addCallback(toFeed)
        return feedDeferred
