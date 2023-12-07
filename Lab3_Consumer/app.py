import os
import time

from flask import Flask, redirect, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, distinct
from flask import jsonify
from pymongo import MongoClient
import struct


GENERAL_TABLE_NAME = os.getenv("RESULTS_TABLE_NAME")
OUT_CSV_FILE = os.getenv("OUTPUT_FILE_NAME")

# DB_CONFIG = {'user': 'postgres',
#              'password': 'AI3006',
#              'host': 'localhost',
#              'port': 5432,
#              'database': 'zno'}

DB_CONFIG = {'user': os.getenv("DB_USER"),
             'password': os.getenv("DB_PASSWORD"),
             'host': os.getenv("DB_HOST"),
             'port': os.getenv("DB_PORT"),
             'database': os.getenv("DB_NAME")}

SQLA_CONFIG_STR = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

app = Flask(__name__, template_folder='templates')



mongo_host = os.getenv('MONGO_HOST')
mongo_port = int(os.getenv('MONGO_PORT'))
mongo_db = os.getenv('MONGO_DB')

client = MongoClient(f'mongodb://{mongo_host}:{mongo_port}')
db1 = client[f'{mongo_db}']








def get_table_model(table_name):
    table_models = {
        'educational_institutions': EducationalInstitution,
        'territories': Territory,
        'participants': Participant,
        'points_of_observation': PointOfObservation,
        'testings': Testing
    }
    return table_models.get(table_name)


def get_table_data(selected_table, count_limit):
    models = [EducationalInstitution, Participant, Territory, PointOfObservation, Testing]
    if selected_table not in [model.__tablename__ for model in models]:
        raise ValueError('Недопустимый запрос. Неверное имя таблицы')
    for model in models:
        if selected_table == model.__tablename__:
            table_data = model.query.order_by(model.ID).limit(count_limit).all()
            column_names = [column.key for column in model.__table__.columns]

    return column_names, table_data


@app.route('/')
def index():
    return render_template('site.html')


@app.route('/query', methods=['GET'])
def query():
    reg_names = [reg_name[0] for reg_name in db.session.query(Participant.RegName).distinct().all()]
    tests = [test[0] for test in db.session.query(Testing.Test).distinct().all()]
    average_scores = False

    return render_template('query.html', reg_names=reg_names, tests=tests, average_scores=average_scores)


@app.route('/query', methods=['POST'])
def execute_query():
    reg_name = request.form.get('reg_name')
    test_name = request.form.get('test_name')
    year = request.form.getlist('year')
    score_type = request.form.get('score_type')

    arguments = {'selected_reg_name': reg_name, 'selected_test_name': test_name, 'selected_year': year,
                 'score_type': score_type}

    year_options = [str(y[0]) for y in db.session.query(Testing.Year).distinct().all()]
    reg_names = [reg_name[0] for reg_name in db.session.query(Participant.RegName).distinct().all()]
    tests = [test[0] for test in db.session.query(Testing.Test).distinct().all()]

    if reg_name == 'all':
        query = db.session.query(
            Participant.RegName,
            Testing.Year,
            func.avg(Testing.Ball100).label('average'),
            func.max(Testing.Ball100).label('max'),
            func.min(Testing.Ball100).label('min')
        ).join(Testing, Participant.ID == Testing.Part_ID). \
            filter(Testing.TestStatus == 'Зараховано',
                   Testing.Test == test_name)

        if 'all' not in year:
            query = query.filter(Testing.Year.in_([int(y) for y in year]))

        query_result = query.group_by(Participant.RegName, Testing.Year).all()

        scores_dict = {}
        for reg, y, avg_score, max_score, min_score in query_result:
            scores_dict[f"{reg},{y}"] = {
                'average': avg_score,
                'max': max_score,
                'min': min_score
            }

        return render_template('query.html', reg_names=reg_names, tests=tests, year_options=year_options,
                               average_scores=scores_dict, reg_name=reg_name, year=year, **arguments)

    else:
        scores_dict = {}

        if 'all' in year:
            query = db.session.query(
                Testing.Year,
                func.avg(Testing.Ball100).label('average'),
                func.max(Testing.Ball100).label('max'),
                func.min(Testing.Ball100).label('min')
            ).join(Participant, Participant.ID == Testing.Part_ID). \
                filter(Participant.RegName == reg_name,
                       Testing.Test == test_name,
                       Testing.TestStatus == 'Зараховано'). \
                group_by(Testing.Year)

            query_result = query.all()
            for y, avg_score, max_score, min_score in query_result:
                scores_dict[f"{reg_name},{y}"] = {
                    'average': avg_score,
                    'max': max_score,
                    'min': min_score
                }

            return render_template('query.html', reg_names=reg_names, tests=tests, year_options=year_options,
                                   average_scores=scores_dict, reg_name=reg_name, year=year, **arguments)

        else:
            for y in year:
                query = db.session.query(
                    func.avg(Testing.Ball100).label('average'),
                    func.max(Testing.Ball100).label('max'),
                    func.min(Testing.Ball100).label('min')
                ).join(Participant, Participant.ID == Testing.Part_ID). \
                    filter(Participant.RegName == reg_name,
                           Testing.Test == test_name,
                           Testing.TestStatus == 'Зараховано',
                           Testing.Year == int(y))

                avg_score, max_score, min_score = query.first()

                scores_dict[f"{reg_name},{y}"] = {
                    'average': avg_score,
                    'max': max_score,
                    'min': min_score
                }

            return render_template('query.html', reg_names=reg_names, tests=tests, year_options=year_options,
                                   average_scores=scores_dict, reg_name=reg_name, year=year, **arguments)


@app.route('/update_row', methods=['POST'])
def update_row():
    table_name = request.form.get('table_name')
    row_id = request.form.get('row_id')
    updated_data = {column: request.form.get(column) for column in request.form if
                    column != 'table_name' and column != 'row_id'}

    model_class = get_table_model(table_name)

    if model_class is None:
        return 'Table not found'

    row = model_class.query.get(row_id)

    if row is None:
        return 'Row not found'


    for column, value in updated_data.items():
        setattr(row, column, value)


    db.session.commit()
    selected_table = table_name
    limit = 10
    column_names, table_data = get_table_data(selected_table, limit)
    return render_template('site.html', column_names=column_names, table_data=table_data, table_name=selected_table)


@app.route('/add_row', methods=['GET'])
def add_row():
    return render_template('add_row.html')


def get_distinct_values_p(table_name, column_name):
    YourTableName = get_table_model(table_name)
    distinct_values = db.session.query(distinct(getattr(YourTableName, column_name)).label('count')).all()

    return distinct_values


@app.route('/add_rows', methods=['POST'])
def add_rows():
    table_name = request.form['table_name']
    updated_data = {column: request.form.get(column) for column in request.form if
                    column != 'table_name' and column != 'row_id'}
    model_class = get_table_model(table_name)
    row = model_class(**updated_data)
    db.session.add(row)
    db.session.commit()
    return redirect('/main')


@app.route('/upgate_row', methods=['POST'])
def upgate_row():
    table_name = request.form['table-select']
    column_names, table_data = get_table_data(table_name, 1)
    excluded_column = ['ID']

    for column in excluded_column:
        if column in column_names:
            column_names.remove(column)
    result = {}
    special_colum = []
    for i in column_names:
        temp = get_distinct_values_p(table_name, i)
        if len(temp) <= 25:
            result[i] = [temp]
            special_colum.append(i)
    return render_template('add_row.html', selected_table=table_name, columns=column_names, special_colum=special_colum,
                           result=result)


@app.route('/upgrade', methods=['POST'])
def upgrade():
    row_id = request.form['row_id']
    table_name = request.form['table_name']

    table_model = get_table_model(table_name)
    row = table_model.query.get(row_id)


    for column in row.__table__.columns:
        column_name = column.name
        new_value = request.form.get(column_name)
        setattr(row, column_name, new_value)


    db.session.commit()

    return render_template('edit_row.html', row=row, table_name=table_name, row_id=row_id)


@app.route('/delete_row', methods=['POST'])
def delete_row():
    row_id = request.form['row_id']
    table_name = request.form['table_name']

    table_model = get_table_model(table_name)
    row = table_model.query.get(row_id)
    print(table_name,row)
    db.session.delete(row)
    db.session.commit()

    return redirect('/main')


@app.route('/search', methods=['POST'])
def search():
    table_search = request.form['table_search']
    column_search = request.form['column_search']
    value_search = request.form['value_search']

    model_class = get_table_model(table_search)
    table_data = db.session.query(model_class).filter(getattr(model_class, column_search) == value_search).limit(
        20).all()

    column_names = [column.name for column in model_class.__table__.columns]

    return render_template('site.html', table_data=table_data, table_name=table_search, column_names=column_names,
                           search_data=[table_search, column_search, value_search], limit=10)


@app.route('/get_columns', methods=['POST'])
def get_columns():
    table = request.json['table']
    columns, _ = get_table_data(table, 1)

    return jsonify(columns)


@app.route('/main', methods=['GET', 'POST'])
def table(limit=10):
    if request.method == 'POST':
        selected_table = request.form['table']
        limit = int(request.form['limit'])
        column_names, table_data = get_table_data(selected_table, limit)
    else:
        column_names = None
        table_data = None
        selected_table = None
    return render_template('site.html', column_names=column_names,
                           table_data=table_data, table_name=selected_table, limit=limit)


#
# MONGO


@app.route('/query/mongo', methods=['GET'])
def query_m():
    average_scores = False
    tests = get_test_list()
    reg_names = get_regname_list()

    return render_template('m_query.html', reg_names=reg_names, tests=tests, average_scores=average_scores)


def get_regname_list():
    collection = db1['participant_mongo']

    pipeline = [
        {
            '$group': {
                '_id': '$RegName'
            }
        },
        {
            '$project': {
                '_id': 0,
                'RegName': '$_id'
            }
        }
    ]

    result = collection.aggregate(pipeline)
    regname_list = [document['RegName'] for document in result]

    return regname_list


def get_test_list():
    collection = db1['testing_mongo']

    pipeline = [
        {
            '$group': {
                '_id': '$Test'
            }
        },
        {
            '$project': {
                '_id': 0,
                'Test': '$_id'
            }
        }
    ]

    result = collection.aggregate(pipeline)
    test_list = [document['Test'] for document in result]

    return test_list

@app.route('/query/mongo', methods=['POST'])
def execute_query_m():
    global cache_to_change
    reg_name = request.form.get('reg_name')
    test_name = request.form.get('test_name')
    year = request.form.get('year')
    score_type = request.form.get('score_type')  # Додати можливість вибору типу балу

    tests = get_test_list()
    reg_names = get_regname_list()
    year_options = [2019, 2020]
    arguments = {'selected_reg_name': reg_name, 'selected_test_name': test_name, 'selected_year': year,
                 'score_type': score_type, 'tests': tests, 'reg_names': reg_names, 'year_options': year_options}

    match_filter = {
        'TestStatus': 'Зараховано'
    }

    if test_name != 'all':
        match_filter['Test'] = test_name

    # Додати динамічне формування групування в залежності від вибраного типу балу
    group_fields = {
        '_id': {
            'Year': '$Year',
            'RegName': '$participant.RegName'
        }
    }
    if 'average' in score_type:
        group_fields['average'] = {'$avg': {'$toDouble': '$Ball100'}}
    if 'max' in score_type:
        group_fields['max'] = {'$max': {'$toDouble': '$Ball100'}}
    if 'min' in score_type:
        group_fields['min'] = {'$min': {'$toDouble': '$Ball100'}}

    pipeline = [
        {
            '$match': match_filter
        },
        {
            '$lookup': {
                'from': 'participant_mongo',
                'localField': 'Part_ID',
                'foreignField': '_id',
                'as': 'participant'
            }
        },
        {
            '$group': group_fields
        },
        {
            '$project': {
                '_id': 0,
                'Year': '$_id.Year',
                'RegName': '$_id.RegName',
                'average': 1,
                'max': 1,
                'min': 1
            }
        }
    ]

    if reg_name != 'all':
        pipeline.append({
            '$match': {
                'RegName': reg_name
            }
        })

    if year != 'all':
        pipeline.append({
            '$match': {
                'Year': int(year)
            }
        })

    result = db1['testing_mongo'].aggregate(pipeline)

    scores_dict = {}
    for elem in result:
        RegName = elem["RegName"]
        Year = elem["Year"]
        scores_dict[f'{RegName[0]},{Year}'] = {
            'reg_name': RegName[0],
            'year': Year,
            'average': elem.get('average', None),
            'max': elem.get('max', None),
            'min': elem.get('min', None)
        }

    return render_template('m_query.html', average_scores=scores_dict, reg_name=reg_name, year=year, **arguments)



@app.route('/update_row/mongo', methods=['POST'])
def update_row_m():
    table_name = request.form.get('table_name')
    row_id = request.form.get('row_id')
    updated_data = {}

    for column, value in request.form.items():
        if column not in ['table_name', 'row_id']:
            try:
                # Спробуйте перетворити значення на число
                updated_data[column] = int(value)
            except ValueError:
                # Якщо не вдалося перетворити на число, лишаємо значення як є
                updated_data[column] = value

    collection = db1[table_name]
    global cache_to_change

    if table_name == "testing_mongo" or table_name == 'participant_mongo':
        cache_to_change = False

    if table_name != "participant_mongo":
        query = {'_id': int(row_id)}
    else:
        query = {'_id': row_id}

    update_data = {'$set': updated_data}
    collection.update_one(query, update_data, upsert=True)
    selected_table = table_name
    limit = 10
    column_names = list(collection.find_one().keys())
    all_pts = list(collection.find().limit(limit))
    return render_template('m_site.html', column_names=column_names, table_data=all_pts, table_name=selected_table)


def get_distinct_values(collection_name, column_name):
    collection = db1[collection_name]
    pipeline = [
        {"$group": {"_id": f"${column_name}"}},
        {"$project": {"_id": 0, column_name: "$_id"}}
    ]
    result = collection.aggregate(pipeline, allowDiskUse=True)
    distinct_values = [item[column_name] for item in result]
    return distinct_values


@app.route('/add_row/mongo', methods=['GET'])
def add_row_m():
    return render_template('m_add_row.html')


@app.route('/add_rows/mongo', methods=['POST'])
def add_rows_m():
    collection_name = request.form['table_name']
    updated_data = {column: request.form.get(column) for column in request.form if
                    column != 'table_name' and column != 'row_id'}
    if collection_name != "participant_mongo":
        random_id = struct.unpack('I', uuid.uuid4().bytes[:4])[0]
    else:
        random_id = str(uuid.uuid4())
    for i in updated_data:
        elem = updated_data[i]
        if elem.isdigit():
            updated_data[i] = int(updated_data[i])
    updated_data['_id'] = random_id

    collection = db1[collection_name]
    collection.insert_one(updated_data)
    global cache_to_change
    if collection_name == "testing_mongo" or collection_name == 'participant_mongo':
        cache_to_change = False
    return redirect('/main/mongo')


@app.route('/upgate_row/mongo', methods=['POST'])
def upgate_row_m():

    table_name = request.form['table-select']

    collection = db1[table_name]

    column_names = list(collection.find_one().keys())
    excluded_column = ['_id']

    for column in excluded_column:
        if column in column_names:
            column_names.remove(column)

    result = {}
    special_colum = []
    for i in column_names:
        temp = get_distinct_values(table_name, i)
        if len(temp) <= 25:
            result[i] = [temp]
            special_colum.append(i)
    return render_template('m_add_row.html', selected_table=table_name, columns=column_names, special_colum=special_colum,
                           result=result)



@app.route('/delete_row/mongo', methods=['POST'])
def delete_row_m():
    row_id = request.form['row_id']
    table_name = request.form['table_name']
    global cashe_to_change
    collection = db1[table_name]
    if table_name == "testing_mongo" or table_name =='participant_mongo' :
        cashe_to_change = False
    if table_name != "participant_mongo":
        query = {'_id': int(row_id)}
        collection.delete_one(query)
    else:
        query = {'_id': row_id}
        collection.delete_one(query)

    return redirect('/main/mongo')


@app.route('/search/mongo', methods=['POST'])
def search_m():
    table_search = request.form['table_search']
    column_search = request.form['column_search']
    value_search = request.form['value_search']

    collection = db1[table_search]
    if str(value_search).isdigit():
        query = {column_search: int(value_search)}
    else:
        query = {column_search: value_search}

    results = collection.find(query).limit(20)

    table_data = list(results)

    column_names = list(collection.find_one().keys())

    return render_template('m_site.html', table_data=table_data, table_name=table_search, column_names=column_names,
                           search_data=[table_search, column_search, value_search], limit=10)


@app.route('/get_columns/mongo', methods=['POST'])
def get_columns_m():
    table = request.json['table']
    collection = db1[table]
    first_document = collection.find_one()
    column_names = list(first_document.keys())
    return jsonify(column_names)


@app.route('/select_database', methods=['POST'])
def select_database_m():
    database = request.form.get('database')
    if database == "mongo":
        return redirect('/main/mongo')
    else:
        return redirect('/main')


@app.route('/main/mongo', methods=['GET', 'POST'])
def table_m(limit=10):
    if request.method == 'POST':
        selected_table = request.form['table']
        limit = int(request.form['limit'])
        collection = db1[selected_table]

        column_names = list(collection.find_one().keys())
        all_pts = list(collection.find().limit(limit))
    else:
        all_pts = None
        column_names = None
        selected_table = None
    return render_template('m_site.html', column_names=column_names,
                           table_data=all_pts, table_name=selected_table, limit=limit)


if __name__ == '__main__':
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLA_CONFIG_STR
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db = SQLAlchemy()
    from models import *

    db.init_app(app)

    start_time = time.time()

    app.run(
        host='0.0.0.0',
        debug=True,
        port=5000
    )
    fin_time = time.time() - start_time
