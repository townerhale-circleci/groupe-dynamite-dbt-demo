-- =============================================================================
-- Groupe Dynamite demo — Snowflake bootstrap TEMPLATE (DO NOT auto-run).
-- =============================================================================
-- Purpose: provision the minimal, least-privilege objects the dbt Core demo
-- needs. All objects are prefixed with GROUPE_DYNAMITE_DEMO so they are easy to
-- identify and tear down. Statements use IF NOT EXISTS to be idempotent.
--
-- HOW TO USE: review every statement, then execute manually in a Snowflake
-- worksheet with an appropriately privileged role. Replace <SET_A_STRONG_PASSWORD>
-- and grant only what your security policy allows.
--
-- Least privilege notes:
--   * The demo role gets USAGE on the warehouse/database and full rights ONLY
--     on the demo schema — never ACCOUNTADMIN, never access to other databases.
--   * Object creation (warehouse/db/role/user) requires an admin role
--     (SYSADMIN for compute/db, SECURITYADMIN for role/user). Run those parts
--     with the least-privileged admin role that can perform each action.
-- =============================================================================

-- --- Compute (run as SYSADMIN or a role with CREATE WAREHOUSE) ---------------
CREATE WAREHOUSE IF NOT EXISTS GROUPE_DYNAMITE_DEMO_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60            -- suspend quickly to minimize demo cost
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Groupe Dynamite dbt demo warehouse (least-privilege, cost-capped).';

-- --- Database & schema (run as SYSADMIN or a role with CREATE DATABASE) ------
CREATE DATABASE IF NOT EXISTS GROUPE_DYNAMITE_DEMO
    COMMENT = 'Groupe Dynamite dbt Core demo database.';

-- The dbt target schema is created from DBT_SCHEMA (default ANALYTICS below).
-- dbt will also create this on first run; created here for explicit bootstrap.
CREATE SCHEMA IF NOT EXISTS GROUPE_DYNAMITE_DEMO.ANALYTICS
    COMMENT = 'Target schema for dbt models (matches DBT_SCHEMA).';

-- --- Role & user (run as SECURITYADMIN) --------------------------------------
CREATE ROLE IF NOT EXISTS GROUPE_DYNAMITE_DEMO_ROLE
    COMMENT = 'Least-privilege role for the Groupe Dynamite dbt demo.';

CREATE USER IF NOT EXISTS GROUPE_DYNAMITE_DEMO_USER
    PASSWORD = '<SET_A_STRONG_PASSWORD>'   -- rotate immediately; never commit real values
    DEFAULT_ROLE = GROUPE_DYNAMITE_DEMO_ROLE
    DEFAULT_WAREHOUSE = GROUPE_DYNAMITE_DEMO_WH
    MUST_CHANGE_PASSWORD = TRUE
    COMMENT = 'Service user for the Groupe Dynamite dbt demo.';

-- --- Grants: warehouse + database usage (least privilege) --------------------
GRANT USAGE ON WAREHOUSE GROUPE_DYNAMITE_DEMO_WH TO ROLE GROUPE_DYNAMITE_DEMO_ROLE;
GRANT USAGE ON DATABASE GROUPE_DYNAMITE_DEMO TO ROLE GROUPE_DYNAMITE_DEMO_ROLE;

-- --- Grants: full control scoped to the demo schema ONLY ---------------------
GRANT USAGE ON SCHEMA GROUPE_DYNAMITE_DEMO.ANALYTICS TO ROLE GROUPE_DYNAMITE_DEMO_ROLE;
GRANT CREATE TABLE ON SCHEMA GROUPE_DYNAMITE_DEMO.ANALYTICS TO ROLE GROUPE_DYNAMITE_DEMO_ROLE;
GRANT CREATE VIEW ON SCHEMA GROUPE_DYNAMITE_DEMO.ANALYTICS TO ROLE GROUPE_DYNAMITE_DEMO_ROLE;

-- Future objects created by dbt inherit read/select for the same role.
GRANT SELECT ON FUTURE TABLES IN SCHEMA GROUPE_DYNAMITE_DEMO.ANALYTICS
    TO ROLE GROUPE_DYNAMITE_DEMO_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA GROUPE_DYNAMITE_DEMO.ANALYTICS
    TO ROLE GROUPE_DYNAMITE_DEMO_ROLE;

-- --- Assign the role to the demo user (run as SECURITYADMIN) -----------------
GRANT ROLE GROUPE_DYNAMITE_DEMO_ROLE TO USER GROUPE_DYNAMITE_DEMO_USER;
