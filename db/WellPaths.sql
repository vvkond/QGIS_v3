SELECT
    wh.TIG_LATEST_WELL_NAME "Well Name",
    wh.DB_SLDNID "Well_ID",
    wh.TIG_LATITUDE "Latitude",
    wh.TIG_LONGITUDE "Longitude",
    wh.TIG_LONGITUDE,
    wh.TIG_LATITUDE,
    cd.TIG_DELTA_X_ORDINATE,
    cd.TIG_DELTA_Y_ORDINATE
FROM
    tig_well_history wh,
    tig_computed_deviation cd
WHERE
    (:well_id IS NULL OR wh.DB_SLDNID = :well_id)
    AND cd.TIG_WELL_SLDNID = wh.DB_SLDNID
    AND wh.TIG_LONGITUDE != 0
    AND wh.TIG_LATITUDE != 0
    AND wh.TIG_ONLY_PROPOSAL <= 1
    AND cd.DB_SLDNID IN
    (SELECT
        MAX(cd2.DB_SLDNID)
    FROM
        tig_computed_deviation cd2
    WHERE
        cd2.TIG_WELL_SLDNID = wh.DB_SLDNID
    )