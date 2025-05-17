from django.shortcuts import get_object_or_404, render

from masters.filters import EventFilter

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




      


@login_required(login_url='login_admin')
def add_coupon(request):

    if request.method == 'POST':

        forms = coupon_Form(request.POST, request.FILES)

        if forms.is_valid():
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


from django.http import JsonResponse
from .filters import *

class get_coupon(ListAPIView):
    queryset = coupon.objects.all()
    serializer_class = coupon_serializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'  # enables filtering on all fields
    filterset_class = couponFilter  # enables filtering on all fields



@login_required(login_url='login_admin')
def add_event(request):

    if request.method == 'POST':

        forms = event_Form(request.POST, request.FILES)

        if forms.is_valid():
            forms.save()
            return redirect('list_event')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_event.html', context)
    
    else:

        forms = event_Form()

        context = {
            'form': forms
        }
        return render(request, 'add_event.html', context)

        

@login_required(login_url='login_admin')
def update_event(request, event_id):

    if request.method == 'POST':

        instance = event.objects.get(id=event_id)

        forms = event_Form(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_event')
        else:
            print(forms.errors)
    
    else:

        instance = event.objects.get(id=event_id)
        forms = event_Form(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_event.html', context)

        

@login_required(login_url='login_admin')
def delete_event(request, event_id):

    event.objects.get(id=event_id).delete()

    return HttpResponseRedirect(reverse('list_event'))


@login_required(login_url='login_admin')
def list_event(request):

    data = event.objects.all()
    context = {
        'data': data
    }
    return render(request, 'list_event.html', context)


from django.http import JsonResponse

class get_event(ListAPIView):
    queryset = event.objects.all()
    serializer_class = event_serializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventFilter  # enables filtering on all fields


    def get_queryset(self):
        return event.objects.filter(start_date__gte=now()).order_by('start_date')


def add_testimonials(request):
    
    if request.method == "POST":

        forms = testimonials_Form(request.POST, request.FILES)

        if forms.is_valid():
            forms.save()
            return redirect('list_testimonials')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_testimonials.html', context)
    
    else:

        # create first row using admin then editing only

        

        return render(request, 'add_testimonials.html', { 'form' : testimonials_Form()})

def update_testimonials(request, testimonials_id):
    
    instance = testimonials.objects.get(id = testimonials_id)

    if request.method == "POST":

        forms = testimonials_Form(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_testimonials')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_testimonials.html', context)

    
    else:

        # create first row using admin then editing only

        forms = testimonials_Form(instance=instance)
                
        context = {
            'form': forms
        }
        
        return render(request, 'add_testimonials.html', context)


def list_testimonials(request):

    data = testimonials.objects.all()

    return render(request, 'list_testimonials.html', {'data' : data})


def delete_testimonials(request, testimonials_id):

    data = testimonials.objects.get(id = testimonials_id).delete()

    return redirect('list_testimonials')



from django.views import View


class get_testimonials(ListAPIView):
    queryset = testimonials.objects.all()
    serializer_class = testimonials_serializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'  # enables filtering on all fields




def add_product_category(request):
    
    if request.method == "POST":

        forms = product_category_Form(request.POST, request.FILES)

        if forms.is_valid():
            forms.save()
            return redirect('list_product_category')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_product_category.html', context)


    else:

        # create first row using admin then editing only

        

        return render(request, 'add_product_category.html', { 'form' : product_category_Form()})

def update_product_category(request, product_category_id):
    
    instance = product_category.objects.get(id = product_category_id)

    if request.method == "POST":

        forms = product_category_Form(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_product_category')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_product_category.html', context)
    
    else:

        # create first row using admin then editing only

        forms = product_category_Form(instance=instance)

        return render(request, 'add_product_category.html', {'form' : forms})


def list_product_category(request):

    data = product_category.objects.all()

    return render(request, 'list_product_category.html', {'data' : data})


def delete_product_category(request, product_category_id):

    data = product_category.objects.get(id = product_category_id).delete()

    return redirect('list_product_category')


from django.views import View



class get_product_category(ListAPIView):
    queryset = product_category.objects.all()
    serializer_class = product_category_serializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = product_categoryFilter
    


from rest_framework.response import Response

from rest_framework.views import APIView

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

 
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import JSONParser



class customer_address_ViewSet(ModelViewSet):

    permission_classes = [IsCustomer]

    serializer_class = customer_address_serializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsCustomer]  # Or use IsAuthenticated if needed

    def get_queryset(self):
        return customer_address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        

def update_customer_address(request, customer_address_id):
    
    instance = customer_address.objects.get(id = customer_address_id)

    if request.method == "POST":

        forms = customer_address_Form(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_customer_address')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_customer_address.html', context)
    
    else:

        # create first row using admin then editing only

        forms = customer_address_Form(instance=instance)
        
        context = {
                'form': forms
            }

        return render(request, 'add_customer_address.html', context)


def list_customer_address(request):

    data = customer_address.objects.all()

    return render(request, 'list_customer_address.html', {'data' : data})


def delete_customer_address(request, customer_address_id):

    data = customer_address.objects.get(id = customer_address_id).delete()

    return redirect('list_customer_address')


from django.views import View



class get_customer_address(ListAPIView):
    queryset = customer_address.objects.all()
    serializer_class = customer_address_serializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'  # enables filtering on all fields

    def get_queryset(self):
        return customer_address.objects.filter(user=self.request.user)



@login_required(login_url='login_admin')
def add_product(request):

    if request.method == 'POST':

        forms = product_Form(request.POST, request.FILES)

        if forms.is_valid():
            forms.save()
            return redirect('list_product')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }
            return render(request, 'add_product.html', context)
    
    else:

        forms = product_Form()

        context = {
            'form': forms
        }
        return render(request, 'add_product.html', context)

        

@login_required(login_url='login_admin')
def update_product(request, product_id):

    if request.method == 'POST':

        instance = product.objects.get(id=product_id)

        forms = product_Form(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_product')
        else:
            print(forms.errors)
    
    else:

        instance = product.objects.get(id=product_id)
        forms = product_Form(instance=instance)

        context = {
            'form': forms
        }
        return render(request, 'add_product.html', context)

        

@login_required(login_url='login_admin')
def delete_product(request, product_id):

    product.objects.get(id=product_id).delete()

    return HttpResponseRedirect(reverse('list_product'))


@login_required(login_url='login_admin')
def list_product(request):

    data = product.objects.all()
    context = {
        'data': data
    }
    return render(request, 'list_product.html', context)


from django.http import JsonResponse


class get_product(ListAPIView):
    queryset = product.objects.all()
    serializer_class = product_serializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'  # enables filtering on all fields
    filterset_class = productFilter  # enables filtering on all fields





def add_home_banner(request):
    
    if request.method == "POST":

        forms = home_banner_Form(request.POST, request.FILES)

        if forms.is_valid():
            forms.save()
            return redirect('list_home_banner')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }

            return render(request, 'add_home_banner.html', context)
    
    else:

        # create first row using admin then editing only

        

        return render(request, 'add_home_banner.html', { 'form' : home_banner_Form()})

def update_home_banner(request, home_banner_id):
    
    instance = home_banner.objects.get(id = home_banner_id)

    if request.method == "POST":


        instance = home_banner.objects.get(id=home_banner_id)

        forms = home_banner_Form(request.POST, request.FILES, instance=instance)

        if forms.is_valid():
            forms.save()
            return redirect('list_home_banner')
        else:
            print(forms.errors)
            context = {
                'form': forms
            }

            return render(request, 'add_home_banner.html', context)

    
    else:

        # create first row using admin then editing only

        forms = home_banner_Form(instance=instance)
                
        context = {
            'form': forms
        }

        return render(request, 'add_home_banner.html', context)


def list_home_banner(request):

    data = home_banner.objects.all()

    return render(request, 'list_home_banner.html', {'data' : data})


def delete_home_banner(request, home_banner_id):

    data = home_banner.objects.get(id = home_banner_id).delete()

    return redirect('list_home_banner')


from django.views import View

def get_home_banner(request):
  
    data = home_banner.objects.all()  # Assuming home_banner is the model name


    serialized_data = HomeBannerSerializer(data, many=True, context={'request': request}).data
    return JsonResponse({"data": serialized_data}, status=200)


from rest_framework import status


from rest_framework import viewsets


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


from users.permissions import *

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