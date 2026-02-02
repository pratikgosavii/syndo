from django.urls import path

from .views import *

from django.conf import settings
from django.conf.urls.static import static




from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'coupon', CouponViewSet, basename='CouponViewSet')
router.register(r'banner-campaigns', BannerCampaignViewSet, basename='banner-campaign')
router.register(r'onlineStoreSetting', OnlineStoreSettingViewSet, basename='OnlineStoreSettingViewSet')
router.register(r'company-profile', CompanyProfileViewSet, basename='CompanyProfileViewSet')
router.register(r'delivery-discount', DeliveryDiscountViewSet, basename='DeliveryDiscountViewSet')
router.register(r'store-working-hour', StoreWorkingHourViewSet, basename='StoreWorkingHourViewSet')

router.register(r'customer', customerViewSet, basename='customerViewSet')
router.register(r'vendor', vendorViewSet, basename='vendorViewSet')

router.register(r'post', PostViewSet, basename='PostViewSet')
router.register(r'reel', ReelViewSet, basename='ReelViewSet')
router.register(r'spotlight-product', SpotlightProductViewSet, basename='ProductAddon')

router.register(r'expense', ExpenseViewSet, basename='ExpenseViewSet')
router.register(r'purchase', PurchaseViewSet, basename='PurchaseViewSet')

router.register(r'PrintVariant', PrintVariantViewSet, basename='PrintVariantViewSet')
router.register(r'product', ProductViewSet, basename='product')
router.register(r'super-catalogue', SuperCatalogueViewSet, basename='super-catalogue')
router.register(r'productsetting', ProductSettingsViewSet, basename='ProductSettingsViewSet')
router.register(r'addon', AddonViewSet, basename='AddonViewSet')
router.register(r'product-addon', ProductAddonViewSet, basename='ProductAddonViewSet')

router.register(r'vendor-bank', bankViewSet, basename='bankViewSet')
router.register(r'cash-balance', CashBalanceViewSet, basename='CashBalanceViewSet')
router.register(r'cash-transfers', CashTransferViewSet, basename='CashTransferViewSet')
router.register(r'bank-to-bank-transfers', BankTransferViewSet, basename='BankTransferViewSet')
router.register(r'online-order-ledger', OnlineOrderLedgerViewSet, basename='online-order-ledger')
router.register(r'expense-ledger', ExpenseLedgerViewSet, basename='expense-ledger')
router.register(r'store-reviews', StoreReviewViewSet, basename='store-reviews')

router.register(r'notifcation-campaign', NotificationCampaignViewSet, basename='NotificationCampaignViewSet')

router.register(r'vendor-dashboard', VendorDashboardViewSet, basename='vendor-dashboard')

router.register(r'sales', SaleViewSet, basename='sale')

router.register(r'deliverysettings', DeliverySettingsViewSet, basename='deliverysettings')
router.register(r'deliveryboys', DeliveryBoyViewSet, basename='deliveryboys')
router.register(r'deliverymode', DeliveryModeViewSet, basename='delivery-mode')

router.register(r'taxsettings', TaxSettingsViewSet, basename='taxsettings')
router.register(r'invoicesettings', InvoiceSettingsViewSet, basename='invoicesettings')

router.register(r'payments', PaymentViewSet, basename='payment')

router.register(r'reminder-settings', ReminderSettingViewSet, basename='reminder-settings')
router.register(r'reminders', ReminderViewSet, basename='reminders')
router.register(r'sms-settings', SMSSettingViewSet, basename='sms-settings')
router.register(r'orders', OrderViewSet, basename='orders')

router.register(r'offer', OfferViewSet, basename="offer")
router.register(r'order-notification-message', OrderNotificationMessageViewSet, basename="order-notification-message")



router.register(r'coverage', VendorCoverageViewSet, basename='vendor-coverage')


urlpatterns = [

    
    path('request-list/', requestlist.as_view(), name='request-lists'),
    # Customer-facing invoice PDF (POS)
    path('customer-sale-invoice/', customer_sale_invoice.as_view(), name='customer-sale-invoice'),
    path('return-exchange/<int:order_item_id>/', VendorReturnManageAPIView.as_view(), name='vendor-return-manage-detail'),
    path('return-exchange/', VendorReturnManageAPIView.as_view(), name='vendor-return-manage'),
    path('daybook/', DayBookAPIView.as_view(), name='daybook'),
    path('daybook-report/', daybook_report, name='daybook_report'),
    
    path('add-company-profile/', add_company_profile, name='add_company_profile'),
    path('update-company-profile/<company_profile_id>', update_company_profile, name='update_company_profile'),
    path('delete-company-profile/<company_profile_id>', delete_company_profile, name='delete_company_profile'),
    path('list-company-profile/', list_company_profile, name='list_company_profile'),
    
    path("vendor-stores/", VendorStoreAPIView.as_view(), name="vendor-store-list"),

    path('add-coupon/', add_coupon, name='add_coupon'),
    path('update-coupon/<coupon_id>', update_coupon, name='update_coupon'),
    path('delete-coupon/<coupon_id>', delete_coupon, name='delete_coupon'),
    path('list-coupon/', list_coupon, name='list_coupon'),

    path('add-vendor/', add_vendor, name='add_vendor'),
    path('update-vendor/<vendor_id>', update_vendor, name='update_vendor'),
    path('delete-vendor/<vendor_id>', delete_vendor, name='delete_vendor'),
    path('list-vendor/', list_vendor, name='list_vendor'),
    path('get-vendor/', get_vendor.as_view(), name='get_vendor'),

    path('list-post/', list_post, name='list_post'),
    path('delete-post/<post_id>', delete_post, name='delete_post'),
    
    path('list-reel/', list_reel, name='list_reel'),
    path('delete-reel/<reel_id>', delete_reel, name='delete_reel'),

    path('add-party/', add_party, name='add_party'),
    path('update-party/<party_id>', update_party, name='update_party'),
    path('delete-party/<party_id>', delete_party, name='delete_party'),
    path('list-party/', list_party, name='list_party'),

    path('add-bannercampaign/', add_bannercampaign, name='add_bannercampaign'),
    path('update-bannercampaign/<bannercampaign_id>', update_bannercampaign, name='update_bannercampaign'),
    path('delete-bannercampaign/<bannercampaign_id>', delete_bannercampaign, name='delete_bannercampaign'),
    path('list-bannercampaign/', list_bannercampaign, name='list_bannercampaign'),

    path('add-bank/', add_bank, name='add_bank'),
    path('update-bank/<bank_id>', update_bank, name='update_bank'),
    path('delete-bank/<bank_id>', delete_bank, name='delete_bank'),
    path('list-bank/', list_bank, name='list_bank'),
    path('get-bank/', get_bank.as_view(), name='get_bank'),

    path('bank/<int:id>/ledger/', BankLedgerAPIView.as_view(), name='BankLedgerAPIView'),
    path('cash/ledger/', CashLedgerAPIView.as_view(), name='CashLedgerAPIView'),
    path("customer/<int:customer_id>/ledger/", CustomerLedgerAPIView.as_view(), name="customer-ledger"),
    path("vendor/<int:vendor_id>/ledger/", VendorLedgerAPIView.as_view(), name="vendor-ledger"),

    path('bank-ledger/<int:bank_id>/', bank_ledger, name='bank-ledger'),
    path('customer-ledger/<int:customer_id>/', customer_ledger, name='customer-ledger'),
    path('vendor-ledger/<int:vendor_id>/', vendor_ledger, name='vendor-ledger'),
    path('cash-ledger/', cash_ledger, name='cash-ledger'),
    
    path('add-customer/', add_customer, name='add_customer'),
    path('add-customer-modal/', add_customer_modal, name='add_customer_modal'),
    path('update-customer/<customer_id>', update_customer, name='update_customer'),
    path('delete-customer/<customer_id>', delete_customer, name='delete_customer'),
    path('list-customer/', list_customer, name='list_customer'),
    
    path('add-super-catalogue/', add_super_catalogue, name='add_super_catalogue'),
    path('add-to-super-catalogue/<product_id>', add_to_super_catalogue, name='add_to_super_catalogue'),
    path('update-super-catalogue/<int:super_catalogue_id>/', update_super_catalogue, name='update_super_catalogue'),
    path('delete_super-catalogue/<int:super_catalogue_id>/', delete_super_catalogue, name='delete_super_catalogue'),
    path('list-super-catalogue/', list_super_catalogue, name='list_super_catalogue'),
    
    path('add-product/', add_product, name='add_product'),
    path('add-products/<int:parent_id>/variant/', add_product, name='add_variant'),
    path('update-products/<int:parent_id>/variant/', add_product, name='update_variant'),
    path('update-product/<int:product_id>/', update_product, name='update_product'),
    path('delete_product/<int:product_id>/', delete_product, name='delete_product'),
    path('list-product/', list_product, name='list_product'),
    path('product-setting/', product_setting, name='product_settings'),
    path('barcode-setting/', barcode_setting, name='barcode_setting'),
    path('product_defaults/', product_defaults, name='product_defaults'),
    path('product-defaults/', product_default.as_view(), name='product_default'),

    path('list-stock/', list_stock, name='list_stock'),
    
    path('generate-barcode/', generate_barcode, name='generate_barcode'),

    path('print-variant/choices/', PrintVariantChoiceAPIView.as_view(), name='print-variant-choices'),
    
    path('add-expense/', add_expense, name='add_expense'),
    path('update-expense/<int:expense_id>/', update_expense, name='update_expense'),
    path('delete_expense/<int:expense_id>/', delete_expense, name='delete_expense'),
    path('list-expense/', list_expense, name='list_expense'),

    path('add-purchase/', add_purchase, name='add_purchase'),
    path('purchase-invoice/', purchase_invoice_view, name='purchase-invoice'),
    path('update-purchase/<int:purchase_id>/', update_purchase, name='update_purchase'),
    path('delete_purchase/<int:purchase_id>/', delete_purchase, name='delete_purchase'),
    path('list-purchase/', list_purchase, name='list_purchase'),
    path("get-next-purchaseeno/", NextPurchaseNumberAPI.as_view(), name="NextPurchaseNumberAPI"),

    path('add-addon/', add_addon, name='add_addon'),
    path('update-addon/<addon_id>', update_addon, name='update_addon'),
    path('delete_addon/<addon_id>', delete_addon, name='delete_addon'),
    path('list-addon/', list_addon, name='list_addon'),
    path('get-addon/', get_addon.as_view(), name='get_addon'),

    path('add-payment/', add_payment, name='add_payment'),
    path('update-payment/<payment_id>', update_payment, name='update_payment'),
    path('delete_payment/<payment_id>', delete_payment, name='delete_payment'),
    path('list-payment/', list_payment, name='list_payment'),

    path('store-working-hours/', store_hours_view, name='store_hours'),
    path('online-store-setting/', online_store_setting, name='online_store_setting'),

    path("get-next-invoiceno/", NextInvoiceNumberAPI.as_view(), name="NextInvoiceNumberAPI"),
    path("get_invoice_number/", get_next_invoice_number_api, name="get_invoice_number"),

    path('pos/', pos, name='create-sale'),
    path('barcode-lookup/', barcode_lookup, name='barcode_lookup'),
    path('list-sale/', list_sale, name='list_sale'),
    path('update-sale/<sale_id>', update_sale, name='bill_details_view'),
    path('delete-sale/<sale_id>', delete_sale, name='delete_sale'),

    path('sale-bill-details/<sale_id>', sale_bill_details, name='sale_bill_details'),

    path('get_product_price/', get_product_price, name='get_product_price'),
    path('pos-wholesale/<sale_id>', pos_wholesaless, name='pos_wholesale'),
    path('sale-invoice/<sale_id>', sale_invoice, name='sale_invoice'),

    path('order-details/<order_id>', order_details, name='order_details'),
    path('order-invoice-pdf/<int:order_id>/', order_invoice_pdf, name='order_invoice_pdf'),
    path('order-list/', order_list, name='order_list'),
    path('update-order-item-status/<order_item_id>/', update_order_item_status, name='update_order_item_status'),
    path('order-item-status/<order_item_id>/', UpdateOrderItemStatusAPIView.as_view(), name='order_item_status'),
    path('order-item-tracking/<order_item_id>/', UpdateOrderItemTrackingAPIView.as_view(), name='order_item_tracking'),

    path('order-exchange-list/', order_exchange_list, name='order_exchange_list'),
    path('return-detail/<return_item_id>/', return_detail, name='return_detail'),
    path('approve_return/<return_item_id>/', approve_return, name='approve_return'),
    path('reject-return/<return_item_id>/', reject_return, name='reject_return'),
    path('completed-return/<return_item_id>/', completed_return, name='completed_return'),
    
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    
    # KYC Verification (QuickKYC)
    path('kyc/verify-pan/', VerifyPANAPIView.as_view(), name='verify_pan'),
    path('kyc/verify-gstin/', VerifyGSTINAPIView.as_view(), name='verify_gstin'),
    path('kyc/verify-bank/', VerifyBankAPIView.as_view(), name='verify_bank'),
    path('kyc/verify-fssai/', VerifyFSSAIAPIView.as_view(), name='verify_fssai'),
    path('accept-order/<order_id>', accept_order, name='accept_order'),
    path('assign-delivery-boy/<order_id>', assign_delivery_boy, name='assign_delivery_boy'),
    
    path('delivery-management/', delivery_management, name='delivery_management'),
    path('manage-delivery-boy/', manage_delivery_boy, name='manage_delivery_boy'),
    path('delivery-settings/', delivery_settings_view, name='delivery_settings'),
    path('auto-assign-delivery/', auto_assign_delivery, name='auto_assign_delivery'),

    path('cash-in-hand/', cash_in_hand, name='cash_in_hand'),
    path('adjust-cash/', adjust_cash, name='adjust_cash'),
    path('cash-adjust-history/', CashAdjustHistoryAPIView.as_view(), name='cash_adjust_history'),
    path('cash-adjust-history-fb/', cash_adjust_history_view, name='cash_adjust_history_fb'),
    path('cash-in-hand/transfer/', bank_transfer, name='bank_transfer'),

    path('tax-setting/', tax_setting, name='tax_setting'),
    path('invoice-setting/', invoice_setting, name='invoice_setting'),
    
    # Top Rated Products API
    path('top-rated-products/', TopRatedProductsAPIView.as_view(), name='top_rated_products'),
    
    # Vendor Activity Feed API (no limit)
    path('activity-feed/', VendorActivityFeedAPIView.as_view(), name='vendor_activity_feed'),

]  + router.urls

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)