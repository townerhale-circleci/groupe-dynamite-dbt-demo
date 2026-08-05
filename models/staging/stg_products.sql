select
    cast(product_id as integer) as product_id,
    cast(brand_id as integer) as brand_id,
    sku,
    product_name,
    category,
    cast(unit_price as number(10, 2)) as unit_price,
    cast(unit_cost as number(10, 2)) as unit_cost
from {{ ref('products') }}
