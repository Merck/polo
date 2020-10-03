"""
sql.py
==================
This file contains most of the hand-crafted SQL queries used by various methods in the API.
"""

sql_tree_user_node = """
SELECT id
  FROM TreeNode
WHERE name = ?
  AND ParentID = 3
"""

sql_tree = """
    SELECT t.ParentID as parent_id,
           t.id,
           p.id as plate_id,
           p.Barcode as barcode,
           t.Type as node_type,
           CASE
             WHEN p.id IS NULL THEN t.name
             ELSE CONCAT(p.PlateNumber, ',', p.id, ',', p.Barcode)
           END as name,
           CASE
             WHEN (SELECT COUNT(id) FROM TreeNode tn WHERE tn.ParentID = t.id) = 0
             THEN CAST(0 AS BIT)
             ELSE CAST(1 AS BIT)
            END as has_children  
    FROM dbo.TreeNode t
           FULL OUTER JOIN Plate p on p.TreeNodeID = t.id
    WHERE ParentID = ?
      AND name NOT LIKE '[_]%'
      AND name NOT IN ('Formulatrix', 'Instant Imaging', 'Quality Test', 'Timing Test')
      AND Type IN ('Project', 'ProjectsFolder', 'ProjectFolder', 'Experiment', 'ExperimentPlate')
    ORDER BY name
    """

sql_all = """
    SELECT ranked.id,
           plate_id,
           barcode,
           well_num,
           drop_num,
           crystal,
           other,
           DATE_FORMAT(date_imaged, "%%m/%%d/%%Y") date_imaged,
           CONCAT(s.url_prefix, relative_path) url
    FROM (SELECT id,
                 plate_id,
                 barcode,
                 well_num,
                 drop_num,
                 crystal,
                 other,
                 date_imaged,
                 source_id,
                 relative_path,
                 @pwd_rank := IF(@current_plate = plate_id AND @current_well = well_num AND @current_drop = drop_num, @pwd_rank + 1, 1) AS pwd_rank,
                 @current_plate := plate_id,
                 @current_well := well_num,
                 @current_drop := drop_num
          FROM image_scores
          WHERE source_id = %s
            AND scored_by = %s
            AND plate_id IN ({query_placeholders})
            {temperature_filter}
            {drop_filter}
            {score_filter}
            AND crystal IS NOT NULL
            AND crystal > {min_score}
          ORDER BY plate_id, well_num, drop_num, {rank_method} DESC
         ) ranked, sources s
    WHERE pwd_rank <= 1
      AND source_id = s.id
    """

sql_set_sort_order = "SET @sort_dir = %s; SET @pwd_rank = 0;"
sql_paginated_without_timecourse = """
    SELECT CONCAT(CAST(plate_num AS CHAR), ',', CAST(plate_id as CHAR), ',', barcode) as plate_name,
           ranked.id,
           plate_id,
           well_num,
           CONCAT(row_letter, CAST(column_num AS CHAR))                               as well_name,
           drop_num,
           crystal,
           other,
           date_imaged                                                                   date_imaged_orig,
           DATE_FORMAT(date_imaged, "%%m/%%d/%%Y")                                       date_imaged,
           CONCAT(s.url_prefix, relative_path)                                           url,
           temperature,
           (
             SELECT CAST(GROUP_CONCAT(manual_call ORDER BY disputed_at ASC) AS CHAR)
             FROM image_scores i,
                  disputes d
             WHERE i.id = d.image_score_id
               AND ranked.id = d.image_score_id
               AND ranked.source_id = i.source_id
           )                                                                             disputes
    FROM (SELECT id,
                 plate_id,
                 barcode,
                 plate_num,
                 well_num,
                 row_letter,
                 column_num,
                 drop_num,
                 crystal,
                 other,
                 date_imaged,
                 source_id,
                 relative_path,
                 temperature,
                 @pwd_rank := IF(@current_plate = plate_id AND @current_well = well_num AND @current_drop = drop_num, @pwd_rank + 1, 1) AS pwd_rank,
                 @current_plate := plate_id,
                 @current_well := well_num,
                 @current_drop := drop_num
          FROM image_scores
          WHERE source_id = %s
            AND scored_by = %s
            AND plate_id IN ({query_placeholders})
            {temperature_filter}
            {drop_filter}
            {score_filter}
            AND crystal IS NOT NULL
            AND crystal > {min_score}
          ORDER BY plate_id, well_num, drop_num, {rank_method} desc
         ) ranked,
         sources s
    WHERE pwd_rank <= 1
      AND source_id = s.id
    ORDER BY 
        CASE WHEN @sort_dir = 'plate_id asc' THEN plate_id END ASC,
        CASE WHEN @sort_dir = 'plate_id desc' THEN plate_id END DESC,
        CASE WHEN @sort_dir = 'well_num asc' THEN well_num END ASC,
        CASE WHEN @sort_dir = 'well_num desc' THEN well_num END DESC,
        CASE WHEN @sort_dir = 'drop_num asc' THEN drop_num END ASC,
        CASE WHEN @sort_dir = 'drop_num desc' THEN drop_num END DESC,
        CASE WHEN @sort_dir = 'barcode asc' THEN barcode END ASC,
        CASE WHEN @sort_dir = 'barcode desc' THEN barcode END DESC,
        CASE WHEN @sort_dir = 'crystal asc' THEN crystal END ASC,
        CASE WHEN @sort_dir = 'crystal desc' THEN crystal END DESC,
        CASE WHEN @sort_dir = 'other asc' THEN other END ASC,
        CASE WHEN @sort_dir = 'other desc' THEN other END DESC,
        CASE WHEN @sort_dir = 'date_imaged asc' THEN date_imaged_orig END ASC,
        CASE WHEN @sort_dir = 'date_imaged desc' THEN date_imaged_orig END DESC,
        CASE WHEN @sort_dir = 'temperature asc' THEN temperature END ASC,
        CASE WHEN @sort_dir = 'temperature desc' THEN temperature END DESC,
        crystal DESC
    LIMIT %s
    OFFSET %s
"""

sql_paginated_with_timecourse = """
    SELECT CONCAT(CAST(plate_num AS CHAR), ',', CAST(plate_id as CHAR), ',', barcode) as plate_name,
           ranked.id,
           plate_id,
           well_num,
           CONCAT(row_letter, CAST(column_num AS CHAR))                               as well_name,
           drop_num,
           crystal,
           other,
           date_imaged                                                                   date_imaged_orig,
           DATE_FORMAT(date_imaged, "%%m/%%d/%%Y")                                       date_imaged,
           CONCAT(s.url_prefix, relative_path)                                           url,
           temperature,
           (
             SELECT CAST(GROUP_CONCAT(manual_call ORDER BY disputed_at ASC) AS CHAR)
             FROM image_scores i,
                  disputes d
             WHERE i.id = d.image_score_id
               AND ranked.id = d.image_score_id
               AND ranked.source_id = i.source_id
           )                                                                             disputes,
           (
             SELECT CAST(GROUP_CONCAT(date_imaged ORDER BY date_imaged ASC) AS CHAR)
             FROM image_scores i
             WHERE ranked.source_id = i.source_id
               AND ranked.plate_id = i.plate_id
               AND ranked.well_num = i.well_num
               AND ranked.drop_num = i.drop_num
           )                                                                             all_dates_imaged,
           (
             SELECT CAST(GROUP_CONCAT(crystal ORDER BY date_imaged ASC) AS CHAR)
             FROM image_scores i
             WHERE ranked.source_id = i.source_id
               AND ranked.plate_id = i.plate_id
               AND ranked.well_num = i.well_num
               AND ranked.drop_num = i.drop_num
           )                                                                             all_crystal_scores,
           (
             SELECT CAST(GROUP_CONCAT(other ORDER BY date_imaged ASC) AS CHAR)
             FROM image_scores i
             WHERE ranked.source_id = i.source_id
               AND ranked.plate_id = i.plate_id
               AND ranked.well_num = i.well_num
               AND ranked.drop_num = i.drop_num
           )                                                                             all_other_scores
    FROM (SELECT id,
                 plate_id,
                 barcode,
                 plate_num,
                 well_num,
                 row_letter,
                 column_num,
                 drop_num,
                 crystal,
                 other,
                 date_imaged,
                 source_id,
                 relative_path,
                 temperature,
                 @pwd_rank := IF(@current_plate = plate_id AND @current_well = well_num AND @current_drop = drop_num, @pwd_rank + 1, 1) AS pwd_rank,
                 @current_plate := plate_id,
                 @current_well := well_num,
                 @current_drop := drop_num
          FROM image_scores
          WHERE source_id = %s
            AND scored_by = %s
            AND plate_id IN ({query_placeholders})
            {temperature_filter}
            {drop_filter}
            {score_filter}
            AND crystal IS NOT NULL
            AND crystal > {min_score}
          ORDER BY plate_id, well_num, drop_num, {rank_method} desc
         ) ranked,
         sources s
    WHERE pwd_rank <= 1
      AND source_id = s.id
    ORDER BY 
        CASE WHEN @sort_dir = 'plate_id asc' THEN plate_id END ASC,
        CASE WHEN @sort_dir = 'plate_id desc' THEN plate_id END DESC,
        CASE WHEN @sort_dir = 'well_num asc' THEN well_num END ASC,
        CASE WHEN @sort_dir = 'well_num desc' THEN well_num END DESC,
        CASE WHEN @sort_dir = 'drop_num asc' THEN drop_num END ASC,
        CASE WHEN @sort_dir = 'drop_num desc' THEN drop_num END DESC,
        CASE WHEN @sort_dir = 'barcode asc' THEN barcode END ASC,
        CASE WHEN @sort_dir = 'barcode desc' THEN barcode END DESC,
        CASE WHEN @sort_dir = 'crystal asc' THEN crystal END ASC,
        CASE WHEN @sort_dir = 'crystal desc' THEN crystal END DESC,
        CASE WHEN @sort_dir = 'other asc' THEN other END ASC,
        CASE WHEN @sort_dir = 'other desc' THEN other END DESC,
        CASE WHEN @sort_dir = 'date_imaged asc' THEN date_imaged_orig END ASC,
        CASE WHEN @sort_dir = 'date_imaged desc' THEN date_imaged_orig END DESC,
        CASE WHEN @sort_dir = 'temperature asc' THEN temperature END ASC,
        CASE WHEN @sort_dir = 'temperature desc' THEN temperature END DESC,
        crystal DESC
    LIMIT %s
    OFFSET %s
"""

# GET CONDITIONS ONE PLATE AT A TIME SINCE I CANNOT GET THE WHERE IN BIND PARAMETER TO WORK PROPERLY
sql_conditions = """
        WITH a as (
      SELECT Plate.ID                                                      AS plate_id,
             Well.WellNumber                                               AS well_num,
             CONCAT(WellLayerIngredient.Concentration, ' ', IngredientStock.ConcentrationUnits, ' ',
                    Ingredient.ShortName,
                    (CASE
                       WHEN WellLayerIngredient.PH IS NOT NULL
                         THEN CONCAT(' pH ', WellLayerIngredient.PH) END)) AS condition
      FROM Plate
             JOIN Well ON Well.PlateID = Plate.ID
             JOIN WellLayer on WellLayer.WellID = Well.ID
             JOIN WellLayerIngredient on WellLayerIngredient.WellLayerID = WellLayer.ID
             JOIN IngredientStock on WellLayerIngredient.IngredientStockID = IngredientStock.ID
             JOIN Ingredient on IngredientStock.IngredientID = Ingredient.ID
      WHERE Plate.ID = ?
    )
    SELECT plate_id,
           well_num,
           conditions = STUFF(
               (
                 SELECT '; ' + condition
                 FROM a
                 WHERE a.plate_id = b.plate_id
                   AND a.well_num = b.well_num FOR XML PATH ('')
               ), 1, 2, '')
    from a b
    GROUP BY plate_id, well_num
"""

sql_conditions_protein = """
WITH a as (
  SELECT Plate.ID                                                      AS plate_id,
         Well.WellNumber                                               AS well_num,
         WellDrop.DropNumber                                           AS drop_num,
         TreeNode.Name                                                 AS protein,
         ProteinFormulation.Notes                                      AS protein_notes,
         CONCAT(WellLayerIngredient.Concentration, ' ', IngredientStock.ConcentrationUnits, ' ',
                Ingredient.ShortName,
                (CASE
                   WHEN WellLayerIngredient.PH IS NOT NULL
                     THEN CONCAT(' pH ', WellLayerIngredient.PH) END)) AS condition
  FROM Plate
         JOIN Well ON Well.PlateID = Plate.ID
         JOIN WellDrop ON Well.ID = WellDrop.WellID
         JOIN ProteinFormulation ON WellDrop.ProteinFormulationID = ProteinFormulation.ID
         JOIN TreeNode ON ProteinFormulation.TreeNodeID = TreeNode.ID
         JOIN WellLayer on WellLayer.WellID = Well.ID
         JOIN WellLayerIngredient on WellLayerIngredient.WellLayerID = WellLayer.ID
         JOIN IngredientStock on WellLayerIngredient.IngredientStockID = IngredientStock.ID
         JOIN Ingredient on IngredientStock.IngredientID = Ingredient.ID
  WHERE Plate.ID = ?
)
SELECT plate_id,
  well_num,
  drop_num,
  protein,
  protein_notes,
       conditions = STUFF(
           (
             SELECT '; ' + condition
             FROM a
             WHERE a.plate_id = b.plate_id
               AND a.drop_num = b.drop_num
               AND a.well_num = b.well_num FOR XML PATH ('')
           ), 1, 2, '')
from a b
GROUP BY plate_id, well_num, drop_num, protein, protein_notes
"""

sql_timecourse = """
    SELECT scores.id,
           plate_num,
           plate_id,
           barcode,
           well_num,
           drop_num,
           crystal,
           other,
           date_imaged date_imaged_orig,
           DATE_FORMAT(date_imaged, "%%m/%%d/%%Y") date_imaged,
           CONCAT(s.url_prefix, relative_path) url
      FROM image_scores scores, sources s
     WHERE s.id = %s
       AND scored_by = %s
       AND plate_id = %s
       AND well_num = %s
       AND drop_num = %s
  ORDER BY date_imaged_orig DESC
"""

sql_path_to_experiments_like_text = """
-- FIND PATH TO EXPERIMENTS MATCHING TEXT
WITH treecte(nodeid, Name, Type, ParentID, LEVEL, treepath)
       AS (SELECT ID                          AS nodeid,
                  Name,
                  Type,
                  ParentID,
                  0                           AS LEVEL,
                  CAST(Name AS VARCHAR(1024)) AS treepath
           FROM TreeNode
           WHERE ParentID = 3 -- stop at Projects folder
           UNION ALL
           SELECT tn.ID                                                                         AS nodeid,
                  tn.Name,
                  tn.Type,
                  tn.ParentID,
                  PCTE.LEVEL + 1                                                                AS LEVEL,
                  CAST(PCTE.treepath + ' > ' + CAST(tn.Name AS VARCHAR(1024)) AS VARCHAR(1024)) AS treepath
           FROM TreeNode As tn
                  INNER JOIN treecte As PCTE ON PCTE.nodeid = tn.ParentID
           WHERE tn.Type in ('Project', 'ProjectFolder', 'ProjectsFolder', 'Experiment', 'ExperimentPlate')
  )
SELECT nodeid as id, Name as folder_name, treepath as path
FROM treecte
where Name like ?
  and Type = 'Experiment'
ORDER BY treepath
"""

sql_path_to_experiments_via_nodeids = """
-- FIND PATH TO EXPERIMENTS GIVEN NODE IDS
WITH treecte(nodeid, Name, Type, ParentID, LEVEL, treepath)
       AS (SELECT ID                          AS nodeid,
                  Name,
                  Type,
                  ParentID,
                  0                           AS LEVEL,
                  CAST(Name AS VARCHAR(1024)) AS treepath
           FROM TreeNode
           WHERE ParentID = 3 -- stop at Projects folder
           UNION ALL
           SELECT tn.ID                                                                         AS nodeid,
                  tn.Name,
                  tn.Type,
                  tn.ParentID,
                  PCTE.LEVEL + 1                                                                AS LEVEL,
                  CAST(PCTE.treepath + ' > ' + CAST(tn.Name AS VARCHAR(1024)) AS VARCHAR(1024)) AS treepath
           FROM TreeNode As tn
                  INNER JOIN treecte As PCTE ON PCTE.nodeid = tn.ParentID
           WHERE tn.Type in ('Project', 'ProjectFolder', 'ProjectsFolder', 'Experiment', 'ExperimentPlate')
  )
SELECT nodeid as id, Name as folder_name, treepath as path
FROM treecte
where nodeid in ({query_placeholders})
  and Type = 'Experiment'
ORDER BY treepath
"""

sql_plates_from_experiment_nodes = """
select TreeNode.ParentID                                            as parent_id,
       TreeNode.ID                                                  as id,
       Plate.ID                                                     as plate_id,
       Plate.Barcode                                                as barcode,
       CONCAT(Plate.PlateNumber, ',', Plate.ID, ',', Plate.Barcode) as name
from Plate,
     TreeNode
where Plate.TreeNodeID = TreeNode.ID
  and TreeNode.ParentID in ({query_placeholders})
order by plate_id ASC
"""

sql_nodes_from_matching_plateid = """
select TreeNode.ID                                                  as id,
       Plate.ID                                                     as plate_id,
       Plate.Barcode                                                as barcode,
       CONCAT(Plate.PlateNumber, ',', Plate.ID, ',', Plate.Barcode) as name
from TreeNode,
     Plate
where Plate.ID like ?
  and Plate.TreeNodeID = TreeNode.ID
"""

sql_nodes_from_matching_barcode = """
select TreeNode.ID                                                  as id,
       Plate.ID                                                     as plate_id,
       Plate.Barcode                                                as barcode,
       CONCAT(Plate.PlateNumber, ',', Plate.ID, ',', Plate.Barcode) as name
from TreeNode,
     Plate
where Plate.Barcode like ?
  and Plate.TreeNodeID = TreeNode.ID
"""

sql_plates_from_matching_protein = """
WITH treecte(nodeid, Name, Type, ParentID, LEVEL, treepath)
       AS (SELECT ID                          AS nodeid,
                  Name,
                  Type,
                  ParentID,
                  0                           AS LEVEL,
                  CAST(Name AS VARCHAR(1024)) AS treepath
           FROM TreeNode
           WHERE ParentID = 3 -- stop at Projects folder
           UNION ALL
           SELECT tn.ID                                                                         AS nodeid,
                  tn.Name,
                  tn.Type,
                  tn.ParentID,
                  PCTE.LEVEL + 1                                                                AS LEVEL,
                  CAST(PCTE.treepath + ' > ' + CAST(tn.Name AS VARCHAR(1024)) AS VARCHAR(1024)) AS treepath
           FROM TreeNode As tn
                  INNER JOIN treecte As PCTE ON PCTE.nodeid = tn.ParentID
           WHERE tn.Type in ('Project', 'ProjectsFolder', 'Experiment', 'ExperimentPlate')
  ),
     protein(protein_id, protein_name) as (select ProteinFormulation.ID,
                                                  TreeNode.name
                                           from ProteinFormulation,
                                                TreeNode
                                           where TreeNode.name like ?
                                             and ProteinFormulation.TreeNodeID = TreeNode.ID)
select distinct Plate.ID as plate_id,
                TreeNode.ID as id,
                protein.protein_name as folder_name,
                treecte.treepath as path,
                Plate.Barcode as barcode,
                CONCAT(Plate.PlateNumber, ',', Plate.ID, ',', Plate.Barcode) as name
from protein,
     treecte,
     TreeNode,
     Plate,
     Experiment,
     ProteinLayer PL,
     ProteinLayerProteinFormulation PLPF,
     ProteinFormulation PF
where protein.protein_id = PF.ID
  and PF.ID = PLPF.ProteinFormulationID
  and PL.ID = PLPF.ProteinLayerID
  and Experiment.ID = PL.ExperimentID
  and Experiment.ID = Plate.ExperimentID
  and TreeNode.ID = Plate.TreeNodeID
  and treecte.nodeid = TreeNode.ParentID
"""

sql_image_prefix = """
    select s.url_prefix prefix
      from sources s
     where s.id = %s
"""

sql_other_images = """
    SELECT Plate.Barcode                                             AS barcode,
           FORMAT(ImagingTask.DateImaged, 'MM/dd/yyyy')              AS date_imaged,
           ImagingTask.DateImaged                                    AS date_imaged_orig,
           WellDrop.DropNumber                                       AS drop_num,
           Plate.ID                                                  AS plate_id,
           Plate.PlateNumber                                         AS plate_num,
           CONCAT(?, '/', Plate.ID % 1000, '/plateID_', Plate.ID, '/batchID_', ImageBatch.ID, '/wellNum_',
                  Well.WellNumber, '/profileID_', CaptureProfile.ID, '/d', WellDrop.DropNumber,
                  '_r', Region.ID, '_', ImageType.ShortName, CASE WHEN CaptureProfile.Name LIKE '%UV%' THEN '.png' ELSE '.jpg' END) AS url,
           Well.WellNumber                                           AS well_num,
           CaptureProfile.Name                                       AS image_type
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
    WHERE ImageType.ShortName = 'ef'
      AND Plate.ID = ?
      AND Well.WellNumber = ?
      AND WellDrop.DropNumber = ?
    ORDER BY date_imaged_orig DESC
"""