{% macro initcap(column_name) %}
list_reduce(
    list_transform(
        regexp_split_to_array({{ column_name }}, '\s+'),
        w -> upper(w[1]) || lower(w[2:])),
    (x,y) -> x || ' ' || y
)
{% endmacro %}
