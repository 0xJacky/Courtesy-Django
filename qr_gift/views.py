from django.shortcuts import render
from django.http import HttpResponse
from django.db import IntegrityError
from django.shortcuts import render_to_response
from django.contrib import auth
from django import forms
from django.core.exceptions import *
import django.utils.timezone as timezone

from .models import *
import re
import json
import hashlib
from wsgiref.util import FileWrapper
from os.path import join as jn
import zipfile
import StringIO
import time
import Image
import datetime

SITE_ADDR="http://10.1.0.2222:8000/"

#######################################################
################## USER PART #######################
#######################################################

def login(request,post_data,ret):
    #TODO:is logined
    #  if request.user.is_authenticated():
        #  ret['error']=408
        #  return ret
    try:
        req = post_data["account"]

        user = auth.authenticate(username=req['email'], password=req['pwd'])
        if user is None:
            ret['error']=406
        if ret['error']==0 and not user.is_active:
            ret['error']=407
        else:
            auth.login(request, user)
        #  um=UserModel.objects.get(user_ptr_id=request.user.id)
        #  um.last_login=timezone.now
        #  um.save()

    except KeyError as e:
        ret['error']=401
        ret["field"]=str(e)[1:-1]
    except AttributeError as e:
        if ret['error']!=406:
            ret['error']=406
            ret["field"]=str(e)[1:-1]
        #  ret['user_model']=UserModel.objects.get(user_ptr_id=user.id).toDict()
    #  return ret
    return ret

def register(request,post_data,ret):
    req=post_data["account"]
    try:
        user = UserModel.objects.create_user(
                                         username=req['email'],
                                         email=req['email'],
                                         )
        user.set_password(req['pwd'])
        user.nick=req["email"].split("@")[0]
        user.save()

        user = auth.authenticate(username=req['email'], password=req['pwd'])
        auth.login(request, user)
    except IntegrityError as e:
        ret['error']=405
        ret['field']=str(e).replace("username","email").split(" ")[1]
    #  except Exception:
        #  ret['error']=404


    return ret

def logout(request,post_data,ret):
    if not request.user.is_authenticated():
        ret["error"]=403
    else:
        try:
            auth.logout(request)
        except Exception:
            ret['error']=404

    return ret

def user_info(request,post_data,ret):
    if not request.user.is_authenticated():
        ret["error"]=403
    else:
        ret["account_info"]=UserModel.objects.get(user_ptr_id=request.user.id).toDict()
        ret["account_info"]["has_profile"] = True;
    return ret

def user_edit_profile(request,post_data,ret):
    try:
        if not request.user.is_authenticated():
            ret["error"]=403
        else:
            profile=post_data["profile"]
            user_model=UserModel.objects.get(user_ptr_id=request.user.id)
            user_model.nick=profile["nick"]
            #TODO:
            #  user_model.avatar=profile["avatar"]
            user_model.mobile=profile["mobile"]
            user_model.birthday=profile["birthday"]
            user_model.gender=profile["gender"]
            user_model.detailed_info=profile["introduction"]
            user_model.province=profile["province"]
            user_model.city=profile["city"]
            user_model.area=profile["area"]
            #  user_model.constellation=profile["constellation"]
            user_model.save()

    except KeyError as e:
        ret['error']=401
        ret["field"]=str(e)[1:-1]

    return ret


#######################################################
################## QR_CODE PART #######################
#######################################################
def qr_query(request,post_data,ret):
    qr_id=post_data["id"]
    try:
        qr_model=QRCodeModel.objects.get(unique_id=qr_id)
    except ( ValueError,ObjectDoesNotExist ):
        ret["error"]=423
        return ret
    ret["qr_info"]=qr_model.toDict()
    qr_model.scan_count=qr_model.scan_count+1
    if qr_model.is_recorded==True:
        card=qr_model.card_token
        ret["card_info"]=card.toDict()
        if request.user.email!=card.author.email:
            card.view_count=card.view_count+1

    return ret

def card_query(request,post_data,ret):
    try:
        card=CardModel.objects.get(token=post_data["token"])
    except ( ValueError,ObjectDoesNotExist ):
        ret["error"]=423
        return ret
    ##TODO
    if card.banned:
        ret["error"]=426
        return ret
    ret["card_info"]=card.toDict()
    return ret
def card_edit(request,post_data,ret):
    if not request.user.is_authenticated():
        ret["error"]=403
        return ret
    card_info=post_data["card_info"]
    try:
        card=CardModel.objects.get(token=post_data["token"])
    except ( ValueError,ObjectDoesNotExist ):
        ret["error"]=423
        return ret
    ##TODO
    card.author=UserModel.objects.get(user_ptr_id=request.user.id)
    if request.user.email!=card.author.email:
        ret["error"]=425
        return ret
    if card.banned:
        ret["error"]=426
        return ret
    card.local_template=card_info["local_template"]
    card.is_public=card_info["is_public"]
    card.is_editable=card_info["is_editable"]

    card.visible_at=card_info["visible_at"]
    card.save()
    ret["card_info"]=card.toDict()
    return ret

def card_create(request,post_data,ret):
    if not request.user.is_authenticated():
        ret["error"]=403
        return ret
    card_info=post_data["card_info"]
    qr_code=QRCodeModel.objects.get(unique_id=post_data["qr_id"])
    if qr_code.is_recorded:
        ret["error"]=424
        return ret

    new_card=CardModel()
    new_card.author=UserModel.objects.get(user_ptr_id=request.user.id)
    new_card.local_template=card_info["local_template"]
    new_card.is_public=card_info["is_public"]
    new_card.is_editable=card_info["is_editable"]
    new_card.token=hashlib.md5(post_data["qr_id"]).hexdigest()
    new_card.visible_at=card_info["visible_at"]
    new_card.save()
    qr_code.is_recorded=True
    qr_code.recorded_at=str(datetime.datetime.now())
    qr_code.card_token=new_card
    qr_code.save()
    ret["card_info"]=new_card.toDict()
    return ret



#######################################################
################## UPLOAD PART ########################
#######################################################

def handle_uploaded_file(file,md5_str,path):
    m2=hashlib.md5(file.name.encode("utf-8")+md5_str)
    file_type=file.name.split('.')[1]
    des_path=jn("qr_gift","static",path,m2.hexdigest()+"."+file_type)
    destination = open(des_path , 'wb+')
    for chunk in file.chunks():
        destination.write(chunk)
    destination.close()
    return m2.hexdigest(),des_path,file_type

class UserAvatarUpload(object):
    def __init__(self,request,ret):
        self.request=request
        self.ret=ret
    class UploadForm(forms.Form):
        avatar=forms.ImageField(required=True)

    def upload(self,uf):
        [id_md5,server_path,kind]=handle_uploaded_file(self.request.FILES['avatar'],str(time.time()),"avatar")
        url_path=server_path[7:]
        img=Image.open(server_path)
        res=CommonResourceModel(id_md5=id_md5)
        res.save()
        self.ret["id"]=id_md5
        for size in [300,150,60]:
            img.thumbnail((size,size),Image.ANTIALIAS)
            save_to_path=server_path[:-4]+"_"+str(size)+".png"
            res=CommonResourceModel(id_md5=id_md5+"_"+str(size)+".png")
            res.save()
            #  self.ret[str(size)+"px"]={"id_md5":id_md5+".png"}
            img.save(save_to_path,"png")
            if size==300:
                um=UserModel.objects.get(user_ptr_id=self.request.user.id)
                um.avatar=res
                um.save()

class QRStyleUpload(object):
    def __init__(self,request,ret):
        self.request=request
        self.ret=ret
    class UploadForm(forms.Form):
        name = forms.CharField(required=True)

        style_border_binary=forms.FileField(required=False)
        style_center_binary=forms.FileField(required=False)
        style_script=forms.FileField(required=True)
    def upload(self,uf):
        name = uf.cleaned_data['name']
        try:
            model=QRStyleModel(name=name)
            sysarg=[]
            if self.request.FILES.has_key('style_border_binary'):
                file_id,file_path,kind=handle_uploaded_file(self.request.FILES['style_border_binary'],name,jn("qr_template","border"))
                res1=CommonResourceModel(id_md5=file_id,kind=kind)
                res1.save()
                model.style_border_binary=res1
                sysarg.append(file_id)

            if self.request.FILES.has_key('style_center_binary'):
                file_id,file_path,kind=handle_uploaded_file(self.request.FILES['style_center_binary'],name,jn("qr_template","center"))
                res2=CommonResourceModel(id_md5=file_id,kind=kind)
                res2.save()
                model.style_center_binary=res2
                sysarg.append(file_id)

            if self.request.FILES.has_key('style_script'):
                file_id,file_path,kind=handle_uploaded_file(self.request.FILES['style_script'],name,jn("qr_template","script"))
                res3=CommonResourceModel(id_md5=file_id,kind=kind)
                res3.save()
                model.style_script=res3
                sysarg.append(file_id)


            model.save()

            self.ret["file_id"]=sysarg
        except Exception,e:
            self.ret["error"]=e

class CardResourceUpload(object):
    def __init__(self,request,ret):
        self.request=request
        self.ret=ret
    class UploadForm(forms.Form):
        card_res=forms.FileField(required=True)
    def upload(self,uf):
        [id_md5,server_path,kind]=handle_uploaded_file(self.request.FILES['card_res'],str(time.time()),"card_res")
        url_path=server_path[7:]
        res=CommonResourceModel(id_md5=id_md5,kind=kind)
        res.save()
        self.ret["id"]=id_md5

def common_upload(request,action):
    if not request.user.is_authenticated():
        ret={"error":403}
        return HttpResponse(json.dumps(ret), content_type="application/json")

    act2class={
        "avatar":UserAvatarUpload,
        "qr_style":QRStyleUpload,
        "card_resource":CardResourceUpload,
    }
    ret={"error":0}
    common_upload_class=act2class[action](request,ret)
    common_upload_form=common_upload_class.UploadForm

    if request.method == "POST":
        uf = common_upload_form(request.POST,request.FILES)
        if uf.is_valid():
            common_upload_class.upload(uf)
            ret=common_upload_class.ret
        else:
            ret={"error":401}

        ret["time"]=int(round(time.time() * 1e3)/1e3)
        return HttpResponse(json.dumps(ret), content_type="application/json")
    else:
        uf = common_upload_form()
        return render_to_response('common_upload.html',{'uf':uf})

# TODO:
def password_change():
    res={'error':-1}
    if (request.method=='POST'):
        res['error']=0
        if not request.user.is_authenticated():
            res['error']=0
        else:
            request.user.set_password()

    return HttpResponse(json.dumps(res), content_type="application/json")


class QRArriseDownload(object):
    def __init__(self,request):
        self.request=request
    class Form(forms.Form):
        choice=[]
        QRStyles=QRStyleModel.objects.all()
        for QRStyle in QRStyles:
            choice.append( (QRStyle.name,QRStyle.name) )

        qr_style = forms.ChoiceField(choices=choice)
        channel=forms.CharField(required=True)
        num=forms.IntegerField(required=True)
    def download(self,uf):
        qr_style_name = uf.cleaned_data['qr_style']
        qr_channel = uf.cleaned_data['channel']
        num = uf.cleaned_data['num']
        qr_style_model=QRStyleModel.objects.get(name=qr_style_name)

        qr_list=[]
        qr_content=[]
        for i in range(0,num):
            qr_id=hashlib.md5(str(time.time())+str(i)).hexdigest()
            qr_list.append(QRCodeModel(channel=qr_channel,style=qr_style_model,unique_id=qr_id))
            qr_content.append(qr_id)

        QRCodeModel.objects.bulk_create(qr_list)

        qr_context_path=jn("qr_gift","static","qrlist","qrlist.txt" )
        qr_context=open(qr_context_path,"w")
        qr_context.write( "\n".join(qr_content) )
        qr_context.close()

        # Open StringIO to grab in-memory ZIP contents
        s = StringIO.StringIO()
        # The zip compressor
        zf = zipfile.ZipFile(s, "w")

        if qr_style_model.style_border_binary:
            filename = qr_style_model.style_border_binary.id_md5+".png"
            fpath = jn("qr_gift","static","qr_template","border",filename)
            zf.write(fpath, "border.png")
        if qr_style_model.style_center_binary:
            filename = qr_style_model.style_center_binary.id_md5
            fpath = jn("qr_gift","static","qr_template","center",qr_style_model.style_border_binary.id_md5+".png")
            zf.write(fpath, "center.png")

        filename = qr_style_model.style_script.id_md5
        fpath = jn("qr_gift","static","qr_template","script",qr_style_model.style_script.id_md5+".py")
        zf.write(fpath, "script.py")
        zf.write(qr_context_path, "list.txt")
        zf.close()
        resp = HttpResponse(s.getvalue(), content_type = "application/x-zip-compressed")
        resp['Content-Disposition'] = 'attachment; filename={0}.zip'.format(qr_style_name)
        os.remove(qr_context_path)
        return resp

def common_download(request,action):
    if not request.user.is_authenticated():
        ret={"error":403}
        return HttpResponse(json.dumps(ret), content_type="application/json")

    act2class={
        "qr_arrise":QRArriseDownload,
    }
    #  ret={"error":0}
    common_download_class=act2class[action](request)
    common_download_form=common_download_class.Form

    if request.method == "POST":
        uf = common_download_form(request.POST,request.FILES)
        if uf.is_valid():
            ret=common_download_class.download(uf)
        #  else:
            #  ret={"error":401}

        #  ret["time"]=int(round(time.time() * 1e3)/1e3)
            return ret
    else:
        uf = common_download_form()
        return render_to_response('common_upload.html',{'uf':uf})

def qr_arrise(request):
    if not request.user.is_authenticated():
        return HttpResponse("need super user!")
    if request.method == "POST":
        uf = QR_Form(request.POST)
        if uf.is_valid():
            pass
    else:
        uf = QR_Form()
    return render_to_response('qr_arrise.html',{'uf':uf})


def api(request):
    ret={"error":0}

    if request.method!='POST':
        ret["error"]=400
    post_data=json.loads(request.body)
    if ret["error"]==0 and not "action" in post_data:
        ret["error"]=402
        ret["field"]="action"

    #  try:
        #  request_action=post_data["action"]
        #  print request_action
        #  request_action_func_list={
            #  "user_register":register,
            #  "user_login":login,
            #  "user_logout":logout,
            #  "user_info":user_info,
            #  "user_edit_profile":user_edit_profile,
            #  "qr_query":qr_query,
        #  }
        #  if ret["error"]==0 and not request_action in request_action_func_list.keys():
            #  ret["error"]=404

        #  if ret["error"]==0:
            #  ret=request_action_func_list[request_action](request,post_data,ret)
    #  except Exception,e:
        #  ret["error"]=e
    #  finally:
        #  ret["time"]=int(round(time.time() * 1e3)/1e3)
        #  return HttpResponse(json.dumps(ret), content_type="application/json")

    request_action=post_data["action"]
    print request_action
    request_action_func_list={
        "user_register":register,
        "user_login":login,
        "user_logout":logout,
        "user_info":user_info,
        "user_edit_profile":user_edit_profile,
        "qr_query":qr_query,
        "card_edit":card_edit,
        "card_create":card_create,
        "card_query":card_query,
    }
    if ret["error"]==0 and not request_action in request_action_func_list.keys():
        ret["error"]=404

    if ret["error"]==0:
        ret=request_action_func_list[request_action](request,post_data,ret)

    ret["time"]=int(round(time.time() * 1e3)/1e3)
    return HttpResponse(json.dumps(ret), content_type="application/json")

def qr_style_upload(request):
    if request.method == "POST":
        uf = UserForm(request.POST,request.FILES)
        if uf.is_valid():
            name = uf.cleaned_data['name']
            try:
                model=QRStyleModel(name=name)
                sysarg=[]
                if request.FILES.has_key('style_border_binary'):
                    file_path=handle_uploaded_file(request.FILES['style_border_binary'],name,jn("qr_template","border"))
                    file_path=file_path[7:]
                    res1=CommonResourceModel(origin_url=file_path)
                    res1.save()
                    model.style_border_binary=res1
                    sysarg.append(file_path)

                if request.FILES.has_key('style_center_binary'):
                    file_path=handle_uploaded_file(request.FILES['style_center_binary'],name,jn("qr_template","center"))
                    file_path=file_path[7:]
                    res2=CommonResourceModel(origin_url=file_path)
                    res2.save()
                    model.style_center_binary=res2
                    sysarg.append(file_path)

                if request.FILES.has_key('style_script'):
                    file_path=handle_uploaded_file(request.FILES['style_script'],name,jn("qr_template","script"))
                    file_path=file_path[7:]
                    res3=CommonResourceModel(origin_url=file_path)
                    res3.save()
                    model.style_script=res3
                    sysarg.append(file_path)

                if request.FILES.has_key('Sytle_'):
                    file_path=handle_uploaded_file(request.FILES['style_script'],name,jn("qr_template","script"))
                    file_path=file_path[7:]
                    res3=CommonResourceModel(origin_url=file_path)
                    res3.save()
                    model.style_script=res3
                    sysarg.append(file_path)


                model.save(args)

                return HttpResponse(sysarg)
            except Exception,e:
                return HttpResponse(e)

    else:
        uf = UserForm()
    return render_to_response('qr_style_upload.html',{'uf':uf})

