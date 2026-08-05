{#
    Guarded teardown of a disposable per-PR schema.

    Invoked from CI cleanup as:
        dbt run-operation drop_pr_schema

    By default it targets `target.schema` (which CI sets to the resolved
    GROUPE_DYNAMITE_DEMO_PR_
    schema via DBT_SCHEMA). A schema may also be passed explicitly:
        dbt run-operation drop_pr_schema --args '{schema_name: GROUPE_DYNAMITE_DEMO_PR_42}'

    SAFEGUARDS (defence in depth -- the resolver already guarantees the prefix):
      * Only schemas beginning `GROUPE_DYNAMITE_DEMO_PR_` may be dropped.
      * The RAW, DEV, and PROD demo schemas are refused explicitly.
    Any violation raises a compiler error and drops NOTHING.
#}
{% macro drop_pr_schema(schema_name=none) %}

    {%- set target_schema = (schema_name if schema_name is not none else target.schema) -%}
    {%- set target_schema = (target_schema | trim | upper) -%}

    {%- if not target_schema.startswith('GROUPE_DYNAMITE_DEMO_PR_') -%}
        {{ exceptions.raise_compiler_error(
            "drop_pr_schema refused: '" ~ target_schema ~
            "' is not a prefixed disposable demo PR schema."
        ) }}
    {%- endif -%}

    {%- if target_schema in [
        'GROUPE_DYNAMITE_DEMO_RAW',
        'GROUPE_DYNAMITE_DEMO_DEV',
        'GROUPE_DYNAMITE_DEMO_PROD'
    ] -%}
        {{ exceptions.raise_compiler_error(
            "drop_pr_schema refused: '" ~ target_schema ~
            "' is a protected promotion schema."
        ) }}
    {%- endif -%}

    {%- set drop_sql -%}
        drop schema if exists {{ target.database }}.{{ target_schema }} cascade
    {%- endset -%}

    {%- if execute -%}
        {{ log("drop_pr_schema: dropping " ~ target.database ~ "." ~ target_schema, info=True) }}
        {%- do run_query(drop_sql) -%}
        {{ log("drop_pr_schema: dropped " ~ target_schema, info=True) }}
    {%- endif -%}

{% endmacro %}
