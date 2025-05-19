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

from rest_framework.generics import ListAPIView
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

    if request.method == 'POST':

        forms = CompanyProfileForm(request.POST, request.FILES)

        if forms.is_valid():
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_company_profile')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_company_profile.html', context)
    
    else:

        forms = CompanyProfileForm()

        context = {
            'form': forms
        }
        return render(request, 'add_company_profile.html', context)

        

@login_required(login_url='login_admin')
def update_company_profile(request, company_profile_id):

    if request.method == 'POST':

        instance = CompanyProfile.objects.get(id=company_profile_id)

        forms = CompanyProfileForm(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
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

    data = coupon.objects.all()
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

        

@login_required(login_url='login_admin')
def update_customer(request, vendor_id):

    if request.method == 'POST':

        instance = vendor_customers.objects.get(id=vendor_id)

        forms = vendor_vendorsForm(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_vendor')
        else:
            print(forms.errors)
    
    else:

        instance = vendor_customers.objects.get(id=vendor_id)
        forms = vendor_vendorsForm(instance=instance)

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





from rest_framework.response import Response

from rest_framework.views import APIView

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



@login_required(login_url='login_admin')
def add_product(request):

    AddonFormSet = inlineformset_factory(
        product, product_addon,
        form=ProductAddonForm,
        fields=['addon'],
        extra=1,
        can_delete=True
        )

    if request.method == 'POST':
        product_form = product_Form(request.POST, request.FILES)
        

        if product_form.is_valid():
            product_instance = product_form.save(commit=False)
            product_instance.user = request.user
            product_instance.save()  # fully save the product

            formset = AddonFormSet(request.POST, request.FILES, instance=product_instance)

            if formset.is_valid():
                formset.save()
                return redirect('list_product')
            else:
                print("Addon formset errors:", formset.errors)
        else:
            print("Product form errors:", product_form.errors)

        # Return with errors
        context = {
            'form': product_form,
            'formset': formset if 'formset' in locals() else AddonFormSet(),
        }
        return render(request, 'add_product.html', context)

    else:
        product_form = product_Form()
        formset = AddonFormSet()

        context = {
            'form': product_form,
            'formset': formset,
        }
        return render(request, 'add_product.html', context)

        

@login_required(login_url='login_admin')
def update_product(request, product_id):

    instance = product.objects.get(id=product_id)

    AddonFormSet = inlineformset_factory(
        product, product_addon,
        form=ProductAddonForm,
        fields=['addon'],
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        product_form = product_Form(request.POST, request.FILES, instance=instance)
        formset = AddonFormSet(request.POST, request.FILES, instance=instance)

        if product_form.is_valid() and formset.is_valid():
            product_form.save()
            formset.save()
            return redirect('list_product')
        else:
            print("Product form errors:", product_form.errors)
            print("Addon formset errors:", formset.errors)

    else:
        product_form = product_Form(instance=instance)
        formset = AddonFormSet(instance=instance)

    context = {
        'form': product_form,
        'formset': formset,
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
def product_setting(request):


    settings, _ = ProductSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        checkbox_fields = [
            'wholesale_price', 'stock', 'imei', 'low_stock_alert', 'category', 'sub_category', 'brand_name', 'color', 'size',
            'batch_number', 'expiry_date', 'description', 'image', 'tax', 'food',
            'instant_delivery', 'self_pickup', 'general_delivery',
            'return_policy', 'cod', 'replacement', 'shop_exchange', 'shop_warranty', 'brand_warranty',
            'online_catalog_only'
        ]

        for field in checkbox_fields:
            setattr(settings, field, request.POST.get(field) == 'on')

        settings.save()
        return redirect('product_settings')  # Stay on the same page after saving

    return render(request, 'product_settings.html', {'settings': settings})





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

    data = addon.objects.all()
    context = {
        'data': data
    }
    return render(request, 'list_addon.html', context)





from rest_framework import status


from rest_framework import viewsets

from users.permissions import *



class OnlineStoreSettingViewSet(viewsets.ModelViewSet):
    serializer_class = OnlineStoreSettingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OnlineStoreSetting.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class ProductViewSet(viewsets.ModelViewSet):
    queryset = product.objects.all()
    serializer_class = product_serializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        # Return only products of logged-in user
        return product.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign logged-in user to the product
        serializer.save(user=self.request.user)

class ProductSettingsViewSet(viewsets.ViewSet):
    permission_classes = [IsVendor]

    def list(self, request):
        settings, created = ProductSettings.objects.get_or_create(user=request.user)
        serializer = ProductSettingsSerializer(settings)
        return Response(serializer.data)

    def update(self, request, pk=None):
        settings, created = ProductSettings.objects.get_or_create(user=request.user)
        serializer = ProductSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class ProductAddonViewSet(viewsets.ModelViewSet):
    queryset = addon.objects.all()
    serializer_class = AddonSerializer


class AddonViewSet(viewsets.ModelViewSet):
    queryset = product_addon.objects.all()
    serializer_class = ProductAddonSerializer


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

class CouponViewSet(viewsets.ModelViewSet):
    queryset = coupon.objects.all()
    serializer_class = coupon_serializer
    permission_classes = [IsVendor]

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
        # Return only products of logged-in user
        return CompanyProfile.objects.filter(user=self.request.user)

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


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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

    if request.method == 'POST':

        forms = PurchaseForm(request.POST, request.FILES, user=request.user)

        if forms.is_valid():
          
            forms = forms.save(commit=False)
            forms.user = request.user  # assign user here
            forms.save()
            return redirect('list_purchase')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_purchase.html', context)
    
    else:

        forms = PurchaseForm()

        context = {
            'form': forms
        }
        return render(request, 'add_purchase.html', context)

        

@login_required(login_url='login_admin')
def update_purchase(request, purchase_id):

    if request.method == 'POST':

        instance = Purchase.objects.get(id=purchase_id)

        forms = PurchaseForm(request.POST, request.FILES, instance=instance, user=request.user)

        if forms.is_valid():
            forms.save()
            return redirect('list_purchase')
        else:
            print(forms.errors)
    
    else:

        instance = Purchase.objects.get(id=purchase_id)
        forms = PurchaseForm(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_purchase.html', context)

        

@login_required(login_url='login_admin')
def delete_purchase(request, purchase_id):

    Purchase.objects.get(id=purchase_id).delete()

    return HttpResponseRedirect(reverse('list_purchase'))


@login_required(login_url='login_admin')
def list_purchase(request):

    data = Purchase.objects.filter(user = request.user)
    context = {
        'data': data
    }
    return render(request, 'list_purchase.html', context)






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
            'form': forms
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

    data = Expense.objects.filter(user = request.user)
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
    
    store_instance = vendor_store.objects.get(user=request.user)
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

            obj, created = StoreWorkingHour.objects.get_or_create(store=store_instance, day=day)

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
    hours_qs = StoreWorkingHour.objects.filter(store=store_instance)
    hours = {hour.day: hour for hour in hours_qs}

    return render(request, "store_hours.html", {
        "days": days,
        "hours": hours
    })