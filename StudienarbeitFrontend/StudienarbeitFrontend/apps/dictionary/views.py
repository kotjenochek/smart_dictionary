import os
from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from imageai.Detection import ObjectDetection
from googletrans import Translator
from gtts import gTTS

from StudienarbeitFrontend import settings
from .models import User, Learnword, Training, UnsavedLearnword, Picture


def index(request):
    user_list = User.objects.order_by('-xp')
    logged_user = get_logged_user(request.COOKIES)

    return render(request, 'dictionary/homepage.html', {'user_list': user_list, 'logged_user': logged_user})


def change_recognized_object(request, o_id, language):
    word = request.POST['word']
    unsaved_learnword = UnsavedLearnword.objects.get(id=o_id)

    if language == 'de':
        unsaved_learnword.german_word = word
        russian_word = translate_from_german_to_russian(word)
        unsaved_learnword.russian_word = russian_word
        unsaved_learnword.save()
    elif language == 'ru':
        unsaved_learnword.russian_word = word
        german_word = translate_from_russian_to_german(word)
        unsaved_learnword.german_word = german_word
        unsaved_learnword.save()

    logged_user = get_logged_user(request.COOKIES)
    unsaved_recognized_objects = UnsavedLearnword.objects.order_by('german_word')
    return render(request, 'dictionary/show_pictures_with_recognized_objects.html',
                  {'logged_user': logged_user, 'unsaved_recognized_objects': unsaved_recognized_objects})


def edit_recognized_object(request, language, o_id):
    logged_user = get_logged_user(request.COOKIES)
    unsaved_recognized_objects = UnsavedLearnword.objects.order_by('german_word')
    return render(request, 'dictionary/show_pictures_with_recognized_objects.html',
                  {'language': language, 'object_id': o_id, 'logged_user': logged_user,
                   'unsaved_recognized_objects': unsaved_recognized_objects})


def select_pictures_to_upload(request):
    logged_user = get_logged_user(request.COOKIES)
    response = render(request, 'dictionary/load_picture.html', {"logged_user": logged_user})
    UnsavedLearnword.objects.all().delete()
    if 'image_was_edit' in request.COOKIES:
        response.delete_cookie('image_was_edit')

    return response


def show_pictures_with_recognized_objects(request):
    logged_user = get_logged_user(request.COOKIES)
    pictures_to_recognize_path = settings.MEDIA_ROOT
    object_recognition_library_path = os.path.join(settings.MEDIA_ROOT, 'libraries_for_object_recognition')
    print()

    if 'image_was_edit' not in request.COOKIES:
        UnsavedLearnword.objects.all().delete()
        images_list = []
        for file in request.FILES.getlist("files"):
            Picture.objects.create(image=file)
            images_list.append(file)
        recognize_images(images_list, pictures_to_recognize_path, object_recognition_library_path, logged_user)
        unsaved_recognized_objects = UnsavedLearnword.objects.order_by('german_word')
        response = render(request, 'dictionary/show_pictures_with_recognized_objects.html',
                          {'logged_user': logged_user, 'unsaved_recognized_objects': unsaved_recognized_objects})
        response.set_cookie('image_was_edit', 'True')
        return response

    unsaved_recognized_objects = UnsavedLearnword.objects.order_by('german_word')
    return render(request, 'dictionary/show_pictures_with_recognized_objects.html',
                  {'logged_user': logged_user, 'unsaved_recognized_objects': unsaved_recognized_objects})


def recognize_images(images_list, pictures_to_recognize_path, object_recognition_library_path, logged_user):
    for image in images_list:
        image_url = os.path.join(pictures_to_recognize_path, str(image))
        detector = ObjectDetection()
        detector.setModelTypeAsRetinaNet()
        detector.setModelPath(os.path.join(object_recognition_library_path,
                                           "resnet50_coco_best_v2.0.1.h5"))
        detector.loadModel(detection_speed="fastest")

        try:
            recognized_object_list = detector.detectObjectsFromImage(
                input_image=image_url,
                output_image_path=image_url,
                minimum_percentage_probability=50,
                display_percentage_probability=False,
                display_object_name=False
            )
            print(image_url)
            create_unsaved_learnwords(recognized_object_list, image, logged_user.id)
        except:
            create_unsaved_learnwords(None, image, logged_user.id)


def create_unsaved_learnwords(recognized_object_list, image_url, logged_user_id):
    recognized_objects_name = []

    if recognized_object_list:
        for eachObject in recognized_object_list:
            object_name = eachObject["name"]
            if object_name not in recognized_objects_name:
                recognized_objects_name.append(object_name)

    if len(recognized_objects_name) == 0:
        recognized_objects_name.append('nothing is detected')

    for recognized_object_name in recognized_objects_name:
        german_word = translate_to_german(recognized_object_name)
        russian_word = translate_to_russian(recognized_object_name)
        print("Create UnsavedLearnwords with ...", str(image_url))
        UnsavedLearnword.objects.create(User_id=logged_user_id, german_word=german_word,
                                        russian_word=russian_word, image=image_url)


def translate_from_russian_to_german(recognized_object_name):
    translator = Translator()
    translation_de = translator.translate(recognized_object_name, dest='de', src='ru')
    german_word = translation_de.text
    return german_word


def translate_from_german_to_russian(recognized_object_name):
    translator = Translator()
    translation_de = translator.translate(recognized_object_name, dest='ru', src='de')
    german_word = translation_de.text
    return german_word


def translate_to_german(recognized_object_name):
    translator = Translator()
    translation_de = translator.translate(recognized_object_name, dest='de')
    german_word = translation_de.text
    return german_word


def translate_to_russian(recognized_object_name):
    translator = Translator()
    translation_ru = translator.translate(recognized_object_name, dest='ru')
    return translation_ru.text


def log_in(request, user_id):
    user_list = User.objects.order_by('name')

    try:
        logged_user = User.objects.get(id=user_id)
        response = render(request, 'dictionary/homepage.html', {'user_list': user_list, 'logged_user': logged_user})
        response.set_cookie('logged_user_id', logged_user.id)
    except:
        raise Http404("User was not found")

    return response


def remove_user(request, u_id):
    user = User.objects.get(id=u_id)
    user.image.delete()
    User.delete(user)
    response = redirect(reverse("dictionary:index"))
    response.delete_cookie('logged_user_id')

    return response


def create_user(request):
    return render(request, 'dictionary/create_user.html')


def add_user(request):
    name = request.POST['name']

    if User.objects.filter(name=name).exists():
        messages.warning(request, 'A user with this name already exists', extra_tags='alert')
        return redirect(reverse("dictionary:create_user"))
    else:
        try:
            if request.FILES['image']:
                image = request.FILES['image']
                User.objects.create(name=name, image=image)
        except:
            User.objects.create(name=name, image=None)

        logged_user = User.objects.get(name=name)
        response = redirect(reverse("dictionary:index"))
        response.set_cookie("logged_user_id", logged_user.id)
        return response


def show_dictionary(request):
    logged_user = get_logged_user(request.COOKIES)
    words_list = get_user_words(logged_user)

    return render(request, 'dictionary/dictionary.html',
                  {'words_list': words_list, 'logged_user': logged_user})


def choosed_method(request, method_nr):
    logged_user = get_logged_user(request.COOKIES)
    words_list = get_user_words(logged_user)
    word = None

    if len(words_list) != 0:
        word = words_list[0]

    return render(request, 'dictionary/learn.html', {'word': word, 'logged_user': logged_user, 'method_nr': method_nr})


def show_result_by_knowing(request, w_id, method_nr):
    word = Learnword.objects.get(id=w_id)
    logged_user = get_logged_user(request.COOKIES)
    return render(request, 'dictionary/show_result_by_knowing.html',
                  {'logged_user': logged_user, 'word': word, 'method_nr': method_nr})


def show_result_by_unknowing(request, w_id, method_nr):
    word = Learnword.objects.get(id=w_id)
    logged_user = get_logged_user(request.COOKIES)
    return render(request, 'dictionary/show_result_by_unknowing.html',
                  {'logged_user': logged_user, 'word': word, 'method_nr': method_nr})


def show_result_by_knowing2(request, w_id, method_nr):
    try:
        word = Training.objects.get(id=w_id)
    except:
        word = Training.objects.get(learnword_id=w_id)

    logged_user = get_logged_user(request.COOKIES)
    return render(request, 'dictionary/show_result_by_knowing2.html',
                  {'logged_user': logged_user, 'word': word, 'method_nr': method_nr})


def show_result_by_unknowing2(request, w_id, method_nr):
    try:
        word = Training.objects.get(id=w_id)
    except:
        word = Training.objects.get(learnword_id=w_id)

    logged_user = get_logged_user(request.COOKIES)
    return render(request, 'dictionary/show_result_by_unknowing2.html',
                  {'logged_user': logged_user, 'word': word, 'method_nr': method_nr})


def answer_is_given(request, w_id, xp, method_nr):
    logged_user_id = get_logged_user_id(request.COOKIES)
    logged_user = User.objects.get(id=logged_user_id)
    logged_user.xp = logged_user.xp + xp
    logged_user.save()

    word_list = logged_user.learnword_set.order_by('german_word')
    word = Learnword.objects.get(id=w_id)
    w_index = list(word_list).index(word) + 2
    print(w_index)

    if w_index >= len(word_list):
        Training.objects.all().delete()
        for w in word_list:
            logged_user.training_set.create(german_word=w.german_word, russian_word=w.russian_word, image=w.image,
                                            german_pronunciation=w.german_pronunciation,
                                            russian_pronunciation=w.russian_pronunciation,
                                            learnword_id=w.id, counter=0)
        return render(request, 'dictionary/learn2.html',
                      {'logged_user': logged_user, 'word': word, 'method_nr': method_nr})
    else:
        word = word_list[w_index]
        return render(request, 'dictionary/learn.html',
                      {'logged_user': logged_user, 'word': word, 'method_nr': method_nr})


def answer_is_given2(request, w_id, xp, method_nr):
    logged_user_id = get_logged_user_id(request.COOKIES)
    logged_user = User.objects.get(id=logged_user_id)
    logged_user.xp = logged_user.xp + xp
    logged_user.save()

    try:
        training_word = Training.objects.get(id=w_id)
        training_list = logged_user.training_set.order_by('german_word')
        w_index = list(training_list).index(training_word) + 2

        if xp == 2:
            training_word.counter = training_word.counter + 1
            training_word.save()

            if training_word.counter == 3:
                w_index = list(training_list).index(training_word)
                Training.delete(training_word)
                print('Word was learned')
                training_list = logged_user.training_set.order_by('german_word')


        if w_index < len(training_list):
            word = training_list[w_index]
            print(w_index)
        else:
            if Training.objects.exists():
                training_list = list(logged_user.training_set.order_by('german_word'))
                word = training_list[0]
            else:
                return render(request, 'dictionary/end_learning.html', {'logged_user': logged_user})
    except (ValueError, IndexError):
        print("Help, I am dead :(")

    return render(request, 'dictionary/learn2.html',
                  {'logged_user': logged_user, 'word': word, 'method_nr': method_nr})


def start_learning(request):
    logged_user = get_logged_user(request.COOKIES)
    return render(request, 'dictionary/start_learning.html', {'logged_user': logged_user})


def get_logged_user_id(cookies):
    if 'logged_user_id' in cookies:
        logged_user_id = cookies['logged_user_id']
    else:
        logged_user_id = ''

    return logged_user_id


def get_logged_user(cookies):
    if 'logged_user_id' in cookies:
        logged_user_id = cookies['logged_user_id']
        logged_user = User.objects.get(id=logged_user_id)
    else:
        logged_user = None

    return logged_user


def get_learning_dictionary(cookies):
    if 'learning_dictionary' in cookies:
        learning_dictionary = cookies['learning_dictionary']
    else:
        learning_dictionary = {}

    return learning_dictionary


def get_user_words(logged_user):
    if (logged_user is None):
        words_list = None
    else:
        words_list = logged_user.learnword_set.order_by('german_word')

    return words_list


def remove_picture_from_dictionary(request, w_id):
    word_list = Learnword.objects.order_by('german_word')
    learnword = Learnword.objects.get(id=w_id)
    delete_object_image_and_audio_if_not_need(word_list, learnword, "Learnword")
    return redirect(reverse("dictionary:show_dictionary"))


# Delete object and image if there is not other words in dictionary that use the same image
def delete_object_image_and_audio_if_not_need(word_list, object, objects_class):
    need_image = False
    for l in word_list:
        if l.image == object.image and l.id != object.id:
            need_image = True
            break
    if not need_image:
        object.image.delete()

    if objects_class == "Learnword":
        need_audio = False
        for l in word_list:
            if l.german_pronunciation == object.german_pronunciation and l.id != object.id:
                need_audio = True
                break
        if not need_audio:
            object.german_pronunciation.delete()
            object.russian_pronunciation.delete()
        Learnword.delete(object)
    elif objects_class == "UnsavedLearnword":
        UnsavedLearnword.delete(object)


def remove_recognized_object(request, o_id):
    logged_user = get_logged_user(request.COOKIES)
    word_list = UnsavedLearnword.objects.order_by('german_word')
    unsaved_object = UnsavedLearnword.objects.get(id=o_id)
    delete_object_image_and_audio_if_not_need(word_list, unsaved_object, "UnsavedLearnword")
    unsaved_recognized_objects = UnsavedLearnword.objects.order_by('german_word')

    return render(request, 'dictionary/show_pictures_with_recognized_objects.html',
                  {'logged_user': logged_user, 'unsaved_recognized_objects': unsaved_recognized_objects})


def save_new_words(request):
    logged_user = get_logged_user(request.COOKIES)
    for word in UnsavedLearnword.objects.order_by('german_word'):
        german_audio = save_and_get_audio(word.german_word, 'de')
        russian_audio = save_and_get_audio(word.russian_word, 'ru')
        Learnword.objects.create(User_id=logged_user.id, german_word=word.german_word, russian_word=word.russian_word,
                                 image=word.image, german_pronunciation=german_audio, russian_pronunciation=russian_audio)
    UnsavedLearnword.objects.all().delete()
    response = render(request, 'dictionary/new_words_are_successefuly_saved.html', {'logged_user': logged_user})
    response.delete_cookie('image_was_edit')
    return response


def save_and_get_audio(text, language):
    path = settings.MEDIA_ROOT + '\\Audio\\' + language + '\\' + text + '.mp3'
    audio = gTTS(text=text, lang=language, slow=False)
    audio.save(path)
    return path
