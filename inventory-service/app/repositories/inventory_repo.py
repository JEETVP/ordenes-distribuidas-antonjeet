from models import InventoryItem


class InventoryRepository:
    def __init__(self, session):
        self.session = session

    def get(self, sku: str):
        return self.session.get(InventoryItem, sku)

    def upsert_stock(self, sku: str, stock: int):
        item = self.get(sku)

        if item is None:
            item = InventoryItem(sku=sku, stock=stock)
            self.session.add(item)
        else:
            item.stock = stock

        return item

    def reserve_stock(self, sku: str, qty: int):
        item = self.get(sku)

        if item is None:
            item = InventoryItem(sku=sku, stock=0)
            self.session.add(item)
            self.session.flush()

        item.stock -= qty
        return item
