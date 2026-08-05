{#
    Generic (data) test: fail if any row has a negative value in `column_name`.

    Retail business rule usage: net sales, return amounts, and inventory
    availability must never be negative. Current dbt generic-test syntax:
    a {% test %} block that returns the *failing* rows.
#}
{% test non_negative(model, column_name) %}

select
    {{ column_name }} as failing_value
from {{ model }}
where {{ column_name }} < 0

{% endtest %}
