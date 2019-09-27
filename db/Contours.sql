SELECT
    ms.TIG_MAP_SET_NO,
    msp.TIG_MAP_SET_PARAMETER_NO,
    mss.TIG_MAP_SUBSET_NO,
    ms.TIG_MAP_SET_NAME,
    msp.TIG_PARAM_LONG_NAME,
    mss.TIG_MAP_SUBSET_NAME,
    mss.TIG_MAP_X,
    mss.TIG_MAP_Y,
    mssp.TIG_MAP_PARAM_VRLONG,
    mv.TIG_MAP_VARIABLE_NAME
FROM
    TIG_MAP_SET ms,
    TIG_MAP_SET_PARAM msp left join TIG_MAP_VARIABLE mv on mv.DB_SLDNID=msp.TIG_PARAM_SHORT_NAME,
    TIG_MAP_SUBSET mss,
    TIG_MAP_SUBSET_PARAM_VAL mssp
WHERE
    ms.TIG_MAP_SET_NO = msp.TIG_MAP_SET_NO
    AND ms.TIG_MAP_SET_NO = mss.TIG_MAP_SET_NO
    AND ms.TIG_MAP_SET_NO = mssp.TIG_MAP_SET_NO
    AND mssp.TIG_MAP_SET_PARAMETER_NO = msp.TIG_MAP_SET_PARAMETER_NO
    AND mssp.TIG_MAP_SUBSET_NO = mss.TIG_MAP_SUBSET_NO
    AND(ms.TIG_MAP_SET_NO = :group_id
    OR :group_id IS NULL)
    AND(msp.TIG_MAP_SET_PARAMETER_NO = :set_id
    OR :set_id IS NULL)
    AND ms.TIG_MAP_SET_TYPE = 1
    AND msp.TIG_MAP_SET_CP_SOURCE = 4
