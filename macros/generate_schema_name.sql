{#
    Build the target schema from DBT_SCHEMA (surfaced as target.schema via
    profiles.yml) instead of dbt's default "<target>_<custom>" concatenation.

    - No custom schema on a model  -> use the connection's schema (DBT_SCHEMA).
    - Custom schema on a model      -> use that name verbatim.

    This keeps demo objects in a single, predictable schema created from the
    DBT_SCHEMA environment variable.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
