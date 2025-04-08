import json
from collections import defaultdict

class OrderManager:
    def __init__(self, order_json_path):
        with open(order_json_path, 'r') as f:
            self.order_data = json.load(f)

        self.required = defaultdict(int)
        self.scanned = defaultdict(int)
        for item in self.order_data['items']:
            sku = item['sku']
            qty = item['quantity']
            self.required[sku] += qty

        self.current_sku = None

    def scan_product(self, sku):
        if sku not in self.required:
            return "Invalid SKU", False

        self.scanned[sku] += 1

        if self.scanned[sku] == self.required[sku]:
            return f"✅ {sku} complete. Ready to print label.", True
        elif self.scanned[sku] < self.required[sku]:
            remaining = self.required[sku] - self.scanned[sku]
            return f"🛒 {sku} scanned. {remaining} more to go.", False
        else:
            return f"⚠️ Extra {sku} scanned. Already complete.", False

    def is_order_complete(self):
        return all(self.scanned[sku] >= self.required[sku] for sku in self.required)

    def get_pending_items(self):
        return {
            sku: self.required[sku] - self.scanned.get(sku, 0)
            for sku in self.required
            if self.scanned.get(sku, 0) < self.required[sku]
        }

    def reset(self):
        self.scanned = defaultdict(int)