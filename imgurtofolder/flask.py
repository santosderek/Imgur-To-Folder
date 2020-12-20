from .configuration import Configuration
from flask import Flask, request
import json


def create_application(configuration: Configuration):

    app = Flask(__name__)

    @app.route('/', methods=['GET'])
    def index():
        access_token = request.args.get('access_token')
        refresh_token = request.args.get('refresh_token')

        if access_token is None:
            return 'Could not find {} as a parameter.'.format(access_token)

        if refresh_token is None:
            return 'Could not find {} as a parameter.'.format(refresh_token)


        configuration.set_access_token(access_token)
        configuration.set_refresh_token(refresh_token)
        configuration.save_configuration()

        return 'Authorized!'

    return app
