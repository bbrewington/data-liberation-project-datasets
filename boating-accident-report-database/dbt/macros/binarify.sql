{% macro binarify(column_name) %}
case
    when {{ column_name }}::STRING in ('Y', '-1') then TRUE
    when {{ column_name }}::STRING in ('N', '0') then FALSE
    else NULL
end
{% endmacro %}
