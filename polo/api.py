"""
api.py
==============================
The methods contained in this file represent the POLO backend, which is called by the frontend code.
The endpoints should be considered a private API, which may change with no notice based on changes
to the frontend code, specifically found in polo/static/js/application.js.
"""

import re
import shlex
from flask import request, jsonify, abort

from polo import app
from polo.common import get_result, merge_dicts
from polo.database import polo_engine, rm_engines
from polo.sql import *


@app.after_request
def apply_caching(response):
    """
    This method applies a cookie to each response, which avoids an error in Chrome, which looks like:
      "A cookie associated with a cross-site resource at <URL> was set without the `SameSite`attribute. A f..."
    :param response:
    :return: response with cookie set to avoid issues with cross-site resources
    """
    response.headers["Set-Cookie"] = "HttpOnly;Secure;SameSite=Strict";
    return response


@app.route('/healthy', methods=['GET'])
def healthy():
    """
    get:
        summary: Return a simple string with a status code of 200 to signify
                 that this web application is working properly. This is used
                 in systems such as Cloud Foundry.
        description: simple response indicates application is running.
        parameters:
        responses:
            200:
                description: text
    """
    return "POLO is healthy"


@app.route('/cloudfoundryapplication', methods=['GET'])
def cloudfoundry():
    """
    get:
        summary: Return a simple string with a status code of 200 to signify
                 that this web application is working properly. This is used
                 in systems such as Cloud Foundry.
        description: simple response indicates application is running.
        parameters:
        responses:
            200:
                description: text
    """
    return "POLO can be run in Cloud Foundry"


@app.route('/status', methods=['GET'])
def status():
    """
    get:
        summary: Return JSON with information about all of the connected databases to show
                 that this web application not only works, but can also connect to the
                 dependent databases
        description: response indicates application is running and that database connections are valid
        parameters:
        responses:
            200:
                description: JSON with information about number of database records, containing an errors
                             key with error information
    """
    results = {}
    errors = []

    # POLO database
    try:
        connection = polo_engine.connect()
        sql = 'select count(*) as c from image_scores'
        resultproxy = connection.execute(sql)
        results['polo_score_count'] = get_result(resultproxy)[0]['c']
        connection.close()
    except:
        errors.append("Problem connecting to POLO database")
    finally:
        if 'connection' in locals():
            connection.close()

    # RockMaker databases
    for rm_engine_key in rm_engines.keys():
        try:
            connection = rm_engines[rm_engine_key].connect()
            sql = 'select count(*) as c from Plate'
            resultproxy = connection.execute(sql)
            results[f'rm_{rm_engine_key}_plate_count'] = get_result(resultproxy)[0]['c']
            connection.close()
        except:
            errors.append(f"Problem connecting to RockMaker database {rm_engine_key}")
        finally:
            if 'connection' in locals():
                connection.close()

    return jsonify({'results': results, 'errors': errors})


@app.route('/api/dispute/', methods=['POST'])
def dispute():
    """
    post:
        summary: Save a manual annotation for a single scored image
        description: response indicates application is running and that database connections are valid
        parameters:
            - name: image_score_id
              description: ID for the image_score to dispute
              type: integer
              required: true
            - name: disputed_by
              description: the username of the person manually annotating the score
              type: string
              required: true
            - name: manual_call
              description: a string representing the manual call, typically one character of 'CPXOD'
              type: string
              required: true
        responses:
            200:
                description: A JSON object with the details of the inserted row, including ID
    """
    image_score_id = request.form.get('image_score_id')
    disputed_by = request.form.get('disputed_by')
    manual_call = request.form.get('manual_call')

    if image_score_id and disputed_by and manual_call:
        connection = polo_engine.connect()

        sql = 'insert into disputes (image_score_id, disputed_by, manual_call) values (%s, %s, %s)'
        resultproxy = connection.execute(sql, (int(image_score_id), disputed_by, manual_call))

        # get last insert (including automatically-generated ID and DATE
        sql = 'select * from disputes where id = LAST_INSERT_ID()'
        resultproxy = connection.execute(sql)
        entry = get_result(resultproxy)

        connection.close()
        return jsonify(entry)
    else:
        return abort(400, "Need to POST key/value pairs for image_score_id, disputed_by, and manual_call")


@app.route('/api/favorite/', methods=['POST'])
def toggle_favorite():
    """
    Under construction
    """
    image_score_id = request.form.get('image_score_id')
    favorited_by = request.form.get('favorited_by')

    if image_score_id and favorited_by:
        connection = polo_engine.connect()
        sql = 'select plate_id, well_num, drop_num from image_scores where id = %s'
        resultproxy = connection.execute(sql, (int(image_score_id)))
        result = get_result(resultproxy)[0]
        plate_id = result['plate_id']
        well_num = result['well_num']
        drop_num = result['drop_num']
    else:
        connection.close()
        return abort(400, "Need to POST key/value pairs for image_score_id and favorited_by")

    if plate_id and well_num and drop_num:
        sql = 'select count(id) as count from favorites where plate_id = %s and well_num = %s and drop_num = %s and favorited_by = %s'
        resultproxy = connection.execute(sql, (plate_id, well_num, drop_num, favorited_by))
        result = get_result(resultproxy)[0]

    connection.close()
    return jsonify(result)


@app.route('/api/search/', methods=['GET'])
def search():
    """
    get:
        summary: Search a RockMaker instance for matching plate, barcode, or experiment name
        description: Search a RockMaker instance for matching plate, barcode, or experiment name
        parameters:
            - name: source_id
              description: primary key in POLO database for RockMaker instance to search. Default: 1
              type: integer
              required: false
            - name: folder
              description: name of top-level folder used to limit search
              type: string
              required: false
            - name: q
              description: query string, which can be split by spaces unless enclosed by quotation to find multiple plates
              type: string
              required: true
        responses:
            200:
                description: A JSON object containing tree information for matching plates, barcodes, and experiments
    """
    source_id = request.args.get('source_id')
    if source_id is None:
        source_id = 1
    else:
        source_id = int(source_id)

    folder = request.args.get('folder') or request.args.get('isid')

    query_string = request.args.get('q')
    if query_string is None or query_string == '':
        return jsonify([])

    rm_connection = rm_engines[source_id].connect()

    # split by space unless enclosed by quotation - use shlex.split (via https://stackoverflow.com/questions/79968/split-a-string-by-spaces-preserving-quoted-substrings-in-python)
    parsed_query = shlex.split(query_string)

    # only accept queries which are 3+ characters
    limited_parsed_query = [p for p in parsed_query if len(p) > 2]
    if limited_parsed_query == []:
        return jsonify([])

    matching_plates = []
    for p in limited_parsed_query:
        # MATCHING TREENODES VIA PLATE ID
        resultproxy = rm_connection.execute(sql_nodes_from_matching_plateid, f'%{p}%')
        m = get_result(resultproxy)
        node_ids = [x['id'] for x in m]
        if len(node_ids) > 0:
            # get paths for matching plate nodes
            query_placeholders = ','.join(['?'] * len(node_ids))
            resultproxy = rm_connection.execute(
                sql_path_to_experiments_via_nodeids.format(query_placeholders=query_placeholders), node_ids)
            paths = get_result(resultproxy)
            merged = merge_dicts(m, paths, 'id')

            if folder:
                merged = [x for x in merged if x['path'].startswith(folder)]

            for x in merged:
                x['node_type'] = 'ExperimentPlate'
                if 'folder_name' in x:

                    # OBFUSCATION FOR DEMO PURPOSES
                    if 'demo' in request.args or app.config['DEMO']:
                        x['path'] = 'XXXXX'
                        x['folder_name'] = 'XXXXX'

                    if len(x['folder_name']) > 22:
                        x.update({'name': x['folder_name'][:20] + '... > ' + x['name']})
                    else:
                        x.update({'name': x['folder_name'] + ' > ' + x['name']})
            matching_plates.extend(merged)

    matching_barcodes = []
    for p in limited_parsed_query:
        # MATCHING TREENODES VIA PLATE BARCODE
        resultproxy = rm_connection.execute(sql_nodes_from_matching_barcode, f'%{p}%')
        m = get_result(resultproxy)
        node_ids = [x['id'] for x in m]
        if len(node_ids) > 0:
            # get paths for matching plate nodes
            query_placeholders = ','.join(['?'] * len(node_ids))
            resultproxy = rm_connection.execute(
                sql_path_to_experiments_via_nodeids.format(query_placeholders=query_placeholders), node_ids)
            paths = get_result(resultproxy)
            merged = merge_dicts(m, paths, 'id')

            if folder:
                merged = [x for x in merged if x['path'].startswith(folder)]

            for x in merged:
                x['node_type'] = 'ExperimentPlate'
                if 'folder_name' in x:

                    # OBFUSCATION FOR DEMO PURPOSES
                    if 'demo' in request.args or app.config['DEMO']:
                        x['path'] = 'XXXXX'
                        x['folder_name'] = 'XXXXX'

                    if len(x['folder_name']) > 22:
                        x.update({'name': x['folder_name'][:20] + '... > ' + x['name']})
                    else:
                        x.update({'name': x['folder_name'] + ' > ' + x['name']})
            matching_barcodes.extend(merged)

    matching_experiments = []
    for p in limited_parsed_query:
        # MATCHING EXPERIMENTS VIA TEXT
        resultproxy = rm_connection.execute(sql_path_to_experiments_like_text, f'%{p}%')
        m = get_result(resultproxy)
        app.logger.debug("Matching experiments {} {}".format(len(m), m))

        node_ids = [x['id'] for x in m]
        if len(node_ids) > 0:
            # get plates for matching experiment nodes
            query_placeholders = ','.join(['?'] * len(node_ids))
            sql = sql_plates_from_experiment_nodes.format(query_placeholders=query_placeholders)
            resultproxy = rm_connection.execute(sql, node_ids)
            plates = get_result(resultproxy)
            app.logger.debug("Plates {} {}".format(len(plates), plates))

            merged = []
            for plate in plates:
                for match in m:
                    if plate['parent_id'] == match['id']:
                        plate['folder_name'] = match['folder_name']
                        plate['path'] = match['path']
                        merged.append(plate)

            app.logger.debug("Merged {} {}".format(len(merged), merged))

            if folder:
                merged = [x for x in merged if x['path'].startswith(folder)]

            for x in merged:
                x['node_type'] = 'ExperimentPlate'
                if 'folder_name' in x:
                    if 'name' not in x:
                        x['name'] = '?'

                    # OBFUSCATION FOR DEMO PURPOSES
                    if 'demo' in request.args or app.config['DEMO']:
                        x['path'] = 'XXXXX'
                        x['folder_name'] = 'XXXXX'

                    if len(x['folder_name']) > 22:
                        x.update({'name': x['folder_name'][:20] + '... > ' + x['name']})
                    else:
                        x.update({'name': x['folder_name'] + ' > ' + x['name']})
            matching_experiments.extend(merged)

    # MATCHING EXPERIMENTS VIA PROTEIN FORMULATION
    matching_proteins = []
    for p in limited_parsed_query:
        # MATCHING PLATES VIA PROTEIN
        resultproxy = rm_connection.execute(sql_plates_from_matching_protein, f'%{p}%')
        m = get_result(resultproxy)

        if folder:
            m = [x for x in m if x['path'].startswith(folder)]

        if len(m) > 0:
            for x in m:
                x['node_type'] = 'ExperimentPlate'
                if 'folder_name' in x:

                    # OBFUSCATION FOR DEMO PURPOSES
                    if 'demo' in request.args or app.config['DEMO']:
                        x['path'] = 'XXXXX'
                        x['folder_name'] = 'XXXXX'

                    if len(x['folder_name']) > 22:
                        x.update({'name': x['folder_name'][:20] + '... > ' + x['name']})
                    else:
                        x.update({'name': x['folder_name'] + ' > ' + x['name']})
            matching_proteins.extend(m)

    matches = []

    if len(matching_plates) > 0:
        matches.append({'name': 'Matching plate IDs',
                        'id': '0',
                        'node_type': 'Folder',
                        'has_children': True,
                        'children': matching_plates})

    if len(matching_barcodes) > 0:
        matches.append({'name': 'Matching barcodes',
                        'id': '00',
                        'node_type': 'Folder',
                        'has_children': True,
                        'children': matching_barcodes})

    if len(matching_experiments) > 0:
        matches.append({'name': 'Matching experiments',
                        'id': '000',
                        'node_type': 'Folder',
                        'has_children': True,
                        'children': matching_experiments})

    if len(matching_proteins) > 0:
        matches.append({'name': 'Matching proteins',
                        'id': '0000',
                        'node_type': 'Folder',
                        'has_children': True,
                        'children': matching_proteins})

    return jsonify(matches)


@app.route('/api/tree/', methods=['GET'])
def get_tree():
    """
    get:
        summary: Get RockMaker tree nodes
        description: Obtain the RockMaker tree, optionally limited to a top-level folder, or by a parentID to
                     allow for lazy-loading of a tree element
        parameters:
            - name: source_id
              description: primary key in POLO database for RockMaker instance to search. Default: 1
              type: integer
              required: false
            - name: folder
              description: name of top-level folder used to limit search
              type: string
              required: false
            - name: parentId
              description: name of top-level folder used to limit search, default: 3
              type: string
              required: false
        responses:
            200:
                description: A JSON object containing tree information below specified or default node
    """
    source_id = request.args.get('source_id')
    if source_id is None:
        source_id = 1
    else:
        source_id = int(source_id)

    rm_connection = rm_engines[source_id].connect()

    # default
    start_node = 3

    # if folder is set, determine root node from that...
    folder = request.args.get('folder') or request.args.get('isid')
    if folder is not None:
        try:
            resultproxy = rm_connection.execute(sql_tree_user_node, folder)
            start_node = get_result(resultproxy)[0]['id']
        except:
            start_node = 3

    # but if parentId is specified, use that instead. If neither specified, use node_id = 3
    # node_id = 3 is the "Projects" level in RockMaker
    parent_id = request.args.get('parentId') or request.args.get('parent_id') or request.args.get('ParentID')
    if parent_id is not None:
        start_node = parent_id

    resultproxy = rm_connection.execute(sql_tree, start_node)
    nodes = get_result(resultproxy)
    rm_connection.close()

    # OBFUSCATION FOR DEMO PURPOSES
    if 'demo' in request.args or app.config['DEMO']:
        for node in nodes:
            if node['node_type'] != 'ExperimentPlate':
                node['name'] = 'XXXXX'

    return jsonify(nodes)


@app.route('/api/sources/', methods=['GET'])
def get_sources():
    """
    get:
        summary: Get list of configured RockMaker instances
        description: Return list of RockMaker source_id values and their associated information,
                     including name and url_prefix for constructing URLs to images and date of
                     last update
        parameters:
        responses:
            200:
                description: JSON object with information for all configured RockMaker instances
    """
    polo_connection = polo_engine.connect()
    sql = "select * from sources"
    resultproxy = polo_connection.execute(sql)
    sources = get_result(resultproxy)

    # add last score date from each source to the source name.
    # This *should* be done in a single query, but it's been too slow.
    sql = """
        select DATE_FORMAT(i.date_scored, '%%d-%%b-%%Y %%H:%%i') d
        from image_scores i
        where i.source_id = %s
        order by date_scored DESC
        LIMIT 1
    """
    for source in sources:
        resultproxy = polo_connection.execute(sql, source['id'])
        source['name'] += " ({})".format(get_result(resultproxy)[0]['d'])

    sources[0]['selected'] = True
    polo_connection.close()
    return jsonify(sources)


@app.route('/api/algorithms/', methods=['GET'])
def get_algorithms():
    """
    get:
        summary: Return list of unique algorithms used for scoring images
        description: Return list of unique algorithms used for scoring images
        parameters:
        responses:
            200:
                description: JSON object with information for all unique algorithms
    """
    polo_connection = polo_engine.connect()
    sql = "select scored_by as id, scored_by as name, count(scored_by) as count from image_scores group by scored_by"
    resultproxy = polo_connection.execute(sql)
    algos = get_result(resultproxy)
    algos[0]['selected'] = True
    for algo in algos:
        algo['name'] += " ({:,})".format(algo['count'])

    polo_connection.close()
    return jsonify(algos)


@app.route('/api/timecourse/', methods=['GET'])
def get_timecourse():
    """
    get:
        summary: Get visible image data for a plate/well/drop
        description: Obtain the list of all visible images for a source/plate/well/drop combination scored
                     using a specified algorithm
        parameters:
            - name: source_id
              description: primary key in POLO database for RockMaker instance to search. Default: 1
              type: integer
              required: false
            - name: algo_name
              description: Show scores from this algorithm. Default: first one detected
              type: string
              required: false
            - name: plate_id
              description: Plate ID, same as RockMaker Plate.ID
              type: integer
              required: true
            - name: well_num
              description: Well number, same as RockMaker Well.WellNumber
              type: integer
              required: true
            - name: drop_num
              description: Drop number, same as RockMaker WellDrop.DropNumber
              type: integer
              required: true
        responses:
            200:
                description: JSON list of image metadata
    """
    source_id = request.args.get('source_id')
    if source_id is None:
        source_id = 1
    else:
        source_id = int(source_id)

    plate_id = request.args.get('plate_id')
    well_num = request.args.get('well_num')
    drop_num = request.args.get('drop_num')
    algo_name = request.args.get('algo_name')

    if algo_name is None:
        sql = "select distinct scored_by from image_scores"
        resultproxy = polo_connection.execute(sql)
        algo_name = get_result(resultproxy)[0]['scored_by']

    polo_connection = polo_engine.connect()
    resultproxy = polo_connection.execute(sql_timecourse, source_id, algo_name, int(plate_id), int(well_num),
                                          int(drop_num))
    scores = get_result(resultproxy)
    polo_connection.close()
    return jsonify(scores)


@app.route('/api/other/', methods=['GET'])
def get_other():
    """
    get:
        summary: Get all image data for a plate/well/drop
        description: Obtain the list of all images (including visible, UV, etc.) for a source/plate/well/drop combination
        parameters:
            - name: source_id
              description: primary key in POLO database for RockMaker instance to search. Default: 1
              type: integer
              required: false
            - name: plate_id
              description: Plate ID, same as RockMaker Plate.ID
              type: integer
              required: true
            - name: well_num
              description: Well number, same as RockMaker Well.WellNumber
              type: integer
              required: true
            - name: drop_num
              description: Drop number, same as RockMaker WellDrop.DropNumber
              type: integer
              required: true
        responses:
            200:
                description: JSON list of image metadata
    """

    source_id = request.args.get('source_id')
    if source_id is None:
        source_id = 1
    else:
        source_id = int(source_id)

    plate_id = request.args.get('plate_id')
    well_num = request.args.get('well_num')
    drop_num = request.args.get('drop_num')

    polo_connection = polo_engine.connect()
    resultproxy = polo_connection.execute(sql_image_prefix, source_id)
    prefix = get_result(resultproxy)[0]['prefix']

    rm_connection = rm_engines[source_id].connect()
    resultproxy = rm_connection.execute(sql_other_images, prefix, int(plate_id), int(well_num), int(drop_num))
    scores = get_result(resultproxy)
    rm_connection.close()

    return jsonify(scores)


@app.route('/api/scores/', methods=['GET'])
def get_scores():
    """
    get:
        summary: Get scores for one or more plates, optionally filtered/sorted/paginated.
        description: Obtain the list of all scores and other data for one or more plates. Sorting, filtering,
                     and pagination is supported.
            - name: source_id
              description: primary key in POLO database for RockMaker instance to search. Default: 1
              type: integer
              required: false
            - name: algo_name
              description: Show scores from this algorithm. Default: first one detected
              type: string
              required: false
            - name: plate_ids
              description: comma-delimited plate ids, expressed as RockMaker Plate.ID
              type: string
              required: true
            - name: min_score
              description: only return scores greater than this one (on "crystal" column)
              type: float
              required: false
            - name: method
              description: which score to use for a source/plate/well/drop: either "date_imaged" (for most recent) or
                           "crystal" (for highest crystal score). Default: date_imaged
              type: string
              required: false
            - name: drop_num
              description: comma-delimited image drop number(s) to filter on
              type: string
              required: false
            - name: temperature
              description: comma-delimited temperature values to filter on
              type: string
              required: false
            - name: limit
              description: how many scores to return. Default: 10
              type: int
              required: false
            - name: page
              description: which page to return. Default: 1
              type: int
              required: false
            - name: sortBy
              description: which column to sort on. Default: crystal
              type: string
              required: false
            - name: direction
              description: which direction to sort. Default: DESC
              type: string
              required: false
        responses:
            200:
                description: JSON list of scores and associated metadata
    """

    method = request.args.get('method')
    if method is None:
        method = "date_imaged"

    source_id = request.args.get('source_id')
    if source_id is None:
        source_id = 1
    else:
        source_id = int(source_id)

    algo_name = request.args.get('algo_name')  # handle case when None below

    min_score = request.args.get('min_score')
    if min_score is None:
        min_score = 0.0
    else:
        min_score = float(min_score)

    plate_ids = request.args.get('plate_ids').split(',')
    if plate_ids == ['']:
        return jsonify([])

    # DATABASE FILTERS
    try:
        drop_num = request.args.get('drop_num')
        if drop_num is not None and len(drop_num) > 0:
            # avoid injection attack by converting to integers, and back to comma-separated
            drops = ','.join([str(int(d)) for d in re.split(r'\s*,\s*|\s+', drop_num)])
            drop_filter = "AND drop_num IN ({})".format(drops)  # allow to select multiple through use of commas
        else:
            drop_filter = ''
    except:
        drop_filter = ''

    try:
        temperature = request.args.get('temperature')
        if temperature is not None and len(temperature) > 0:
            # avoid injection attack by converting to integers, and back to comma-separated
            temperatures = ','.join([str(int(d)) for d in re.split(r'\s*,\s*|\s+', temperature)])
            temperature_filter = "AND temperature IN ({})".format(
                temperatures)  # allow to select multiple through use of commas
        else:
            temperature_filter = ''
    except:
        temperature_filter = ''

    # POST-DATABASE FILTER
    # conditions = request.args.get('conditions')
    # if conditions is not None:
    #     condition_filter = "AND conditions LIKE '%{}%".format(conditions)

    plate_ids = [int(plate_id) for plate_id in plate_ids]

    limit = request.args.get('limit', 10)
    page = request.args.get('page', 1)
    sort_by = request.args.get('sortBy', 'crystal')
    direction = request.args.get('direction', 'DESC')

    if sort_by == 'well_name':
        sort_by = 'well_num'

    if sort_by == 'plate_name':
        sort_by = 'plate_id'

    offset = (int(page) - 1) * int(limit)
    sort_dir = f'{sort_by} {direction}'

    scores = request.args.getlist('scores[]')
    if scores:
        score_filter = 'AND id IN ({})'.format(",".join(scores))
    else:
        score_filter = ''

    # MAKE DATABASE CONNECTIONS
    polo_connection = polo_engine.connect()
    rm_connection = rm_engines[source_id].connect()

    if algo_name is None:
        sql = "select distinct scored_by from image_scores"
        resultproxy = polo_connection.execute(sql)
        algo_name = get_result(resultproxy)[0]['scored_by']

    # GET TOTAL IMAGE SCORES
    query_placeholders = ','.join(['%s'] * len(plate_ids))
    params = [source_id, algo_name]
    params.extend(plate_ids)
    resultproxy = polo_connection.execute(
        sql_all.format(temperature_filter=temperature_filter, drop_filter=drop_filter, score_filter=score_filter,
                       rank_method=method, min_score=min_score, query_placeholders=query_placeholders), params)
    total = len(get_result(resultproxy))

    # SET SORT ORDER BASED AND GET PAGINATED REQUEST
    polo_connection.execute(sql_set_sort_order, sort_dir)
    params = [source_id, algo_name]
    params.extend(plate_ids)
    params.append(int(limit))
    params.append(int(offset))

    resultproxy = polo_connection.execute(
        sql_paginated.format(temperature_filter=temperature_filter, drop_filter=drop_filter, score_filter=score_filter,
                             rank_method=method, min_score=min_score, query_placeholders=query_placeholders), params)

    scores = get_result(resultproxy)

    try:
        for plate_id in plate_ids:
            resultproxy = rm_connection.execute(sql_conditions_protein, plate_id)
            conditions = get_result(resultproxy)
            for condition in conditions:
                for score in scores:
                    if score['plate_id'] == plate_id and \
                            score['well_num'] == condition['well_num'] and \
                            score['drop_num'] == condition['drop_num']:
                        score['conditions'] = condition['conditions']
                        score['protein'] = condition['protein']
                        score['protein_notes'] = condition['protein_notes']
    except IndexError:
        print("IndexError getting conditions and/or protein for plate", plate_id)

    polo_connection.close()
    rm_connection.close()

    # OBFUSCATION FOR DEMO PURPOSES
    if 'demo' in request.args or app.config['DEMO']:
        for score in scores:
            score['protein'] = 'XXXXX'

    return jsonify({'total': total, 'records': scores})
