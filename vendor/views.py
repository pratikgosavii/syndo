from django.shortcuts import get_object_or_404, render

from masters.filters import EventFilter
from vendor.filters import productFilter

# Create your views here.


from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from django.urls import reverse
from django.http.response import HttpResponseRedirect
from django.http import HttpResponse
from .serializers import *

from users.permissions import *
from django.db.models import Sum

from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from integrations.uengage import notify_delivery_event, create_delivery_task
from vendor.models import DeliveryBoy, DeliveryMode, CompanyProfile, DeliveryDiscount, AutomateNotificationOnOrder


from django_filters.rest_framework import DjangoFilterBackend

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger




      
def online_store_setting(request):
    setting, created = OnlineStoreSetting.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OnlineStoreSettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            return redirect('online_store_setting')
    else:
        form = OnlineStoreSettingForm(instance=setting)

    return render(request, 'store_setting.html', {'form': form})




@login_required(login_url='login_admin')
def add_company_profile(request):

     # ✅ Check if user already has a company profile
    if CompanyProfile.objects.filter(user=request.user).exists():
        messages.error(request, "You already have a company profile. Only one profile is allowed.")
        return redirect('list_company_profile')
    

    if request.method == 'POST':
        form = CompanyProfileForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.save()
            return redirect('list_company_profile')
        else:
            return render(request, 'add_company_profile.html', {
                'form': form,
                'error': 'Please fix the errors below.'
            })
    else:
        form = CompanyProfileForm()
        return render(request, 'add_company_profile.html', {'form': form})

        

@login_required(login_url='login_admin')
def update_company_profile(request, company_profile_id):

    if request.method == 'POST':

        instance = CompanyProfile.objects.get(id=company_profile_id)

        forms = CompanyProfileForm(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_company_profile')
        else:
            print(forms.errors)
    
    else:

        instance = CompanyProfile.objects.get(id=company_profile_id)
        forms = CompanyProfileForm(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_company_profile.html', context)

        

@login_required(login_url='login_admin')
def delete_company_profile(request, company_profile_id):

    CompanyProfile.objects.get(id=company_profile_id).delete()

    return HttpResponseRedirect(reverse('list_company_profile'))


@login_required(login_url='login_admin')
def list_company_profile(request):
    
    data = CompanyProfile.objects.filter(user = request.user)
    context = {
        'data': data
    }
    return render(request, 'list_company_profile.html', context)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import vendor_store
from .serializers import VendorStoreSerializer

class VendorStoreAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.user)
        """Get the logged-in vendor's store"""
        try:
            store = vendor_store.objects.get(user=request.user)
            serializer = VendorStoreSerializer(store)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except vendor_store.DoesNotExist:
            return Response({"detail": "Store not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        """Update the logged-in vendor's store"""
        try:
            store = vendor_store.objects.get(user=request.user)
            serializer = VendorStoreSerializer(store, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(user=request.user)  # make sure store stays linked to vendor
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except vendor_store.DoesNotExist:
            return Response({"detail": "Store not found."}, status=status.HTTP_404_NOT_FOUND)      

@login_required(login_url='login_admin')
def add_coupon(request):

    if request.method == 'POST':

        forms = coupon_Form(request.POST, request.FILES)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_coupon')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_coupon.html', context)
    
    else:

        forms = coupon_Form()

        context = {
            'form': forms
        }
        return render(request, 'add_coupon.html', context)

        

@login_required(login_url='login_admin')
def update_coupon(request, coupon_id):

    if request.method == 'POST':

        instance = coupon.objects.get(id=coupon_id)

        forms = coupon_Form(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_coupon')
        else:
            print(forms.errors)
    
    else:

        instance = coupon.objects.get(id=coupon_id)
        forms = coupon_Form(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_coupon.html', context)

        

@login_required(login_url='login_admin')
def delete_coupon(request, coupon_id):

    coupon.objects.get(id=coupon_id).delete()

    return HttpResponseRedirect(reverse('list_coupon'))


@login_required(login_url='login_admin')
def list_coupon(request):

    data = coupon.objects.filter(user = request.user)
    context = {
        'data': data
    }
    return render(request, 'list_coupon.html', context)



@login_required(login_url='login_admin')
def add_vendor(request):

    if request.method == 'POST':

        forms = vendor_vendorsForm(request.POST, request.FILES)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_vendor')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_vendor.html', context)
    
    else:

        forms = vendor_vendorsForm()

        context = {
            'form': forms
        }
        return render(request, 'add_vendor.html', context)

        

@login_required(login_url='login_admin')
def update_vendor(request, vendor_id):

    if request.method == 'POST':

        instance = vendor_vendors.objects.get(id=vendor_id)

        forms = vendor_vendorsForm(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_vendor')
        else:
            print(forms.errors)
    
    else:

        instance = vendor_vendors.objects.get(id=vendor_id)
        forms = vendor_vendorsForm(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_vendor.html', context)

        

@login_required(login_url='login_admin')
def delete_vendor(request, vendor_id):

    vendor_vendors.objects.get(id=vendor_id).delete()

    return HttpResponseRedirect(reverse('list_vendor'))


@login_required(login_url='login_admin')
def list_vendor(request):

    data = vendor_vendors.objects.filter(user = request.user)
    context = {
        'data': data
    }
    return render(request, 'list_vendor.html', context)


from .serializers import *

class get_vendor(ListAPIView):
    
    serializer_class = vendor_serializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'

    def get_queryset(self):
        return vendor_vendors.objects.filter(user=self.request.user)


@login_required(login_url='login_admin')
def add_party(request):

    if request.method == 'POST':

        forms = PartyForm(request.POST, request.FILES)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_party')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_party.html', context)
    
    else:

        forms = PartyForm()

        context = {
            'form': forms
        }
        return render(request, 'add_party.html', context)

        

@login_required(login_url='login_admin')
def update_party(request, party_id):

    if request.method == 'POST':

        instance = Party.objects.get(id=party_id)

        forms = PartyForm(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_party')
        else:
            print(forms.errors)
    
    else:

        instance = Party.objects.get(id=party_id)
        forms = PartyForm(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_party.html', context)

        

@login_required(login_url='login_admin')
def delete_party(request, party_id):

    Party.objects.get(id=party_id).delete()

    return HttpResponseRedirect(reverse('list_party'))


@login_required(login_url='login_admin')
def list_party(request):

    data = Party.objects.filter(user = request.user)
    context = {
        'data': data
    }
    return render(request, 'list_party.html', context)


@login_required(login_url='login_admin')
def add_bannercampaign(request):

    if request.method == 'POST':

        forms = BannerCampaignForm(request.POST, request.FILES)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_bannercampaign')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_bannercampaign.html', context)
    
    else:

        forms = BannerCampaignForm()

        context = {
            'form': forms
        }
        return render(request, 'add_bannercampaign.html', context)

        

@login_required(login_url='login_admin')
def update_bannercampaign(request, bannercampaign_id):

    if request.method == 'POST':

        instance = BannerCampaign.objects.get(id=bannercampaign_id)

        forms = BannerCampaignForm(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_bannercampaign')
        else:
            print(forms.errors)
    
    else:

        instance = BannerCampaign.objects.get(id=bannercampaign_id)
        forms = BannerCampaignForm(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_bannercampaign.html', context)

        

@login_required(login_url='login_admin')
def delete_bannercampaign(request, bannercampaign_id):

    BannerCampaign.objects.get(id=bannercampaign_id).delete()

    return HttpResponseRedirect(reverse('list_bannercampaign'))


@login_required(login_url='login_admin')
def list_bannercampaign(request):

    data = BannerCampaign.objects.filter(user = request.user)
    context = {
        'data': data
    }
    return render(request, 'list_bannercampaign.html', context)




@login_required(login_url='login_admin')
def add_bank(request):

    if request.method == 'POST':

        forms = VendorBankForm(request.POST, request.FILES)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_bank')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_bank.html', context)
    
    else:

        forms = VendorBankForm()

        context = {
            'form': forms
        }
        return render(request, 'add_bank.html', context)

        

@login_required(login_url='login_admin')
def update_bank(request, bank_id):

    if request.method == 'POST':

        instance = vendor_bank.objects.get(id=bank_id)

        forms = VendorBankForm(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_bank')
        else:
            print(forms.errors)
    
    else:

        instance = vendor_bank.objects.get(id=bank_id)
        forms = VendorBankForm(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_bank.html', context)

        

@login_required(login_url='login_admin')
def delete_bank(request, bank_id):

    vendor_bank.objects.get(id=bank_id).delete()

    return HttpResponseRedirect(reverse('list_bank'))


@login_required(login_url='login_admin')
def list_bank(request):

    data = vendor_bank.objects.filter(user = request.user)
    context = {
        'data': data
    }
    return render(request, 'list_bank.html', context)



class get_bank(ListAPIView):
    serializer_class = vendor_bank_serializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'

    def get_queryset(self):
        return vendor_bank.objects.filter(user=self.request.user)


from rest_framework import generics


class BankLedgerAPIView(APIView):
    def get(self, request, id):
        try:
            bank = vendor_bank.objects.get(id=id)
        except vendor_bank.DoesNotExist:
            return Response({"error": "Bank not found"}, status=404)

        serializer = BankWithLedgerSerializer(bank)

        # Optional: also include current total of ledger entries
        ledger_total = bank.ledger_entries.aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "bank_id": bank.id,
            "bank_name": bank.name,
            "opening" :  bank.opening_balance,
            "balance": bank.opening_balance + ledger_total,
            "ledger": serializer.data.get("ledger_entries", [])
        })
    

class CashLedgerAPIView(APIView):
    """
    Returns all cash ledger entries and current cash balance.
    """
    def get(self, request):
        # All cash ledger entries ordered by latest
        ledger_entries = CashLedger.objects.filter(user=request.user).order_by("-created_at")
        serializer = CashLedgerSerializer(ledger_entries, many=True)

        # Current cash balance from CashBalance model (updated by signals)
        from .models import CashBalance
        try:
            balance_obj = CashBalance.objects.get(user=request.user)
            cash_balance = balance_obj.balance or 0
        except CashBalance.DoesNotExist:
            # Fallback: calculate from ledger entries
            cash_balance = ledger_entries.aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "cash_balance": cash_balance,
            "ledger": serializer.data
        })
    

from customer.serializers import *


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.prefetch_related('items__product').filter(user=self.request.user).order_by('-id')

    def update(self, request, *args, **kwargs):
        """Restrict update to only allowed fields"""
        instance = self.get_object()
        previous_status = instance.status
        allowed_fields = {"status", "delivery_boy", "is_paid"}
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Auto-assign logic when order moves to ready_to_shipment (post-pack)
        try:
            if (
                "status" in data
                and data["status"] == "ready_to_shipment"
                and previous_status != "ready_to_shipment"
            ):
                print("\n" + "=" * 80)
                print("🚚 [Vendor OrderViewSet] Auto-assign on ready_to_shipment")
                print(f"📦 Order ID: {instance.order_id}")
                print(f"👤 Previous status: {previous_status}")

                # Identify vendor user from first item
                item0 = instance.items.select_related("product").first()
                vendor_user = item0.product.user if item0 and getattr(item0.product, "user", None) else None
                print(f"🏪 Vendor user: {vendor_user}")
                if vendor_user:
                    mode = DeliveryMode.objects.filter(user=vendor_user).first()
                else:
                    mode = None
                print(f"⚙️ Delivery mode: {mode}")

                if mode and mode.is_auto_assign_enabled:
                    print(f"✅ Auto-assign enabled (self_delivery={getattr(mode, 'is_self_delivery_enabled', False)})")
                    # Skip if already assigned or task created
                    if getattr(instance, "delivery_boy_id", None) or getattr(instance, "uengage_task_id", None):
                        print("⏭️ Already has delivery_boy or uengage_task_id; skipping assignment")
                    # Prefer self delivery if enabled and rider available
                    elif getattr(mode, "is_self_delivery_enabled", False):
                        rider = DeliveryBoy.objects.filter(user=vendor_user, is_active=True).order_by("total_deliveries").first()
                        if rider:
                            print(f"👷 Assigned self-delivery rider: {rider}")
                            instance.delivery_boy = rider
                            instance.save(update_fields=["delivery_boy"])
                        else:
                            print("⚠️ No active self-delivery rider found")
                    else:
                        rider = None

                    # If no rider was set above, attempt external task creation
                    if not getattr(instance, "delivery_boy_id", None) and not getattr(instance, "uengage_task_id", None):
                        print("🌐 Creating external delivery task via uEngage")
                        res = create_delivery_task(instance)
                        print(f"📊 uEngage response: {res}")
                        if res.get("ok"):
                            # persist task id and tracking across items
                            task_id = res.get("task_id")
                            tracking = res.get("tracking_url")
                            if task_id:
                                print(f"💾 Saving uEngage task_id: {task_id}")
                                instance.uengage_task_id = task_id
                                instance.save(update_fields=["uengage_task_id"])
                            if tracking:
                                for it in instance.items.all():
                                    if not it.tracking_link:
                                        it.tracking_link = tracking
                                        it.save(update_fields=["tracking_link"])
                                print(f"🔗 Applied tracking link to items: {tracking}")
                        else:
                            # Could notify vendor here about failure; do not block
                            print("💥 uEngage task creation failed or not ok; skipping assignment")
                else:
                    print("⏭️ Auto-assign disabled or mode missing; no assignment attempted")
                print("=" * 80 + "\n")
        except Exception:
            pass

        # Notify via uEngage on status change (order-level)
        try:
            if "status" in data and data["status"] != previous_status:
                mapping = {
                    "accepted": "order_confirmed",
                    "completed": "delivered",
                    "cancelled": "cancelled",
                }
                evt = mapping.get(instance.status)
                if evt:
                    notify_delivery_event(instance, evt)
        except Exception:
            pass
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """PATCH behaves same as restricted PUT"""
        return self.update(request, *args, **kwargs)


    

@login_required(login_url='login_admin')
def add_customer(request):

    if request.method == 'POST':

        forms = vendor_customersForm(request.POST, request.FILES)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_vendor')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_customer.html', context)
    
    else:

        forms = vendor_customersForm()

        context = {
            'form': forms
        }
        return render(request, 'add_customer.html', context)

     
def add_customer_modal(request):
    if request.method == "POST":
        form = vendor_customersForm(request.POST)
        if form.is_valid():
            forms = form.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return JsonResponse({
                'success': True,
                'id': forms.id,
                'name': forms.name
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = vendor_customersForm()
    return render(request, 'partials/add_customer_modal_form.html', {'form': form})   

@login_required(login_url='login_admin')
def update_customer(request, customer_id):

    if request.method == 'POST':

        instance = vendor_customers.objects.get(id=customer_id)

        forms = vendor_customersForm(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_customer')
        else:
            print(forms.errors)
    
    else:

        instance = vendor_customers.objects.get(id=customer_id)
        forms = vendor_customersForm(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_customer.html', context)

        

@login_required(login_url='login_admin')
def delete_customer(request, vendor_id):

    vendor_customers.objects.get(id=vendor_id).delete()

    return HttpResponseRedirect(reverse('list_vendor'))


@login_required(login_url='login_admin')
def list_customer(request):
    
   
    data = vendor_customers.objects.filter(user = request.user)


    context = {
        'data': data
    }
    return render(request, 'list_customer.html', context)




# ---- Customer Ledger ----
class CustomerLedgerAPIView(APIView):
    def get(self, request, customer_id):
        from .models import vendor_customers
        from decimal import Decimal
        
        ledger_entries = CustomerLedger.objects.filter(customer_id=customer_id).order_by("created_at")

        # Get balance from customer model (updated by signals) or calculate from ledger
        try:
            customer = vendor_customers.objects.get(id=customer_id)
            balance = customer.balance or 0
        except vendor_customers.DoesNotExist:
            # Fallback: calculate from ledger entries
            balance = ledger_entries.aggregate(total=Sum("amount"))["total"] or 0
       
        # Convert balance to Decimal if it's not already
        if not isinstance(balance, Decimal):
            balance = Decimal(str(balance))
        
        # Add sale balance_amount to the balance

        serializer = CustomerLedgerSerializer(ledger_entries, many=True)
        return Response({
            "customer_id": customer_id,
            "balance": balance,
            "ledger": serializer.data
        })


# ---- Vendor Ledger ----
class VendorLedgerAPIView(APIView):
    def get(self, request, vendor_id):
        ledger_entries = VendorLedger.objects.filter(vendor_id=vendor_id).order_by("created_at")

        # Running balance
        balance = ledger_entries.aggregate(total=Sum("amount"))["total"] or 0

        serializer = VendorLedgerSerializer(ledger_entries, many=True)
        return Response({
            "vendor_id": vendor_id,
            "balance": balance,
            "ledger": serializer.data
        })
    

def bank_ledger(request, bank_id):
    bank = get_object_or_404(vendor_bank, id=bank_id)
    ledger_entries = bank.ledger_entries.order_by("created_at")

    ledger_total = ledger_entries.aggregate(total=Sum("amount"))["total"] or 0
    balance = (bank.opening_balance or 0) + ledger_total

    return render(request, "bank_ledger.html", {
        "bank": bank,
        "balance": balance,
        "ledger": ledger_entries,
    })


def customer_ledger(request, customer_id):
    from .models import vendor_customers
    
    ledger_entries = CustomerLedger.objects.filter(customer_id=customer_id).order_by("created_at")
    
    # Get balance from customer model (updated by signals) or calculate from ledger
    try:
        customer = vendor_customers.objects.get(id=customer_id)
        balance = customer.balance or 0
    except vendor_customers.DoesNotExist:
        # Fallback: calculate from ledger entries
        balance = ledger_entries.aggregate(total=Sum("amount"))["total"] or 0

    return render(request, "customer_ledger.html", {
        "customer_id": customer_id,
        "balance": balance,
        "ledger": ledger_entries,
    })


def vendor_ledger(request, vendor_id):
    ledger_entries = VendorLedger.objects.filter(vendor_id=vendor_id).order_by("created_at")
    balance = ledger_entries.aggregate(total=Sum("amount"))["total"] or 0

    return render(request, "vendor_ledger.html", {
        "vendor_id": vendor_id,
        "balance": balance,
        "ledger": ledger_entries,
    })

def cash_ledger(request):
    ledger_entries = CashLedger.objects.filter(user = request.user).order_by("created_at")
    balance = ledger_entries.aggregate(total=Sum("amount"))["total"] or 0

    return render(request, "cash_ledger.html", {
        "balance": balance,
        "ledger": ledger_entries,
    })



from rest_framework.response import Response


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

 
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import JSONParser



from django.views import View

from django.forms import inlineformset_factory


@login_required(login_url='login_admin')
def add_super_catalogue(request):

    if request.method == 'POST':

        forms = super_catalogue_Form(request.POST, request.FILES)

        if forms.is_valid():
            forms.save()
            return redirect('list_super_catalogue')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_super_catalogue.html', context)
    
    else:

        forms = super_catalogue_Form()

        context = {
            'form': forms
        }
        return render(request, 'add_super_catalogue.html', context)

        

@login_required(login_url='login_admin')
def add_to_super_catalogue(request, product_id):

    p = get_object_or_404(product, id=product_id)

    # Clone fields from product -> super_catalogue (1:1 as far as possible)
    clone_data = {
        "user": request.user,
        "parent": p.parent,  # keep variant grouping if needed
        "product_type": p.product_type,
        "sale_type": p.sale_type,
        "food_type": getattr(p, "food_type", None),

        "name": p.name,
        "category": p.category,
        "sub_category": getattr(p, "sub_category", None),

        # pricing
        "wholesale_price": p.wholesale_price,
        "purchase_price": p.purchase_price,
        "sales_price": p.sales_price,
        "mrp": p.mrp,

        # tax
        "gst": p.gst,
        "sgst_rate": p.sgst_rate,
        "cgst_rate": p.cgst_rate,

        # uom / hsn
        "unit": p.unit,
        "hsn": p.hsn,

        # stock
        "track_serial_numbers": p.track_serial_numbers,
        "opening_stock": p.opening_stock,
        "low_stock_alert": p.low_stock_alert,
        "low_stock_quantity": p.low_stock_quantity,
        "stock": p.stock,

        # optionals
        "brand_name": getattr(p, "brand_name", None),
        "color": getattr(p, "color", None),
        "size": getattr(p, "size", None),
        "batch_number": getattr(p, "batch_number", None),
        "expiry_date": getattr(p, "expiry_date", None),

        "description": p.description,
        "image": (p.image.url if getattr(p.image, "name", None) else None),
        "gallery_images": [
            (gi.image.url if getattr(gi.image, "name", None) else None)
            for gi in getattr(p, "gallery_images", []).all()
        ],

        # delivery/policies
        "is_customize": getattr(p, "is_customize", False),
        "instant_delivery": p.instant_delivery,
        "self_pickup": p.self_pickup,
        "general_delivery": p.general_delivery,
        "is_on_shop": getattr(p, "is_on_shop", False),

        "return_policy": p.return_policy,
        "cod": p.cod,
        "replacement": p.replacement,
        "shop_exchange": p.shop_exchange,
        "shop_warranty": p.shop_warranty,
        "brand_warranty": p.brand_warranty,

        # flags
        "is_food": getattr(p, "is_food", False),
        "tax_inclusive": getattr(p, "tax_inclusive", False),
        "is_popular": p.is_popular,
        "is_featured": p.is_featured,
        "is_active": p.is_active,
        "is_online": getattr(p, "is_online", False),
        "stock_cached": getattr(p, "stock_cached", 0),
    }

    # Filter to only fields that exist on current super_catalogue schema and coerce where needed
    model_fields = {f.name: f for f in super_catalogue._meta.get_fields() if getattr(f, "concrete", False) and not getattr(f, "many_to_many", False) and not getattr(f, "one_to_many", False)}

    # Coerce sub_category if it's a CharField on super_catalogue
    if "sub_category" in model_fields:
        from django.db.models import ForeignKey
        sc_field = model_fields["sub_category"]
        if not isinstance(sc_field, ForeignKey):
            clone_data["sub_category"] = getattr(getattr(p, "sub_category", None), "name", None)

    # Coerce size if it's a CharField on super_catalogue
    if "size" in model_fields:
        try:
            from django.db.models import ForeignKey as _FK
            is_fk = isinstance(model_fields["size"], _FK)
        except Exception:
            is_fk = False
        if not is_fk:
            clone_data["size"] = getattr(getattr(p, "size", None), "name", None)

    filtered = {k: v for k, v in clone_data.items() if k in model_fields}

    super_catalogue.objects.create(**filtered)

    return redirect('list_super_catalogue')

        

@login_required(login_url='login_admin')
def update_super_catalogue(request, super_catalogue_id):

    if request.method == 'POST':

        instance = super_catalogue.objects.get(id=super_catalogue_id)

        forms = super_catalogue_Form(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_super_catalogue')
        else:
            print(forms.errors)
    
    else:

        instance = super_catalogue.objects.get(id=super_catalogue_id)
        forms = super_catalogue_Form(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_super_catalogue.html', context)

        
        

@login_required(login_url='login_admin')
def delete_super_catalogue(request, super_catalogue_id):

    super_catalogue.objects.get(id=super_catalogue_id).delete()

    return HttpResponseRedirect(reverse('list_super_catalogue'))


@login_required(login_url='login_admin')
def list_super_catalogue(request):
    data = super_catalogue.objects.filter(is_active=True)
    context = {
        'data': data
    }
    return render(request, 'list_super_catalogue.html', context)




from django.db import transaction
from django.shortcuts import get_object_or_404

@login_required(login_url='login_admin')
@transaction.atomic
def add_product(request, parent_id=None):
    AddonFormSet = inlineformset_factory(
        product, product_addon,
        form=ProductAddonForm,
        extra=1,
        can_delete=True
    )
    VariantFormSet = inlineformset_factory(
        product, PrintVariant,
        form=PrintVariantForm,
        extra=1,
        can_delete=True
    )
    CustomizePrintVariantFormSet = inlineformset_factory(
        product, CustomizePrintVariant,
        form=CustomizePrintVariantForm,
        extra=1,
        can_delete=True
    )

    parent_instance = None
    if parent_id:
        parent_instance = get_object_or_404(product, id=parent_id)

    if request.method == 'POST':
        product_form = product_Form(request.POST, request.FILES)

        if product_form.is_valid():
            product_instance = product_form.save(commit=False)
            product_instance.user = request.user

            # 🔑 Assign parent automatically if parent_id passed
            if parent_instance:
                product_instance.parent = parent_instance

            product_instance.save()

            addon_formset = AddonFormSet(
                request.POST, request.FILES,
                instance=product_instance,
                prefix='addon',
                form_kwargs={'user': request.user}
            )
            variant_formset = VariantFormSet(
                request.POST, request.FILES,
                instance=product_instance,
                prefix='print_variants'
            )
            customize_variant_formset = CustomizePrintVariantFormSet(
                request.POST, request.FILES,
                instance=product_instance,
                prefix='customize_print_variants'
            )

            if addon_formset.is_valid() and variant_formset.is_valid() and customize_variant_formset.is_valid():
                addon_formset.save()
                variant_formset.save()
                customize_variant_formset.save()
                return redirect('list_product')
            else:
                # Debug errors
                print("Addon formset errors:", addon_formset.errors)
                print("Variant formset errors:", variant_formset.errors)
                print("Customize variant formset errors:", customize_variant_formset.errors)
        else:
            print("Product form errors:", product_form.errors)

            # keep formsets so template doesn’t break
            addon_formset = AddonFormSet(request.POST, request.FILES, prefix='addon', form_kwargs={'user': request.user})
            variant_formset = VariantFormSet(request.POST, request.FILES, prefix='print_variants')
            customize_variant_formset = CustomizePrintVariantFormSet(request.POST, request.FILES, prefix='customize_print_variants')

    else:
        product_form = product_Form()
        addon_formset = AddonFormSet(prefix='addon', form_kwargs={'user': request.user})
        variant_formset = VariantFormSet(prefix='print_variants')
        customize_variant_formset = CustomizePrintVariantFormSet(prefix='customize_print_variants')

    context = {
        'form': product_form,
        'formset': addon_formset,
        'variant_formset': variant_formset,
        'customize_print_variant_formset': customize_variant_formset,
        'parent_instance': parent_instance,  # useful for template if variant
    }
    return render(request, 'add_product.html', context)


@login_required(login_url='login_admin')
@transaction.atomic
def update_product(request, product_id):
    instance = get_object_or_404(product, id=product_id)

    AddonFormSet = inlineformset_factory(
        product, product_addon,
        form=ProductAddonForm,
        fields=['addon'],
        extra=1,
        can_delete=True
    )
    VariantFormSet = inlineformset_factory(
        product, PrintVariant,
        form=PrintVariantForm,
        extra=1,
        can_delete=True
    )
    CustomizePrintVariantFormSet = inlineformset_factory(
        product, CustomizePrintVariant,
        form=CustomizePrintVariantForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        product_form = product_Form(request.POST, request.FILES, instance=instance)

        addon_formset = AddonFormSet(request.POST, request.FILES, instance=instance, prefix='addon', form_kwargs={'user': request.user})
        variant_formset = VariantFormSet(request.POST, request.FILES, instance=instance, prefix='print_variants')
        customize_variant_formset = CustomizePrintVariantFormSet(request.POST, request.FILES, instance=instance, prefix='customize_print_variants')

        if product_form.is_valid() and addon_formset.is_valid() and variant_formset.is_valid() and customize_variant_formset.is_valid():
            product_instance = product_form.save(commit=False)
            product_instance.user = request.user
            product_instance.save()

            addon_formset.save()
            variant_formset.save()
            customize_variant_formset.save()

            return redirect('list_product')
        else:
            print("Product form errors:", product_form.errors)
            print("Addon formset errors:", addon_formset.errors)
            print("Variant formset errors:", variant_formset.errors)
            print("Customize variant formset errors:", customize_variant_formset.errors)

    else:
        product_form = product_Form(instance=instance)
        addon_formset = AddonFormSet(instance=instance, prefix='addon', form_kwargs={'user': request.user})
        variant_formset = VariantFormSet(instance=instance, prefix='print_variants')
        customize_variant_formset = CustomizePrintVariantFormSet(instance=instance, prefix='customize_print_variants')

    context = {
        'form': product_form,
        'formset': addon_formset,
        'variant_formset': variant_formset,
        'customize_print_variant_formset': customize_variant_formset,
        'instance': instance,
    }
    return render(request, 'add_product.html', context)


        

@login_required(login_url='login_admin')
def delete_product(request, product_id):

    product.objects.get(id=product_id).delete()

    return HttpResponseRedirect(reverse('list_product'))


@login_required(login_url='login_admin')
def list_product(request):

    if request.user.is_superuser:
        data = product.objects.all()
    
    else:
        data = product.objects.filter(user=request.user, is_active=True)
    context = {
        'data': data
    }
    return render(request, 'list_product.html', context)


@login_required(login_url='login_admin')
def list_stock(request):

    queryset = product.objects.filter(is_active=True, user=request.user)
    product_filter = productFilter(request.GET, queryset=queryset)
    products = product_filter.qs

    # To keep filter state in the template (e.g. highlight active button)
    current_filter = request.GET.get('sale_type', 'all')
    search_query = request.GET.get('search', '')

    return render(request, 'list_stock.html', {
        'data': products,
        'current_filter': current_filter,
        'search_query': search_query,
        'filter': product_filter,
    })


@login_required(login_url='login_admin')
def barcode_setting(request):

    settings, created = BarcodeSettings.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = BarcodeSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return redirect("barcode_setting")  # reload page
    else:
        form = BarcodeSettingsForm(instance=settings)

    return render(request, "barcode_settings.html", {"form": form})


from io import BytesIO
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.units import mm
from reportlab.lib import colors
from .models import product, CompanyProfile

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, KeepInFrame, PageBreak
)


from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.graphics.barcode import code128
from reportlab.lib.utils import ImageReader
from num2words import num2words
from datetime import datetime


def generate_barcode(request):
    # Example product details (replace these with DB data)

    if request.method == "POST":

        ids = request.POST.getlist("selected_products")
        products = product.objects.filter(id__in=ids, is_active=True)

        if not products.exists(): 
            return HttpResponse("No products selected", status=400) 
        try: 
            user_settings = BarcodeSettings.objects.get(user=request.user) 
        except BarcodeSettings.DoesNotExist: user_settings = None

        try: 
            company = CompanyProfile.objects.get(user=request.user) 
            company_name = company.company_name or "COMPANY NAME" 
        except CompanyProfile.DoesNotExist: 
            company_name = "COMPANY NAME"
        
       


        # Dynamically set layout size
        # if user_settings and user_settings.barcode_size == "50x100":
        #     PAGE_WIDTH = 100 * mm
        #     PAGE_HEIGHT = 50 * mm
        #     barcode_height = 18 * mm
        #     font_title = 10
        #     font_text = 8
        #     font_price = 9
        # else:
        #     PAGE_WIDTH = 50 * mm
        #     PAGE_HEIGHT = 25 * mm
        #     barcode_height = 10 * mm
        #     font_title = 7
        #     font_text = 5
        #     font_price = 6

        PAGE_WIDTH = 100 * mm
        PAGE_HEIGHT = 50 * mm
        barcode_height = 18 * mm
        font_title = 10
        font_text = 9
        font_price = 9

        # Create PDF

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

        for i in products:
            item_name = i.name
            mrp = i.mrp
            discount = i.wholesale_price
            sale_price = i.sales_price
            package_date = datetime.now().strftime("%d/%m/%Y")
            note = "The small note here"
            barcode_value = str("svindo" + i.id)

          
            # Margin padding
            x_margin = 2 * mm
            y_margin = 2 * mm

            # Draw rounded border
            p.setStrokeColor(colors.black)
            p.roundRect(x_margin, y_margin, PAGE_WIDTH - 2 * x_margin, PAGE_HEIGHT - 2 * y_margin, 3 * mm, stroke=1, fill=0)

            # Starting coordinates
            x_left = x_margin + 5
            y_top = PAGE_HEIGHT - y_margin - 8

           # === Company Name (Top Center) ===
            p.setFont("Helvetica-Bold", font_title + 2)
            p.drawCentredString(PAGE_WIDTH / 2, y_top - 4, company_name)

            # Add extra vertical gap below company name
            company_name_gap = 10  # ⬅️ increase this for more distance
            content_start_y = y_top - 4 - company_name_gap

            # === Left Side (Item / MRP / Discount) ===
            p.setFont("Helvetica-Bold", font_text)
            line_gap = 12  # spacing between each text line
            start_y = content_start_y - 10  # ⬅️ start content a bit below the heading

            # Item
            p.drawString(x_left, start_y, "Item:")
            p.setFont("Helvetica", font_text)
            p.drawString(x_left + 28, start_y, str(item_name))

            # MRP
            p.setFont("Helvetica-Bold", font_text)
            p.drawString(x_left, start_y - line_gap, "MRP:")
            p.setFont("Helvetica", font_text)
            p.drawString(x_left + 28, start_y - line_gap, f"{mrp:.2f}")

            # Discount
            p.setFont("Helvetica-Bold", font_text)
            p.drawString(x_left, start_y - 2 * line_gap, "Discount:")
            p.setFont("Helvetica", font_text)
            p.drawString(x_left + 45, start_y - 2 * line_gap, str(discount if discount else "None"))

            # === NOTE BOX (Anchored near bottom left) ===
            note_box_height = 12 * mm
            note_box_y = y_margin + 8 * mm  # padding from bottom
            p.setFont("Helvetica-Bold", font_text)
            p.drawString(x_left, note_box_y + 14 * mm, "Note:")  # was 12 * mm
            p.rect(x_left, note_box_y-2, 45 * mm, 12 * mm)
            p.setFont("Helvetica", font_text - 1)
            p.drawString(x_left + 5, note_box_y + note_box_height / 2 - 3, note)

            # === RIGHT SIDE (Package Date / Barcode / Sale Price / In Word) ===
            right_start_x = PAGE_WIDTH - (x_margin + 45 * mm)

            # Add this vertical offset to push everything down
            right_section_offset = 25  # ⬅️ increase this for more gap from the top
            right_top_y = y_top - right_section_offset

            # Package Date
            p.setFont("Helvetica", font_text)
            p.drawString(right_start_x, right_top_y, f"Package Date - {package_date}")

            # Barcode (centered nicely below package date)
            barcode_top_gap = 5 * mm  # vertical gap between date and barcode
            barcode = code128.Code128(barcode_value, barHeight=barcode_height, barWidth=0.6)

            barcode_x = PAGE_WIDTH - x_margin - 40 * mm
            barcode_y = right_top_y - barcode_top_gap - barcode_height
            barcode.drawOn(p, barcode_x, barcode_y)

            # Sale Price (pushed below barcode)
            price_gap = 10  # distance between barcode and Sale Price
            p.setFont("Helvetica-Bold", font_price)
            p.drawString(right_start_x, barcode_y - price_gap, f"Sale Price: {sale_price:.2f}")

            # In Word — right-aligned with the note box bottom
            p.setFont("Helvetica", font_text - 1)
            inword_text = f"In Word: {num2words(sale_price)}"
            text_width = p.stringWidth(inword_text, "Helvetica", font_text - 1)
            p.drawString(PAGE_WIDTH - x_margin - text_width - 5, note_box_y - 12, inword_text)
            # Finish up
            p.showPage()
        p.save()

        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')


    else:

        data = product.objects.filter(user=request.user, is_active=True)
        context = {
            'data': data
        }
        return render(request, 'list_product_barcode.html', context)

        



@login_required(login_url='login_admin')
def product_setting(request):


    settings, _ = ProductSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        checkbox_fields = [
            'wholesale_price', 'stock', 'imei', 'low_stock_alert', 'category', 'sub_category', 'brand_name', 'color', 'size',
            'batch_number', 'expiry_date', 'description', 'image', 'tax', 'food',
            'instant_delivery', 'self_pickup', 'general_delivery', 'shop_orders',
            'return_policy', 'cod', 'replacement', 'shop_exchange', 'shop_warranty', 'brand_warranty',
            'online_catalog_only'
        ]

        for field in checkbox_fields:
            setattr(settings, field, request.POST.get(field) == 'on')

        settings.save()
        return redirect('product_settings')  # Stay on the same page after saving

    return render(request, 'product_settings.html', {'settings': settings})



def product_defaults(request):


    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=401)

    try:
        settings = ProductSettings.objects.get(user=request.user)
        data = {
            "wholesale_price": settings.wholesale_price,
            "stock": settings.stock,
            "imei": settings.imei,
            "low_stock_alert": settings.low_stock_alert,
            "category": settings.category,
            "sub_category": settings.sub_category,
            "brand_name": settings.brand_name,
            "color": settings.color,
            "size": settings.size,
            "batch_number": settings.batch_number,
            "expiry_date": settings.expiry_date,
            "description": settings.description,
            "image": settings.image,
            "tax": settings.tax,
            "food": settings.food,
            "instant_delivery": settings.instant_delivery,
            "self_pickup": settings.self_pickup,
            "general_delivery": settings.general_delivery,
            "shop_orders": settings.shop_orders,
            "return_policy": settings.return_policy,
            "cod": settings.cod,
            "replacement": settings.replacement,
            "shop_exchange": settings.shop_exchange,
            "shop_warranty": settings.shop_warranty,
            "brand_warranty": settings.brand_warranty,
            "online_catalog_only": settings.online_catalog_only,
        }
        return JsonResponse({"success": True, "data": data})

    except ProductSettings.DoesNotExist:
        return JsonResponse({"success": False, "error": "No defaults found"})




class product_default(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            settings = ProductSettings.objects.get(user=request.user)
            data = {
                "wholesale_price": settings.wholesale_price,
                "stock": settings.stock,
                "imei": settings.imei,
                "low_stock_alert": settings.low_stock_alert,
                "category": settings.category,
                "sub_category": settings.sub_category,
                "brand_name": settings.brand_name,
                "color": settings.color,
                "size": settings.size,
                "batch_number": settings.batch_number,
                "expiry_date": settings.expiry_date,
                "description": settings.description,
                "image": settings.image.url if settings.image else None,
                "tax": settings.tax,
                "food": settings.food,
                "instant_delivery": settings.instant_delivery,
                "self_pickup": settings.self_pickup,
                "general_delivery": settings.general_delivery,
                "shop_orders": settings.shop_orders,
                "return_policy": settings.return_policy,
                "cod": settings.cod,
                "replacement": settings.replacement,
                "shop_exchange": settings.shop_exchange,
                "shop_warranty": settings.shop_warranty,
                "brand_warranty": settings.brand_warranty,
                "online_catalog_only": settings.online_catalog_only,
            }
            return Response({"success": True, "data": data})
        except ProductSettings.DoesNotExist:
            return Response({"success": False, "error": "No defaults found"}, status=404)



from django.http import JsonResponse


class get_product(ListAPIView):
    queryset = product.objects.filter(is_active=True)
    serializer_class = product_serializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'  # enables filtering on all fields
    filterset_class = productFilter  # enables filtering on all fields



@login_required(login_url='login_admin')
def add_addon(request):

    if request.method == 'POST':

        forms = addon_Form(request.POST, request.FILES)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_addon')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_addon.html', context)
    
    else:

        forms = addon_Form()

        context = {
            'form': forms
        }
        return render(request, 'add_addon.html', context)

        

@login_required(login_url='login_admin')
def update_addon(request, addon_id):

    if request.method == 'POST':

        instance = addon.objects.get(id=addon_id)

        forms = addon_Form(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_addon')
        else:
            print(forms.errors)
    
    else:

        instance = addon.objects.get(id=addon_id)
        forms = addon_Form(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_addon.html', context)

        

@login_required(login_url='login_admin')
def delete_addon(request, addon_id):

    addon.objects.get(id=addon_id).delete()

    return HttpResponseRedirect(reverse('list_addon'))


@login_required(login_url='login_admin')
def list_addon(request):

    data = addon.objects.filter(user = request.user)
    context = {
        'data': data
    }
    return render(request, 'list_addon.html', context)


class get_addon(ListAPIView):

    serializer_class = AddonSerializer

    def get_queryset(self):
        return addon.objects.filter(user=self.request.user)
    

@login_required(login_url='login_admin')
def add_payment(request):

    if request.method == 'POST':

        print(request.POST)

        forms = PaymentForm(request.POST, request.FILES)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_payment')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_payment.html', context)
    
    else:

        forms = PaymentForm()

        context = {
            'form': forms
        }
        return render(request, 'add_payment.html', context)

        

@login_required(login_url='login_admin')
def update_payment(request, payment_id):

    if request.method == 'POST':

        instance = Payment.objects.get(id=payment_id)

        forms = PaymentForm(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_payment')
        else:
            print(forms.errors)
    
    else:

        instance = Payment.objects.get(id=payment_id)
        forms = PaymentForm(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_payment.html', context)

        

@login_required(login_url='login_admin')
def delete_payment(request, payment_id):

    Payment.objects.get(id=payment_id).delete()

    return HttpResponseRedirect(reverse('list_payment'))


@login_required(login_url='login_admin')
def list_payment(request):

    data = Payment.objects.filter(user = request.user)
    context = {
        'data': data
    }
    return render(request, 'list_payment.html', context)





from rest_framework import status


from rest_framework import viewsets

from users.permissions import *

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .services.quickkyc import (
    verify_pan as kyc_verify_pan,
    verify_gstin as kyc_verify_gstin,
    verify_bank as kyc_verify_bank,
    verify_fssai as kyc_verify_fssai,
    QuickKYCError,
)
from .models import vendor_store


class VerifyPANAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        def _is_success(result: dict) -> bool:
            status_txt = str(result.get("status", "")).lower()
            code = result.get("status_code")
            return status_txt == "success" and str(code) == "200"

        pan = request.data.get("pan")
        name = request.data.get("name", "")
        if not pan:
            return Response({"detail": "pan is required"}, status=status.HTTP_400_BAD_REQUEST)

        store = vendor_store.objects.filter(user=request.user).first()
        if not store:
            return Response({"detail": "Vendor store not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            result = kyc_verify_pan(pan, name)
            success = _is_success(result)
            store.pan_number = pan
            store.is_pan_verified = success
            store.pan_verified_at = timezone.now() if success else None
            store.kyc_last_error = None if success else (result.get("message") or "PAN verification failed")
            store.save(update_fields=["pan_number", "is_pan_verified", "pan_verified_at", "kyc_last_error"])
            return Response({"verified": success, "result": result}, status=200 if success else 400)
        except QuickKYCError as e:
            store.kyc_last_error = str(e)
            store.is_pan_verified = False
            store.save(update_fields=["kyc_last_error", "is_pan_verified"])
            return Response({"verified": False, "error": str(e)}, status=502)


class VerifyGSTINAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        def _is_success(result: dict) -> bool:
            status_txt = str(result.get("status", "")).lower()
            code = result.get("status_code")
            return status_txt == "success" and str(code) == "200"

        gstin = request.data.get("gstin")
        if not gstin:
            return Response({"detail": "gstin is required"}, status=status.HTTP_400_BAD_REQUEST)

        store = vendor_store.objects.filter(user=request.user).first()
        if not store:
            return Response({"detail": "Vendor store not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            result = kyc_verify_gstin(gstin)
            success = _is_success(result)
            store.gstin = gstin
            store.is_gstin_verified = success
            store.gstin_verified_at = timezone.now() if success else None
            store.kyc_last_error = None if success else (result.get("message") or "GSTIN verification failed")
            store.save(update_fields=["gstin", "is_gstin_verified", "gstin_verified_at", "kyc_last_error"])
            return Response({"verified": success, "result": result}, status=200 if success else 400)
        except QuickKYCError as e:
            store.kyc_last_error = str(e)
            store.is_gstin_verified = False
            store.save(update_fields=["kyc_last_error", "is_gstin_verified"])
            return Response({"verified": False, "error": str(e)}, status=502)


class VerifyBankAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        def _is_success(result: dict) -> bool:
            status_txt = str(result.get("status", "")).lower()
            code = result.get("status_code")
            return status_txt == "success" and str(code) == "200"

        account_number = request.data.get("account_number")
        ifsc = request.data.get("ifsc")
        name = request.data.get("name", "")
        if not account_number or not ifsc:
            return Response({"detail": "account_number and ifsc are required"}, status=status.HTTP_400_BAD_REQUEST)

        store = vendor_store.objects.filter(user=request.user).first()
        if not store:
            return Response({"detail": "Vendor store not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            result = kyc_verify_bank(account_number, ifsc, name)
            success = _is_success(result)
            store.bank_account_number = account_number
            store.bank_ifsc = ifsc
            store.is_bank_verified = success
            store.bank_verified_at = timezone.now() if success else None
            store.kyc_last_error = None if success else (result.get("message") or "Bank verification failed")
            store.save(update_fields=[
                "bank_account_number", "bank_ifsc",
                "is_bank_verified", "bank_verified_at", "kyc_last_error"
            ])
            return Response({"verified": success, "result": result}, status=200 if success else 400)
        except QuickKYCError as e:
            store.kyc_last_error = str(e)
            store.is_bank_verified = False
            store.save(update_fields=["kyc_last_error", "is_bank_verified"])
            return Response({"verified": False, "error": str(e)}, status=502)


class VerifyFSSAIAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        def _is_success(result: dict) -> bool:
            status_txt = str(result.get("status", "")).lower()
            code = result.get("status_code")
            return status_txt == "success" and str(code) == "200"

        fssai = request.data.get("fssai")
        if not fssai:
            return Response({"detail": "fssai is required"}, status=status.HTTP_400_BAD_REQUEST)

        store = vendor_store.objects.filter(user=request.user).first()
        if not store:
            return Response({"detail": "Vendor store not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            result = kyc_verify_fssai(fssai)
            success = _is_success(result)
            store.fssai_number = fssai
            store.is_fssai_verified = success
            store.fssai_verified_at = timezone.now() if success else None
            store.kyc_last_error = None if success else (result.get("message") or "FSSAI verification failed")
            store.save(update_fields=["fssai_number", "is_fssai_verified", "fssai_verified_at", "kyc_last_error"])
            return Response({"verified": success, "result": result}, status=200 if success else 400)
        except QuickKYCError as e:
            store.kyc_last_error = str(e)
            store.is_fssai_verified = False
            store.save(update_fields=["kyc_last_error", "is_fssai_verified"])
            return Response({"verified": False, "error": str(e)}, status=502)


class OnlineStoreSettingViewSet(viewsets.ModelViewSet):
    
    permission_classes = [IsAuthenticated]

    def list(self, request):
        setting, _ = OnlineStoreSetting.objects.get_or_create(user=request.user)
        serializer = OnlineStoreSettingSerializer(setting)
        return Response(serializer.data)

    def create(self, request):
        setting, _ = OnlineStoreSetting.objects.get_or_create(user=request.user)
        serializer = OnlineStoreSettingSerializer(setting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def update(self, request, pk=None):
        try:
            setting = OnlineStoreSetting.objects.get(user=request.user)
        except OnlineStoreSetting.DoesNotExist:
            return Response({'detail': 'Setting not found'}, status=404)

        serializer = OnlineStoreSettingSerializer(setting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)





class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = product_serializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return product.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class SuperCatalogueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List/read super catalogue products (public).
    GET /vendor/super-catalogue/?category=&sub_category=&sale_type=
    """
    serializer_class = SuperCatalogueSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super_catalogue.objects.filter(is_active=True).order_by("-created_at")
        category_id = self.request.query_params.get("category")
        sub_category_id = self.request.query_params.get("sub_category")
        sale_type = self.request.query_params.get("sale_type")
        if category_id:
            qs = qs.filter(category_id=category_id)
        if sub_category_id:
            qs = qs.filter(sub_category_id=sub_category_id)
        if sale_type:
            qs = qs.filter(sale_type=sale_type)
        return qs


from rest_framework.decorators import action

class ProductSettingsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsVendor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def retrieve(self, request, *args, **kwargs):
        settings, _ = ProductSettings.objects.get_or_create(user=request.user)
        serializer = ProductSettingsSerializer(settings)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        return self.retrieve(request)  # Same as retrieve for one-to-one

    @action(detail=False, methods=['post'], url_path='update')
    def update_settings(self, request):
        settings, _ = ProductSettings.objects.get_or_create(user=request.user)
        serializer = ProductSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductAddonViewSet(viewsets.ModelViewSet):
    queryset = product_addon.objects.all()
    serializer_class = ProductAddonSerializer


class AddonViewSet(viewsets.ModelViewSet):
    
    queryset = addon.objects.all()
    serializer_class = AddonSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser] 

    def get_queryset(self):
        # Return only products of logged-in user
        return addon.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign logged-in user to the product
        serializer.save(user=self.request.user)

class SpotlightProductViewSet(viewsets.ModelViewSet):
    queryset = SpotlightProduct.objects.all()
    serializer_class = SpotlightProductSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        # Return only products of logged-in user
        return SpotlightProduct.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign logged-in user to the product
        serializer.save(user=self.request.user)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        # Return only products of logged-in user
        return Post.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign logged-in user to the product
        serializer.save(user=self.request.user)


class ReelViewSet(viewsets.ModelViewSet):
    queryset = Reel.objects.all()
    serializer_class = ReelSerializer
    permission_classes = [IsVendor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Enable file uploads

    def get_queryset(self):
        # Return only products of logged-in user
        return Reel.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign logged-in user to the product
        serializer.save(user=self.request.user)


from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

class CouponViewSet(viewsets.ModelViewSet):
    queryset = coupon.objects.all()
    serializer_class = coupon_serializer
    permission_classes = [IsVendor]
    parser_classes = [MultiPartParser, FormParser, JSONParser] 

    def get_queryset(self):
        # Return only products of logged-in user
        return coupon.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign logged-in user to the product
        serializer.save(user=self.request.user)


class CompanyProfileViewSet(viewsets.ModelViewSet):
    queryset = CompanyProfile.objects.all()
    serializer_class = CompanyProfileSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        # Return only company profile of logged-in user
        return CompanyProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Check if profile already exists
        if CompanyProfile.objects.filter(user=self.request.user).exists():
            raise ValidationError({"detail": "Company profile already exists for this user."})
        company_profile = serializer.save(user=self.request.user)
        
        # Update vendor_store profile_image and name if they don't have values
        try:
            store = vendor_store.objects.get(user=self.request.user)
            update_fields = []
            
            # Update profile_image if company has it and store doesn't
            if company_profile.profile_image and not store.profile_image:
                store.profile_image = company_profile.profile_image
                update_fields.append('profile_image')
            
            # Update store name from brand_name if store doesn't have a name
            if company_profile.brand_name and not store.name:
                store.name = company_profile.brand_name
                update_fields.append('name')
            
            # Save only if there are fields to update
            if update_fields:
                store.save(update_fields=update_fields)
        except vendor_store.DoesNotExist:
            pass  # Vendor store doesn't exist yet, skip


class DeliveryDiscountViewSet(viewsets.ModelViewSet):
    queryset = DeliveryDiscount.objects.all()
    serializer_class = DeliveryDiscountSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        # Return only delivery discount of logged-in user
        return DeliveryDiscount.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Use get_or_create since there's only one delivery discount per vendor
        delivery_discount, created = DeliveryDiscount.objects.get_or_create(
            user=self.request.user,
            defaults=serializer.validated_data
        )
        if not created:
            # If it already exists, update it with new data
            for key, value in serializer.validated_data.items():
                setattr(delivery_discount, key, value)
            delivery_discount.save()
        # Update serializer instance to return the created/updated object
        serializer.instance = delivery_discount

    def perform_update(self, serializer):
        # Ensure user can only update their own delivery discount
        serializer.save(user=self.request.user)


class AutomateNotificationOnOrderViewSet(viewsets.ModelViewSet):
    queryset = AutomateNotificationOnOrder.objects.all()
    serializer_class = AutomateNotificationOnOrderSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        # Return only automate notification settings of logged-in user
        return AutomateNotificationOnOrder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Use get_or_create since there's only one automate notification setting per vendor
        automate_notification, created = AutomateNotificationOnOrder.objects.get_or_create(
            user=self.request.user,
            defaults=serializer.validated_data
        )
        if not created:
            # If it already exists, update it with new data
            for key, value in serializer.validated_data.items():
                setattr(automate_notification, key, value)
            automate_notification.save()
        # Update serializer instance to return the created/updated object
        serializer.instance = automate_notification

    def perform_update(self, serializer):
        # Ensure user can only update their own automate notification settings
        serializer.save(user=self.request.user)


class customerViewSet(viewsets.ModelViewSet):
    queryset = vendor_customers.objects.all()
    serializer_class = vendor_customers_serializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        # Return only products of logged-in user
        return vendor_customers.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign logged-in user to the product
        serializer.save(user=self.request.user)



class vendorViewSet(viewsets.ModelViewSet):
    queryset = vendor_vendors.objects.all()
    serializer_class = vendor_vendors_serializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        # Return only products of logged-in user
        return vendor_vendors.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign logged-in user to the product
        serializer.save(user=self.request.user)



class bankViewSet(viewsets.ModelViewSet):
    queryset = vendor_bank.objects.all()
    serializer_class = vendor_bank_serializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        # Return only products of logged-in user
        return vendor_bank.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign logged-in user to the product
        serializer.save(user=self.request.user)



class PurchaseViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def partial_update(self, request, *args, **kwargs):
        """Custom partial update method for Purchase"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Update the purchase
            self.perform_update(serializer)
            
            # Handle purchase items if provided
            if 'items' in request.data:
                # Delete existing items
                PurchaseItem.objects.filter(purchase=instance).delete()
                
                # Create new items
                from decimal import Decimal
                for item_data in request.data['items']:
                    quantity = item_data.get('quantity', 1)
                    price = item_data.get('price', 0)
                    PurchaseItem.objects.create(
                        purchase=instance,
                        product_id=item_data['product'],
                        quantity=quantity,
                        price=price,
                        total=Decimal(str(quantity)) * Decimal(str(price)),
                    )
                
                # Calculate and save total_amount from all items
                instance.calculate_total()
                
                # Refresh instance to get updated total_amount in response
                instance.refresh_from_db()
        
        return Response(serializer.data)




class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def partial_update(self, request, *args, **kwargs):
        """Custom partial update method for Expense"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Update the expense
        self.perform_update(serializer)
        
        return Response(serializer.data)


def generate_unique_code(self):
    prefix = "PUR-"
    last_purchase = Purchase.objects.filter(purchase_code__startswith=prefix).order_by('purchase_code').last()
    if not last_purchase:
        new_number = 1
    else:
        # Extract the numeric part after prefix and convert to int
        last_number = int(last_purchase.purchase_code.replace(prefix, ''))
        new_number = last_number + 1

    # Format with leading zeros, e.g. PUR-00001
    return f"{prefix}{new_number:05d}"



@login_required(login_url='login_admin')
def add_purchase(request):

    data = product.objects.filter(is_active=True, user=request.user)

    if request.method == 'POST':

        
        forms = PurchaseForm(request.POST)
        if forms.is_valid():

            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            
            product_ids = request.POST.getlist('products')
            quantity_ids = request.POST.getlist('quantity')
            price_ids = request.POST.getlist('price')
            total_price_ids = request.POST.getlist('total_price')

            for product_id, qty, price, total in zip(product_ids, quantity_ids, price_ids, total_price_ids):
                if product_id:  # make sure it's not empty
                    PurchaseItem.objects.create(
                        purchase=forms,
                        product_id=int(product_id),
                        quantity=int(qty) if qty else 0,
                        price=float(price) if price else 0.0,
                        total=float(total) if total else 0.0
                    )

            return redirect('list_purchase')  # or your desired URL
   
        else:
            print(forms.errors)

            context = {
                'form': forms,
                'data': data,
            }
            return render(request, 'add_purchase.html', context)
    
    else:


        forms = PurchaseForm(user=request.user)

        context = {
            'form': forms,
            "banks" : vendor_bank.objects.all(),

            'data': data,
        }
        return render(request, 'add_purchase.html', context)

        

@login_required(login_url='login_admin')
def update_purchase(request, purchase_id):
    data = product.objects.filter(is_active=True, user=request.user)
    instance = Purchase.objects.get(id=purchase_id)

    if request.method == 'POST':
        form = PurchaseForm(request.POST, request.FILES, instance=instance, user=request.user)

        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.user = request.user  # Ensure user is set
            # Do NOT touch purchase_code
            purchase.save()

            # Get product items from POST
            product_ids = request.POST.getlist('products')
            quantities = request.POST.getlist('quantity')
            prices = request.POST.getlist('price')
            totals = request.POST.getlist('total_price')

            # Delete old items
            instance.items.all().delete()

            # Add new items
            for pid, qty, price, total in zip(product_ids, quantities, prices, totals):
                if pid:
                    PurchaseItem.objects.create(
                        purchase=instance,
                        product_id=int(pid),
                        quantity=int(qty) if qty else 0,
                        price=float(price) if price else 0.0,
                        total=float(total) if total else 0.0
                    )

            return redirect('list_purchase')
        else:
            print(form.errors)
    else:
        form = PurchaseForm(instance=instance, user=request.user)

    existing_product_ids = list(instance.items.values_list('product_id', flat=True))

    context = {
        'form': form,
        'existing_product_ids': existing_product_ids,
        'data': data,
    }
    return render(request, 'add_purchase.html', context)




        

@login_required(login_url='login_admin')
def delete_purchase(request, purchase_id):

    Purchase.objects.get(id=purchase_id).delete()

    return HttpResponseRedirect(reverse('list_purchase'))


@login_required(login_url='login_admin')
def list_purchase(request):

    data = Purchase.objects.filter(user = request.user).order_by('-id')
    context = {
        'data': data
    }
    return render(request, 'list_purchase.html', context)


class NextPurchaseNumberAPI(APIView):

    permission_classes = [IsAuthenticated]


    def get(self, request):
        from vendor.utils import generate_serial_number
        from django.utils import timezone
        
        user = request.user

        new_code = generate_serial_number(
            prefix='PUR',
            model_class=Purchase,
            date=timezone.now().date(),
            user=user
        )

        return Response({"purchase_number": new_code})




@login_required(login_url='login_admin')
def add_expense(request):

    if request.method == 'POST':

        forms = ExpenseForm(request.POST, request.FILES)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_expense')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_expense.html', context)
    
    else:

        forms = ExpenseForm()

        context = {
            'form': forms,
            "banks" : vendor_bank.objects.all(),

        }
        return render(request, 'add_expense.html', context)

        

@login_required(login_url='login_admin')
def update_expense(request, expense_id):

    if request.method == 'POST':

        instance = Expense.objects.get(id=expense_id)

        forms = ExpenseForm(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_expense')
        else:
            print(forms.errors)
    
    else:

        instance = Expense.objects.get(id=expense_id)
        forms = ExpenseForm(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_expense.html', context)

        

@login_required(login_url='login_admin')
def delete_expense(request, expense_id):

    Expense.objects.get(id=expense_id).delete()

    return HttpResponseRedirect(reverse('list_expense'))


@login_required(login_url='login_admin')
def list_expense(request):

    data = Expense.objects.filter(user = request.user).order_by('-id')
    context = {
        'data': data
    }
    return render(request, 'list_expense.html', context)



from django.forms import modelformset_factory

StoreWorkingHourFormSet = modelformset_factory(
    StoreWorkingHour,
    form=StoreWorkingHourForm,
    extra=0  # We don't want to add blank extra rows
)


def store_hours_view(request):
    
    # Days of the week
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    if request.method == "POST":
        print(request.POST)

        for day in days:
            
            open_time_str = request.POST.get(f"{day.lower()}_open")
            close_time_str = request.POST.get(f"{day.lower()}_close")
            is_open = request.POST.get(f"{day.lower()}_is_open") == "on"

            # Convert to time objects (if not empty)
            open_time = datetime.strptime(open_time_str, "%H:%M").time() if open_time_str else None
            close_time = datetime.strptime(close_time_str, "%H:%M").time() if close_time_str else None

            obj, created = StoreWorkingHour.objects.get_or_create(user=request.user, day=day)

            if created:
                obj.day = day

            obj.open_time = open_time
            obj.close_time = close_time
            obj.is_open = is_open
            obj.save()

            print(open_time)
            print(close_time)
            print(is_open)

        return redirect("store_hours")  # make sure this name matches your urlpattern

    # Load existing hours into a dict
    hours_qs = StoreWorkingHour.objects.filter(user=request.user)
    hours = {hour.day: hour for hour in hours_qs}

    return render(request, "store_hours.html", {
        "days": days,
        "hours": hours
    })



class PartyViewSet(viewsets.ModelViewSet):
    serializer_class = PartySerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return Party.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return Sale.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def partial_update(self, request, *args, **kwargs):
        """Custom partial update method for Sale"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Update the sale
            self.perform_update(serializer)
            
            # Handle sale items if provided
            if 'items' in request.data:
                # Delete existing items
                SaleItem.objects.filter(sale=instance).delete()
                
                # Create new items
                for item_data in request.data['items']:
                    SaleItem.objects.create(
                        user=request.user,
                        sale=instance,
                        product_id=item_data['product'],
                        quantity=item_data['quantity'],
                        price=item_data['price'],
                    )
        
        return Response(serializer.data)


from django.db import transaction

from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from .models import Sale, SaleItem, Party, product  # Adjust as per your app structure


from rest_framework.authentication import TokenAuthentication

class NextInvoiceNumberAPI(APIView):

    permission_classes = [IsAuthenticated]


    def get(self, request):
        from vendor.utils import generate_serial_number
        from django.utils import timezone
        
        invoice_type = request.GET.get('invoice_type')
        user = request.user

        type_prefix_map = {
            'invoice': 'SAL',
            'sales_return': 'SRN',
            'sales_order': 'SOR',
            'proforma': 'PFI',
            'quotation': 'QTN',
            'delivery_challan': 'DC',
            'credit_note': 'CRN',
            'debit_note': 'DBN',
            'e_invoice': 'EIN',
        }

        prefix = type_prefix_map.get(invoice_type, 'SAL')

        invoice_number = generate_serial_number(
            prefix=prefix,
            model_class=pos_wholesale,
            date=None,
            user=user,
            filter_kwargs={'invoice_type': invoice_type}
        )
        return Response({"invoice_number": invoice_number})




def get_next_invoice_number_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    from vendor.utils import generate_serial_number
    
    invoice_type = request.GET.get('invoice_type')
    user = request.user

    type_prefix_map = {
        'invoice': 'SAL',
        'sales_return': 'SRN',
        'sales_order': 'SOR',
        'proforma': 'PFI',
        'quotation': 'QTN',
        'delivery_challan': 'DC',
        'credit_note': 'CRN',
        'debit_note': 'DBN',
        'e_invoice': 'EIN',
    }

    prefix = type_prefix_map.get(invoice_type, 'SAL')

    invoice_number = generate_serial_number(
        prefix=prefix,
        model_class=pos_wholesale,
        date=None,
        user=user,
        filter_kwargs={'invoice_type': invoice_type}
    )
    return JsonResponse({"invoice_number": invoice_number})




@login_required
def pos(request):

    sale_form = SaleForm()
    customer_form = vendor_customersForm()
    wholesale_form = pos_wholesaleForm()

    # Pre-fill default company_profile for GET (and as initial on form)
    try:
        default_cp = CompanyProfile.objects.filter(user=request.user).first()
    except Exception:
        default_cp = None
    try:
        if default_cp and "company_profile" in sale_form.fields:
            sale_form.fields["company_profile"].initial = default_cp
    except Exception:
        pass

    if request.method == 'POST':
        print(request.POST)
        sale_form = SaleForm(request.POST)
        customer_form = vendor_customersForm(request.POST)  # if needed
        wholesale_form = pos_wholesaleForm(request.POST, request.FILES)

        products = request.POST.getlist("product")
        quantities = request.POST.getlist("quantity")
        prices = request.POST.getlist("price")

        if not sale_form.is_valid() or not wholesale_form.is_valid():
            # return immediately with form errors before saving anything
            print(sale_form.errors)
            print(wholesale_form.errors)
            context = {
                "form": sale_form,
                "customer_forms": customer_form,
                "wholesale_forms": wholesale_form,
                "saleitemform": SaleItemForm(),
                "products": product.objects.filter(user=request.user, is_active=True),
            }
            return render(request, "pos_form.html", context)

        with transaction.atomic():
            try:
                # Save sale
                sale_instance = sale_form.save(commit=False)
                sale_instance.user = request.user
                # Fallback: set default company_profile if not submitted
                if not getattr(sale_instance, "company_profile_id", None):
                    if default_cp:
                        sale_instance.company_profile = default_cp
                sale_instance.save()

                # Process Sale Items
                total_items = 0
                total_amount = Decimal("0.00")

                for p, q, pr in zip(products, quantities, prices):
                    if p and q and pr:
                        qty = int(q)
                        price = Decimal(pr)
                        amount = qty * price

                        SaleItem.objects.create(
                            user=request.user,
                            sale=sale_instance,
                            product_id=p,
                            quantity=qty,
                            price=price,
                        )

                        total_items += qty
                        total_amount += amount

                # Save wholesale
                invoice = wholesale_form.save(commit=False)
                invoice.user = request.user
                invoice.sale = sale_instance
                invoice.save()


                return redirect("sale_bill_details", sale_id=sale_instance.id)

            except Exception as e:
                # Catch-all for any errors in atomic block
                transaction.set_rollback(True)
                context = {
                    "form": sale_form,
                    "customer_forms": customer_form,
                    "wholesale_forms": wholesale_form,
                    "saleitemform": SaleItemForm(),
                    "products": product.objects.filter(user=request.user, is_active=True),
                    "error_message": str(e),
                }
                return render(request, "pos_form.html", context)

    return render(request, "pos_form.html", {
        "form": sale_form,
        "banks" : vendor_bank.objects.all(),
        "customer_forms": customer_form,
        "wholesale_forms": wholesale_form,
        "saleitemform": SaleItemForm(),
        "products": product.objects.filter(user=request.user, is_active=True),
    })



    
def update_sale(request, sale_id):

    sale_instance = get_object_or_404(Sale, id=sale_id, user=request.user)
    existing_items = SaleItem.objects.filter(sale=sale_instance)

    # Default company profile to use if missing
    try:
        default_cp = CompanyProfile.objects.filter(user=request.user).first()
    except Exception:
        default_cp = None

    # ✅ Prepare dict list with amount calculation
    items_with_amount = []
    for item in existing_items:
        items_with_amount.append({
            "id": item.id,
            "product": item.product,
            "quantity": item.quantity,
            "price": item.price,
            "amount": item.quantity * item.price,
        })

    if request.method == "POST":
        sale_form = SaleForm(request.POST, instance=sale_instance)
        customer_form = vendor_customersForm(request.POST)
        wholesale_instance = getattr(sale_instance, 'pos_wholesale', None)
        wholesale_form = pos_wholesaleForm(request.POST, request.FILES, instance=wholesale_instance)

        products = request.POST.getlist("product[]")
        quantities = request.POST.getlist("quantity[]")
        prices = request.POST.getlist("price[]")
        existing_item_ids = request.POST.getlist("existing_item_ids[]")
        delete_item_ids = request.POST.getlist("delete_item_ids[]")

        if not sale_form.is_valid() or not wholesale_form.is_valid():
            context = {
                "form": sale_form,
                "customer_forms": customer_form,
                "wholesale_forms": wholesale_form,
                "saleitemform": SaleItemForm(),
                "products": product.objects.filter(user=request.user, is_active=True),
                "existing_items": items_with_amount,  # ✅ Use calculated data
                "error_message": "Please correct the errors below.",
            }
            return render(request, "pos_form.html", context)

        with transaction.atomic():
            try:
                sale_instance = sale_form.save(commit=False)
                sale_instance.user = request.user
                # Fallback: set default company_profile when not provided in update
                if not getattr(sale_instance, "company_profile_id", None) and default_cp:
                    sale_instance.company_profile = default_cp
                sale_instance.save()

                # 1. Delete marked items
                if delete_item_ids:
                    SaleItem.objects.filter(id__in=delete_item_ids, sale=sale_instance).delete()

                total_items = 0
                total_amount = Decimal("0.00")

                # 2. Iterate through rows
                for idx, (p, q, pr) in enumerate(zip(products, quantities, prices)):
                    if not (p and q and pr):
                        continue

                    qty = int(q)
                    price = Decimal(pr)
                    amount = qty * price

                    if idx < len(existing_item_ids) and existing_item_ids[idx] and existing_item_ids[idx] not in delete_item_ids:
                        # Update existing
                        SaleItem.objects.filter(id=existing_item_ids[idx], sale=sale_instance).update(
                            product_id=p,
                            quantity=qty,
                            price=price
                        )
                    else:
                        # Create new
                        SaleItem.objects.create(
                            user=request.user,
                            sale=sale_instance,
                            product_id=p,
                            quantity=qty,
                            price=price,
                        )

                    total_items += qty
                    total_amount += amount

                # 3. Save wholesale
                invoice = wholesale_form.save(commit=False)
                invoice.user = request.user
                invoice.sale = sale_instance
                invoice.save()

                return redirect("sale_bill_details", sale_id=sale_instance.id)

            except Exception as e:
                print("IntegrityError:", e)  # Will show exact DB constraint error
                messages.error(request, f"Error: {e}")
                transaction.set_rollback(True)
                context = {
                    "form": sale_form,
                    "customer_forms": customer_form,
                    "wholesale_forms": wholesale_form,
                    "saleitemform": SaleItemForm(),
                    "products": product.objects.filter(user=request.user, is_active=True),
                    "existing_items": items_with_amount,  # ✅ Keep calculated
                    "error_message": str(e),
                }
                return render(request, "pos_form.html", context)

    else:
        sale_form = SaleForm(instance=sale_instance)
        customer_form = vendor_customersForm()
        wholesale_instance = getattr(sale_instance, 'pos_wholesale', None)
        wholesale_form = pos_wholesaleForm(instance=wholesale_instance)
        # Pre-fill initial if sale has no company_profile already
        try:
            if default_cp and "company_profile" in sale_form.fields and not getattr(sale_instance, "company_profile_id", None):
                sale_form.fields["company_profile"].initial = default_cp
        except Exception:
            pass

        context = {
            "form": sale_form,
            "customer_forms": customer_form,
            "wholesale_forms": wholesale_form,
            "saleitemform": SaleItemForm(),
            "products": product.objects.filter(user=request.user),
            "existing_items": items_with_amount,  # ✅ Use calculated
        }
        return render(request, "pos_form.html", context)
    




def delete_sale(request, sale_id):
    sale = Sale.objects.get(id = sale_id).delete()

    return redirect('list_sale')

def sale_bill_details(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    wholesale = pos_wholesale.objects.filter(sale=sale, user= request.user).first()  # get wholesale data if exists

    context = {
        'sale': sale,
        'wholesale': wholesale,
    }
    return render(request, 'sale_bill_details.html', context)


from django.db.models import Prefetch

def list_sale(request):

    data = Sale.objects.prefetch_related(
        'items__product',
        Prefetch('wholesales', queryset=pos_wholesale.objects.all())
    ).filter(user = request.user).order_by('-id')

    context = {
        'data': data
    }
    return render(request, 'list_sale.html', context)

    
        



from django.views.decorators.http import require_GET

@require_GET
def get_product_price(request):
    product_id = request.GET.get('product_id')
    try:
        product_instance = product.objects.get(id=product_id)
        return JsonResponse({'price': str(product_instance.purchase_price)})
    except product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    



from num2words import num2words  # make sure you installed: pip install num2words
import math

def sale_invoice(request, sale_id):
    
    sale = (
        Sale.objects
        .prefetch_related('items__product')
        .select_related('customer', 'company_profile')
        .get(id=sale_id)
    )
    wholesale = sale.wholesales.first()

    # --- Safety checks ---
    if not wholesale:
        return HttpResponse("No wholesale details found for this sale.", status=400)

    sale_type = wholesale.invoice_type.lower().replace(" ", "_")  # normalize e.g. "Retail Sale" -> "retail_sale"
    is_registered = bool(sale.company_profile and sale.company_profile.gstin)

    # Determine store GST type (CGST if vendor/customer state matches else IGST)
    vendor_state_name = None
    if getattr(sale, "company_profile", None) and getattr(sale.company_profile, "state", None):
        vendor_state_name = sale.company_profile.state.name
    customer_state_name = getattr(sale.customer, "billing_state", None) or getattr(sale.customer, "dispatch_state", None)
    same_state = False
    if vendor_state_name and customer_state_name:
        same_state = vendor_state_name.strip().lower() == str(customer_state_name).strip().lower()
    store_gst = "cgst" if same_state else "igst"

    # --- Template path decision across types ---
    template_map = {
        "proforma": {
            "igst": "sale_invoice/igst_proforma.html",
            "cgst": "sale_invoice/cgst_proforma.html",
        },
        "invoice": {
            "igst": "sale_invoice/igst_invoice.html",
            "cgst": "sale_invoice/cgst_tax_invoice.html",
        },
        "quotation": {
            "igst": "sale_invoice/igst_quotation.html",
            "cgst": "sale_invoice/cgst_quotation.html",
        },
        "delivery_challan": {
            "igst": "sale_invoice/igst_delivery_challan.html",
            "cgst": "sale_invoice/cgst_delivery_challan.html",
        },
    }
    template_name = template_map.get(sale_type, {}).get(store_gst)
    if not template_name:
        # Fallback
        template_name = "sale_invoice/online_invoice.html"

    # --- Charges and totals ---
    delivery = wholesale.delivery_charges or 0
    packaging = wholesale.packaging_charges or 0
    total_amount = sale.total_amount + delivery + packaging

    rounded_total = round(total_amount)
    round_off_value = round(rounded_total - total_amount, 2)

    # --- HSN Summary ---
    hsn_summary = {}
    total_tax = 0
    total_taxable = 0
    total_quantity = 0
    total_sgst = 0
    total_cgst = 0
    total_igst = 0
    items_with_tax = []
    for item in sale.items.all():
        if not item.product:
            # Skip items without a product
            continue
            
        hsn = getattr(item.product, "hsn", None) or "N/A"
        sgst_rate = getattr(item.product, "sgst_rate", None) or 9
        cgst_rate = getattr(item.product, "cgst_rate", None) or 9
        taxable_val = float(item.amount)

        if hsn not in hsn_summary:
            hsn_summary[hsn] = {
                'taxable_value': 0,
                'sgst_rate': sgst_rate,
                'cgst_rate': cgst_rate,
            }
        hsn_summary[hsn]['taxable_value'] += taxable_val
        total_tax += item.tax_amount
        total_taxable += float(item.amount)
        total_quantity += int(item.quantity or 0)

        # tax splits
        sgst_amt = round(taxable_val * float(sgst_rate) / 100, 2)
        cgst_amt = round(taxable_val * float(cgst_rate) / 100, 2)
        total_sgst += sgst_amt
        total_cgst += cgst_amt
        total_igst += float(item.tax_amount or 0)

        items_with_tax.append({
            "name": getattr(item.product, "name", "N/A"),
            "hsn": getattr(item.product, "hsn", None) or "N/A",
            "price": float(item.price),
            "quantity": int(item.quantity),
            "taxable_value": taxable_val,
            "sgst_percent": float(sgst_rate or 0),
            "cgst_percent": float(cgst_rate or 0),
            "sgst_amount": sgst_amt,
            "cgst_amount": cgst_amt,
            "igst_percent": float(getattr(item.product, "gst", 0) or 0),
            "igst_amount": float(item.tax_amount or 0),
            "total_with_tax": float(item.total_with_tax),
        })

    for hsn, data in hsn_summary.items():
        data['sgst_amount'] = round(data['taxable_value'] * data['sgst_rate'] / 100, 2)
        data['cgst_amount'] = round(data['taxable_value'] * data['cgst_rate'] / 100, 2)
        data['total_tax'] = data['sgst_amount'] + data['cgst_amount']
        # Helpful for IGST proforma
        data['igst_rate'] = round((data['sgst_rate'] or 0) + (data['cgst_rate'] or 0), 2)
        data['igst_amount'] = round(data['total_tax'], 2)

    total_in_words = num2words(rounded_total, to='currency', lang='en_IN').title()

    paid_amount = float(sale.advance_amount or 0)
    balance_amount = round(rounded_total - paid_amount, 2)

    context = {
        'sale_instance': sale,
        'wholesale': wholesale,
        'total_amount': total_amount,
        'rounded_total': rounded_total,
        'round_off_value': round_off_value,
        'hsn_summary': hsn_summary.items(),
        'total_in_words': total_in_words,
        'total_tax': total_tax,
        'store_gst': store_gst,
        'sum_taxable': round(total_taxable, 2),
        'sum_sgst': round(total_sgst, 2),
        'sum_cgst': round(total_cgst, 2),
        'sum_igst': round(total_igst, 2),
        'total_quantity': total_quantity,
        'discount_percentage': sale.discount_percentage or 0,
        'discount_amount': sale.discount_amount or 0,
        'paid_amount': paid_amount,
        'balance_amount': balance_amount,
        'items_with_tax': items_with_tax,
    }
    
    # Generate PDF using html2pdf.app API
    try:
        import requests
        from django.template.loader import get_template
        from django.conf import settings
        
        # Render template to HTML string
        template = get_template(template_name)
        html_content = template.render(context, request)
        
        # Generate PDF using html2pdf.app
        api_response = requests.post(
            'https://api.html2pdf.app/v1/generate',
            json={
                'html': html_content,
                'apiKey': getattr(settings, 'HTML2PDF_API_KEY', ''),
                'options': {
                    'printBackground': True,
                    'margin': '1cm',
                    'pageSize': 'A4'
                }
            }
        )
        
        if api_response.status_code == 200:
            response = HttpResponse(api_response.content, content_type='application/pdf')
            filename = f"sale_invoice_{sale_id}_{sale_type}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            return HttpResponse(f"Error generating PDF: {api_response.text}", status=500)
    except Exception as e:
        # Fallback to HTML if PDF generation fails
        return render(request, template_name, context)


def pos_wholesaless(request, sale_id):

    sale = get_object_or_404(Sale, id=sale_id)

    if request.method == 'POST':
        form = pos_wholesaleForm(request.POST, request.FILES)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.user = request.user
            invoice.sale = sale            # 👈 assign the sale from URL
            invoice.save()
            return redirect('list_sale')
        
        else:

            print(form.errors)

            context = {
                "form" : form
            }

            return render(request, 'pos_wholesale.html', context)

    else:

        form = pos_wholesaleForm()

        context = {
            "form" : form
        }

        return render(request, 'pos_wholesale.html', context)


def order_details(request, order_id):

    order = Order.objects.get(id=order_id)
    delivery_boy_data = DeliveryBoy.objects.filter(user = request.user)

    context = {
        "data" : order,
        "delivery_boy_data" : delivery_boy_data
    }

    return render(request, 'order_details.html', context)


from customer.models import *


def order_list(request):

    data = Order.objects.filter(
        items__product__user=request.user
    ).distinct().order_by('-created_at')

    context = {
        "data" : data
    }
    return render(request, 'list_order.html', context)



def update_order_item_status(request, order_item_id):

    if request.method == "POST":
        item = get_object_or_404(OrderItem, id=order_item_id)
        status = request.POST.get("status")
        if status in dict(OrderItem.STATUS_CHOICES):
            item.status = status
            item.save()
            messages.success(request, f"Status for {item.product.name} updated to {status}.")
        else:
            messages.error(request, "Invalid status selected.")
    return redirect(request.META.get("HTTP_REFERER", "/"))




class UpdateOrderItemStatusAPIView(APIView):
    def post(self, request, order_item_id):
        item = OrderItem.objects.get(id=order_item_id)
        status_value = request.data.get("status")

        # Guard: auto-assign rider/external task when moving to ready_to_shipment (instead of intransit)
        if status_value == "ready_to_shipment":
            try:
                order = item.order
                item0 = order.items.select_related("product").first()
                vendor_user = item0.product.user if item0 and getattr(item0.product, "user", None) else None
                mode = DeliveryMode.objects.filter(user=vendor_user).first() if vendor_user else None
                if mode and mode.is_auto_assign_enabled:
                    if not (getattr(order, "delivery_boy_id", None) or getattr(order, "uengage_task_id", None)):
                        # Try auto-assign now
                        rider = DeliveryBoy.objects.filter(user=vendor_user, is_active=True).order_by("total_deliveries").first()
                        if rider:
                            order.delivery_boy = rider
                            order.save(update_fields=["delivery_boy"])
                        else:
                            res = create_delivery_task(order)
                            if res.get("ok"):
                                order.uengage_task_id = res.get("task_id")
                                order.save(update_fields=["uengage_task_id"])
                                tracking = res.get("tracking_url")
                                if tracking and not item.tracking_link:
                                    item.tracking_link = tracking
                                    item.save(update_fields=["tracking_link"])
                            else:
                                return Response({"error": "No delivery boy available and external assignment failed."}, status=status.HTTP_400_BAD_REQUEST)
            except Exception:
                pass

        if status_value in dict(OrderItem.STATUS_CHOICES):
            item.status = status_value
            item.save()
            # Notify via uEngage for item-level delivery events
            try:
                event_map = {
                    "ready_to_shipment": "ready_to_deliver",
                    "intransit": "out_for_delivery",
                    "delivered": "delivered",
                    "ready_to_deliver": "ready_to_deliver",
                    "cancelled": "cancelled",
                }
                evt = event_map.get(status_value)
                if evt:
                    tracking = item.tracking_link
                    notify_delivery_event(item.order, evt, tracking_link=tracking)
            except Exception:
                pass
            return Response(
                {"message": f"Status for {item.product.name} updated to {status_value} ✅"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Invalid status selected."},
                status=status.HTTP_400_BAD_REQUEST
            )
        

def order_exchange_list(request):

    data = ReturnExchange.objects.filter(
        order_item__product__user=request.user
    ).distinct().order_by('-created_at')

    print(data)
    context = {
        "data" : data
    }
    return render(request, 'list_exchange.html', context)

def return_detail(request, return_item_id):
    data = get_object_or_404(ReturnExchange, id=return_item_id)
    context = {"data": data}
    return render(request, 'return_exchange_detail.html', context)


def approve_return(request, return_item_id):
    data = get_object_or_404(ReturnExchange, id=return_item_id)

    if data.order_item.status != 'returned/replaced_requested':
        messages.error(request, "Only requested items can be approved.")
    else:
       
      
        data.order_item.status = 'returned/replaced_approved' 
        data.order_item.save()
        messages.success(request, f"{data.get_type_display()} request approved successfully.")

    return redirect('return_detail', return_item_id=return_item_id)


def reject_return(request, return_item_id):
    data = get_object_or_404(ReturnExchange, id=return_item_id)

    if data.order_item.status != 'returned/replaced_requested':
        messages.error(request, "Only requested items can be rejected.")
    else:
        data.status = 'returned/replaced_rejected'
        data.save()
        messages.success(request, f"{data.get_type_display()} request rejected.")

    return redirect('return_detail', return_item_id=return_item_id)


def completed_return(request, return_item_id):
    data = get_object_or_404(ReturnExchange, id=return_item_id)

    if data.order_item.status != 'returned/replaced_approved':
        messages.error(request, "Only approved requests can be marked as completed.")
    else:
        data.status = 'returned/replacement_completed'
        data.save()
        # Update OrderItem status as delivered
        data.order_item.status = 'returned/replaced_completed'
        data.order_item.save()
        messages.success(request, f"{data.get_type_display()} request marked as completed.")

    return redirect('return_detail', return_item_id=return_item_id)






def privacy_policy(request):

  
    return render(request, 'privacy_policy.html')




def accept_order(request, order_id):

    order = Order.objects.prefetch_related('items__product').get(id=order_id)

    order.status = "accepted"
    order.save()

    return redirect('order_details', order_id = order_id)

def assign_delivery_boy(request, order_id):

    order = Order.objects.prefetch_related('items__product').get(id=order_id)
    delivery_boy_id = request.POST.get('delivery_boy_id')
    delivery_boy_instance = DeliveryBoy.objects.get(id = delivery_boy_id)
    order.delivery_boy = delivery_boy_instance
    order.save()

    return redirect('order_details', order_id = order_id)




from django.shortcuts import render, redirect
from .models import DeliveryBoy, DeliverySettings
from .forms import DeliveryBoyForm, DeliverySettingsForm

def delivery_management(request):
    return render(request, 'delivery/delivery_management.html')

def manage_delivery_boy(request):
    form = DeliveryBoyForm()
    delivery_boys = DeliveryBoy.objects.filter(user = request.user)
    if request.method == 'POST':
        form = DeliveryBoyForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_delivery_boy')
    return render(request, 'delivery/delivery_boy.html', {'form': form, 'delivery_boys': delivery_boys})

def delivery_settings_view(request):
    settings, _ = DeliverySettings.objects.get_or_create(user=request.user)
    form = DeliverySettingsForm(instance=settings)
    if request.method == 'POST':
        form = DeliverySettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return redirect('delivery_settings')
    return render(request, 'delivery/delivery_settings.html', {'form': form})




@login_required
def auto_assign_delivery(request):
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(user=user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-date', '-time')

    delivery_mode, _ = DeliveryMode.objects.get_or_create(user=user)
    form = DeliveryModeForm(instance=delivery_mode)

    if request.method == 'POST':
        form = DeliveryModeForm(request.POST, instance=delivery_mode)
        if form.is_valid():
            form.save()
            return redirect('auto_assign_delivery')

    return render(request, 'delivery/auto_assign_delivery.html', {
        'wallet': wallet,
        'transactions': transactions,
        'form': form
    })




from .models import CashBalance, vendor_bank, CashTransfer

@login_required
def cash_in_hand(request):
    balance_obj, _ = CashBalance.objects.get_or_create(user=request.user)
    bank_accounts = vendor_bank.objects.filter(user=request.user)
    data = CashTransfer.objects.filter(user = request.user)
    return render(request, 'cash_in_hand.html', {
        'balance': balance_obj,
        'bank_accounts': bank_accounts,
        'data': data,
    })


@login_required
def adjust_cash(request):
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount'))
            print("Amount entered:", amount)

            from .models import CashLedger
            from .signals import create_ledger

            balance_obj, _ = CashBalance.objects.get_or_create(user=request.user)
            previous_balance = Decimal(balance_obj.balance or 0)
            new_balance = Decimal(amount)
            delta = new_balance - previous_balance

            # Create CashLedger entry using the helper function (like all other ledger entries)
            if delta != 0:
                description = f"Manual cash adjust: {previous_balance} → {new_balance}"
                create_ledger(
                    parent=None,
                    ledger_model=CashLedger,
                    transaction_type="adjustment",
                    reference_id=None,
                    amount=delta,
                    description=description,
                    user=request.user
                )
            print('Balance updated successfully')
            
            return redirect('cash_in_hand')

        except Exception as e:
            messages.error(request, "Somethig went wrong.")
    

  # optionally handle errors
    return redirect('cash_in_hand')

def adjust_cash_history(request):
    from .models import CashLedger
    # Get adjustment entries from CashLedger instead of CashAdjustHistory
    data = CashLedger.objects.filter(
        user=request.user,
        transaction_type="adjustment"
    ).order_by('-created_at')
    return render(request, 'cash_adjust_history.html', {'data': data})

from django.contrib import messages


@login_required
def bank_transfer(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        bank_id = request.POST.get('bank_account')

        print('bank_id')
        print(bank_id)

        try:
            amount = float(amount)
            bank = vendor_bank.objects.get(id=bank_id, user=request.user)
            balance_obj, _ = CashBalance.objects.get_or_create(user=request.user)

            if amount > balance_obj.balance:
                messages.error(request, "Insufficient balance.")
            else:
              

                CashTransfer.objects.create(user=request.user, bank_account=bank, amount=amount)

                messages.success(request, "Transfer request submitted.")
        except Exception as e:
            print('Error while adjusting cash:', str(e))

    return redirect('cash_in_hand')




from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
class CashAdjustHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import CashLedger
        # Get adjustment entries from CashLedger instead of CashAdjustHistory
        qs = CashLedger.objects.filter(
            user=request.user,
            transaction_type="adjustment"
        ).order_by('-created_at')
        
        # Format response similar to CashAdjustHistory
        data = []
        for entry in qs:
            previous_balance = Decimal(entry.opening_balance) / 100  # Convert from int to Decimal
            new_balance = Decimal(entry.balance_after) / 100
            delta = Decimal(entry.amount) / 100
            data.append({
                'id': entry.id,
                'previous_balance': str(previous_balance),
                'new_balance': str(new_balance),
                'delta_amount': str(delta),
                'note': entry.description,
                'created_at': entry.created_at,
            })
        
        return Response(data)

@login_required(login_url='login_admin')
def cash_adjust_history_view(request):
    from .models import CashLedger
    # Get adjustment entries from CashLedger instead of CashAdjustHistory
    qs = CashLedger.objects.filter(
        user=request.user,
        transaction_type="adjustment"
    ).order_by('-created_at')
    
    context = {
        'data' : qs
    }

    return render(request, 'cash_adjust_history.html', context)

class StoreWorkingHourViewSet(viewsets.ModelViewSet):
    serializer_class = StoreWorkingHourSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        store, _ = vendor_store.objects.get_or_create(user=self.request.user)
        return StoreWorkingHour.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        store, _ = vendor_store.objects.get_or_create(user=self.request.user)
        serializer.save(store=store)

    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk_create(self, request):
        store, _ = vendor_store.objects.get_or_create(user=self.request.user)
        data = request.data  # expecting a list of day/hour dicts

        created = []
        errors = []

        for entry in data:
            entry['store'] = store.id
            try:
                obj, created = StoreWorkingHour.objects.update_or_create(
                    user=request.user,
                    day=entry['day'],
                    defaults={
                        'open_time': entry.get('open_time'),
                        'close_time': entry.get('close_time'),
                        'is_open': entry.get('is_open', True)
                    }
                )
            except Exception as e:
                errors.append({'day': entry['day'], 'error': str(e)})

        if errors:
            return Response({'created': created, 'errors': errors}, status=status.HTTP_207_MULTI_STATUS)
        
        return Response({'message': ' Done'}, status=status.HTTP_201_CREATED)




from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from .models import CashBalance, CashTransfer, OnlineOrderLedger
from .serializers import CashBalanceSerializer, CashTransferSerializer, OnlineOrderLedgerSerializer
from vendor.models import vendor_bank



class CashBalanceViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        balance_obj, _ = CashBalance.objects.get_or_create(user=request.user)
        serializer = CashBalanceSerializer(balance_obj)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='adjust')
    def adjust_cash(self, request):
        try:
            from .models import CashLedger
            from .signals import create_ledger
            
            amount = Decimal(request.data.get('amount', 0))
            note = request.data.get('note', '')
            balance_obj, _ = CashBalance.objects.get_or_create(user=request.user)
            previous = Decimal(balance_obj.balance or 0)
            new = amount
            delta = new - previous
            
            if delta != 0:
                # Create CashLedger entry using the helper function (like all other ledger entries)
                description = note or f"Cash adjustment: {previous} → {new}"
                create_ledger(
                    parent=None,
                    ledger_model=CashLedger,
                    transaction_type="adjustment",
                    reference_id=None,
                    amount=delta,
                    description=description,
                    user=request.user
                )
            
            return Response({'message': 'Balance updated'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='adjust-history')
    def list_adjust_history(self, request):
        from .models import CashLedger
        # Get adjustment entries from CashLedger instead of CashAdjustHistory
        qs = CashLedger.objects.filter(
            user=request.user,
            transaction_type="adjustment"
        ).order_by('-created_at')
        
        # Format response similar to CashAdjustHistory
        data = []
        for entry in qs:
            previous_balance = Decimal(entry.opening_balance) / 100  # Convert from int to Decimal
            new_balance = Decimal(entry.balance_after) / 100
            delta = Decimal(entry.amount) / 100
            data.append({
                'id': entry.id,
                'previous_balance': str(previous_balance),
                'new_balance': str(new_balance),
                'delta_amount': str(delta),
                'note': entry.description,
                'created_at': entry.created_at,
            })
        
        return Response(data)


# -------------------------------
# Day Book API
# -------------------------------
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from django.utils import timezone as dj_timezone
from .models import (
    CustomerLedger,
    VendorLedger,
    CashLedger as CashLedgerModel,
    BankLedger as BankLedgerModel,
    StockTransaction,
)


class DayBookAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _day_bounds(self, date_str):
        if date_str:
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                d = dj_timezone.localdate()
        else:
            d = dj_timezone.localdate()
        start = datetime.combine(d, datetime.min.time()).astimezone(dj_timezone.get_current_timezone())
        end = datetime.combine(d, datetime.max.time()).astimezone(dj_timezone.get_current_timezone())
        return d.isoformat(), start, end

    def _sum_amount(self, qs):
        agg = qs.aggregate(total=Sum('amount'))
        return int(agg['total'] or 0)

    def get(self, request):
        user = request.user
        date_str = request.query_params.get('date')  # YYYY-MM-DD
        date_iso, start, end = self._day_bounds(date_str)

        # Tiles (totals)
        sales_total = self._sum_amount(CustomerLedger.objects.filter(
            customer__user=user, transaction_type='sale', created_at__range=(start, end)
        ))
        purchases_total = self._sum_amount(VendorLedger.objects.filter(
            vendor__user=user, transaction_type='purchase', created_at__range=(start, end)
        ))
        receipts_total = self._sum_amount(CustomerLedger.objects.filter(
            customer__user=user, transaction_type='payment', created_at__range=(start, end)
        ))
        payments_total = abs(self._sum_amount(VendorLedger.objects.filter(
            vendor__user=user, transaction_type='payment', created_at__range=(start, end)
        )))
        expenses_bank = abs(self._sum_amount(BankLedgerModel.objects.filter(
            bank__user=user, transaction_type='expense', created_at__range=(start, end)
        )))
        expenses_cash = abs(self._sum_amount(CashLedgerModel.objects.filter(
            user=user, transaction_type='expense', created_at__range=(start, end)
        )))
        expenses_total = expenses_bank + expenses_cash

        stock_count = StockTransaction.objects.filter(
            product__user=user, created_at__range=(start, end)
        ).count()

        # Opening/closing balances
        # Cash
        last_cash_before = CashLedgerModel.objects.filter(user=user, created_at__lt=start).order_by('-created_at').first()
        opening_cash = int(getattr(last_cash_before, 'balance_after', 0) or 0)
        last_cash_on = CashLedgerModel.objects.filter(user=user, created_at__lte=end).order_by('-created_at').first()
        closing_cash = int(getattr(last_cash_on, 'balance_after', opening_cash) or opening_cash)

        # Bank: sum across all user banks
        bank_accounts = vendor_bank.objects.filter(user=user)
        opening_bank = 0
        closing_bank = 0
        for b in bank_accounts:
            lb_before = BankLedgerModel.objects.filter(bank=b, created_at__lt=start).order_by('-created_at').first()
            opening_bank += int(getattr(lb_before, 'balance_after', 0) or 0)
            lb_on = BankLedgerModel.objects.filter(bank=b, created_at__lte=end).order_by('-created_at').first()
            closing_bank += int(getattr(lb_on, 'balance_after', getattr(lb_before, 'balance_after', 0) or 0))

        # Entries list (cash + bank ledgers)
        def entry_from_cash(e):
            amt = int(e.amount or 0)
            return {
                'type': e.transaction_type,
                'medium': 'Cash',
                'debit': abs(amt) if amt < 0 else 0,
                'credit': amt if amt > 0 else 0,
                'time': e.created_at,
                'reference_id': e.reference_id,
                'description': e.description or ''
            }

        def entry_from_bank(e):
            amt = int(e.amount or 0)
            return {
                'type': e.transaction_type,
                'medium': f"Bank - {e.bank.name}",
                'debit': abs(amt) if amt < 0 else 0,
                'credit': amt if amt > 0 else 0,
                'time': e.created_at,
                'reference_id': e.reference_id,
                'description': e.description or ''
            }

        cash_entries = [entry_from_cash(e) for e in CashLedgerModel.objects.filter(user=user, created_at__range=(start, end)).order_by('created_at')]
        bank_entries = [entry_from_bank(e) for e in BankLedgerModel.objects.filter(bank__user=user, created_at__range=(start, end)).order_by('created_at')]

        entries = sorted(cash_entries + bank_entries, key=lambda x: x['time'])

        return Response({
            'date': date_iso,
            'tiles': {
                'sales': {'total': sales_total},
                'purchases': {'total': purchases_total},
                'stock': {'count': stock_count},
                'receipts': {'total': receipts_total},
                'payments': {'total': payments_total},
                'expenses': {'total': expenses_total},
            },
            'accounts': {
                'cash_in_hand': {'opening': opening_cash, 'closing': closing_cash},
                'bank_balance': {'opening': opening_bank, 'closing': closing_bank},
            },
            'entries': [
                {
                    'type': e['type'],
                    'medium': e['medium'],
                    'debit': e['debit'],
                    'credit': e['credit'],
                    'time': e['time'],
                    'reference_id': e['reference_id'],
                    'description': e['description']
                } for e in entries
            ]
        })


@login_required
def daybook_report(request):
    user = request.user
    date_str = request.GET.get('date')

    def _day_bounds(date_str_local):
        if date_str_local:
            try:
                d = datetime.strptime(date_str_local, "%Y-%m-%d").date()
            except ValueError:
                d = dj_timezone.localdate()
        else:
            d = dj_timezone.localdate()
        start_local = datetime.combine(d, datetime.min.time()).astimezone(dj_timezone.get_current_timezone())
        end_local = datetime.combine(d, datetime.max.time()).astimezone(dj_timezone.get_current_timezone())
        return d.isoformat(), start_local, end_local

    def _sum_amount(qs):
        agg = qs.aggregate(total=Sum('amount'))
        return int(agg['total'] or 0)

    date_iso, start, end = _day_bounds(date_str)

    sales_total = _sum_amount(CustomerLedger.objects.filter(customer__user=user, transaction_type='sale', created_at__range=(start, end)))
    purchases_total = _sum_amount(VendorLedger.objects.filter(vendor__user=user, transaction_type='purchase', created_at__range=(start, end)))
    receipts_total = _sum_amount(CustomerLedger.objects.filter(customer__user=user, transaction_type='payment', created_at__range=(start, end)))
    payments_total = abs(_sum_amount(VendorLedger.objects.filter(vendor__user=user, transaction_type='payment', created_at__range=(start, end))))
    expenses_bank = abs(_sum_amount(BankLedgerModel.objects.filter(bank__user=user, transaction_type='expense', created_at__range=(start, end))))
    expenses_cash = abs(_sum_amount(CashLedgerModel.objects.filter(user=user, transaction_type='expense', created_at__range=(start, end))))
    expenses_total = expenses_bank + expenses_cash

    stock_count = StockTransaction.objects.filter(product__user=user, created_at__range=(start, end)).count()

    last_cash_before = CashLedgerModel.objects.filter(user=user, created_at__lt=start).order_by('-created_at').first()
    opening_cash = int(getattr(last_cash_before, 'balance_after', 0) or 0)
    last_cash_on = CashLedgerModel.objects.filter(user=user, created_at__lte=end).order_by('-created_at').first()
    closing_cash = int(getattr(last_cash_on, 'balance_after', opening_cash) or opening_cash)

    bank_accounts = vendor_bank.objects.filter(user=user)
    opening_bank = 0
    closing_bank = 0
    for b in bank_accounts:
        lb_before = BankLedgerModel.objects.filter(bank=b, created_at__lt=start).order_by('-created_at').first()
        opening_bank += int(getattr(lb_before, 'balance_after', 0) or 0)
        lb_on = BankLedgerModel.objects.filter(bank=b, created_at__lte=end).order_by('-created_at').first()
        closing_bank += int(getattr(lb_on, 'balance_after', getattr(lb_before, 'balance_after', 0) or 0))

    def entry_from_cash(e):
        amt = int(e.amount or 0)
        return {
            'type': e.transaction_type,
            'medium': 'Cash',
            'debit': abs(amt) if amt < 0 else 0,
            'credit': amt if amt > 0 else 0,
            'time': e.created_at,
            'reference_id': e.reference_id,
            'description': e.description or ''
        }

    def entry_from_bank(e):
        amt = int(e.amount or 0)
        return {
            'type': e.transaction_type,
            'medium': f"Bank - {e.bank.name}",
            'debit': abs(amt) if amt < 0 else 0,
            'credit': amt if amt > 0 else 0,
            'time': e.created_at,
            'reference_id': e.reference_id,
            'description': e.description or ''
        }

    cash_entries = [entry_from_cash(e) for e in CashLedgerModel.objects.filter(user=user, created_at__range=(start, end)).order_by('created_at')]
    bank_entries = [entry_from_bank(e) for e in BankLedgerModel.objects.filter(bank__user=user, created_at__range=(start, end)).order_by('created_at')]
    entries = sorted(cash_entries + bank_entries, key=lambda x: x['time'])

    context = {
        'date': date_iso,
        'tiles': {
            'sales': {'total': sales_total},
            'purchases': {'total': purchases_total},
            'stock': {'count': stock_count},
            'receipts': {'total': receipts_total},
            'payments': {'total': payments_total},
            'expenses': {'total': expenses_total},
        },
        'accounts': {
            'cash_in_hand': {'opening': opening_cash, 'closing': closing_cash},
            'bank_balance': {'opening': opening_bank, 'closing': closing_bank},
        },
        'entries': entries,
    }
    return render(request, 'daybook.html', context)


class OnlineOrderLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OnlineOrderLedgerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OnlineOrderLedger.objects.filter(user=self.request.user).order_by('-created_at')


# -------------------------------
# Store Reviews (vendor moderation)
# -------------------------------
from customer.models import Review, Order, OrderItem, Follower, Favourite
from customer.serializers import ReviewSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from datetime import timedelta, datetime
from collections import defaultdict


class VendorDashboardViewSet(viewsets.ViewSet):
    """
    Vendor Dashboard API - Provides comprehensive statistics for vendor dashboard
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """
        Get vendor dashboard statistics
        
        Query Parameters:
        - product_id: Filter by specific product
        - order_item_id: Filter by specific order item
        - user_id: Filter by specific user (for sales)
        """
        user = request.user
        
        # Get filter parameters
        product_id = request.query_params.get('product_id')
        order_item_id = request.query_params.get('order_item_id')
        user_id = request.query_params.get('user_id')
        
        # Build base querysets (no date filtering - get all data)
        sale_qs = Sale.objects.filter(user=user)
        purchase_qs = Purchase.objects.filter(user=user)
        expense_qs = Expense.objects.filter(user=user)
        order_qs = Order.objects.filter(user=user)
        
        # Apply product filter
        if product_id:
            sale_qs = sale_qs.filter(items__product_id=product_id).distinct()
            order_qs = order_qs.filter(items__product_id=product_id).distinct()
        
        # Apply order_item filter
        if order_item_id:
            order_qs = order_qs.filter(items__id=order_item_id).distinct()
        
        # Apply user filter (for sales - customer)
        if user_id:
            sale_qs = sale_qs.filter(customer_id=user_id)
        
        # 1. Total Sales (POS Sales)
        total_sales = sale_qs.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # 2. Total Purchases
        total_purchases = purchase_qs.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # 3. Total Expenses
        total_expenses = expense_qs.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # 4. Offline Sales (POS Sales) - Same as total sales
        offline_sales = total_sales
        
        # 5. Online Sales (Customer Orders)
        online_sales = order_qs.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # 6. Total Followers
        total_followers = Follower.objects.filter(user=user).count()
        
        # 7. Followers Chart Data (per day)
        followers_chart_data = self._get_followers_chart_data(user)
        
        # 8. Top Liked Products
        top_liked_products = self._get_top_liked_products(user, request, limit=10)
        
        # 9. Low Stock Products
        low_stock_products = self._get_low_stock_products(user, request)
        
        return Response({
            'total_sales': float(total_sales),
            'total_purchases': float(total_purchases),
            'total_expenses': float(total_expenses),
            'offline_sales': float(offline_sales),
            'online_sales': float(online_sales),
            'total_followers': total_followers,
            'followers_chart': followers_chart_data,
            'top_liked_products': top_liked_products,
            'low_stock_products': low_stock_products,
        })
    
    def _get_followers_chart_data(self, user, days=30):
        """Get followers count per day for chart"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get all followers in the date range
        followers = Follower.objects.filter(
            user=user,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(count=Count('id')).order_by('date')
        
        # Create a dictionary for easy lookup
        followers_dict = {}
        for item in followers:
            # Convert date to date object if it's a string
            date_key = item['date']
            if isinstance(date_key, str):
                try:
                    date_key = datetime.strptime(date_key, '%Y-%m-%d').date()
                except ValueError:
                    continue
            followers_dict[date_key] = item['count']
        
        # Generate data for all days in range (fill missing days with 0)
        chart_data = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            count = followers_dict.get(current_date, 0)
            chart_data.append({
                'date': date_str,
                'count': count
            })
            current_date += timedelta(days=1)
        
        return chart_data
    
    def _get_top_liked_products(self, user, request, limit=10):
        """Get top liked products for the vendor"""
        from vendor.serializers import product_serializer
        
        # Get products with like counts
        products = product.objects.filter(user=user).annotate(
            like_count=Count('favourited_by')
        ).order_by('-like_count')[:limit]
        
        return product_serializer(products, many=True, context={'request': request}).data
    
    def _get_low_stock_products(self, user, request):
        """Get products with low stock (stock <= low_stock_quantity)"""
        from vendor.serializers import product_serializer
        
        # Get products where stock is tracked and is low
        low_stock = product.objects.filter(
            user=user,
            track_stock=True,
            low_stock_alert=True
        ).filter(
            Q(stock__lte=F('low_stock_quantity')) | 
            Q(stock__isnull=True, low_stock_quantity__isnull=False)
        )
        
        return product_serializer(low_stock, many=True, context={'request': request}).data


class StoreReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        qs = Review.objects.select_related('order_item__product', 'user')
        # Default: vendor sees own store's reviews
        qs = qs.filter(order_item__product__user=self.request.user)

        # Optional filter: admin can pass store_user_id to view specific store
        store_user_id = self.request.query_params.get('store_user_id')
        if store_user_id:
            qs = Review.objects.filter(order_item__product__user_id=store_user_id)

        is_visible = self.request.query_params.get('is_visible')
        if is_visible is not None:
            val = str(is_visible).lower() in ('true', '1', 'yes')
            qs = qs.filter(is_visible=val)

        return qs.order_by('-created_at')

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Only the vendor owning the product (or superuser) can toggle visibility
        if (getattr(instance.order_item.product, 'user', None) != request.user) and (not request.user.is_superuser):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        is_visible = request.data.get('is_visible', None)
        if is_visible is None:
            return Response({"error": "is_visible is required"}, status=status.HTTP_400_BAD_REQUEST)

        instance.is_visible = str(is_visible).lower() in ('true', '1', 'yes')
        instance.save(update_fields=['is_visible'])
        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)


class CashTransferViewSet(viewsets.ModelViewSet):
    serializer_class = CashTransferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only show transfers belonging to the logged-in user
        return CashTransfer.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        amount = serializer.validated_data.get('amount')
        bank_account = serializer.validated_data.get('bank_account')

        # Get or create balance record
        balance_obj, _ = CashBalance.objects.get_or_create(user=user)

        # Validation
        if amount > balance_obj.balance:
            raise serializers.ValidationError({"amount": "Insufficient balance."})

        # Save transfer record only; signals will adjust cash and bank
        serializer.save(user=user, bank_account=bank_account)



class BankTransferViewSet(viewsets.ModelViewSet):
    serializer_class = BankTransferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # User can only see their own transfers
        return BankTransfer.objects.filter(user=self.request.user).order_by("-date")

    def perform_create(self, serializer):
        # Auto-assign logged-in user
        serializer.save(user=self.request.user)


class BannerCampaignViewSet(viewsets.ModelViewSet):
    queryset = BannerCampaign.objects.all()
    serializer_class = BannerCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        redirect_to = self.request.data.get('redirect_to')

        if redirect_to == 'store':
            try:
                store = vendor_store.objects.get(user=self.request.user)
            except vendor_store.DoesNotExist:
                raise ValidationError({"store": "Vendor store not found for this user."})
            serializer.save(user=self.request.user, store=store, product=None)
        else:
            serializer.save(user=self.request.user, store=None)





class NotificationCampaignViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationCampaign.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        # check monthly quota (e.g., max 3 notifications per month)
        user = self.request.user
        month_count = NotificationCampaign.objects.filter(
            user=user, created_at__month=self.request.user.date_joined.month
        ).count()
        if month_count >= 3:
            raise serializers.ValidationError("You have reached your monthly limit.")
        
        redirect_to = self.request.data.get('redirect_to')
        
        # If redirect_to is 'store' and no store provided, auto-assign user's store
        if redirect_to == 'store':
            store = serializer.validated_data.get('store')
            if not store:
                try:
                    store = vendor_store.objects.get(user=user)
                    serializer.validated_data['store'] = store
                except vendor_store.DoesNotExist:
                    raise serializers.ValidationError({
                        'store': 'No store found for this user. Please create a store first.'
                    })
                except vendor_store.MultipleObjectsReturned:
                    # If multiple stores, get the first one
                    store = vendor_store.objects.filter(user=user).first()
                    serializer.validated_data['store'] = store
        
        serializer.save(user=user)




class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter by logged-in user
        return Sale.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save(user=self.request.user)
            # Ensure default company_profile if missing
            try:
                if not getattr(instance, "company_profile_id", None):
                    cp = CompanyProfile.objects.filter(user=self.request.user).first()
                    if cp:
                        instance.company_profile = cp
                        instance.save(update_fields=["company_profile"])
            except Exception:
                pass



class DeliveryBoyViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryBoySerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return DeliveryBoy.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DeliverySettingsViewSet(viewsets.ModelViewSet):
    serializer_class = DeliverySettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DeliverySettings.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        instance, _ = DeliverySettings.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        instance, _ = DeliverySettings.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    

from rest_framework.exceptions import ValidationError

class DeliveryModeViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryModeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DeliveryMode.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        user = request.user

        # Ensure delivery mode exists
        delivery_mode, _ = DeliveryMode.objects.get_or_create(user=user)
        delivery_mode_data = DeliveryModeSerializer(delivery_mode).data

        # Ensure wallet exists
        wallet, _ = Wallet.objects.get_or_create(user=user)
        transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-date', '-time')
        transactions_data = WalletTransactionSerializer(transactions, many=True).data

        return Response({
            "delivery_mode": delivery_mode_data,
            "wallet_transactions": transactions_data
        })

    def create(self, request, *args, **kwargs):
        """
        POST will create DeliveryMode if missing,
        or update the existing record for this user.
        """
        instance, _ = DeliveryMode.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

   


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)




def tax_setting(request):
    setting, created = TaxSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = TaxSettingsForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            return redirect('tax_setting')
    else:
        form = TaxSettingsForm(instance=setting)

    return render(request, 'TaxSettings.html', {'form': form})


def invoice_setting(request):
    setting, created = InvoiceSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = InvoiceSettingsForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            return redirect('online_store_setting')
    else:
        form = OnlineStoreSettingForm(instance=setting)

    return render(request, 'InvoiceSettings.html', {'form': form})


class PrintVariantChoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "paper_choices": [
                {"value": key, "label": label} for key, label in PrintVariant.PAPER_CHOICES
            ],
            "color_type_choices": [
                {"value": key, "label": label} for key, label in PrintVariant.COLOR_CHOICES
            ],
            "unit_choices": [
                {"value": key, "label": label} for key, label in product.UNIT_CHOICES
            ],
            "sided_choices": [
                {"value": key, "label": label} for key, label in PrintVariant.SIDED_CHOICES
            ]
        })
    


class PrintVariantViewSet(viewsets.ModelViewSet):
    queryset = PrintVariant.objects.all()
    serializer_class = PrintVariantSerializer
    permission_classes = [permissions.IsAuthenticated]




class ReminderSettingViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSettingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReminderSetting.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        instance, _ = ReminderSetting.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        instance, _ = ReminderSetting.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class SMSSettingViewSet(viewsets.ModelViewSet):
    serializer_class = SMSSettingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SMSSetting.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Use get_or_create to get existing instance or create new one
        instance, _ = SMSSetting.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        # Use get_or_create to ensure instance exists
        instance, _ = SMSSetting.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        # Use get_or_create to ensure instance exists
        instance, _ = SMSSetting.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter reminders by the logged-in user
        queryset = Reminder.objects.filter(user=self.request.user)
        
        # Optional: Filter by reminder_type if provided
        reminder_type = self.request.query_params.get('reminder_type', None)
        if reminder_type:
            queryset = queryset.filter(reminder_type=reminder_type)
        
        # Optional: Filter by is_read status if provided
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
        
        return queryset.order_by('-created_at')

    def partial_update(self, request, *args, **kwargs):
        """Allow updating is_read status"""
        instance = self.get_object()
        # Only allow updating is_read field
        if 'is_read' in request.data:
            instance.is_read = request.data['is_read']
            instance.save(update_fields=['is_read'])
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return Response({'detail': 'Only is_read field can be updated'}, status=status.HTTP_400_BAD_REQUEST)


class TaxSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = TaxSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TaxSettings.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
   
    def list(self, request, *args, **kwargs):
        instance, _ = TaxSettings.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    


class InvoiceSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSettingsSerializer  # ✅ FIXED
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InvoiceSettings.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        instance, _ = InvoiceSettings.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)



from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def barcode_lookup(request):
    # Normalize input
    barcode = (request.GET.get('barcode') or '').strip()
    if not barcode:
        return JsonResponse({'success': False}, status=400)

    # Determine price key (optionally accept wholesale=1)
    price_attr = 'sales_price'
    wholesale_flag = (request.GET.get('wholesale') or '').lower()
    if wholesale_flag in ('1', 'true', 'yes', 'on'):
        price_attr = 'wholesale_price'

    # Case 1: internal svindo<ID> format
    if barcode.lower().startswith('svindo'):
        pid = barcode[6:]
        try:
            prod = product.objects.get(id=pid)
            price = getattr(prod, price_attr, None) or prod.sales_price
            return JsonResponse({'success': True, 'id': prod.id, 'name': prod.name, 'price': float(price)})
        except product.DoesNotExist:
            return JsonResponse({'success': False})

    # Case 2: direct product barcode field
    prod = product.objects.filter(assign_barcode=barcode).first()
    if prod:
        price = getattr(prod, price_attr, None) or prod.sales_price
        return JsonResponse({'success': True, 'id': prod.id, 'name': prod.name, 'price': float(price)})

    # Case 3: serial/IMEI resolves to product
    try:
        from vendor.models import serial_imei_no  # local import avoids circulars
        serial = serial_imei_no.objects.select_related('product').filter(value=barcode).first()
        if serial and serial.product_id:
            prod = serial.product
            price = getattr(prod, price_attr, None) or prod.sales_price
            return JsonResponse({'success': True, 'id': prod.id, 'name': prod.name, 'price': float(price)})
    except Exception:
        pass

    return JsonResponse({'success': False})
    



class VendorStoreListAPIView(generics.ListAPIView):
    serializer_class = VendorStoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return vendor_store.objects.filter(user=user)


class requestlist(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = ProductRequest.objects.all().order_by("-created_at")
        serializer = ProductRequestSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        
class VendorReturnManageAPIView(APIView):
    """
    Vendor can view, approve, reject, or complete return/exchange requests
    """
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def get(self, request):
        """
        List all return/exchange requests related to vendor's products
        """
        vendor_user = request.user
        queryset = ReturnExchange.objects.filter(order_item__product__user=vendor_user).order_by('-created_at')
        serializer = ReturnExchangeVendorSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """
        Update status of a return/exchange request
        action = "approve" | "reject" | "complete"
        """
        req_id = request.data.get("id")
        action = request.data.get("action")

        if not req_id or not action:
            return Response({"error": "Both 'id' and 'action' are required."}, status=400)

        try:
            instance = ReturnExchange.objects.get(id=req_id, order_item__product__user=request.user)
        except ReturnExchange.DoesNotExist:
            return Response({"error": "Invalid request or not related to your products."}, status=404)

        # ✅ Logic same as before
        if action == "approve":
            if instance.order_item.status != 'returned/replaced_requested':
                return Response({"error": "Only requested items can be approved."}, status=400)

            instance.status = 'returned/replaced_approved'
            instance.order_item.status = 'returned/replaced_approved'
            instance.order_item.save()

        elif action == "reject":
            if instance.order_item.status != 'returned/replaced_requested':
                return Response({"error": "Only requested items can be rejected."}, status=400)

            instance.status = 'returned/replaced_rejected'

        elif action == "complete":
            if instance.order_item.status != 'returned/replaced_approved':
                return Response({"error": "Only approved requests can be marked as completed."}, status=400)

            instance.status = 'returned/replacement_completed'
            instance.order_item.status = 'returned/replaced_completed'
            instance.order_item.save()

        else:
            return Response({"error": "Invalid action. Use 'approve', 'reject', or 'complete'."}, status=400)

        instance.save()

        return Response({
            "success": f"{action.capitalize()} successful",
            "id": instance.id,
            "status": instance.status
        }, status=200)



    

class VendorCoverageViewSet(viewsets.ModelViewSet):
    serializer_class = VendorCoverageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VendorCoverage.objects.filter(user=self.request.user).select_related("pincode")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user = request.user
        pincode_ids = request.data.get("pincode_ids", [])
        
        if not isinstance(pincode_ids, list) or not all(isinstance(pid, int) for pid in pincode_ids):
            return Response(
                {"detail": "Invalid format. 'pincode_ids' must be a list of integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete old coverage and add new
        VendorCoverage.objects.filter(user=user).delete()
        pincodes = Pincode.objects.filter(id__in=pincode_ids)
        VendorCoverage.objects.bulk_create([
            VendorCoverage(user=user, pincode=p) for p in pincodes
        ])

        serializer = self.get_serializer(VendorCoverage.objects.filter(user=user), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


    
class OfferViewSet(viewsets.ModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  
    def get_queryset(self):
        # Show all offers related to the user's requests or their own offers
        user = self.request.user
        return Offer.objects.filter(
            models.Q(request__user=user) | models.Q(seller=user)
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)