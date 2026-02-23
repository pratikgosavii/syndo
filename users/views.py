from email import message
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from vendor.models import vendor_store


from .forms import *


# def login_page(request):
#     forms = LoginForm()
#     if request.method == 'POST':
#         forms = LoginForm(request.POST)
#         if forms.is_valid():
#             username = forms.cleaned_data['username']
#             password = forms.cleaned_data['password']
#             print(username)
#             print(password)
#             user = authenticate(username=username, password=password)
#             if user:
#                 login(request, user)

#                 if user.is_doctor:
#                     print('---------------------------------')
#                     print('---------------------------------')
#                     print('---------------------------------')
#                 return redirect('dashboard')
#             else:
#                 messages.error(request, 'wrong username password')
#     context = {'form': forms}
#     return render(request, 'adminLogin.html', context)

from firebase_admin import auth as firebase_auth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User  # Your custom user model


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get("idToken")
        user_type = request.data.get("user_type")
        name = request.data.get("name")
        email = request.data.get("email")

        if not id_token or not user_type:
            return Response({"error": "idToken and user_type are required"}, status=400)

        try:
            if isinstance(id_token, str):
                id_token = id_token.strip()
            decoded_token = firebase_auth.verify_id_token(id_token)
            mobile = decoded_token.get("phone_number")
            uid = decoded_token.get("uid")

            if not mobile:
                return Response({"error": "Phone number not found in Firebase token"}, status=400)

            # Role flags
            role_flags = {
                "is_customer": False,
                "is_vendor": False,
            }

            if f"is_{user_type}" not in role_flags:
                return Response({"error": "Invalid user_type"}, status=400)

            user = User.objects.filter(mobile=mobile).first()
            created = False

            if user:
                # Already exists – check role
                existing_roles = [key for key, value in {
                    "customer": user.is_customer,
                    "vendor": user.is_vendor,
                }.items() if value]

                if existing_roles and user_type not in existing_roles:
                    return Response({
                        "error": f"This number is already registered as a {existing_roles[0]}. Cannot register again as {user_type}."
                    }, status=400)

                if user.firebase_uid != uid:
                    user.firebase_uid = uid
                    user.save()

            else:
                role_flags[f"is_{user_type}"] = True

                # Ensure email is unique
                if email and User.objects.filter(email=email).exists():
                    return Response({"error": "This email is already in use."}, status=400)

                user = User.objects.create(
                    mobile=mobile,
                    firebase_uid=uid,
                    first_name=name or "",
                    email=email or decoded_token.get("email", ""),
                    **role_flags
                )
                created = True

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "mobile": user.mobile,
                    "email": user.email,
                    "name": user.first_name,
                    "user_type": user_type,
                    "created": created
                }
            })

        except ValueError as e:
            print(f"Signup failed: malformed idToken - {e}")
            return Response({"error": "Malformed idToken provided."}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


from .serializer import *

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        id_token = request.data.get("idToken")
        print("-------1------------ id_token fetched", id_token)
        user_type = request.data.get("user_type")
        print("-------2------------ user_type fetched", user_type)

        if not id_token:
            print("-------3------------ id_token missing")
            return Response({"error": "idToken is required"}, status=400)

        try:
            if isinstance(id_token, str):
                id_token = id_token.strip()
            # Verify token with Firebase
            decoded_token = firebase_auth.verify_id_token(id_token)
            print("-------4------------ token verified")
            mobile = decoded_token.get("phone_number")
            print(f"-------5------------ mobile: {mobile}")
            uid = decoded_token.get("uid")
            print(f"-------6------------ uid: {uid}")

            if not mobile:
                print("-------7------------ phone number missing in token")
                return Response({"error": "Phone number not found in token"}, status=400)

            user = User.objects.filter(mobile=mobile).first()
            print(f"-------8------------ user lookup done: {bool(user)}")
            created = False
            print("-------9------------ created flag initialized")

            if user:
                print("-------10------------ user exists branch")
                if not user.is_active:
                    user.is_active = True
                    print("-------11------------ user activated")
                if user.firebase_uid != uid:
                    user.firebase_uid = uid
                    print('--------------------------------------------')
                    print(user)
                    print("-------12------------ firebase_uid updated")
                user.save()
                print("-------13------------ existing user saved")
            else:
                print("-------14------------ user create branch")
                user = User.objects.create(
                    mobile=mobile,
                    firebase_uid=uid,
                )
                print("-------15------------ user created")

                if user_type == "vendor":   
                    vendor_store.objects.create(user = user)
                    print("-------16------------ vendor_store created")
                    
                created = True
                print("-------17------------ created flag set True")

                # Set user type flags based on frontend
                if user_type == "vendor":
                    user.is_vendor = True
                    print("-------18------------ is_vendor set True")
                elif user_type == "customer":
                    user.is_customer = True
                    print("-------19------------ is_customer set True")
                user.save()
                print("-------20------------ new user saved")

            # Update device token if provided (for push notifications)
            device_token = request.data.get("device_token") or request.data.get("fcm_token")
            if device_token:
                try:
                    from .models import DeviceToken
                    DeviceToken.objects.update_or_create(
                        user=user,
                        defaults={"token": device_token.strip()}
                    )
                    print("-------21------------ device token updated/created")
                except Exception as e:
                    print(f"-------21------------ device token update failed: {e}")
                    # Don't fail login if device token update fails
            
            # Token creation
            refresh = RefreshToken.for_user(user)
            print("-------22------------ refresh token created")
            user_details = UserProfileSerializer(user).data
            print("-------23------------ user_details serialized")

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "mobile": user.mobile,
                    "is_vendor": user.is_vendor,
                    "is_customer": user.is_customer,
                    "created": created
                },
                "user_details": user_details
            }, status=201 if created else 200)
            print("-------24------------ response returned")

        except ValueError as e:
            print(f"Login failed: malformed idToken - {e}")
            return Response({"error": "Malformed idToken provided."}, status=400)
        except Exception as e:
            print(f"Login failed: {e}")
            print("-------24------------ exception path")
            return Response({"error": "Invalid or expired Firebase token."}, status=400)


from rest_framework.permissions import IsAuthenticated

class DeleteUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response(
            {"detail": "User deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
    

from .permissions import *


class UsergetView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request):
        user = request.user
        return Response({
            "name": user.first_name,
            "email": user.email,
        })

class UserUpdateView(APIView):
    permission_classes = [IsCustomer]

    def put(self, request):
        user = request.user
        name = request.data.get("name")
        email = request.data.get("email")

        updated = False

        # Do not allow name change once PAN is verified (vendor_store.is_pan_verified)
        if name:
            try:
                from vendor.models import vendor_store
                store = vendor_store.objects.filter(user=user).first()
                if store and store.is_pan_verified:
                    name = None  # ignore name update
            except Exception:
                pass
            if name:
                user.first_name = name
                updated = True

        if email:
            user.email = email
            updated = True

        if updated:
            user.save()
            return Response({"message": "Profile updated successfully."})
        else:
            return Response({"message": "No changes provided."}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    def post(self, request):
        id_token = request.data.get("idToken")
        new_password = request.data.get("new_password")

        if not id_token or not new_password:
            return Response({"error": "idToken and new_password are required"}, status=400)

        try:
            # Decode the token to get UID
            decoded = firebase_auth.verify_id_token(id_token)
            uid = decoded.get("uid")

            # Update Firebase password
            firebase_auth.update_user(uid, password=new_password)

            return Response({"message": "Password updated successfully."})

        except Exception as e:
            return Response({"error": str(e)}, status=400)
        



def  login_admin(request):

    forms = LoginForm()
    if request.method == 'POST':
        forms = LoginForm(request.POST)
        if forms.is_valid():
            mobile = forms.cleaned_data['mobile']
            password = forms.cleaned_data['password']
            print(mobile)
            print(password)
            user = authenticate(mobile=mobile, password=password)
            if user:
                login(request, user)

                if user.is_superuser:
                    print('---------------------------------')
                    print('---------------------------------')
                    print('---------------------------------')
                return redirect('dashboard')
            else:
                messages.error(request, 'wrong username password')
    context = {'form': forms}
    return render(request, 'adminLogin.html', context)


def  login_vendor(request):

    forms = LoginForm()
    if request.method == 'POST':
        forms = LoginForm(request.POST)
        if forms.is_valid():
            mobile = forms.cleaned_data['mobile']
            password = forms.cleaned_data['password']
            mobile = '+91' + mobile 
            print(mobile)
            print(password)
            user = authenticate(mobile=mobile, password=password)
            if user:
                login(request, user)

                if user.is_vendor:
                    print('---------------------------------')
                    print('---------------------------------')
                    print('---------------------------------')
                return redirect('dashboard')
            else:
                messages.error(request, 'wrong username password')
    context = {'form': forms}
    return render(request, 'vendorLogin.html', context)


def vendor_forgot_password(request):
    from django.core.mail import send_mail
    from django.conf import settings
    from django.urls import reverse
    from .forms import VendorForgotPasswordForm

    if request.method == 'POST':
        form = VendorForgotPasswordForm(request.POST)
        if form.is_valid():
            mobile = form.cleaned_data['mobile'].strip()
            lookup_mobile = '+91' + mobile
            user = User.objects.filter(mobile=lookup_mobile, is_vendor=True).first()
            if user:
                if not user.email or not user.email.strip():
                    messages.error(
                        request,
                        'No email is registered for this account. Please contact support to add your email for password reset.'
                    )
                else:
                    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)
                    reset_url = request.build_absolute_uri(
                        reverse('vendor_reset_password_confirm', kwargs={'uidb64': uidb64, 'token': token})
                    )
                    subject = 'Reset your vendor password'
                    message = (
                        f'Hello,\n\n'
                        f'You requested a password reset for your vendor account (mobile: {mobile}).\n\n'
                        f'Click the link below to set a new password:\n{reset_url}\n\n'
                        f'This link is valid for a limited time. If you did not request this, please ignore this email.\n\n'
                        f'— Svindo'
                    )
                    try:
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[user.email],
                            fail_silently=False,
                        )
                        messages.success(
                            request,
                            'If an account exists with this mobile number, we have sent password reset instructions to your registered email. Please check your inbox.'
                        )
                    except Exception as e:
                        messages.error(
                            request,
                            'We could not send the reset email. Please try again later or contact support.'
                        )
            else:
                messages.success(
                    request,
                    'If an account exists with this mobile number, we have sent password reset instructions to your registered email. Please check your inbox.'
                )
            return redirect('vendor_forgot_password')
    else:
        form = VendorForgotPasswordForm()
    return render(request, 'vendorForgotPassword.html', {'form': form})


def vendor_reset_password_confirm(request, uidb64, token):
    from .forms import VendorSetPasswordForm

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid, is_vendor=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, 'Reset link is invalid or has expired. Please request a new one.')
        return redirect('vendor_forgot_password')

    if request.method == 'POST':
        form = VendorSetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            messages.success(request, 'Your password has been set. You can now log in.')
            return redirect('login_vendor')
    else:
        form = VendorSetPasswordForm()
    return render(request, 'vendorResetPasswordConfirm.html', {'form': form, 'uidb64': uidb64, 'token': token})


# def resgister_page(request):

#     forms = registerForm()
#     if request.method == 'POST':
#         forms = registerForm(request.POST)
#         if forms.is_valid():
#             forms.save()
#             username = forms.cleaned_data['username']
#             password = forms.cleaned_data['password1']
#             user = authenticate(username=username, password=password)
#             if user:
                
#                 messages.error(request, 'user already exsist')
#                 return redirect('dashboard')
#             else:
#                 return redirect('resgister')
#         else:
#             print(forms.errors)
#     else:
#         print(forms.as_p)

#         context = {'form': forms}

#         return render(request, 'users/resgister.html', context)


def logout_page(request):
    # Determine redirect before logout (request.user is anonymous after logout)
    is_staff = getattr(request.user, 'is_staff', False) if request.user.is_authenticated else False
    is_vendor = getattr(request.user, 'is_vendor', False) if request.user.is_authenticated else False
    logout(request)
    if is_staff:
        return redirect('login_admin')
    if is_vendor:
        return redirect('login_vendor')
    return redirect('login_admin')

def user_list(request):

    data = User.objects.all()

    return render(request, 'user_list.html', { 'data' : data})

def list_user_customer(request):

    data = User.objects.filter(is_customer=True)

    return render(request, 'list_user_customer.html', { 'data' : data})

def list_user_vendor(request):

    data = User.objects.filter(is_vendor=True).select_related('user_company_profile').prefetch_related('vendor_store')

    return render(request, 'list_user_vendor.html', { 'data' : data})




from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from .serializer import UserProfileSerializer
from .models import User
from rest_framework.decorators import action


from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class UserProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @action(detail=False, methods=['get', 'put'], url_path='me')
    def me(self, request):
        user = request.user

        if request.method == 'GET':
            serializer = UserProfileSerializer(user)
            return Response(serializer.data)

        elif request.method == 'PUT':

            serializer = UserProfileSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


from django.shortcuts import render, redirect, get_object_or_404
from .forms import RoleWithModulesForm
from .models import Role

def role_create(request):
    form = RoleWithModulesForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('role_list')  # or any success URL
    return render(request, 'role_form.html', {'form': form})


def role_update(request, pk):
    role = get_object_or_404(Role, pk=pk)
    form = RoleWithModulesForm(request.POST or None, instance=role)
    if form.is_valid():
        form.save()
        return redirect('role_list')
    return render(request, 'role_form.html', {'form': form})


def role_list(request):
    roles = Role.objects.all()
    return render(request, 'role_list.html', {'roles': roles})



def assign_roles_to_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    form = UserRoleAssignForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        return redirect('user_list')  # your user list page
    return render(request, 'users/assign_roles.html', {'form': form, 'user': user})


def create_user_with_roles(request):
    form = UserCreateWithRolesForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('user_list')  # or success page
    else:
        print(form.errors)
    return render(request, 'add_user_with_roles.html', {'form': form})


from .models import DeviceToken

class RegisterDeviceTokenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token required"}, status=400)
        DeviceToken.objects.update_or_create(user=request.user, defaults={"token": token})
        return Response({"success": True})


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json

@login_required(login_url='login_admin')
def toggle_user_status(request):
    """
    Toggle user active/inactive status
    POST /users/toggle-user-status/
    Body: {"user_id": 1}
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    user_id = data.get("user_id")
    if not user_id:
        return JsonResponse({"error": "user_id is required"}, status=400)
    
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    # Toggle is_active status
    target_user.is_active = not target_user.is_active
    target_user.save()
    
    return JsonResponse({
        "success": True,
        "message": f"User {'enabled' if target_user.is_active else 'disabled'} successfully",
        "user_id": target_user.id,
        "is_active": target_user.is_active
    })


@login_required(login_url='login_admin')
def toggle_global_supplier(request):
    """
    Toggle global_supplier status for vendor
    POST /users/toggle-global-supplier/
    Body: {"user_id": 1}
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    user_id = data.get("user_id")
    if not user_id:
        return JsonResponse({"error": "user_id is required"}, status=400)
    
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    if not target_user.is_vendor:
        return JsonResponse({"error": "User is not a vendor"}, status=400)
    
    # Get vendor store
    try:
        vendor_store_obj = vendor_store.objects.get(user=target_user)
    except vendor_store.DoesNotExist:
        return JsonResponse({"error": "Vendor store not found"}, status=404)
    
    # Toggle global_supplier status
    vendor_store_obj.global_supplier = not vendor_store_obj.global_supplier
    vendor_store_obj.save()
    
    return JsonResponse({
        "success": True,
        "message": f"Vendor {'marked as' if vendor_store_obj.global_supplier else 'removed from'} global supplier",
        "user_id": target_user.id,
        "global_supplier": vendor_store_obj.global_supplier
    })


@login_required(login_url='login_admin')
def verify_vendor(request, store_id):
    """
    Show vendor verification page: submitted data + API responses, with Verify GST / Verify Bank buttons.
    """
    store = get_object_or_404(vendor_store, pk=store_id)
    user = store.user
    import json
    gstin_response_json = json.dumps(store.gstin_response_data, indent=2, default=str) if store.gstin_response_data else ""
    bank_response_json = json.dumps(store.bank_response_data, indent=2, default=str) if store.bank_response_data else ""
    return render(request, 'verify_vendor.html', {
        'store': store,
        'user': user,
        'gstin_response_json': gstin_response_json,
        'bank_response_json': bank_response_json,
    })


@login_required(login_url='login_admin')
def verify_vendor_gst(request):
    """POST: set is_gstin_verified=True for the given store_id."""
    if request.method != 'POST':
        return redirect('list_user_vendor')
    from django.utils import timezone
    store_id = request.POST.get('store_id')
    if not store_id:
        messages.error(request, 'Store ID is required.')
        return redirect('list_user_vendor')
    store = get_object_or_404(vendor_store, pk=store_id)
    store.is_gstin_verified = True
    store.gstin_verified_at = timezone.now()
    store.save(update_fields=['is_gstin_verified', 'gstin_verified_at'])
    messages.success(request, 'GST verified for this vendor.')
    return redirect('verify_vendor', store_id=store.id)


@login_required(login_url='login_admin')
def verify_vendor_bank(request):
    """POST: set is_bank_verified=True for the given store_id."""
    if request.method != 'POST':
        return redirect('list_user_vendor')
    from django.utils import timezone
    store_id = request.POST.get('store_id')
    if not store_id:
        messages.error(request, 'Store ID is required.')
        return redirect('list_user_vendor')
    store = get_object_or_404(vendor_store, pk=store_id)
    store.is_bank_verified = True
    store.bank_verified_at = timezone.now()
    store.save(update_fields=['is_bank_verified', 'bank_verified_at'])
    messages.success(request, 'Bank verified for this vendor.')
    return redirect('verify_vendor', store_id=store.id)