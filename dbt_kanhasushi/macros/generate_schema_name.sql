-- This macro overrides dbt's default schema generation.
-- Without this, dbt concatenates: profiles.schema + "_" + dbt_project.yml schema
-- e.g.  "" + "_" + "analytics" = "_analytics"  ← wrong
-- With this macro: it uses ONLY the custom schema from dbt_project.yml
-- e.g. "analytics" or "staging" exactly as defined

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
