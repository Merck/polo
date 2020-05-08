#!/usr/bin/env python
# coding: utf-8

# * This file needs to be adjusted before use. Specifically,
#   - POLO database information (search for 'XXX')
#   - RockMaker instance(s) (search for 'YYY' and 'ZZZ')
#   - How to run classification model (search for 'def marco')
#   - Name and version of classification model (search for 'NAME AND VERSION')
#
# * You will need a Python 3 environment where the packages below are available
# * You will need a mechanism to serve RockMaker images. See README.md for details

import pandas as pd
import pypyodbc  # for SQL Server (for RockMaker database)
import mysql.connector  # for MySQL (for POLO database)
import json
import traceback
import sys
from datetime import datetime, timedelta
from pathlib import Path

##############################################################################################
# REDIRECT STDOUT TO LOG

now = datetime.now()
print("=" * 60)
print("Updating POLO on", now.strftime("%Y-%m-%d %H:%M"))

##############################################################################################
# CHECK IF PREVIOUS POLO STILL SCORING

marcopolo_file = '/tmp/marcopolo'
if Path(marcopolo_file).exists():
    print(
        "*** Looks like POLO scoring is still happening, so skipping this round. If the update is not running, remove the file",
        marcopolo_file)
    exit(1)

Path(marcopolo_file).touch()
try:
    # DEFINE ALL OF THE SQL COMMANDS IN ONE PLACE

    sql_get_source_id = """
        SELECT id, url_prefix
        FROM sources
        WHERE name = ?
    """

    sql_find_images_by_date = """
        SELECT Plate.ID                                                  AS plate_id,
               Plate.PlateNumber                                         AS plate_num,
               Plate.Barcode                                             AS barcode,
               CONCAT('/', Plate.ID % 1000, '/plateID_', Plate.ID, '/batchID_', ImageBatch.ID, '/wellNum_',
                      Well.WellNumber, '/profileID_', CaptureProfile.ID, '/d', WellDrop.DropNumber,
                      '_r', Region.ID, '_', ImageType.ShortName, '.jpg') AS relative_path,
               Well.WellNumber                                           As well_num,
               Well.Rowletter                                            As row_letter,
               Well.ColumnNumber                                         As column_num,
               WellDrop.DropNumber                                       As drop_num,
               ImagingTask.DateImaged                                    As date_imaged,
               IncubationTemp.Temperature                                AS temperature
        FROM WellDrop
               INNER JOIN Well ON Well.ID = WellDrop.WellID
               INNER JOIN Plate ON Plate.ID = Well.PlateID
               INNER JOIN Region ON Region.WellDropID = WellDrop.ID
               INNER JOIN CaptureResult ON CaptureResult.REGIONID = REGION.ID
               INNER JOIN CaptureProfileVersion ON CaptureProfileVersion.ID = CaptureResult.CaptureProfileVersionID
               INNER JOIN CaptureProfile ON CaptureProfile.ID = CaptureProfileVersion.CaptureProfileID
               INNER JOIN Image ON Image.CaptureResultID = CaptureResult.ID
               INNER JOIN ImageType ON ImageType.ID = Image.ImageTypeID
               INNER JOIN ImageStore on ImageStore.ID = Image.ImageStoreID
               INNER JOIN ImageBatch on ImageBatch.ID = CAPTURERESULT.ImageBatchID
               INNER JOIN ImagingTask on ImagingTask.ID = ImageBatch.ImagingTaskID
               INNER JOIN Experiment on Plate.ExperimentID = Experiment.ID
               INNER JOIN IncubationTemp on Experiment.IncubationTempID = IncubationTemp.ID
        WHERE ImageType.ShortName = 'ef'
          AND CaptureProfile.ID IN (1,5)
          AND DateImaged > Convert(datetime, ?)
    """

    sql_get_images = """
        select source_id, scored_by, relative_path from image_scores
        where CONCAT(source_id, '|', scored_by, '|', relative_path) IN ({query_placeholders})
    """

    sql_save_score = """
        INSERT INTO image_scores (source_id,scored_by,plate_id,barcode,relative_path,
                                  well_num,row_letter,column_num,drop_num,date_imaged,
                                  classification,crystal,other,precipitate,clear,plate_num,temperature)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    # POLO DATABASE CONNECTION
    polo = mysql.connector.connect(
        host="XXX",
        user="XXX",
        passwd="XXX",
        database="XXX"
    )
    pcursor = polo.cursor(prepared=True)


    ##############################################################################################

    def marco(url_list):
        """
        Given a list of image URLs, return a MARCO classification
        :param url: URL to an image to classify
        :return: JSON list of dicts which looks something like
        [
          {
            "input": "http://image.host.name/path/to/image/filename.jpg",
            "scores":
            {
              "Clear": 0.02,
              "Crystals": 0.93,
              "Other": 0.02,
              "Precipitate": 0.02
            }
          },
          {
            "input": "http://image.host.name/path/to/differentimage/filename.jpg",
            "scores":
            {
              "Clear": 0.87,
              "Crystals": 0.03,
              "Other": 0.02,
              "Precipitate": 0.02
            }
          },
          ...
          ]
        """
        result = do_something_with_url_list(url_list)
        return result


    ##############################################################################################
    # LOOP OVER EACH BACKEND IMAGING SYSTEM

    for instance in ["RockMaker 1", "RockMaker 2"]:
        print("  Working on {}".format(instance))

        # GET THE POLO SOURCE ID OF THE CURRENT INSTANCE, GIVEN THE NAME
        pcursor.execute(sql_get_source_id, (instance,))  # need the trailing comma for a tuple of a single object
        (source_id, source_url) = pcursor.fetchone()

        # MAKE RockMaker DATABASE CONNECTION
        if instance == "RockMaker 1":
            connection_string = 'DSN=YYY;UID=YYY;PWD=YYY;'
        elif instance == "RockMaker 2":
            connection_string = 'DSN=ZZZ;UID=ZZZ;PWD=ZZZ;'
        else:
            raise "No image database selected"

        rm_conn = pypyodbc.connect(connection_string)
        rm_cursor = rm_conn.cursor()

        # GET LIST OF IMAGES FROM TODAY MINUS A WINDOW (e.g. 1 day)
        window_start = datetime.today() - timedelta(days=5)
        _ = rm_cursor.execute(sql_find_images_by_date, (window_start,))
        r = pd.DataFrame(rm_cursor.fetchall())

        # SKIP TO NEXT INSTANCE IF THERE'S NOTHING TO SCORE
        if len(r) == 0:
            print("    no images to score")
            continue

        r.columns = ['plate_id', 'plate_num', 'barcode', 'relative_path', 'well_num', 'row_letter', 'column_num',
                     'drop_num', 'date_imaged', 'temperature']
        r['url'] = source_url.decode("utf-8") + r['relative_path']
        r['source_id'] = source_id
        r['scored_by'] = '<NAME AND VERSION OF CLASSIFICATION MODEL>'

        recent_images = r['source_id'].astype(str) + '|' + r['scored_by'] + '|' + r['relative_path']

        # GET A LIST OF ANY OF THESE WHICH ARE ALREADY IN POLO - NEED TO CONSIDER source_id, scored_by, AND relative_path

        query_placeholders = ','.join(['?'] * len(recent_images))
        result = pcursor.execute(sql_get_images.format(query_placeholders=query_placeholders), recent_images.tolist())
        matches = pd.DataFrame(pcursor.fetchall())

        if len(matches) > 0:
            matches.columns = ['source_id', 'scored_by', 'relative_path']
            # matches comes back as a list of bytearrays which need to be decode()-ed
            matches['scored_by'] = matches['scored_by'].str.decode("utf-8")
            matches['relative_path'] = matches['relative_path'].str.decode("utf-8")

            to_score = pd.merge(r, matches, on=['source_id', 'scored_by', 'relative_path'], how="outer", indicator=True)
            to_score = to_score[to_score['_merge'] == 'left_only']
        else:
            # nothing matches, so we have to score them all
            to_score = r

        if len(to_score) == 0:
            print("   no images to score after comparison")
            continue

        batch_size = 2

        # SCORE IN PARALLEL
        chunks = [to_score[i:i + batch_size]['url'] for i in range(0, len(to_score.index), batch_size)]
        print("    Scoring {size_all} images in {batches} batches of {batch_size}".format(size_all=len(to_score.index),
                                                                                          batches=len(chunks),
                                                                                          batch_size=batch_size))
        for chunknum, chunk in enumerate(chunks):
            print(f"      Batch {chunknum + 1}", flush=True)
            try:
                current_images = []
                for result in marco(list(chunk)):
                    current_images.append(result['input'])
                    to_score.loc[to_score['url'] == result['input'], 'classification'] = json.dumps(result['scores'])
                    to_score.loc[to_score['url'] == result['input'], 'crystal'] = result['scores']['Crystals']
                    to_score.loc[to_score['url'] == result['input'], 'other'] = result['scores']['Other']
                    to_score.loc[to_score['url'] == result['input'], 'precipitate'] = result['scores']['Precipitate']
                    to_score.loc[to_score['url'] == result['input'], 'clear'] = result['scores']['Clear']

                # Update POLO database now, rather than waiting for all images to be scored
                current_scores = pd.DataFrame(to_score[to_score['url'].isin(current_images)])  # make new DF

                # PREPARE LIST OF TUPLES TO INSERT INTO POLO DATABASE
                current_scores['date_imaged_str'] = current_scores['date_imaged'].astype(str)
                data = current_scores[['source_id', 'scored_by', 'plate_id', 'barcode', 'relative_path',
                                       'well_num', 'row_letter', 'column_num', 'drop_num', 'date_imaged_str',
                                       'classification', 'crystal', 'other', 'precipitate', 'clear', 'plate_num',
                                       'temperature']]
                scores = [tuple(x) for x in data.values]

                # UPDATE THE POLO DATABASE WITH SCORES
                pcursor.executemany(sql_save_score, scores)
                polo.commit()
                print(f"        Updated {len(scores)} images", flush=True)
            except:
                print("ERROR: problem")
                print('-' * 60)
                print(result)
                traceback.print_exc(file=sys.stdout)
                print('-' * 60)
    polo.close()
except:
    print("Ugh..there was a problem")
    traceback.print_exc()
finally:
    Path(marcopolo_file).unlink()

now = datetime.now()
print("Finished at", now.strftime("%Y-%m-%d %H:%M"))
