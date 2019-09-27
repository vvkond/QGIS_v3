SELECT
    wh.TIG_LATEST_WELL_NAME AS "well_name",
    TRIM(z.TIG_DESCRIPTION) AS "zonation_name",
    TRIM(i.TIG_INTERVAL_NAME) AS "zone_name",
    v.TIG_VARIABLE_SHORT_NAME AS "parameter_name",
    vi.TIG_TOP_POINT_DEPTH AS "top_depth",
    vi.TIG_BOT_POINT_DEPTH AS "bottom_depth",
    wh.DB_SLDNID AS "well_id",
    z.DB_SLDNID AS "zonation_id",
    vi.DB_SLDNID AS "zone_id",
    v.DB_SLDNID AS "parameter_id",
    wh.TIG_LONGITUDE,
    wh.TIG_LATITUDE,
    cd.TIG_DELTA_X_ORDINATE AS "cd_x",
    cd.TIG_DELTA_Y_ORDINATE AS "cd_y",
    cd.TIG_INDEX_TRACK_DATA AS "cd_md",
    cd.TIG_Z_ORDINATE AS "cd_tvd",
    z.TIG_ZONATION_PARAMS,
    v.TIG_VARIABLE_SHORT_NAME,
    v.TIG_VARIABLE_REAL_DFLT,
    v.TIG_VARIABLE_REAL_MIN,
    v.TIG_VARIABLE_REAL_MAX,
    v.TIG_VARIABLE_REAL_NULL,
    elev."Elevation",
    i.tig_interval_order,
    i.DB_SLDNID
FROM
    tig_well_interval vi left join
    (SELECT
        e.Well_ID,
        e."Elevation"
    FROM
        (SELECT
            a.DB_SLDNID Elev_ID,
            a.TIG_WELL_SLDNID Well_ID,
            ed1.TIG_DATUM_NAME "Measurement",
            a.TIG_DATUM_OFFSET "Elevation",
            ed2.TIG_DATUM_NAME "Datum"
        FROM
            tig_elevation_changes a,
            tig_elevation_datum ed1,
            tig_elevation_datum ed2
        WHERE
            a.TIG_INITIAL_DATUM = ed1.DB_SLDNID
            AND a.TIG_TERMINAL_DATUM = ed2.DB_SLDNID
            AND(a.TIG_DESCRIPTION IS NULL
            OR a.TIG_DESCRIPTION NOT LIKE 'BOL: %')
        ) e,
        (SELECT
            MAX(tig_elevation_changes.DB_SLDNID) max_elev_Id
        FROM
            tig_elevation_changes
        WHERE(tig_elevation_changes.TIG_DESCRIPTION IS NULL)
            OR(tig_elevation_changes.TIG_DESCRIPTION NOT LIKE 'BOL: %')
        GROUP BY
            tig_elevation_changes.TIG_WELL_SLDNID
        ) i
    WHERE
        e.Elev_ID = i.max_elev_Id
    ) elev on vi.TIG_WELL_SLDNID = elev.Well_ID,
    tig_well_history wh,
    tig_interval i,
    tig_zonation z,
    tig_computed_deviation cd,
    tig_variable v
WHERE
    wh.DB_SLDNID = :well_id
    AND wh.DB_SLDNID = vi.TIG_WELL_SLDNID
    AND vi.TIG_INTERVAL_SLDNID = i.DB_SLDNID
    AND i.TIG_ZONATION_SLDNID = z.DB_SLDNID
    AND(z.DB_SLDNID = :zonation_id
    OR :zonation_id IS NULL)
    AND v.DB_SLDNID = :parameter_id
--    AND(i.DB_SLDNID = :zone_id
--    OR :zone_id IS NULL)
    AND i.tig_interval_order >= :base_order
    AND v.TIG_VARIABLE_TYPE = 2
    AND cd.DB_SLDNID IN
    (SELECT
        MAX(cd2.DB_SLDNID)
    FROM
        tig_computed_deviation cd2
    WHERE
        cd2.TIG_WELL_SLDNID = wh.DB_SLDNID
    )
ORDER BY
    i.tig_interval_order
