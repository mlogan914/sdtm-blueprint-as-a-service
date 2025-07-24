{% macro convert_us_date_to_iso(column_name) %}
    CASE 
        WHEN {{ column_name }} IS NULL OR TRIM({{ column_name }}) = '' THEN NULL
        ELSE STRFTIME(STRPTIME({{ column_name }}, '%m/%d/%Y'), '%Y-%m-%d')
    END
{% endmacro %}

