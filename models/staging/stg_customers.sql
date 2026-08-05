select
    cast(customer_id as integer) as customer_id,
    cast(brand_id as integer) as brand_id,
    first_name,
    last_name,
    email,
    city,
    province,
    loyalty_tier,
    cast(signup_date as date) as signup_date
from {{ ref('customers') }}
