from openerp.addons.runbot_multiple_hosting.models import hosting
import requests


class BitBucketHosting(hosting.Hosting):
    API_URL = 'https://bitbucket.org/api/2.0'
    URL = 'https://bitbucket.org'
    token = (())

    def __init__(self, credentials):
        auth = ('JAFMQPQs4BkT7KQubr','JE54xLmGDFLGqvjKbvKn3NBGGaVAPEC7')
        response = requests.post(self.URL + '/site/oauth2/access_token', auth=auth,
                                 data={'grant_type':'client_credentials'})
        self.token = response.json().get('access_token')
        super(BitBucketHosting, self).__init__()

    @classmethod
    def get_branch_url(cls, owner, repository, branch):
        return cls.get_url('/%s/%s/branch/%s', owner, repository, branch)

    @classmethod
    def get_pull_request_url(cls, owner, repository, pull_number):
        return cls.get_url('/%s/%s/pull-request/%s', owner, repository, pull_number)


    def get_pull_request(self, owner, repository, pull_number):
        url = self.get_api_url('/repositories/%s/%s/pullrequests/%s' % (owner, repository, pull_number))
        reponse = self.session.get('%s?access_token=%s' % (url, self.token))
        return reponse.json()
