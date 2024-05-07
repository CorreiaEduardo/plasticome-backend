from flask import Flask, request
from flask_cors import CORS
from flask_pydantic_spec import FlaskPydanticSpec

from ..controllers.fungi_controller import search_fungi_by_name
from ..controllers.pipeline_controller import execute_main_pipeline

server = Flask(__name__)
CORS(server)
spec = FlaskPydanticSpec(
    'flask', title='PLASTICOME DEMO', version='v1.0', path='docs'
)
spec.register(server)


@server.get('/')
def get_plasticome():
    return 'Plasticome server is running!'


@server.get('/fungi/<fungi_name>')
def get_fungi_id_by_name(fungi_name):
    return search_fungi_by_name(fungi_name)


@server.post('/analyze')
def execute_pipeline():
    return execute_main_pipeline(request.json)


server.run()
