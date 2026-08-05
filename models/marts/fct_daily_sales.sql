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
        orders.order_date,
        brands.brand_id,
        brands.brand_name,
        orders.channel,
        orders.order_id,
        order_items.quantity,
        order_items.gross_amount,
        order_items.discount_amount,
        order_items.net_amount
    from order_items
    inner join orders
        on order_items.order_id = orders.order_id
    inner join stores
        on orders.store_id = stores.store_id
    inner join brands
        on stores.brand_id = brands.brand_id
    where orders.order_status != 'cancelled'
),

aggregated as (
    select
        order_date,
        brand_id,
        brand_name,
        channel,
        count(distinct order_id) as order_count,
        sum(quantity) as unit_count,
        sum(gross_amount) as gross_sales,
        sum(discount_amount) as total_discount,
        sum(net_amount) as net_sales
    from joined
    group by
        order_date,
        brand_id,
        brand_name,
        channel
)

select
    order_date,
    brand_id,
    brand_name,
    channel,
    order_count,
    unit_count,
    gross_sales,
    total_discount,
    net_sales,
    cast(order_date as varchar) || '|' || cast(brand_id as varchar) || '|' || channel as daily_sales_key
from aggregated
