# -*- coding: utf-8 -*-
"""Http Library because the python ecosystem for this is pants."""

import json
from http.client import HTTPConnection, HTTPSConnection
from urllib.parse import urlencode, urlparse


class Url:
    def of(url_string, params={}):
        url = urlparse(url_string)
        return Url(
            scheme=url.scheme,
            hostname=url.hostname,
            port=url.port,
            path=url.path,
            query=urlencode(params)
        )

    def __init__(self, scheme, hostname, port, path, query):
        self.scheme = scheme
        self.hostname = hostname
        self.port = port
        self.path = path
        self.query = query

    @property
    def path_and_query(self):
        if self.query:
            return f"{self.path}?{self.query}"
        return self.path

    def __str__(self):
        if (not self.port) or self.port in ['80', '443']:
            return f"{self.scheme}://{self.hostname}{self.path_and_query}"

        return f"{self.scheme}://{self.hostname}:{self.port}{self.path_and_query}"

class Http:
    class Response:
        def of(connection):
            response = connection.getresponse()
            body = ""
            while chunk := response.read():
                body = body + chunk.decode('utf-8')
            return Http.Response(response, body)

        def __init__(self, raw_response, body):
            self.raw_response = raw_response
            self.body = body

        def json(self):
            return json.loads(self.body)

    class Connection:
        class UnknownSchemeError(Exception):
            pass

        def of(url):
            if url.scheme == 'http':
                return Http.Connection(HTTPConnection(url.hostname), url)
            elif url.scheme == 'https':
                return Http.Connection(HTTPSConnection(url.hostname), url)
            else:
                # TODO: use better error message
                raise Http.Connection.UnknownSchemeError(f"Yo, no idea what scheme this is man. {url.scheme}")

        def __init__(self, connection, url):
            self.connection = connection
            self.url = url

        def request(self, method, headers=None, body=None):
            self.connection.request(
                method,
                self.url.path_and_query,
                headers=headers,
                body=body
            )
            return Http.Response.of(self.connection)

    def __init__(self, headers, base_url=None):
        self.headers = headers
        self.base_url = base_url

    def full_url(self, url_string):
        if not self.base_url:
            return url_string

        return self.base_url + url_string

    def post(self, url_string, params={}, body={}):
        url = Url.of(self.full_url(url_string), params)
        connection = Http.Connection.of(url)
        return connection.request("POST", self.headers, json.dumps(body))

    def get(self, url_string, params={}):
        url = Url.of(self.full_url(url_string), params)
        connection = Http.Connection.of(url)
        return connection.request("GET", self.headers)

    def patch(self, url_string, params={}, body={}):
        url = Url.of(self.full_url(url_string), params)
        connection = Http.Connection.of(url)
        return connection.request("PATCH", self.headers, json.dumps(body))
