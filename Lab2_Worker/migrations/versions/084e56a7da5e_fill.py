"""fill

Revision ID: 084e56a7da5e
Revises: e6ed70b5e6e8
Create Date: 2023-10-27 20:13:18.019940

"""
import os
import time
from alembic import op
import sqlalchemy as sa
from sqlalchemy import and_, union
from flask_sqlalchemy import SQLAlchemy


# revision identifiers, used by Alembic.
revision = '084e56a7da5e'
down_revision = 'e6ed70b5e6e8'
branch_labels = None
depends_on = None


def upgrade():
    GENERAL_TABLE_NAME = "res_zno"
    start_time = time.time()

    db = SQLAlchemy()

    metadata = sa.MetaData()
    metadata.reflect(bind=op.get_bind())

    class ZNOResult(db.Model):
        __table__ = metadata.tables[GENERAL_TABLE_NAME]

    class Meducational_institutions(db.Model):
        __table__ = metadata.tables["educational_institutions"]

    class Mteritory(db.Model):
        __table__ = metadata.tables["territories"]

    class Mparticipants(db.Model):
        __table__ = metadata.tables["participants"]

    class Mpoints_of_observation(db.Model):
        __table__ = metadata.tables["points_of_observation"]

    class Mtestings(db.Model):
        __table__ = metadata.tables["testings"]

    def get_select(param, arg_return=False):
        args = []
        for old_name, new_name in param:
            args.append(ZNOResult.__table__.c[f'{old_name}'].label(f'{new_name}'))
        if arg_return:
            return args
        return sa.select(*args).distinct()

    def fill_table(Model, column_params, query=None):
        if query is None:
            query_dict = op.get_bind().execute(get_select(column_params))
        else:
            query_dict = op.get_bind().execute(query)
        for i, p in enumerate(query_dict.mappings().partitions(100000)):
            print(f"Migrating {Model.__table__} [~ {i * 100000}]")
            op.bulk_insert(Model.__table__, list(map(dict, p)))

    print("Initialization fill tables...")
    # teritory
    print("Migrating Territory")
    column_params = [('tername', 'Name'), ('tertypename', 'TypeName')]
    fill_table(Mteritory, column_params)

    # educational_institutions
    print("Migrating educational_institutions")
    column_params = [('eoname', 'Name'), ('eotypename', 'TypeName'), ('eoregname', 'RegName'),
                     ('eoareaname', 'AreaName'),
                     ('eotername', 'TerName'), ('eoparent', 'Parent')]
    fill_table(Meducational_institutions, column_params)

    # participants
    print("Migrating participants")
    column_params = [('outid', 'ID'), ('birth', 'Birth'), ('sextypename', 'SexTypeName'), ('areaname', 'AreaName'),
                     ('regname', 'RegName'), ('classprofilename', 'ClassProfileName'),
                     ('classlangname', 'ClassLangName')]
    q_select = sa.select(*get_select(column_params, arg_return=True),
                         Mteritory.ID.label("Ter_id"),
                         Meducational_institutions.ID.label("EO_id")) \
        .join(Mteritory, Mteritory.Name == ZNOResult.tername) \
        .join(Meducational_institutions, and_(Meducational_institutions.Name == ZNOResult.eoname,
                                              Meducational_institutions.Parent == ZNOResult.eoparent,
                                              Meducational_institutions.TerName == ZNOResult.eotername,
                                              Meducational_institutions.TypeName == ZNOResult.eotypename)).distinct()
    fill_table(Mparticipants, column_params, q_select)

    # testings and points_of_observation
    print("Migrating Points of observation")

    test_column_params = [('test', 'Test'), ('teststatus', 'TestStatus'),
                          ('ball100', 'Ball100'), ('ball12', 'Ball12'), ('ball', 'Ball')]
    subjects = ['ukr', 'fra', 'deu', 'spa', 'eng', "math", "hist", "phys", "chem", "bio", "geo"]

    boole = {'ukr': Mpoints_of_observation.Name == ZNOResult.ukrptname,
             'math': Mpoints_of_observation.Name == ZNOResult.mathptname,
             'fra': Mpoints_of_observation.Name == ZNOResult.fraptname,
             'deu': Mpoints_of_observation.Name == ZNOResult.deuptname,
             'spa': Mpoints_of_observation.Name == ZNOResult.spaptname,
             'hist': Mpoints_of_observation.Name == ZNOResult.histptname,
             'phys': Mpoints_of_observation.Name == ZNOResult.physptname,
             'chem': Mpoints_of_observation.Name == ZNOResult.chemptname,
             'bio': Mpoints_of_observation.Name == ZNOResult.bioptname,
             'geo': Mpoints_of_observation.Name == ZNOResult.geoptname,
             'eng': Mpoints_of_observation.Name == ZNOResult.engptname
             }

    def get_subject_column_params(subject, columns):
        column_params = []
        lang_subjects = ['ukr', 'fra', 'deu', 'spa', 'eng']
        if subject in lang_subjects and 'Lang' in columns:
            columns.remove('Lang')
        if subject != 'ukr' and 'AdaptScale' in columns:
            columns.remove('AdaptScale')
        if 'Test' in columns:
            for column in columns:
                column_params.append((f"{subject}{column.lower()}", column))
            column_params.append(("year", "Year"))
        else:
            for column in columns:
                column_params.append((f"{subject}{column.lower()}", column[2:]))

        return column_params

    def get_test_select():
        lang_subjects = ['fra', 'deu', 'spa', 'eng']
        other_subjects = ["math", "hist", "phys", "chem", "bio", "geo"]

        pt_list = []

        pt_columns = ['PTName', 'PTRegName', 'PTAreaName', 'PTTerName']

        for subject in other_subjects:
            pt_list.append(get_select(get_subject_column_params(subject, pt_columns)))

        for subject in lang_subjects:
            pt_list.append(get_select(get_subject_column_params(subject, pt_columns)))

        pt_list.append(get_select(get_subject_column_params('ukr', pt_columns)))

        return union(*pt_list)

    fill_table(Mpoints_of_observation, [], query=get_test_select())

    print("Migrating Testings")

    for subject in subjects:
        new_test_column_params = []
        for old_name, new_name in test_column_params:
            new_test_column_params.append((f"{subject}{old_name}", new_name))
        new_test_column_params.append(('year', 'Year'))

        print(f'Filling subject - {subject}')

        q_select = sa.select(*get_select(new_test_column_params, arg_return=True),
                             Mpoints_of_observation.ID.label("Point_ID"),
                             Mparticipants.ID.label("Part_ID")) \
            .join(Mpoints_of_observation, boole[subject]) \
            .join(Mparticipants, Mparticipants.ID == ZNOResult.outid).distinct()
        fill_table(Mtestings, new_test_column_params, q_select)

    fin_time = time.time() - start_time
    print(f"Migrated: {fin_time} seconds ({round(fin_time / 60, 2)} minutes) ")


def downgrade():
    op.drop_table('testings')
    op.drop_table('participants')
    op.drop_table('territories')
    op.drop_table('points_of_observation')
    op.drop_table('educational_institutions')