"""Offline validation of the synthetic seed CSVs.

These tests assert referential integrity and core retail business rules on the
seed data WITHOUT requiring a Snowflake connection. They mirror (and guard) the
dbt generic tests declared in seeds/_seeds.yml and models/**/_*.yml.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEEDS_DIR = PROJECT_ROOT / "seeds"


def load_seed(name: str) -> list[dict[str, str]]:
    with (SEEDS_DIR / f"{name}.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def seeds() -> dict[str, list[dict[str, str]]]:
    names = [
        "brands",
        "stores",
        "products",
        "customers",
        "orders",
        "order_items",
        "returns",
        "inventory",
    ]
    return {name: load_seed(name) for name in names}


def _ids(rows: list[dict[str, str]], key: str) -> set[str]:
    return {row[key] for row in rows}


@pytest.mark.parametrize(
    ("seed_name", "pk"),
    [
        ("brands", "brand_id"),
        ("stores", "store_id"),
        ("products", "product_id"),
        ("customers", "customer_id"),
        ("orders", "order_id"),
        ("order_items", "order_item_id"),
        ("returns", "return_id"),
        ("inventory", "inventory_id"),
    ],
)
def test_primary_keys_unique_and_present(seeds, seed_name: str, pk: str) -> None:
    rows = seeds[seed_name]
    values = [row[pk] for row in rows]
    assert all(v != "" for v in values), f"{seed_name}.{pk} has empty values"
    assert len(values) == len(set(values)), f"{seed_name}.{pk} not unique"


def test_referential_integrity(seeds) -> None:
    brand_ids = _ids(seeds["brands"], "brand_id")
    store_ids = _ids(seeds["stores"], "store_id")
    product_ids = _ids(seeds["products"], "product_id")
    customer_ids = _ids(seeds["customers"], "customer_id")
    order_ids = _ids(seeds["orders"], "order_id")
    order_item_ids = _ids(seeds["order_items"], "order_item_id")

    for store in seeds["stores"]:
        assert store["brand_id"] in brand_ids
    for product in seeds["products"]:
        assert product["brand_id"] in brand_ids
    for customer in seeds["customers"]:
        assert customer["brand_id"] in brand_ids
    for order in seeds["orders"]:
        assert order["customer_id"] in customer_ids
        assert order["store_id"] in store_ids
    for item in seeds["order_items"]:
        assert item["order_id"] in order_ids
        assert item["product_id"] in product_ids
    for ret in seeds["returns"]:
        assert ret["order_id"] in order_ids
        assert ret["order_item_id"] in order_item_ids
        assert ret["product_id"] in product_ids
    for inv in seeds["inventory"]:
        assert inv["store_id"] in store_ids
        assert inv["product_id"] in product_ids


@pytest.mark.parametrize(
    ("seed_name", "column", "allowed"),
    [
        ("stores", "store_type", {"physical", "online"}),
        ("orders", "channel", {"store", "ecommerce", "mobile"}),
        ("orders", "order_status", {"completed", "cancelled", "returned"}),
        ("customers", "loyalty_tier", {"none", "silver", "gold"}),
        ("products", "category",
         {"Tops", "Bottoms", "Dresses", "Outerwear", "Accessories"}),
        ("returns", "return_reason",
         {"size", "defect", "changed_mind", "other"}),
    ],
)
def test_accepted_values(seeds, seed_name, column, allowed) -> None:
    for row in seeds[seed_name]:
        assert row[column] in allowed, f"{seed_name}.{column}={row[column]!r}"


def test_order_item_net_amount_non_negative(seeds) -> None:
    for item in seeds["order_items"]:
        qty = int(item["quantity"])
        price = float(item["unit_price"])
        discount = float(item["discount_amount"])
        net = qty * price - discount
        assert qty >= 1, f"order_item {item['order_item_id']} quantity < 1"
        assert net >= 0, f"order_item {item['order_item_id']} net {net} < 0"


def test_return_amounts_valid(seeds) -> None:
    """Return amount must be non-negative and not exceed the line's net sales."""
    line_net = {}
    for item in seeds["order_items"]:
        qty = int(item["quantity"])
        price = float(item["unit_price"])
        discount = float(item["discount_amount"])
        line_net[item["order_item_id"]] = qty * price - discount

    for ret in seeds["returns"]:
        amount = float(ret["return_amount"])
        qty_returned = int(ret["quantity_returned"])
        assert amount >= 0, f"return {ret['return_id']} amount < 0"
        assert qty_returned >= 1, f"return {ret['return_id']} qty < 1"
        assert amount <= line_net[ret["order_item_id"]] + 1e-9, (
            f"return {ret['return_id']} amount {amount} exceeds line net"
        )


def test_inventory_available_non_negative(seeds) -> None:
    for inv in seeds["inventory"]:
        on_hand = int(inv["quantity_on_hand"])
        reserved = int(inv["quantity_reserved"])
        assert on_hand >= 0
        assert reserved >= 0
        assert on_hand - reserved >= 0, (
            f"inventory {inv['inventory_id']} available < 0"
        )


def test_order_item_product_brand_matches_store_brand(seeds) -> None:
    """A line's product brand must match the brand of the order's store."""
    store_brand = {s["store_id"]: s["brand_id"] for s in seeds["stores"]}
    product_brand = {p["product_id"]: p["brand_id"] for p in seeds["products"]}
    order_store = {o["order_id"]: o["store_id"] for o in seeds["orders"]}

    for item in seeds["order_items"]:
        expected_brand = store_brand[order_store[item["order_id"]]]
        actual_brand = product_brand[item["product_id"]]
        assert actual_brand == expected_brand, (
            f"order_item {item['order_item_id']} brand mismatch: "
            f"product brand {actual_brand} vs store brand {expected_brand}"
        )
