select
    cast(return_id as integer) as return_id,
    cast(order_id as integer) as order_id,
    cast(order_item_id as integer) as order_item_id,
    cast(product_id as integer) as product_id,
    cast(return_date as date) as return_date,
    cast(quantity_returned as integer) as quantity_returned,
    cast(return_amount as number(10, 2)) as return_amount,
    return_reason
from {{ ref('returns') }}
