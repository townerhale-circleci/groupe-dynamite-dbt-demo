select
    cast(store_id as integer) as store_id,
    store_name,
    cast(brand_id as integer) as brand_id,
    store_type,
    city,
    province,
    country,
    cast(opened_date as date) as opened_date
from {{ ref('stores') }}
