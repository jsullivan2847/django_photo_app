from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Profile, Photo, User
from .forms import ProfileForm, PhotoForm
import uuid, boto3

S3_BASE_URL = 'https://s3.us-east-1.amazonaws.com/'
BUCKET = 'django-photo-app-2847'

def Home(request):
    photo_list = Photo.objects.all()
    photo_form = PhotoForm()
    if request.user.is_authenticated:
        current_user  = request.user
        profile = Profile.objects.get(user = current_user.id)
        return render(request,'home.html',
         {'profile': profile, 
         'photo_form': photo_form, 
         'photo_list': photo_list,})
    else: return(render(request, 'home.html'))


def signup(request):
    error = ''
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile_form')
        else:
            error = "Invalid sign up, try again"
    form = UserCreationForm()
    context = {'form': form, 'error': error}
    return render(request, 'registration/signup.html', context)


@login_required
def AddProfileForm(request):
    form = ProfileForm()
    return render(request,'main_app/profile_form.html', {'form': form})

@login_required
def AddProfile(request):
    form = ProfileForm(request.POST)
    if form.is_valid():
        profile = form.save(commit=False)
        profile.user_id = request.user.id
        profile.save()
    return redirect('/')

#to post
@login_required
def PostPhoto(request, profile_id):
        photo_file = request.FILES.get('photo_file', None)
        profile = Profile.objects.get(id = profile_id)
        if photo_file:
            S3 = boto3.client('s3')
            key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        try: 
            S3.upload_fileobj(photo_file, BUCKET, key)
            url = f"{S3_BASE_URL}{BUCKET}/{key}"
            photo = Photo(photo_url = url, user = profile)
            photo.save()
            # profile = Profile.objects.get(id = profile_id)
            # profile.save()
        except Exception as error:
            print('error uploading photo', error)
        return redirect('home')

#to change profile photo
@login_required
def AddProfilePhoto(request, profile_id):
    photo_file = request.FILES.get('photo_file', None)
    if photo_file:
        S3 = boto3.client('s3')
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
    try: 
        S3.upload_fileobj(photo_file, BUCKET, key)
        url = f"{S3_BASE_URL}{BUCKET}/{key}"
        profile = Profile.objects.get(id = profile_id)
        profile.profile_pic = url
        profile.save()
    except Exception as error:
        print('error uploading photo', error)
    return redirect('profile_show', profile_id)

@login_required
def ProfileShow(request, profile_id):
    photos = Photo.objects.filter(user = profile_id)
    profile = Profile.objects.get(id = profile_id)
    return render(request,'main_app/profile_show.html', 
    {'profile': profile,
    'photos': photos,
    })




@login_required
def EditPhotoForm(request, photo_id):
    photo = Photo.objects.get(id = photo_id)
    form = PhotoForm()
    return render(request,'main_app/edit_photo_form.html', {'photo': photo, 'form': form})

@login_required
def PhotoUpdate(request, photo_id):
    photo = Photo.objects.get(id = photo_id)
    form = PhotoForm(request.POST, instance=photo)
    if form.is_valid():
        form.save()
        return redirect('edit_photo', photo_id)

def PhotoDelete(request, photo_id):
    photo = Photo.objects.get(id = photo_id)
    profile = Profile.objects.get(id = photo.user.id)
    if request.method == "POST":
        photo.delete()
        return render(request, "home.html", {'profile': profile})
    

@login_required
class PhotoList(ListView):
    model = Photo

# class AddPhoto(CreateView):
#     model = Photo
#     fields = '__all__'
#     success_url = '/'