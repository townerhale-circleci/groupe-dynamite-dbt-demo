with inventory as (
    select
        cast(inventory_id as integer) as inventory_id,
        cast(store_id as integer) as store_id,
        cast(product_id as integer) as product_id,
        cast(quantity_on_hand as integer) as quantity_on_hand,
        cast(quantity_reserved as integer) as quantity_reserved,
        cast(snapshot_date as date) as snapshot_date
    from {{ ref('inventory') }}
)

select
    inventory_id,
    store_id,
    product_id,
    quantity_on_hand,
    quantity_reserved,
    snapshot_date,
    quantity_on_hand - quantity_reserved as quantity_available
from inventory
