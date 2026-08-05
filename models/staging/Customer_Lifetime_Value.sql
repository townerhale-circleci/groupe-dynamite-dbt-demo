select
    customer_id,
    count(distinct order_id) as lifetime_order_count
from {{ ref('stg_orders') }}
where order_status != 'cancelled'
group by customer_id
