with inventory as (
    select * from {{ ref('stg_inventory') }}
),

stores as (
    select * from {{ ref('stg_stores') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

brands as (
    select * from {{ ref('stg_brands') }}
)

select
    inventory.inventory_id,
    inventory.snapshot_date,
    inventory.store_id,
    stores.store_name,
    stores.store_type,
    brands.brand_id,
    brands.brand_name,
    inventory.product_id,
    products.sku,
    products.product_name,
    products.category,
    inventory.quantity_on_hand,
    inventory.quantity_reserved,
    inventory.quantity_available,
    coalesce(inventory.quantity_available > 0, false) as is_available
from inventory
inner join stores
    on inventory.store_id = stores.store_id
inner join products
    on inventory.product_id = products.product_id
inner join brands
    on stores.brand_id = brands.brand_id
