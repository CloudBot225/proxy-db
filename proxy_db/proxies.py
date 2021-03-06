import six

from proxy_db.exceptions import NoProvidersAvailable
from proxy_db.models import Proxy, create_session
from proxy_db.providers import PROVIDERS


class ProxiesList(object):
    def __init__(self, country=None):
        if isinstance(country, six.string_types):
            country = country.upper()
        self.request_options = dict(
            country=country,
        )
        self._proxies = set()

    def _excluded_proxies(self):
        return [proxy.id for proxy in self._proxies]

    def find_db_proxy(self):
        query = create_session().query(Proxy).filter(Proxy.votes > 0)
        query = query.filter(~Proxy.id.in_(self._excluded_proxies())).order_by(Proxy.votes.desc())
        country = self.request_options['country']
        if country:
            query = query.filter_by(country=country)
        return query.first()

    def find_provider(self):
        for provider in PROVIDERS:
            req = provider.request(**self.request_options)
            if req.requires_update():
                return provider
        raise NoProvidersAvailable

    def reload_provider(self):
        provider = self.find_provider()
        provider.request(**self.request_options).now()

    def __iter__(self):
        self._proxies = set()
        return self

    def try_get_proxy(self, retry=True):
        proxy = self.find_db_proxy()
        if proxy:
            self._proxies.add(proxy)
            return proxy
        else:
            self.reload_provider()
        if retry:
            return self.try_get_proxy(retry=False)
        else:
            raise StopIteration

    def __next__(self):
        return self.try_get_proxy()

    def next(self):
        return self.__next__()
