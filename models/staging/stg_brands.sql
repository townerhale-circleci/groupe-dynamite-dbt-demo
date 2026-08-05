select
    cast(brand_id as integer) as brand_id,
    brand_code,
    brand_name
from {{ ref('brands') }}
