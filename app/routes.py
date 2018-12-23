import collections
import string
import time

from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, Markup
from wtforms import Form, StringField, SelectField
from wtforms.validators import DataRequired, Email, Length, Regexp

import config
from app import cache
from app import db
from app import errors
from app.validators import Region, City


class CommentForm(Form):
    f_name = StringField('First name', validators=[DataRequired('werwr'), Length(min=2, max=25)])
    l_name = StringField('Last name', validators=[DataRequired(), Length(min=2, max=25)])
    m_name = StringField('Middle name')

    region = SelectField(label='Region', validators=[DataRequired(), Region()])
    city = SelectField('City', validators=[DataRequired(), City()])

    email = StringField('Email', validators=[DataRequired(), Email()])

    regex = r'^(\+7|7|8)?(\(?\d{3}\)?)\d{7,10}$'
    message = 'Invalid phone number'
    phone = StringField('Phone', validators=[DataRequired(), Regexp(regex=regex, message=message)])

    comment = StringField('Comment', validators=[DataRequired(), Length(min=10, max=255)])


app = Flask(__name__)


@app.route('/comments', methods=['GET', 'POST'])
def comments():
    comment_form = CommentForm(request.form)

    regions_details = cache.get_regions_from_cache()
    region_choices = ['Select region...'] + sorted(regions_details)
    comment_form.region.choices = [(rc, rc) for rc in region_choices]

    city_choices = ['Select city...']
    if comment_form.city.data != 'None':
        city_choices.append(comment_form.city.data)
    comment_form.city.choices = [(rc, rc) for rc in city_choices]

    if request.method == 'POST' and comment_form.validate():

        insert_stmt = """
            INSERT INTO comments (
                first_name,
                last_name,
                middle_name,
                email,
                phone,
                comment_text,
                city_id
            ) VALUES (
                '{FIRST_NAME}', 
                '{LAST_NAME}',
                '{MIDDLE_NAME}',
                '{EMAIL}',
                '{PHONE}',
                '{COMMENT}',
                '{CITY}'
            )
        """

        try:
            city_id = ''
            for city_details in regions_details[comment_form.region.data]['cities']:
                if city_details['city_name'] == comment_form.city.data:
                    city_id = city_details['city_id']
                    break

            db_instance = db.PostgresDB()
            db_instance.insert(insert_stmt.format(
                FIRST_NAME=comment_form.f_name.data,
                LAST_NAME=comment_form.l_name.data,
                MIDDLE_NAME=comment_form.m_name.data,
                EMAIL=comment_form.email.data,
                PHONE=comment_form.phone.data,
                COMMENT=comment_form.comment.data,
                CITY=city_id
            ))

            flash(u'{} {}, thanks for comment!'.format(
                comment_form.f_name.data,
                comment_form.m_name.data
            ), category='alert-success')

            return redirect(url_for('comments'))

        except:
            flash('Unfortunately, we can not save your comment now.', category='alert-danger')
            return redirect(url_for('comments'))

    return render_template('form.html', form=comment_form)


@app.route('/regions', methods=['GET'])
def regions():
    now = time.strftime("%c")
    regions_details = cache.get_regions_from_cache()

    response_regions = []
    region_from_arg = request.args.get('region')
    if region_from_arg:
        region_detail = regions_details.get(region_from_arg, None)
        if not region_detail:
            message = 'region {} not found'.format(region_from_arg)
            response = {'status': True, 'regions': [], 'message': message, 'timestamp': now}
        else:
            response = {'status': True, 'regions': [regions_details[region_from_arg]], 'timestamp': now}

        return jsonify(response), 200

    for region_name in sorted(regions_details):
        response_regions.append(regions_details[region_name])

    response = {'status': True, 'regions': response_regions, 'timestamp': now}
    return jsonify(response), 200


@app.route('/view', methods=['GET'])
def get_comments():
    default_sort_col = 'created_at'
    date_format = 'DD-MM-YYYY HH24:MI:SS'

    _sort_fields = [
        # db column name and alias
        ('comment_id', 'id'),
        ('first_name', 'First name'),
        ('last_name', 'Last name'),
        ('middle_name', 'Middle name'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('region_name', 'Region'),
        ('city_name', 'City'),
        ('comment_text', 'Comment'),
        (default_sort_col, 'Created')
    ]

    page = request.args.get('page', default=1, type=int)
    if page <= 0:
        page = 1

    limit = request.args.get('limit', default=50, type=int)
    if limit <= 0:
        limit = 100

    regions_ids = request.args.get('regions', 'none').split(',')
    regions_ids = list(filter(lambda _id: _id.isdigit(), regions_ids))
    cities_ids = request.args.get('city', 'none').split(',')
    cities_ids = list(filter(lambda _id: _id.isdigit(), cities_ids))

    sort_order = 'DESC'
    sort_field = request.args.get('sort', default=default_sort_col, type=string)
    if sort_field[0] in '-+':
        sort_order = {'+': 'ASC', '-': 'DESC'}.get(sort_field[0])
        sort_field = sort_field[1:]

    if sort_field not in sum(_sort_fields, ()):
        sort_field = default_sort_col

    where = ''
    if len(regions_ids):
        where = 'WHERE (r.region_id IN({}))'.format(','.join(regions_ids))

    if len(cities_ids):
        where = (where if where + ' AND (c.city_id IN({}))' else 'WHERE c.city_id IN({})'). \
            format(','.join(cities_ids))

    query_stmt = """
        SELECT {COLUMNS}
        FROM regions r JOIN cities c ON r.region_id = c.region_id
            JOIN comments cm ON c.city_id = cm.city_id
        {WHERE} {ORDERED_BY} {OFFSET} {LIMIT};
    """

    try:
        select_columns = ', '.join(["{} \"{}\"".format(col[0], col[1]) for col in _sort_fields[:-1]])
        select_columns += (", to_char({}, '{}') \"{}\"".format(default_sort_col, date_format, _sort_fields[-1][-1]))

        query = query_stmt.format(
            COLUMNS=select_columns,
            WHERE=where,
            ORDERED_BY='ORDER BY {} {}'.format(sort_field, sort_order),
            OFFSET='OFFSET {}'.format((int(page) - 1) * int(limit)),
            LIMIT='LIMIT {}'.format(limit)
        )

        header_only = False
        ordered_comments = []
        db_instance = db.PostgresDB()
        for comment in db_instance.query(query):
            ordered_comments.append(collections.OrderedDict(zip([col[-1] for col in _sort_fields], comment)))

        if not len(ordered_comments):
            ordered_comments.append(
                collections.OrderedDict(zip([col[-1] for col in _sort_fields], ('',) * len(_sort_fields))))
            header_only = True

        return render_template('comments.html', comments=ordered_comments, header_only=header_only)

    except:
        flash('Internal service problem:(', category='alert-danger')
        return redirect(url_for('comments'))


@app.route('/comments/delete', methods=['POST'])
def delete_comments():
    parsed_json_body = request.get_json(force=True)
    if not parsed_json_body:
        raise errors.ErrorResponse('not json request body')

    input_comment_ids = parsed_json_body.get('comment_ids', None)
    if not input_comment_ids:
        raise errors.ErrorResponse('not found required field', payload={'field': 'comment_ids'})

    comments_ids = []
    try:
        comments_ids.append(int(input_comment_ids))
    except:
        if isinstance(input_comment_ids, list):
            for comment_id in input_comment_ids:
                comments_ids.append(comment_id)
        else:
            raise errors.ErrorResponse('must be comment id or arrays of comments ids', payload={'field': 'comment_ids'})

    delete_stmt = 'DELETE FROM comments WHERE comment_id IN({})'
    try:
        db_instance = db.PostgresDB()
        deleted_count = db_instance.delete(delete_stmt.format(','.join(comments_ids)))
        return jsonify({'status': True, 'deleted': deleted_count}), 200

    except errors.DatabaseException:
        raise errors.ErrorResponse('Internal service problem')


@app.route('/stat', methods=['GET'])
def statistic():
    stat_count_path = 'statistic.count'
    conf = config.load_config(config.get_config_path(), {stat_count_path: 5})

    query_stmt = """
        SELECT r.region_id, region_name, COUNT(region_name)
        FROM regions r JOIN cities c ON r.region_id = c.region_id
            JOIN comments cm ON c.city_id = cm.city_id
        GROUP BY r.region_id 
        HAVING COUNT(r.region_id) > {COUNT}
        ORDER BY COUNT(region_name) DESC;
    """

    try:
        header_only = False
        comment_statistics = []
        db_instance = db.PostgresDB()
        for region_stat in db_instance.query(query_stmt.format(COUNT=conf[stat_count_path])):
            region_statistic = collections.OrderedDict()
            url = Markup('<a href="{}">{}</a>'.format(url_for('get_comments', regions=region_stat[0]), region_stat[1]))
            region_statistic['Region'] = url
            region_statistic['Comments'] = region_stat[2]
            comment_statistics.append(region_statistic)

        if not len(comment_statistics):
            comment_statistics.append(collections.OrderedDict(Region='', Comments=''))
            header_only = True

        print(comment_statistics)

        return render_template('stat.html', comment_statistics=comment_statistics, header_only=header_only)

    except:
        flash('Internal service problem:(', category='alert-danger')
        return redirect(url_for('comments'))


@app.errorhandler(errors.ErrorResponse)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.http_code
    return response
