from openerp.addons.runbot_multiple_hosting.models import hosting

class BitBucketHosting(hosting.Hosting):
    API_URL = 'https://bitbucket.org/api/2.0'
    URL = 'https://bitbucket.org'

    def __init__(self, credentials):
        super(BitBucketHosting, self).__init__(credentials)

    def get_pull_request(self, owner, repository, pull_number):
        url = self.get_api_url('/repositories/%s/%s/pullrequests/%s' % (owner, repository, pull_number))
        reponse = self.session.get(url)
        return reponse.json()

    @classmethod
    def get_branch_url(cls, owner, repository, branch):
        return cls.get_url('/%s/%s/branch/%s', owner, repository, branch)

    @classmethod
    def get_pull_request_url(cls, owner, repository, pull_number):
        return cls.get_url('/%s/%s/pull-request/%s', owner, repository, pull_number)