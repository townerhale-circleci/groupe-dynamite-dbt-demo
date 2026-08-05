with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

stores as (
    select * from {{ ref('stg_stores') }}
),

brands as (
    select * from {{ ref('stg_brands') }}
),

joined as (
    select
        stores.store_id,
        stores.store_name,
        stores.store_type,
        brands.brand_id,
        brands.brand_name,
        orders.order_id,
        order_items.quantity,
        order_items.gross_amount,
        order_items.net_amount
    from order_items
    inner join orders
        on order_items.order_id = orders.order_id
    inner join stores
        on orders.store_id = stores.store_id
    inner join brands
        on stores.brand_id = brands.brand_id
    where orders.order_status != 'cancelled'
)

select
    store_id,
    store_name,
    store_type,
    brand_id,
    brand_name,
    count(distinct order_id) as order_count,
    sum(quantity) as unit_count,
    sum(gross_amount) as gross_sales,
    sum(net_amount) as net_sales,
    round(sum(net_amount) / nullif(count(distinct order_id), 0), 2) as avg_order_value
from joined
group by
    store_id,
    store_name,
    store_type,
    brand_id,
    brand_name
