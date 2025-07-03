SELECT
    studyid AS STUDYID,
    rdomain AS RDOMAIN,
    usubjid AS USUBJID,
    idvar AS IDVAR,
    idvarval AS IDVARVAL,
    qnam AS QNAM,
    qlabel AS QLABEL,
    qval AS QVAL
FROM {% raw %}{{ ref('raw_suppdm') }}{% endraw %};