import razorpay
from django.conf import settings

def get_razorpay_client():
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def create_razorpay_order(amount_inr, receipt_id, notes=None):
    client = get_razorpay_client()
    amount_paise = int(amount_inr * 100)
    data = {
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': str(receipt_id),
        'payment_capture': '1',
    }
    if notes:
        data['notes'] = notes
    return client.order.create(data=data)

def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    client = get_razorpay_client()
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }
    try:
        client.utility.verify_payment_signature(params_dict)
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
