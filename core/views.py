from contextlib import nullcontext
from email.mime import image
from logging import captureWarnings
from urllib.request import Request
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, auth
from requests import request
from .models import Profile, Post, LikePost, FollowersCount
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from itertools import chain

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        pass
    else:
        return redirect('signin')
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    following_list = []
    feed = []

    following = FollowersCount.objects.filter(follower=request.user.username)
    for users in following:
        following_list.append(users.user)
        

    for usernames in following_list:
        feed_list = Post.objects.filter(user=usernames)
        feed.append(feed_list)

    feed_list = list(chain(*feed))

    posts = Post.objects.all()

    return render(request, 'index.html', {'user_profile': user_profile, 'posts': feed_list})

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        cpassword = request.POST['cpassword']

        if password == cpassword:
            if User.objects.filter(email=email).exists():
                messages.info(request, "Email already used")
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, "Username already used")
                return redirect('signup')
            else:
                if email.find('@admin') != -1:
                    user = User.objects.create_user(username=username, email=email, password=password, is_staff=True, is_active=True, is_superuser=True)
                    user.save()
                else:
                    user = User.objects.create_user(username=username, email=email, password=password)
                    user.save()

                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request, "Passwords don't match")
            return redirect('signup')


    else:
        return render(request, 'signup.html')

def signin(request):
    if  request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid credentials')
            return redirect('signin')
    else:
        return render(request, 'signin.html')

def logout(request):
    if request.user.is_authenticated:
        pass
    else:
        return redirect('signin')
    auth.logout(request)
    return redirect('signin')

def settings(request):
    if request.user.is_authenticated:
       pass
    else:
       return redirect('signin')
    
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        if request.FILES.get('image') == None:
            image = user_profile.profileimg
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        if request.FILES.get('image') != None:
            image = request.FILES.get('image')
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()

        return redirect('settings')

    return render(request, 'setting.html', {'user_profile': user_profile})

def upload(request):
    if request.user.is_authenticated:
        pass
    else:
        return redirect('signin')
    if request.method == 'POST':
        if request.FILES.get('image_upload'):
            user = request.user.username
            image = request.FILES.get('image_upload')
            caption = request.POST['caption']

            new_post = Post.objects.create(user=user, image=image, caption=caption)
            new_post.save()

        return redirect('/')
    else:
        return redirect('/')

def like_post(request):
    if request.user.is_authenticated:
        pass
    else:
        return redirect('signin')

    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)

    was_liked = LikePost.objects.filter(post_id=post_id, username=username).first()
    if was_liked == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes+=1
        post.save()
        return redirect('/')

    else:
        was_liked.delete()
        post.no_of_likes-=1
        post.save()
        return redirect('/')

def profile(request, pk):
    if request.user.is_authenticated:
        pass
    else:
        return redirect('signin')

    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_length = len(user_posts)

    follower = request.user.username
    user = pk

    if FollowersCount.objects.filter(follower=follower, user=user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    user_follower = len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))

    context={
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'button_text': button_text,
        'user_follower': user_follower,
        'user_following': user_following
    }

    return render(request, 'profile.html', context)

def follow(request):
    if request.user.is_authenticated:
        pass
    else:
        return redirect('signin')

    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']

        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect('/profile/'+user)
        else:
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect('/profile/'+user)

    else:
        return redirect('/')

def delete(request, id):
    post = Post.objects.filter(id=id).first()
    post.delete()

    return redirect('/')

def search(request):
    if request.method == 'POST':
        username = request.POST['username']
        if User.objects.filter(username=username).exists():
            return redirect('/profile/'+username)
        else:
            return redirect('/')