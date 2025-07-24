{% macro binary_int(column_name) %}
case
    when {{ column_name }} = -1 then TRUE
    when {{ column_name }} = 0 then FALSE
    else NULL
end
{% endmacro %}

{% macro binary_str_yn(column_name) %}
case
    when {{ column_name }} in ('Y', '-1') then TRUE
    when {{ column_name }} in ('N', '0') then FALSE
    else NULL
end
{% endmacro %}
