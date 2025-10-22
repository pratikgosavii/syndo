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
from .serializers import *

from users.permissions import *
from django.db.models import Sum

from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework import viewsets, permissions


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
def update_bannercampaign(request, party_id):

    if request.method == 'POST':

        instance = BannerCampaign.objects.get(id=party_id)

        forms = BannerCampaignForm(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_bannercampaign')
        else:
            print(forms.errors)
    
    else:

        instance = BannerCampaign.objects.get(id=party_id)
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

        # Current cash balance (last balance_after or sum of all amounts)
        cash_balance = ledger_entries.aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "cash_balance": cash_balance,
            "ledger": serializer.data
        })
    

from customer.serializers import *


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items__product').all().order_by('-id')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        """Restrict update to only allowed fields"""
        instance = self.get_object()
        allowed_fields = {"status", "delivery_boy", "is_paid"}
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
        ledger_entries = CustomerLedger.objects.filter(customer_id=customer_id).order_by("created_at")

        # Running balance
        balance = ledger_entries.aggregate(total=Sum("amount"))["total"] or 0

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
    ledger_entries = CustomerLedger.objects.filter(customer_id=customer_id).order_by("created_at")
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

    # Create super_catalogue instance with matching fields
    super_catalogue.objects.create(
        product_type=p.product_type,
        sale_type=p.sale_type,
        name=p.name,
        category=p.category,
        sub_category=p.sub_category,
        unit=p.unit,
        hsn=p.hsn,
        track_serial_numbers=p.track_serial_numbers,
        brand_name=p.brand_name,
        color=p.color,
        size=p.size,
        description=p.description,
        image=p.image,
        gallery_images=p.gallery_images,
        instant_delivery=p.instant_delivery,
        self_pickup=p.self_pickup,
        general_delivery=p.general_delivery,
        return_policy=p.return_policy,
        cod=p.cod,
        replacement=p.replacement,
        shop_exchange=p.shop_exchange,
        shop_warranty=p.shop_warranty,
        brand_warranty=p.brand_warranty,
        is_popular=p.is_popular,
        is_featured=p.is_featured,
        is_active=p.is_active,
    )

    return redirect('list_product')  # Replace with the actual redirect target

        

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

    data = super_catalogue.objects.all()
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

    data = product.objects.filter(user = request.user)
    context = {
        'data': data
    }
    return render(request, 'list_product.html', context)


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
        products = product.objects.filter(id__in=ids)

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
            barcode_value = i.id

          
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

        data = product.objects.filter(user = request.user)
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
    queryset = product.objects.all()
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
                for item_data in request.data['items']:
                    PurchaseItem.objects.create(
                        purchase=instance,
                        product_id=item_data['product'],
                        quantity=item_data['quantity'],
                        price=item_data['price'],
                        total=item_data['quantity'] * item_data['price'],
                    )
        
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

    data = product.objects.all()

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
    data = product.objects.all()
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
        
        user = request.user

        last_purchase = Purchase.objects.order_by('-id').first()
        if last_purchase and last_purchase.purchase_code:
            try:
                last_number = int(last_purchase.purchase_code.split('-')[-1])
            except (IndexError, ValueError):
                last_number = 0
        else:
            last_number = 0
        prefix = "PUR"
        new_code = f"{prefix}-{last_number + 1:05d}"

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
        invoice_type = request.GET.get('invoice_type')
        user = request.user

        type_prefix_map = {
            'invoice': 'svin-inv',
            'proforma': 'svin-prof',
            'quotation': 'svin-quot',
            'credit_note': 'svin-crednot',
            'delivery_challan': 'svin-dc',
        }

        prefix = type_prefix_map.get(invoice_type, 'svin-inv')

        last_invoice = pos_wholesale.objects.filter(
            user=user,
            invoice_type=invoice_type,
            invoice_number__startswith=prefix
        ).order_by('-id').first()

        if last_invoice:
            try:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
            except (IndexError, ValueError):
                last_number = 0
        else:
            last_number = 0

        invoice_number = f"{prefix}-{last_number + 1}"
        return Response({"invoice_number": invoice_number})




def get_next_invoice_number_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    invoice_type = request.GET.get('invoice_type')
    user = request.user

    type_prefix_map = {
        'invoice': 'svin-inv',
        'proforma': 'svin-prof',
        'quotation': 'svin-quot',
        'credit_note': 'svin-crednot',
        'delivery_challan': 'svin-dc',
    }

    prefix = type_prefix_map.get(invoice_type, 'svin-inv')

    last_invoice = pos_wholesale.objects.filter(
        user=user,
        invoice_type=invoice_type,
        invoice_number__startswith=prefix
    ).order_by('-id').first()

    if last_invoice:
        try:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
        except (IndexError, ValueError):
            last_number = 0
    else:
        last_number = 0

    invoice_number = f"{prefix}-{last_number + 1}"
    return JsonResponse({"invoice_number": invoice_number})




@login_required
def pos(request):

    sale_form = SaleForm()
    customer_form = vendor_customersForm()
    wholesale_form = pos_wholesaleForm()

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
                "products": product.objects.filter(user=request.user),
            }
            return render(request, "pos_form.html", context)

        with transaction.atomic():
            try:
                # Save sale
                sale_instance = sale_form.save(commit=False)
                sale_instance.user = request.user
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
                    "products": product.objects.filter(user=request.user),
                    "error_message": str(e),
                }
                return render(request, "pos_form.html", context)

    return render(request, "pos_form.html", {
        "form": sale_form,
        "banks" : vendor_bank.objects.all(),
        "customer_forms": customer_form,
        "wholesale_forms": wholesale_form,
        "saleitemform": SaleItemForm(),
        "products": product.objects.filter(user=request.user),
    })



    
def update_sale(request, sale_id):

    sale_instance = get_object_or_404(Sale, id=sale_id, user=request.user)
    existing_items = SaleItem.objects.filter(sale=sale_instance)

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
                "products": product.objects.filter(user=request.user),
                "existing_items": items_with_amount,  # ✅ Use calculated data
                "error_message": "Please correct the errors below.",
            }
            return render(request, "pos_form.html", context)

        with transaction.atomic():
            try:
                sale_instance = sale_form.save(commit=False)
                sale_instance.user = request.user
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
                    "products": product.objects.filter(user=request.user),
                    "existing_items": items_with_amount,  # ✅ Keep calculated
                    "error_message": str(e),
                }
                return render(request, "pos_form.html", context)

    else:
        sale_form = SaleForm(instance=sale_instance)
        customer_form = vendor_customersForm()
        wholesale_instance = getattr(sale_instance, 'pos_wholesale', None)
        wholesale_form = pos_wholesaleForm(instance=wholesale_instance)

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

    delivery = wholesale.delivery_charges or 0 if wholesale else 0
    packaging = wholesale.packaging_charges or 0 if wholesale else 0
    total_amount = sale.total_amount + delivery + packaging

    # Round off calculation
    rounded_total = round(total_amount)
    round_off_value = round(rounded_total - total_amount, 2)

    # Prepare HSN summary
    hsn_summary = {}
    total_tax = 0
    for item in sale.items.all():
        hsn = item.product.hsn or "N/A"
        sgst_rate = item.product.sgst_rate or 9
        cgst_rate = item.product.cgst_rate or 9
        taxable_val = float(item.amount)

        if hsn not in hsn_summary:
            hsn_summary[hsn] = {
                'taxable_value': 0,
                'sgst_rate': sgst_rate,
                'cgst_rate': cgst_rate,
            }
        hsn_summary[hsn]['taxable_value'] += taxable_val

        # Add tax
        total_tax += item.tax_amount

    # Calculate tax per HSN
    for hsn, data in hsn_summary.items():
        data['sgst_amount'] = round(data['taxable_value'] * data['sgst_rate'] / 100, 2)
        data['cgst_amount'] = round(data['taxable_value'] * data['cgst_rate'] / 100, 2)
        data['total_tax'] = data['sgst_amount'] + data['cgst_amount']

    # Convert total to words
    total_in_words = num2words(rounded_total, to='currency', lang='en_IN').title()

    return render(request, 'sale_invoice/cgst_quotation.html', {
        'sale_instance': sale,
        'wholesale': wholesale,
        'total_amount': total_amount,
        'rounded_total': rounded_total,
        'round_off_value': round_off_value,
        'hsn_summary': hsn_summary.items(),
        'total_in_words': total_in_words,
        'total_tax': total_tax,   # ✅ added here
    })


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

    if data.status != 'returned/replaced_requested':
        messages.error(request, "Only requested items can be approved.")
    else:
       
      
        data.order_item.status = 'returned/replaced_approved' 
        data.order_item.save()
        messages.success(request, f"{data.get_type_display()} request approved successfully.")

    return redirect('return_detail', return_item_id=return_item_id)


def reject_return(request, return_item_id):
    data = get_object_or_404(ReturnExchange, id=return_item_id)

    if data.status != 'returned/replaced_requested':
        messages.error(request, "Only requested items can be rejected.")
    else:
        data.status = 'returned/replaced_rejected'
        data.save()
        messages.success(request, f"{data.get_type_display()} request rejected.")

    return redirect('return_detail', return_item_id=return_item_id)


def completed_return(request, return_item_id):
    data = get_object_or_404(ReturnExchange, id=return_item_id)

    if data.status != 'returned/replaced_approved':
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

            balance_obj, _ = CashBalance.objects.get_or_create(user=request.user)
            balance_obj.balance += Decimal(amount)
            balance_obj.save()
            print('Balance updated successfully')
            
            return redirect('cash_in_hand')

        except Exception as e:
            messages.error(request, "Somethig went wrong.")
    

  # optionally handle errors
    return redirect('cash_in_hand')



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
                # Deduct and record transfer
                balance_obj.balance -= Decimal(amount)
                balance_obj.save()

                CashTransfer.objects.create(user=request.user, bank_account=bank, amount=amount)

                messages.success(request, "Transfer request submitted.")
        except Exception as e:
            print('Error while adjusting cash:', str(e))

    return redirect('cash_in_hand')




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
from .models import CashBalance, CashTransfer
from .serializers import CashBalanceSerializer, CashTransferSerializer
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
            amount = Decimal(request.data.get('amount', 0))
            print(amount)
            balance_obj, _ = CashBalance.objects.get_or_create(user=request.user)
            balance_obj.balance = amount
            balance_obj.save()
            return Response({'message': 'Balance updated'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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

        # Deduct balance
        balance_obj.balance -= Decimal(amount)
        balance_obj.save()

        # Save transfer record
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
        serializer.save(user=self.request.user)





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
        serializer.save(user=user)




class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save(user=self.request.user)



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
    barcode = request.GET.get('barcode')
    print(barcode)
    try:
        product_instance = product.objects.get(id=barcode)
        return JsonResponse({'success': True, 'id': product_instance.id, 'name': product_instance.name, 'price': product_instance.sales_price})
    except product.DoesNotExist:
        return JsonResponse({'success': False})
    



class VendorStoreListAPIView(generics.ListAPIView):
    serializer_class = VendorStoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return vendor_store.objects.filter(user=user)



        
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
        Example JSON:
        {
            "id": 12,
            "action": "approve"  # or "reject" / "complete"
        }
        """
        req_id = request.data.get("id")
        action = request.data.get("action")

        if not req_id or not action:
            return Response({"error": "Both 'id' and 'action' are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = ReturnExchange.objects.get(id=req_id, order_item__product__user=request.user)
        except ReturnExchange.DoesNotExist:
            return Response({"error": "Return/Exchange request not found or not related to your products."},
                            status=status.HTTP_404_NOT_FOUND)

        valid_actions = {
            "approve": "approved",
            "reject": "rejected",
            "complete": "completed",
        }

        if action not in valid_actions:
            return Response({"error": "Invalid action. Use 'approve', 'reject', or 'complete'."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Prevent status changes if already completed/rejected
        if instance.status in ['rejected', 'completed']:
            return Response({"error": "This request has already been processed."}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = valid_actions[action]
        instance.save()

        return Response({
            "success": f"Request {action}d successfully.",
            "id": instance.id,
            "status": instance.status
        }, status=status.HTTP_200_OK)
    



    

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