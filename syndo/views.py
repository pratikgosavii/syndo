
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal

from vendor.models import Sale, Purchase, Expense, Payment, product, vendor_customers, vendor_vendors


@login_required(login_url='login_admin')
def dashboard(request):
    user = request.user
    is_admin = user.is_superuser

    # Base querysets - filter by user for vendors, all for admin
    if is_admin:
        sale_qs = Sale.objects.all()
        purchase_qs = Purchase.objects.all()
        expense_qs = Expense.objects.all()
        payment_qs = Payment.objects.all()
        product_qs = product.objects.filter(parent__isnull=True)  # top-level products only
        customer_qs = vendor_customers.objects.all()
        vendor_qs = vendor_vendors.objects.all()
    else:
        sale_qs = Sale.objects.filter(user=user)
        purchase_qs = Purchase.objects.filter(user=user)
        expense_qs = Expense.objects.filter(user=user)
        payment_qs = Payment.objects.filter(user=user)
        product_qs = product.objects.filter(user=user, parent__isnull=True)
        # Customers/Vendors linked to user's company or through their sales/purchases
        customer_qs = vendor_customers.objects.filter(user=user)
        vendor_qs = vendor_vendors.objects.filter(user=user)

    today = timezone.now().date()

    # Week boundaries (Mon-Sun)
    from datetime import timedelta
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    start_of_last_week = start_of_week - timedelta(days=7)
    end_of_last_week = start_of_week - timedelta(days=1)

    # --- Totals ---
    total_sales = sale_qs.aggregate(s=Sum('total_amount'))['s'] or Decimal('0')
    total_purchases = purchase_qs.aggregate(s=Sum('total_amount'))['s'] or Decimal('0')
    total_expenses = expense_qs.aggregate(s=Sum('amount'))['s'] or Decimal('0')

    payments_received = payment_qs.filter(type='received').aggregate(s=Sum('amount'))['s'] or Decimal('0')
    payments_given = payment_qs.filter(type='gave').aggregate(s=Sum('amount'))['s'] or Decimal('0')
    net_payments = payments_received - payments_given

    # --- This week vs last week ---
    sales_this_week = sale_qs.filter(created_at__date__gte=start_of_week, created_at__date__lte=end_of_week)
    sales_last_week = sale_qs.filter(created_at__date__gte=start_of_last_week, created_at__date__lte=end_of_last_week)

    sales_count_this_week = sales_this_week.count()
    sales_count_last_week = sales_last_week.count()
    sales_amount_this_week = sales_this_week.aggregate(s=Sum('total_amount'))['s'] or Decimal('0')
    sales_amount_last_week = sales_last_week.aggregate(s=Sum('total_amount'))['s'] or Decimal('0')

    # Percentage change
    if sales_count_last_week > 0:
        sales_count_pct = round(((sales_count_this_week - sales_count_last_week) / sales_count_last_week) * 100, 1)
    else:
        sales_count_pct = sales_count_this_week * 100 if sales_count_this_week > 0 else 0

    if sales_amount_last_week and sales_amount_last_week > 0:
        sales_amount_pct = round(((float(sales_amount_this_week) - float(sales_amount_last_week)) / float(sales_amount_last_week)) * 100, 1)
    else:
        sales_amount_pct = 100.0 if sales_amount_this_week else 0

    # --- Recent data ---
    recent_sales = sale_qs.select_related('customer').order_by('-created_at')[:8]
    recent_purchases = purchase_qs.select_related('vendor').order_by('-purchase_date')[:5]

    # Low stock products (for vendors who track stock)
    low_stock_list = []
    for p in product_qs.filter(track_stock=True, low_stock_alert=True):
        stock_val = p.stock_cached if p.stock_cached is not None else p.stock
        low_val = p.low_stock_quantity or 0
        if stock_val is not None and low_val > 0 and stock_val <= low_val:
            low_stock_list.append(p)
            if len(low_stock_list) >= 5:
                break

    # Counts
    total_products = product_qs.count()
    total_customers = customer_qs.count()
    total_vendors_count = vendor_qs.count()

    # Today's activity
    today_sales_count = sale_qs.filter(created_at__date=today).count()
    today_sales_amount = sale_qs.filter(created_at__date=today).aggregate(s=Sum('total_amount'))['s'] or Decimal('0')
    today_purchases_count = purchase_qs.filter(purchase_date=today).count()
    today_purchases_amount = purchase_qs.filter(purchase_date=today).aggregate(s=Sum('total_amount'))['s'] or Decimal('0')

    # This month
    start_of_month = today.replace(day=1)
    month_sales = sale_qs.filter(created_at__date__gte=start_of_month, created_at__date__lte=today).aggregate(s=Sum('total_amount'))['s'] or Decimal('0')
    month_purchases = purchase_qs.filter(purchase_date__gte=start_of_month, purchase_date__lte=today).aggregate(s=Sum('total_amount'))['s'] or Decimal('0')

    context = {
        'is_admin': is_admin,
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'total_expenses': total_expenses,
        'payments_received': payments_received,
        'payments_given': payments_given,
        'net_payments': net_payments,
        'sales_count_this_week': sales_count_this_week,
        'sales_count_last_week': sales_count_last_week,
        'sales_count_pct': sales_count_pct,
        'sales_amount_this_week': sales_amount_this_week,
        'sales_amount_last_week': sales_amount_last_week,
        'sales_amount_pct': sales_amount_pct,
        'recent_sales': recent_sales,
        'recent_purchases': recent_purchases,
        'low_stock_products': low_stock_list,
        'total_products': total_products,
        'total_customers': total_customers,
        'total_vendors_count': total_vendors_count,
        'today_sales_count': today_sales_count,
        'today_sales_amount': today_sales_amount,
        'today_purchases_count': today_purchases_count,
        'today_purchases_amount': today_purchases_amount,
        'month_sales': month_sales,
        'month_purchases': month_purchases,
    }

    return render(request, 'adminDashboard.html', context)
