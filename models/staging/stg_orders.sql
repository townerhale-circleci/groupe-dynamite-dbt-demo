select
    cast(order_id as integer) as order_id,
    cast(customer_id as integer) as customer_id,
    cast(store_id as integer) as store_id,
    channel,
    cast(order_date as date) as order_date,
    order_status
from {{ ref('orders') }}
