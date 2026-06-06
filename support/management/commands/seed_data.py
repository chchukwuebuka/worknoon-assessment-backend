from django.core.management.base import BaseCommand
from support.models import Customer, Order
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Seeds the database with test customers and orders'

    def handle(self, *args, **kwargs):
        # Clear existing data
        Customer.objects.all().delete()
        
        today = datetime.now().date()
        
        customers_data = [
            {"id": "CUST001", "name": "John Doe", "product": "Laptop", "amount": 400.00, "days_ago": 7, "final_sale": False, "damaged": False},
            {"id": "CUST002", "name": "Jane Smith", "product": "Monitor", "amount": 700.00, "days_ago": 10, "final_sale": False, "damaged": False},
            {"id": "CUST003", "name": "David King", "product": "Keyboard", "amount": 50.00, "days_ago": 5, "final_sale": True, "damaged": False},
            {"id": "CUST004", "name": "Sarah Lee", "product": "Phone", "amount": 800.00, "days_ago": 2, "final_sale": False, "damaged": True},
            {"id": "CUST005", "name": "Mike Ray", "product": "Mouse", "amount": 25.00, "days_ago": 20, "final_sale": False, "damaged": False},
            {"id": "CUST006", "name": "Emily Johnson", "product": "Headphones", "amount": 150.00, "days_ago": 3, "final_sale": False, "damaged": False},
            {"id": "CUST007", "name": "James Davis", "product": "Tablet", "amount": 600.00, "days_ago": 1, "final_sale": False, "damaged": False},
            {"id": "CUST008", "name": "Lisa Wilson", "product": "Smartwatch", "amount": 250.00, "days_ago": 16, "final_sale": False, "damaged": False},
        ]

        for data in customers_data:
            customer = Customer.objects.create(customer_id=data["id"], name=data["name"])
            
            Order.objects.create(
                customer=customer,
                product_name=data["product"],
                amount=data["amount"],
                purchase_date=today - timedelta(days=data["days_ago"]),
                is_final_sale=data["final_sale"],
                is_damaged=data["damaged"]
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded the database.'))
