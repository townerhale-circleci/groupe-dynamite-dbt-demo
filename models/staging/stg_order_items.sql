with order_items as (
    select
        cast(order_item_id as integer) as order_item_id,
        cast(order_id as integer) as order_id,
        cast(product_id as integer) as product_id,
        cast(quantity as integer) as quantity,
        cast(unit_price as number(10, 2)) as unit_price,
        cast(discount_amount as number(10, 2)) as discount_amount
    from {{ ref('order_items') }}
)

select
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    discount_amount,
    quantity * unit_price as gross_amount,
    (quantity * unit_price) - discount_amount as net_amount
from order_items
