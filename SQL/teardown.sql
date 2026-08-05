-- =============================================================================
-- Groupe Dynamite demo — Snowflake teardown TEMPLATE (DO NOT auto-run).
-- =============================================================================
-- Purpose: remove everything bootstrap.sql created. Every statement uses
-- IF EXISTS so it is idempotent and safe to re-run. Objects are dropped in
-- reverse dependency order.
--
-- HOW TO USE: review, then execute manually with the appropriate admin role.
-- WARNING: DROP DATABASE permanently deletes all demo data. Confirm you are
-- targeting the GROUPE_DYNAMITE_DEMO objects only before running.
--
-- Least privilege notes:
--   * Dropping the role/user requires SECURITYADMIN.
--   * Dropping the warehouse/database requires SYSADMIN (or the object owner).
-- =============================================================================

-- --- Drop user & role (run as SECURITYADMIN) ---------------------------------
-- Dropping the demo user removes its role grant; an explicit REVOKE is omitted
-- because Snowflake has no REVOKE ... IF EXISTS form for an idempotent rerun.
DROP USER IF EXISTS GROUPE_DYNAMITE_DEMO_USER;
DROP ROLE IF EXISTS GROUPE_DYNAMITE_DEMO_ROLE;

-- --- Drop database (cascades schema + objects) and warehouse (SYSADMIN) ------
DROP DATABASE IF EXISTS GROUPE_DYNAMITE_DEMO;
DROP WAREHOUSE IF EXISTS GROUPE_DYNAMITE_DEMO_WH;
