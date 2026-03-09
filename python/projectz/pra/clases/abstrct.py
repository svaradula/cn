from abc import ABC, abstractmethod

class PaymentGateway(ABC):

    def __init__(self):
        print("PaymentGateway initialized")
        pass

    @abstractmethod
    def charge(self, amount: float) -> str:
        """Charge and return transaction id"""
        pass

class StripeGateway(PaymentGateway):
    def __init__(self):
        super().__init__()

    def charge(self, amount: float) -> str:
        return f"stripe_txn_{int(amount * 100)}"

class RazorpayGateway(PaymentGateway):
    def charge(self, amount: float) -> str:
        return f"razorpay_txn_{int(amount * 100)}"

class CheckoutService:
    def __init__(self, gateway: PaymentGateway):
        self.gateway = gateway

    def pay(self, amount: float) -> str:
        if amount <= 0:
            raise ValueError("Amount must be > 0")
        return self.gateway.charge(amount)


checkout = CheckoutService(StripeGateway())
print(checkout.pay(499.0))

checkout2 = CheckoutService(RazorpayGateway())
print(checkout2.pay(499.0))
