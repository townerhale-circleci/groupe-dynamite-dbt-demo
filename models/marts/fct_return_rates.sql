with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

returns as (
    select * from {{ ref('stg_returns') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

brands as (
    select * from {{ ref('stg_brands') }}
),

sold as (
    select
        order_items.product_id,
        sum(order_items.quantity) as units_sold,
        sum(order_items.net_amount) as net_sales
    from order_items
    inner join orders
        on order_items.order_id = orders.order_id
    where orders.order_status != 'cancelled'
    group by order_items.product_id
),

returned as (
    select
        product_id,
        sum(quantity_returned) as units_returned,
        sum(return_amount) as return_amount
    from returns
    group by product_id
)

select
    products.product_id,
    products.sku,
    products.product_name,
    products.category,
    brands.brand_id,
    brands.brand_name,
    coalesce(sold.units_sold, 0) as units_sold,
    coalesce(returned.units_returned, 0) as units_returned,
    coalesce(sold.net_sales, 0) as net_sales,
    coalesce(returned.return_amount, 0) as return_amount,
    round(coalesce(returned.units_returned, 0) / nullif(coalesce(sold.units_sold, 0), 0), 4) as return_rate
from products
inner join brands
    on products.brand_id = brands.brand_id
left join sold
    on products.product_id = sold.product_id
left join returned
    on products.product_id = returned.product_id
